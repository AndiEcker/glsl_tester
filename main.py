"""
GlslTester - play with glsl shaders
===================================

Write, compile and run glsl shader code on any platform supported by Kivy.
"""
import os
from typing import List, Tuple, Union, cast

# noinspection PyProtectedMember
from kivy._clock import ClockEvent
from kivy.clock import Clock
from kivy.core.window import Window
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


__version__ = '0.1.16'


HIST_TOUCH_MAX = 3

PosValType = Tuple[float, float]


def field_calc_key(value: PosValType, matrix: str, key: str) -> PosValType:
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


class ShaderArgInput(BoxLayout):
    """ layout containing label and text input for to edit the value of a shader argument. """
    arg_name = StringProperty()


class ShaderButton(FlowButton):
    """ declare big_shader_id as ObjectProperty to keep reference (no shallow copy/DictProperty). """
    big_shader_id = ObjectProperty()


class GlslTesterApp(SideloadingMainAppMixin, KivyMainApp):
    """ main app class. """
    e_field_pos: PosValType                 #: e-key input field
    hist_touch: List[PosValType]            #: last touch history
    i_field_pos: PosValType                 #: i-key input field
    last_key: float                         #: last key ord code
    last_touch: PosValType                  #: last touch event: init=DefaultTouch(), update=RenderWidget.on_touch_down
    mouse_pos: PosValType                   #: current mouse pointer position in the shader widget
    next_shader: str                        #: non-persistent app state holding the code of the next shader to add
    render_frequency: float                 #: renderer tick timer frequency
    render_widget: ShadersMixin             #: widget for to display shader output
    shader_filename: str                    #: current shader filename app state

    _shader_tick_timer: ClockEvent = None

    def input_callables(self):
        """ return dict of all input callables for to feed shader args. """
        ren_wid = cast(Widget, self.render_widget)

        ica = dict(
            c=lambda: Clock.get_boottime(),
            e=lambda: main_app.e_field_pos,
            i=lambda: main_app.i_field_pos,
            K=lambda: main_app.last_key,
            k=lambda: main_app.last_key / 255.0,
            L=lambda: main_app.last_touch,
            l=lambda: (main_app.last_touch[0] / ren_wid.width, main_app.last_touch[1] / ren_wid.height),
            M=lambda: main_app.mouse_pos,
            m=lambda: (main_app.mouse_pos[0] / ren_wid.width, main_app.mouse_pos[1] / ren_wid.height),
            s=lambda: main_app.sound_volume,
            v=lambda: main_app.vibration_volume,
        )

        hist_len = min(HIST_TOUCH_MAX, len(main_app.hist_touch))

        def _bind_idx(_i):  # def-_i-bind to prevent that the last idx value of the range is used when the lambda runs
            return lambda: main_app.hist_touch[_i]      # .. s.a. https://stackoverflow.com/questions/36805071
        ica.update({'H' + str(idx + 1): _bind_idx(idx) for idx in range(hist_len)})
        ica.update({'H_' + str(abs(idx)): _bind_idx(idx) for idx in range(-hist_len, 0)})

        def _bind_idx_idx(_i):
            return lambda: (main_app.hist_touch[_i][0] / ren_wid.width, main_app.hist_touch[_i][1] / ren_wid.height)
        ica.update({'h' + str(idx + 1): _bind_idx_idx(idx) for idx in range(hist_len)})
        ica.update({'h_' + str(abs(idx)): _bind_idx_idx(idx) for idx in range(-hist_len, 0)})

        return ica

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
        ini_sca_val = 0.501
        ini_pos_val = (ini_sca_val, ini_sca_val)
        self.e_field_pos = ini_pos_val
        self.hist_touch = list()
        self.i_field_pos = ini_pos_val
        self.last_key = ini_sca_val
        self.last_touch = ini_pos_val
        self.mouse_pos = ini_pos_val
        self.render_widget = self.framework_root.ids.render_widget
        self.update_shader_file()

        Window.bind(mouse_pos=self.on_mouse_pos)
        self.on_render_frequency()
        self.update_input_values()
        Clock.schedule_interval(lambda *_args: self.update_input_values(), 0.999999)

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
        ren_wid: Widget = cast(Widget, self.render_widget)
        if ren_wid.collide_point(*ren_wid.to_widget(*pos)):
            self.vpo(f"GlslTesterApp.on_mouse_pos({_instance}, {pos})")
            self.mouse_pos: Tuple[float, ...] = tuple(map(float, pos))      # real type: PosValType
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
        glo_vars.update(Clock=Clock, Window=Window, _add_base_globals=True)
        glo_vars.update(self.input_callables())

        for arg_name in self.shader_arg_names():
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
        next_shader = self.next_shader
        idx = next_shader.find(" " + arg_name + ";")
        if idx >= 0:
            line = next_shader[idx + len(arg_name) + 2:next_shader.find("\n", idx)]
            idx = line.find("// ")
            if idx >= 0:
                arg_name = line[idx + 3:]
        return arg_name

    def shader_arg_names(self, *_args):
        """ shader arg names of the shader code in the loaded shader file.

        :param _args:           unused here - but needed in kv for to bind expression to kivy property
        :return:                tuple of shader arg names of the currently loaded shader code, plus the
                                `start_time` argument which controls, independent from to be included in the shader
                                code, how the `time` argument get prepared/corrected in each render frame (see also
                                :paramref:`ae.kivy_glsl.ShadersMixin.add_shader.start_time` and i18n help texts).
        """
        return (arg_name for arg_name in self.get_var('render_shader_args')
                if arg_name == 'start_time' or " " + arg_name + ";" in self.next_shader)

    def update_input_values(self):
        """ display input values. """
        def _v_f(k_: str, val: Union[float, Tuple[float, ...]]) -> str:
            if isinstance(val, float):
                dig = 3 if k_.islower() else 0
                return f"{val:.{dig}f}"
            return ",".join(_v_f(k_, v_) for v_ in val)

        ica = self.input_callables()
        self.framework_root.ids.input_values.text = "   ".join(k + "=" + _v_f(k, v()) for k, v in ica.items())

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
    main_app = GlslTesterApp(app_name='glsl_tester', multi_threading=True)

    PATH_PLACEHOLDERS['glsl'] = scripts_path = os.path.join(norm_path("{ado}"), "glsl")
    check_moves("glsl", scripts_path)
    for name, code in BUILT_IN_SHADERS.items():
        write_file_text(code, os.path.join(scripts_path, f"{name}.fs.glsl"))

    PATH_PLACEHOLDERS['sug'] = sug_path = os.path.join(norm_path("{ado}"), "sug")
    check_moves("sug", sug_path)

    main_app.run_app()
