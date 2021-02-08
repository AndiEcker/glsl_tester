"""
GlslTester - play with glsl shaders
===================================

Write, compile and run glsl shader code on any platform supported by Kivy.
"""
import os
from typing import Callable, Tuple, cast

from ae.base import UNSET
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.input import MotionEvent
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

# noinspection PyUnresolvedReferences
import ae.droid
from ae.files import read_file_text, write_file_text
from ae.paths import PATH_PLACEHOLDERS, norm_path
from ae.inspector import try_eval
from ae.updater import check_moves
from ae.gui_app import EventKwargsType
from ae.kivy_app import KivyMainApp, get_txt
from ae.kivy_glsl import ShadersMixin, circled_alpha_shader_code, touch_wave_shader_code, plasma_hearts_shader_code


__version__ = '0.0.3'


BUILT_IN_SHADERS = dict(
    circled_alpha=circled_alpha_shader_code, touch_wave=touch_wave_shader_code, plasma_hearts=plasma_hearts_shader_code)


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


class GlslTesterApp(KivyMainApp):
    """ main app class. """
    mouse_pos: Tuple[float, float]          #: current mouse pointer position in the render widget
    last_touch: MotionEvent                 #: last touch event: init=DefaultTouch(), update=RenderWidget.on_touch_down
    next_shader: str                        #: non-persistent app state holding the code of the next shader to add
    on_render_shader_frequency: Callable    #: event handler patched to self._render_shader_restart
    render_shader_frequency: float          #: pending requests timer frequency
    render_widget: ShadersMixin             #: widget for to display shader output
    shader_filename: str                    #: current shader filename app state

    def on_app_start(self):
        """ ensure that the non-persistent app states are available before widget tree build. """
        super().on_app_start()
        self.change_app_state('next_shader', "")  # self.next_shader = self.framework_app.app_states['next_shader'] = ""

    def on_app_started(self):
        """ initialize render_widget after kivy app and window got initialized. """
        super().on_app_started()

        # redirect handler for change of render_shader_frequency app state from user preferences menu
        self.on_render_shader_frequency = self._render_shader_restart

        self.mouse_pos = (0.0, 0.0)
        self.last_touch = DefaultTouch("default_touch", 1, {"x": .5, "y": .5})
        self.render_widget = self.framework_root.ids.render_widget
        self.update_shader_file()

        Window.bind(mouse_pos=self.on_mouse_pos)
        self._render_shader_restart()

    def on_file_chooser_submit(self, file_path: str, chooser_popup: Widget):
        """ event callback from FileChooserPopup.on_submit() on selection of the next shader file to be added.

        :param file_path:       path string of selected file.
        :param chooser_popup:   file chooser popup/container widget.
        """
        if not os.path.isfile(file_path):
            self.show_message(get_txt("{file_path} is not a shader file"), title=get_txt("select single file"))
            file_path = ""

        self.change_app_state('shader_filename', file_path)
        chooser_popup.dismiss()

    def on_mouse_pos(self, _instance, pos):
        """ Window mouse position event handler. """
        self.vpo(f"GlslTesterApp.on_mouse_pos({_instance}, {pos})")
        render_widget: Widget = cast(Widget, self.render_widget)
        if render_widget.collide_point(*render_widget.to_widget(*pos)):
            self.mouse_pos: Tuple[float, ...] = tuple(map(float, pos))

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
        shader_code = self.next_shader  # read_file_text(shader_filename)
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
        glo_vars.update(Clock=Clock, mouse=self.mouse_pos, touch=self.last_touch, Window=Window, _add_base_globals=True)
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
                self.show_message(get_txt("invalid expression in shader argument {arg_name}"), title=title)
                return False

            kwargs[arg_name] = arg_val

        # noinspection PyUnusedLocal
        try:
            self.render_widget.add_renderer(**kwargs)
        except (ValueError, Exception) as ex:
            self.show_message(get_txt("shader compilation/start failed: {ex}"), title=title)
            return False

        self._update_registered_renderers()
        return True

    def on_renderer_del(self, renderer_idx: str, _event_kwargs: EventKwargsType) -> bool:
        """ remove renderer from self.render_widget.

        :param renderer_idx:    index of the renderer to remove.
        :param _event_kwargs:   unused event kwargs.
        :return:                always True for to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_renderer_del", renderer_idx)
        self.render_widget.del_renderer(int(renderer_idx))
        self._update_registered_renderers()
        return True

    def _render_shader_restart(self):
        prf = self.render_shader_frequency
        self.vpo(f"GlslTesterApp.on_render_shader_frequency/_render_shader_restart(): frequency={prf}Hz")
        Clock.unschedule(self.render_shader_tick)
        if prf > self.get_var('render_shader_frequency_min'):
            Clock.schedule_interval(self.render_shader_tick, 1 / prf)

    def render_shader_tick(self, *_args):
        """ timer for the animation of the running shaders. """
        render_widget = self.render_widget
        render_widget.next_tick()
        try:
            render_widget.refresh_renderers()
        except (NameError, ValueError, Exception) as ex:
            self.render_shader_frequency = 0.0
            self._render_shader_restart()
            self.show_message(str(ex), get_txt("animation exception - stopped"))

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

    def update_debug_shader(self, shader_button: Widget):
        """ update the extra debug shader, visible only in debug mode.

        :param shader_button:   instance of the FlowButton for to delete/remove a running shader.
        """
        if shader_button.parent:
            if not self.debug_level:
                return
            screen_shader_dict = self.render_widget.renderers[int(shader_button.text)]
            kwargs = dict()
            if screen_shader_dict['shader_file']:
                kwargs['shader_file'] = screen_shader_dict['shader_file']
            else:
                kwargs['shader_code'] = screen_shader_dict['shader_code']
            shader_button.debug_shader_idx = shader_button.add_renderer(**kwargs, **screen_shader_dict['glsl_dyn_args'])
        else:
            shader_button.del_renderer(shader_button.debug_shader_idx)

    def _update_registered_renderers(self):
        """ update the running shaders buttons after add/delete of a running shader. """
        renderers = self.render_widget.renderers
        registered = list()
        for idx, renderer in enumerate(renderers):
            if not renderer['deleted']:
                renderer['renderer_idx'] = idx
                registered.append(renderer)
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
        write_file_text(code, os.path.join(scripts_path, f"{name}.fs.txt"))

    PATH_PLACEHOLDERS['sug'] = sug_path = os.path.join(norm_path("{ado}"), "sug")
    check_moves("sug", sug_path)

    main_app.run_app()
