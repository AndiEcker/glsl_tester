"""
GlslTester - play with glsl shaders
===================================

Write, compile and run glsl shader code on any platform supported by Kivy.
"""
import os
from typing import Tuple, cast

# noinspection PyProtectedMember
from kivy._clock import ClockEvent
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.input import MotionEvent
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

# noinspection PyUnresolvedReferences
import ae.droid
from ae.base import UNSET
from ae.files import read_file_text, write_file_text
from ae.paths import PATH_PLACEHOLDERS, norm_path
from ae.inspector import try_eval
from ae.updater import check_moves
from ae.gui_app import EventKwargsType
from ae.kivy_app import FlowButton, KivyMainApp, get_txt
from ae.kivy_glsl import ShadersMixin, BUILT_IN_SHADERS
from ae.kivy_sideloading import SideloadingMainAppMixin


__version__ = '0.0.10'


def field_calc_key(value: Tuple[float, float], matrix: str, key: str) -> Tuple[float, float]:
    """
    :param value:               current field value.
    :param matrix:              field char matrix.
    :param key:                 input key character
    :return:                    new field value.
    """
    idx = matrix.find(key)
    if idx == 4:
        return 0.0, 0.0
    if idx != -1:
        return value[0] + (idx % 3 - 1) / 10.0, value[1] + (int(idx / 3) - 1) / 10.0
    return value


class DefaultTouch(MotionEvent):
    """ default touch for to set main_app.last_touch on app startup. """
    def depack(self, args):
        """ pass init args to this touch event. """
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        super().depack(args)


class ShaderArgInput(BoxLayout):
    """ layout containing label and text input for to edit the value of a shader argument. """
    arg_name = StringProperty()


class ShaderButton(FlowButton):
    """ declare big_shader_id as ObjectProperty to keep reference (no shallow copy/DictProperty). """
    big_shader_id = ObjectProperty()


class GlslTesterApp(SideloadingMainAppMixin, KivyMainApp):
    """ main app class. """
    e_field_pos: Tuple[float, float]        #: e-key input field
    i_field_pos: Tuple[float, float]        #: i-key input field
    last_key: float                         #: last key ord code
    last_touch: MotionEvent                 #: last touch event: init=DefaultTouch(), update=RenderWidget.on_touch_down
    mouse_pos: Tuple[float, float]          #: current mouse pointer position in the shader widget
    next_shader: str                        #: non-persistent app state holding the code of the next shader to add
    render_frequency: float                 #: renderer tick timer frequency
    render_widget: ShadersMixin             #: widget for to display shader output
    shader_filename: str                    #: current shader filename app state

    _shader_tick_timer: ClockEvent = None

    def key_press_from_framework(self, modifiers: str, key: str) -> bool:
        """ dispatch key press event, coming normalized from the UI framework.

        :param modifiers:       modifier keys.
        :param key:             key character.
        :return:                True if key got consumed/used else False.
        """
        try:
            self.last_key = float(ord(key))
        except (TypeError, ValueError, SyntaxError):
            pass

        self.e_field_pos = field_calc_key(self.e_field_pos, "sdfwer234", key)
        self.i_field_pos = field_calc_key(self.i_field_pos, "jkluio789", key)

        self.update_input_values()

        return super().key_press_from_framework(modifiers, key)

    def on_app_start(self):
        """ ensure that the non-persistent app states are available before widget tree build. """
        super().on_app_start()
        self.change_app_state('next_shader', "")  # self.next_shader = self.framework_app.app_states['next_shader'] = ""

    def on_app_started(self):
        """ initialize render_widget after kivy app and window got initialized. """
        super().on_app_started()

        if not self.framework_app.app_states.get('file_chooser_initial_path', ""):
            self.change_app_state('file_chooser_initial_path', norm_path("{glsl}"))
        self.e_field_pos = (0.0, 0.0)
        self.i_field_pos = (0.0, 0.0)
        self.last_key = 0.0
        self.last_touch = DefaultTouch("default_touch", 1, {"x": .5, "y": .5})
        self.mouse_pos = (0.0, 0.0)
        self.render_widget = self.framework_root.ids.render_widget
        self.update_shader_file()

        Window.bind(mouse_pos=self.on_mouse_pos)
        self.on_render_frequency()

    def on_file_chooser_submit(self, file_path: str, chooser_popup: Widget):
        """ event callback from FileChooserPopup.on_submit() on selection of the next shader file to be added.

        :param file_path:       path string of selected file.
        :param chooser_popup:   file chooser popup/container widget.
        """
        if chooser_popup.submit_to != 'shader_filename':    # == 'sideloading_file_mask':
            # super().on_file_chooser_submit(file_path, chooser_popup)  # pass selected file to SideloadingMainAppMixin
            return
        if not os.path.isfile(file_path):
            self.show_message(get_txt("{file_path} is not a shader file"), title=get_txt("select single file"))
            return

        self.change_app_state('shader_filename', file_path)
        chooser_popup.register_file_path(file_path, self)
        chooser_popup.dismiss()

    def on_mouse_pos(self, _instance, pos):
        """ Window mouse position event handler. """
        self.vpo(f"GlslTesterApp.on_mouse_pos({_instance}, {pos})")
        render_widget: Widget = cast(Widget, self.render_widget)
        if render_widget.collide_point(*render_widget.to_widget(*pos)):
            self.mouse_pos: Tuple[float, ...] = tuple(map(float, pos))
            self.update_input_values()

    def on_tool_box_toggle(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ toggle between display and hide of tool box.

        :param _flow_key:       unused/empty flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                always True for to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_tool_box_toggle")
        tool_box = self.framework_root.ids.tool_box
        tool_box.visible = not tool_box.visible
        return True

    def on_renderer_add(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ add renderer shader to self.render_widget.

        :param _flow_key:       unused/empty flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                True for to confirm change of flow id else False.
        """
        title = get_txt("add shader error")
        shader_filename = self.shader_filename
        if not os.path.exists(shader_filename):
            self.show_message(get_txt("shader file {shader_filename} not found"), title=title)
            return False

        shader_code = read_file_text(shader_filename)   # reload because self.next_shader could already be outdated
        self.change_app_state('next_shader', shader_code)
        if not shader_code:
            self.show_message(get_txt("empty shader code file {shader_filename}"), title=title)
            return False

        kwargs = dict(time=0.0, update_freq=0.0)

        if ".fs" in shader_filename:
            kwargs['shader_code'] = shader_code
        else:
            kwargs['shader_file'] = shader_filename
            if self.debug:
                lower_code = shader_code.lower()
                if "---vertex" not in lower_code or "---fragment" not in lower_code:
                    self.show_message(get_txt("no vertex/fragment sections in shader {shader_filename}"), title=title)
                    return False

        glo_vars = globals().copy()     # contains main_app variable from module level
        glo_vars.update(
            Clock=Clock, Window=Window, _add_base_globals=True,
            c=lambda: Clock.get_boottime(),
            e=lambda: main_app.e_field_pos,
            i=lambda: main_app.i_field_pos,
            k=lambda: main_app.last_key,
            L=lambda: tuple(map(float, main_app.last_touch)),
            l=lambda: (float(main_app.last_touch[0] / Window.width), float(main_app.last_touch[1] / Window.height)),
            M=lambda: tuple(map(float, main_app.mouse_pos)),
            m=lambda: (float(main_app.mouse_pos[0] / Window.width), float(main_app.mouse_pos[1] / Window.height)),
            s=lambda: main_app.sound_volume,
            v=lambda: main_app.sound_volume,
        )
        shader_args = self.get_var('render_shader_args')
        for arg_name in shader_args:
            arg_inp = getattr(self, 'shader_arg_' + arg_name, UNSET)
            if arg_inp is UNSET:
                self.show_message(get_txt("missing 'shader_arg_{arg_name}' app state"), title=title)
                return False
            if not arg_inp:
                self.vpo(f"   #  skipping empty shader argument {arg_name}")
                continue

            arg_val = try_eval(arg_inp, ignored_exceptions=(Exception, ), glo_vars=glo_vars)
            if arg_val is UNSET:
                self.show_message(get_txt("invalid expression in shader argument {arg_name}={arg_inp}"), title=title)
                return False

            kwargs[arg_name] = arg_val

        self.render_widget.add_shader(**kwargs)

        self._update_registered_renderers()

        return True

    def on_renderer_del(self, _flow_key: str, event_kwargs: EventKwargsType) -> bool:
        """ remove renderer from self.render_widget.

        :param _flow_key:       unused flow key.
        :param event_kwargs:    event kwargs with 'shader_args' item containing the shader kwargs.
        :return:                always True for to confirm change of flow id.
        """
        shader_id = event_kwargs['big_shader_id']
        self.vpo("GlslTesterApp.on_renderer_del", shader_id)
        self.render_widget.del_shader(shader_id)
        self._update_registered_renderers()
        return True

    def on_render_frequency(self):
        """ render frequency changed event handler. """
        prf = self.render_frequency
        self.vpo(f"GlslTesterApp.on_render_frequency(): frequency={prf}Hz")
        if self._shader_tick_timer:
            Clock.unschedule(self._shader_tick_timer)
        if prf > self.get_var('render_frequency_min'):
            self._shader_tick_timer = Clock.schedule_interval(self.render_tick, 1 / prf)

    def render_tick(self, *_args):
        """ timer for the animation of the running shaders. """
        render_widget = self.render_widget
        render_widget.next_tick()
        try:
            render_widget.refresh_started_shaders()
        except (NameError, ValueError, Exception) as ex:
            self.render_frequency = 0.0
            self.on_render_frequency()
            self.show_message(str(ex), title=get_txt("animation exception - stopped"))

    def shader_arg_alias(self, arg_name: str) -> str:
        """ check for alias for the passed shader argument name.

        :param arg_name:        shader arg name.
        :return:                alias (if found) or shader arg name (if not).
        """
        next_shader = self.framework_app.app_states['next_shader']
        idx = next_shader.find(" " + arg_name + ";")
        if idx >= 0:
            line = next_shader[idx + len(arg_name) + 2:next_shader.find("\n", idx)]
            idx = line.find("// ")
            if idx >= 0:
                arg_name = line[idx + 3:]
        return arg_name

    def update_input_values(self):
        """ display input values. """
        wid: Widget = cast(Widget, self.render_widget)
        self.framework_root.ids.input_values.text = \
            f"Inputs:" \
            f"  ex={self.e_field_pos[0]:.3f}  ey={self.e_field_pos[1]:.3f}" \
            f"  ix={self.i_field_pos[0]:.3f}  iy={self.i_field_pos[1]:.3f}" \
            f"  k={self.last_key:.0f}" \
            f"  lx={self.last_touch.x / wid.width:.3f}  ly={self.last_touch.y / wid.height:.3f}" \
            f"  Lx={self.last_touch.x:.0f}  Ly={self.last_touch.y:.0f}" \
            f"  mx={self.mouse_pos[0] / wid.width:.3f}  my={self.mouse_pos[1] / wid.height:.3f}" \
            f"  Mx={self.mouse_pos[0]:.0f}  My={self.mouse_pos[1]:.0f}" \
            f"  c={Clock.get_boottime():.1f}"

    def _update_registered_renderers(self):
        """ update the running shaders buttons after add/delete of a running shader. """
        shaders = self.render_widget.started_shaders
        registered = list()
        for shader_id in shaders:
            kwargs = shader_id.copy()
            kwargs['glsl_dyn_args'].pop('time', None)
            kwargs['update_freq'] = 30.0
            kwargs['_shader_id'] = shader_id
            registered.append(kwargs)
        self.framework_root.ids.running_shaders.registered_renderers = registered

    def update_shader_file(self):
        """ shader file changed event handler. """
        file_name = self.shader_filename
        self.change_app_state('next_shader', read_file_text(file_name) if os.path.exists(file_name) else "")


if __name__ == '__main__':
    main_app = GlslTesterApp(app_name='glsltester', multi_threading=True)

    PATH_PLACEHOLDERS['glsl'] = scripts_path = os.path.join(norm_path("{ado}"), "glsl")
    check_moves("glsl", scripts_path)
    for name, code in BUILT_IN_SHADERS.items():
        write_file_text(code, os.path.join(scripts_path, f"{name}.fs.glsl"))

    PATH_PLACEHOLDERS['sug'] = sug_path = os.path.join(norm_path("{ado}"), "sug")
    check_moves("sug", sug_path)

    main_app.run_app()
