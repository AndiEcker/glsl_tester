"""
GlslTester - play with glsl shaders
===================================

run glsl shader code on any platform supported by Kivy.
"""
import os
# WARNING: uncommenting next line produces thousands of log lines per second:
# os.environ['KIVY_GL_DEBUG'] = '1'

from typing import Any, Dict, List, Tuple, Union, cast

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
from ae.gui_app import APP_STATE_SECTION_NAME, EventKwargsType
from ae.kivy_app import FlowButton, KivyMainApp, get_txt
from ae.kivy_glsl import BUILT_IN_SHADERS, DEFAULT_FPS, ShaderIdType, shader_parameters, ShadersMixin
from ae.kivy_sideloading import SideloadingMainAppMixin


__version__ = '0.2.21'


HIST_TOUCH_MAX = 3

PosValType = Tuple[float, float]


def field_calc_key(value: PosValType, matrix: str, key: str) -> PosValType:
    """ de-/increment x, y component of `value` by 0.1 if pressed `key` is in key `matrix`.

    :param value:               current field value: relative position (x, y) tuple; x/y values between 0.0 and 1.0.
    :param matrix:              field char matrix: 9 chars/keys from bottom/left (-0.1, -0.1) to top/right (+0.1, +0.1).
    :param key:                 pressed key character.
    :return:                    unchanged or de-/incremented field value.
    """
    idx = matrix.find(key)
    if idx == 4:
        return 0.0, 0.0
    if idx != -1:
        return value[0] + (idx % 3 - 1) / 10.0, value[1] + (int(idx / 3) - 1) / 10.0
    return value


class ShaderArgInput(BoxLayout):
    """ layout containing label and text input to edit the value of a shader argument. """
    arg_name = StringProperty()


class ShaderButton(FlowButton):
    """ declare big_shader_id as ObjectProperty to keep reference (no shallow copy/DictProperty). """
    big_shader_id = ObjectProperty()


class GlslTesterApp(SideloadingMainAppMixin, KivyMainApp):
    """ main app class. """
    e_field_pos: PosValType                         #: e-key input field
    hist_touch: List[PosValType]                    #: last touch history
    i_field_pos: PosValType                         #: i-key input field
    last_key: float                                 #: last key ord code
    last_touch: PosValType                          #: event-init=DefaultTouch(), -update=RenderWidget.on_touch_down
    mouse_pos: PosValType                           #: current mouse pointer position in the shader widget
    next_shader: str                                #: code of the next shader to add (non-persistent app state)
    render_frequency: float = DEFAULT_FPS           #: shader tick timer frequency app state
    render_widget: ShadersMixin                     #: widget to display shader output
    shaders_args: List[Dict[str, str]] = list()     #: arguments for added shaders (app state)
    shaders_idx: int = 0                            #: currently editable/selected shader (app state)

    _shader_tick_timer: ClockEvent = None

    def _init_default_user_cfg_vars(self):
        """ add/initialize user-specific app states of this app. """
        super()._init_default_user_cfg_vars()
        self.user_specific_cfg_vars |= {
            (APP_STATE_SECTION_NAME, 'render_frequency'),
            (APP_STATE_SECTION_NAME, 'shaders_args'),
            (APP_STATE_SECTION_NAME, 'shaders_idx'),
        }

    def add_shader_to_render_widget(self) -> bool:
        """ add the currently selected shader to the render widget - even on error in args or file name.

        :return:                True if no error occurred and shader got added, else False.
        """
        shader_args = self.shaders_args[self.shaders_idx]
        shader_id = dict(run_state=shader_args['run_state'], time=0.0, update_freq=0.0)
        errors = list()

        errors.extend(self.eval_and_push_shader_file(shader_args, shader_id))
        if not errors:
            errors.extend(self.eval_and_push_shader_args(shader_args, shader_id))

        self.render_widget.add_shader(**shader_id)

        if errors:
            err_msg = "\n".join(errors)
            self.show_message(err_msg, title=get_txt("shader {self.shaders_idx} error(s)", count=len(errors)))
            self.change_shader_arg('run_state', 'error', error_message=err_msg)

        shader_id['run_state'] = shader_args['run_state']

        return not errors

    def change_shader_arg(self, arg_name: str, value: str, error_message: str = ""):
        """ change value of a single shader argument in shaders_args app state and shader id of selected shader.

        :param arg_name:        shader argument name.
        :param value:           shader argument value to set/change.
        :param error_message:   error message string (passed to shader arg `error_message` if arg_name=='run_state')
        :return:
        """
        shader_args = self.shaders_args[self.shaders_idx]
        shader_id = self.id_of_selected_shader()

        shader_args[arg_name] = value
        self.change_app_state('shaders_args', self.shaders_args)

        if arg_name == 'run_state':
            shader_id['run_state'] = value
            shader_id['error_message'] = error_message
        else:
            if arg_name == 'shader_filename':
                errors = self.eval_and_push_shader_file(shader_args, shader_id)
            else:
                errors = self.eval_and_push_shader_args(shader_args, shader_id)
            if errors and shader_args['run_state'] == 'running':
                err_msg = "\n".join(errors)
                self.show_message(err_msg, title=get_txt("shader {self.shaders_idx} error(s)", count=len(errors)))
                self.change_shader_arg('run_state', 'error', error_message=err_msg)
            elif not errors and shader_args['run_state'] == 'error':
                self.change_shader_arg('run_state', 'running')

        self.render_widget.update_shaders()
        if shader_id['run_state'] != shader_args['run_state']:
            shader_args['run_state'] = shader_id['run_state']
            if shader_id['run_state'] == 'error':
                self.show_message(shader_id['error_message'],
                                  title=get_txt("shader {self.shaders_idx} error(s)", count=1))
        self._update_shader_buttons()

    def eval_and_push_shader_args(self, shader_args: Dict[str, str], shader_id: Dict[str, Any]) -> List[str]:
        """ evaluate shader glsl args/macros entered by user and if ok then push it to respective pre-shader-id kwarg.

        :param shader_args:     shader arguments or lambdas entered by user.
        :param shader_id:       either flat dict with all shader arguments (pre :meth:`~ShadersMixin.add_shader`) or
                                dict that got already converted to a shader id by :meth:`~ShadersMixin.add_shader` (and
                                added to :attr:`~ShadersMixin.added_shaders`).
        :return:                list of errors or empty list if no errors occurred.
        """
        errors = list()
        glo_vars = globals().copy()     # contains main_app variable from module level
        glo_vars.update(Clock=Clock, Window=Window, _add_base_globals=True)
        glo_vars.update(self.input_callables())

        for arg_name in shader_parameters(self.next_shader):
            arg_inp = shader_args.get(arg_name)
            if arg_inp is None:
                errors.append(get_txt("missing shader argument app state [b]{main_app.get_txt_(arg_name)}[/b]"))
                continue
            if not arg_inp:
                self.vpo(f"   #  skipping empty shader argument {arg_name}/{main_app.get_txt_(arg_name)}")
                continue

            arg_val = try_eval(arg_inp, ignored_exceptions=(Exception, ), glo_vars=glo_vars)
            if arg_val is UNSET:
                errors.append(
                    get_txt("invalid expression '{arg_inp}' in shader argument [b]{main_app.get_txt_(arg_name)}[/b]"))
                continue

            dic = shader_id['glsl_dyn_args'] if 'glsl_dyn_args' in shader_id and arg_name != 'start_time' else shader_id
            dic[arg_name] = arg_val

        return errors

    def eval_and_push_shader_file(self, shader_args: Dict[str, str], shader_id: Dict[str, Any]) -> List[str]:
        """ eval shader file name entered by user and if ok then push it to respective pre-shader-id kwarg.

        :param shader_args:     shader arguments or lambdas entered by user.
        :param shader_id:       shader arguments as flat dict (from user input) or as shader id (added shader).
        :return:                list of errors or empty list if no errors occurred.
        """
        errors = list()
        shader_filename = norm_path(shader_args['shader_filename'])
        shader_code = ""
        if not os.path.exists(shader_filename):
            errors.append(get_txt("shader file {shader_filename} not found"))
        else:
            shader_code = read_file_text(shader_filename)   # reload because self.next_shader could already be outdated
            if not shader_code:
                errors.append(get_txt("empty shader code file {shader_filename}"))
        self.change_app_state('next_shader', shader_code)

        if not errors:
            if ".fs" in shader_filename:
                shader_id['shader_code'] = shader_code
            else:
                shader_id['shader_file'] = shader_filename
                if self.debug:
                    lower_code = shader_code.lower()
                    if "---vertex" not in lower_code or "---fragment" not in lower_code:
                        errors.append(get_txt("no vertex/fragment sections in shader {shader_filename}"))
        return errors

    def id_of_selected_shader(self) -> ShaderIdType:
        """ determine the shader_id of the currently selected shader. """
        return self.render_widget.added_shaders[self.shaders_idx]

    def input_callables(self):
        """ return dict of all input callables to feed shader args. """
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
        ica.update({'h_' + str(-idx): _bind_idx_idx(idx) for idx in range(-hist_len, 0)})

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
        self.change_app_state('next_shader', "")  # init. to prevent key-errors in start-event-loop-kv-build

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
        self.last_key = ini_sca_val                                         # between 0.0 and 255.0 (have to be float)
        ini_pos_val = (Window.width / 2.001, Window.height / 2.001)         # window center
        self.last_touch = ini_pos_val
        self.mouse_pos = ini_pos_val
        self.render_widget = self.framework_root.ids.render_widget

        for idx in range(len(self.shaders_args)):
            self.shaders_idx = idx                                          # for change_shader_arg('run_state'..) calls
            self.add_shader_to_render_widget()
        self.shaders_idx = self.framework_app.app_states['shaders_idx']     # reset to persistent app state value

        self.eval_and_push_shader_file(self.shaders_args[self.shaders_idx], self.id_of_selected_shader())
        self._update_shader_buttons()

        self.on_render_frequency()
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.update_input_values()
        Clock.schedule_interval(lambda *_args: self.update_input_values(), 0.333333333)

    def on_file_chooser_submit(self, file_path: str, chooser_popup: Widget):
        """ event callback from FileChooserPopup.on_submit() on selection of the next shader file to be added.

        :param file_path:       path string of selected file.
        :param chooser_popup:   file chooser popup/container widget.
        """
        if chooser_popup.submit_to != 'shader_filename':                # if == 'sideloading_file_mask':
            super().on_file_chooser_submit(file_path, chooser_popup)    # pass selected file to SideloadingMainAppMixin
            return
        if not os.path.isfile(file_path):
            self.show_message(get_txt("{file_path} is not a shader file"), title=get_txt("select single file"))
            return

        self.change_shader_arg('shader_filename', file_path)
        chooser_popup.register_file_path(file_path, self)
        chooser_popup.close()

    def on_mouse_pos(self, _instance, pos):
        """ Window mouse position event handler. """
        ren_wid: Widget = cast(Widget, self.render_widget)
        if ren_wid.collide_point(*ren_wid.to_widget(*pos)):
            self.vpo(f"GlslTesterApp.on_mouse_pos({_instance}, {pos})")
            self.mouse_pos: Tuple[float, ...] = tuple(map(float, pos))      # real type: PosValType
            self.update_input_values()

    def on_render_frequency(self):
        """ render frequency changed event handler. """
        prf = self.render_frequency
        self.vpo(f"GlslTesterApp.on_render_frequency(): frequency={prf}Hz")
        if self._shader_tick_timer:
            Clock.unschedule(self._shader_tick_timer)
        if prf > self.get_var('render_frequency_min'):
            self._shader_tick_timer = Clock.schedule_interval(self.render_tick, 1 / prf)

    def on_shader_add(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ add shader to self.render_widget.

        :param _flow_key:       unused/empty flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                True to confirm change of flow id else False.
        """
        shaders_args = self.shaders_args
        shader_args = shaders_args[self.shaders_idx].copy()

        shaders_args.append(shader_args)
        self.change_app_state('shaders_args', shaders_args)
        self.change_app_state('shaders_idx', len(shaders_args) - 1)
        ret = self.add_shader_to_render_widget()
        self._update_shader_buttons()

        return ret

    # def on_shader_arg_edit(self, flow_key: str, event_kwargs: EventKwargsType) -> bool:
    #     """ notification of shader arg edit field focus change - only for debugging.
    #
    #     :param flow_key:        shader arg or setting name.
    #     :param event_kwargs:    (unused).
    #     :return:                True to change flow id and flow path (actually not needed).
    #     """
    #     self.dpo(f"GlslTesterApp.on_shader_arg_edit {flow_key} {event_kwargs}")
    #     return True

    def on_shader_del(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ remove args of selected shader from shaders_args and delete shader from self.render_widget.

        :param _flow_key:       unused flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                always True to confirm change of flow id.
        """
        shaders_args = self.shaders_args
        shaders_idx = self.shaders_idx
        self.vpo("GlslTesterApp.on_shader_del", shaders_idx)

        self.render_widget.del_shader(self.id_of_selected_shader())
        shaders_args.pop(shaders_idx)
        if shaders_idx == len(shaders_args):
            shaders_idx -= 1
            self.change_app_state('shaders_idx', shaders_idx)
        self.change_app_state('shaders_args', shaders_args)

        self._update_shader_buttons()
        return True

    def on_shader_run(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ toggle the `run_state` shader arg of the currently selected shader.

        :param _flow_key:       unused flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                always True to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_shader_run")
        running = 'paused' if self.shaders_args[self.shaders_idx]['run_state'] == 'running' else 'running'
        self.change_shader_arg('run_state', running)
        return True

    def on_shader_sel(self, flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ select shader, updating fields of shader args edit layout with selected shader values.

        :param flow_key:        str(index-in-shaders_args) + "==" + get_txt(<run-state>).
        :param _event_kwargs:   unused event kwargs.
        :return:                always True to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_shader_sel")
        self.change_app_state('shaders_idx', int(flow_key.split("==", maxsplit=1)[0]))
        self._update_shader_buttons()
        return True

    def on_tool_box_toggle(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ toggle between display and hide of tool box.

        :param _flow_key:       unused/empty flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                always True to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_tool_box_toggle")
        tool_box = self.framework_root.ids.tool_box
        tool_box.visible = not tool_box.visible
        return True

    def render_tick(self, *_args):
        """ timer for the animation of the running shaders. """
        render_widget = self.render_widget
        render_widget.next_tick()
        try:
            render_widget.refresh_running_shaders()
        except (NameError, ValueError, Exception) as ex:
            self.change_app_state('render_frequency', 0.0)
            self.show_message(str(ex), title=get_txt("animation exception - stopped timer"))

    def update_input_values(self):
        """ format and display input values. """
        def _val_str(key: str, val: Union[float, Tuple[float, ...]]) -> str:
            return f"{val:.{3 if key.islower() else 0}f}" if isinstance(val, float) \
                else ",".join(_val_str(key, _v) for _v in val)

        ica = self.input_callables()
        self.framework_root.ids.input_values.text = "   ".join(k + "=" + _val_str(k, v()) for k, v in ica.items())

    def _update_shader_buttons(self):
        """ update the running shaders buttons after add/delete of a running shader. """
        buttons_kwargs = list()
        for idx, shader_args in enumerate(self.shaders_args):
            but_kwargs = dict(text=str(idx) + "==" + get_txt(shader_args['run_state']))
            if shader_args['run_state'] == 'running':
                but_shader_id = self.render_widget.added_shaders[idx].copy()
                but_shader_id['glsl_dyn_args'].pop('time', None)
                but_shader_id['render_shape'] = ('Ellipse', 'RoundedRectangle', 'Rectangle')[self.debug_level]
                but_shader_id['update_freq'] = DEFAULT_FPS
                but_kwargs['added_shaders'] = [but_shader_id]
            buttons_kwargs.append(but_kwargs)

        self.framework_root.ids.running_shaders.shader_buttons = buttons_kwargs


if __name__ == '__main__':
    main_app = GlslTesterApp(app_name='glsl_tester', multi_threading=True)

    PATH_PLACEHOLDERS['glsl'] = scripts_path = os.path.join(norm_path("{ado}"), "glsl")
    check_moves("glsl", scripts_path)
    for name, code in BUILT_IN_SHADERS.items():
        write_file_text(code, os.path.join(scripts_path, f"{name}.fs.glsl"))

    PATH_PLACEHOLDERS['sug'] = sug_path = os.path.join(norm_path("{ado}"), "sug")
    check_moves("sug", sug_path)

    main_app.run_app()
