"""
GlslTester - share files and intents with other devices in the same network
=========================================================================

This app allows to share any files, images, videos and documents between two devices that are connected to a local
network (LAN, Wifi).

On Android all view and send intents get redirected by this app to other devices within your local network.

Additionally it provides http sideloading for to pass files - e.g. the APK of this app - to another device in the same
local network (and without the need to have this app installed in the other/receiving device).

TODO:
    * process send intents, sent from other Android apps for to share them with other devices
    * run transfer server as service on Android devices (removing WAKE_LOCK permission workaround).
    * fix crash of zbarcam.
    * on Android add special choosers for to select images, videos, ...

"""
import datetime
import os
import socket
import threading
from collections import OrderedDict
from functools import partial
from typing import Callable, List, Tuple

from kivy.app import App
from kivy.clock import mainthread, Clock
from kivy.properties import DictProperty, StringProperty
from kivy.uix.widget import Widget

import ae.droid
from ae.base import os_platform
from ae.files import file_transfer_progress
from ae.gui_app import EventKwargsType, flow_action, flow_key, flow_object, id_of_flow
from ae.kivy_app import FlowButton, FlowDropDown, KivyMainApp, get_txt
from ae.kivy_glsl import touch_wave_shader_code
from ae.kivy_sideloading import SideloadingMainAppMixin
from ae.transfer_service import (
    CONNECT_ERR_PREFIX, connect_and_request, service_factory, TransferKwargs, TransferServiceApp)


__version__ = '0.1.50'


MAX_HISTORY_LEN = 12        #: maximum number of entries in the current_object and current_remote history lists

SERVICE_MODE_CHOICES = ('attached', 'standalone')
# standalone services are not working in p4a:
# default_service_mode = SERVICE_MODE_CHOICES[1 if os_platform == 'android' else 0]
default_service_mode = SERVICE_MODE_CHOICES[0]


class RequestTaskItem(FlowButton):
    """ request tasks item (declared in main.py because else progress bar/square_fill_size not updated). """
    data = DictProperty(dict(method_name='', rt_id=''))


class RequestTaskMenuPopup(FlowDropDown):
    """ dropdown menu for send/recv transfer request tasks items. """
    data = DictProperty()           #: request kwargs dict
    title = StringProperty()        #: not displayed in this widget, but passed to IterableDisplayerPopup

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        rt_id = self.data['rt_id']

        self.child_data_maps = [dict(kwargs=dict(
            text=get_txt("request task data"),
            tap_flow_id=id_of_flow('open', 'iterable_displayer', rt_id),
            tap_kwargs=dict(popup_kwargs=dict(title=self.title, data=self.data))))]

        action = flow_action(rt_id)
        if action == 'sideloading':
            action = 'stop' if App.get_running_app().main_app.sideloading_active else 'start'
            self.child_data_maps.append(dict(kwargs=dict(
                text=get_txt(action + " sideloading server"),
                tap_flow_id=id_of_flow(action, 'sideloading_server'),
                tap_kwargs=dict(popups_to_close=(self, )))))

        elif action == 'send':
            self.child_data_maps.append(dict(kwargs=dict(
                text=get_txt("prepare resend"),
                tap_flow_id=id_of_flow('prepare', 'resend', rt_id),
                tap_kwargs=dict(popups_to_close=(self, )))))

            if 'completed' not in self.data and flow_object(rt_id) == 'file':
                if 'error' not in self.data:
                    self.child_data_maps.append(dict(kwargs=dict(
                        text=get_txt("cancel transfer request"),
                        tap_flow_id=id_of_flow('cancel', 'transfer', rt_id),
                        tap_kwargs=dict(popups_to_close=(self, )))))

                if action == 'send':
                    self.child_data_maps.append(dict(kwargs=dict(
                        text=get_txt("recover send request"),
                        tap_flow_id=rt_id,
                        tap_kwargs=dict(popups_to_close=(self, )))))


class GlslTesterApp(SideloadingMainAppMixin, KivyMainApp):
    """ kivy main app class

    Inherit first from SideloadingMainAppMixin then from KivyMainApp for SideloadingMainAppMixin.on_app_start() call.
    """
    close_toolbox_on_send: bool                         #: app state flag closing tool box after pressing send button

    current_object: str                                 #: current message/file app state object to be send
    current_object_history: List[str]                   #: object (message/file) history app state list
    current_remote: str                                 #: current remote host ip address app state string
    current_remote_history: List[str]                   #: remote ip history app state list

    on_pending_requests_frequency: Callable             #: event handler patched to self._pending_requests_restart
    pending_requests_frequency: float                   #: pending requests timer frequency (0=disable for debugging)

    request_tasks: OrderedDict                          #: running and finished transfers and sideloading(s) req tasks

    sideloading_render_idx: int = -1                    #: renderer index of the sideloading server activation animation

    transfer_app: TransferServiceApp                    #: transfer service console app

    def adapt_renderers(self, frequency: float):
        """ synchronize render shaders if passed frequency is above the minima specified as config variables.

        :param frequency:       render shader synchronize frequency (==self.pending_requests_frequency).
        """
        root = self.framework_root
        server_min = self.get_var('renderer_servers_frequency_min')
        wave_min = self.get_var('renderer_wave_frequency_min')
        if frequency < server_min and root.renderers:
            self.dpo(f"adapt_renderers(): deactivating servers activity render shaders")
            for ren_idx, renderer in enumerate(root.renderers):
                if 'shader_code' not in renderer:
                    root.del_renderer(ren_idx)

        if frequency < wave_min:
            if not root.renderers:
                return

            self.dpo(f"adapt_renderers(): deactivating touch wave render shader")
            for ren_idx, renderer in enumerate(root.renderers):
                if 'shader_code' in renderer:
                    root.del_renderer(ren_idx)

        root.next_tick()
        root.refresh_renderers()

    def add_shader(self, **kwargs):
        """ add renderer shader if frequency is high enough (preventing freeze of app especially on mobile devices).

        :param kwargs:          :meth:`~ae.kivy_glsl.ShaderMixin.add_renderer` kwargs.
        :return:                renderer index or -1 if device is to slow for to run shaders.
        """
        if self.pending_requests_frequency < self.get_var('renderer_wave_frequency_min' if 'shader_code' in kwargs else
                                                          'renderer_servers_frequency_min'):
            self.vpo(f"GlslTester.add_shader(): frequency for glsl shader to low; kwargs={kwargs}")
            return -1

        kwargs['time'] = 0.0
        kwargs['update_freq'] = 0.0
        return self.framework_root.add_renderer(**kwargs)

    def add_request_task(self, rt_id: str, request_kwargs: TransferKwargs, transfer: bool = True) -> bool:
        """ add new request task (either from transfer service or from sideloading server).

        :param rt_id:           request tasks id.
        :param request_kwargs:  request kwargs dict.
        :param transfer:        pass False for to add a sideloading server task.
        :return:                True if task got added, False if task already exists.
        """
        if rt_id in self.request_tasks:
            msg = f"server request task with id {rt_id} already exists"
            request_kwargs['error'] = f"add_request_task(): {msg}"
            self.show_message(msg, title=f"add {request_kwargs['method_name']} transfer task error")
            return False

        # create request tasks dict, updated via on_pending_requests timer or on_size_load_server_progress callback
        request_kwargs['rt_id'] = rt_id
        self.request_tasks[rt_id] = request_kwargs

        color_dyn_arg = (lambda: self.flow_path_ink) if not transfer \
            else (lambda: self.selected_item_ink) if flow_object(rt_id) == 'file' \
            else (lambda: self.unselected_item_ink)
        request_kwargs['render_idx'] = self.add_shader(
            shader_code=touch_wave_shader_code, center_pos=partial(self.server_task_center_pos, rt_id),
            alpha=0.33, tex_col_mix=0.63, tint_ink=color_dyn_arg)

        if transfer:        # start background thread only for transfer service tasks
            threading.Thread(target=self.request_thread_call, args=(request_kwargs,)).start()

        return True

    def on_app_run(self):
        """ run app and create timer for to gather pending requests from transfer service. """
        super().on_app_run()

        self.request_tasks = OrderedDict()

        self._pending_requests_restart()
        # redirect handler for change of pending_requests_frequency app state from user preferences menu
        self.on_pending_requests_frequency = self._pending_requests_restart

        if self.sideloading_active:
            self.on_sideloading_server_start("", dict())

    def on_app_started(self):
        """ initialize and start renderers after kivy app, window and widget root got initialized. """
        root = self.framework_root
        ren_idx = self.add_shader(
            center_pos=lambda: (root.width / 3.0 if self.sideloading_active else root.center_x, 0.0),
            alpha=0.9, tex_col_mix=0.54, tint_ink=lambda: self.flow_id_ink)
        if ren_idx != -1:
            # if sideloading is active then start also 2nd renderer
            if self.sideloading_active:
                self.on_sideloading_active()
            # pass apt state values from last app run to contrast/alpha render glsl arguments
            root.on_contrast(self, self.vibration_volume)
            root.on_alpha(self, self.sound_volume)

    def on_app_quit(self):
        """ shutdown service app and join service server thread. """
        if self.sideloading_active:
            self.sideloading_app.stop_server()
        self.sideloading_app.shutdown()

        if self.get_opt('transfer_service_mode') == 'attached':  # and getattr(self, 'transfer_app', False):
            self.transfer_app.shutdown()

        super().on_app_quit()

    def on_current_change(self, app_state_name: str, event_kwargs: EventKwargsType) -> bool:
        """ event handler for to change app state value of current_object or current_remote.

        :param app_state_name:  either 'current_object' or 'current_remote'.
        :param event_kwargs:    event kwargs with 'tap_widget' key.
        :return:                True for to confirm the change.
        """
        self.vpo(f"GlslTesterApp.on_current_change {app_state_name}", event_kwargs)
        self.update_history(app_state_name, event_kwargs['tap_widget'].text, change_state=True)
        return True

    def on_debug_level_change(self, level_name: str, _event_kwargs: EventKwargsType) -> bool:
        """ debug level app state change flow change confirmation event handler.

        :param level_name:      the new debug level name to be set (passed as flow key).
        :param _event_kwargs:   unused event kwargs.
        :return:                True for to confirm the debug level change.
        """
        self.vpo(f"GlslTesterApp.on_debug_level_change to {level_name}")
        ret = super().on_debug_level_change(level_name, _event_kwargs)
        if ret:
            debug_level = self.get_opt('debug_level')
            if self.get_option('transfer_service_mode') == 'attached':
                self.transfer_app.set_opt('debug_level', debug_level)   # keep transfer debug level in sync
            self.sideloading_app.set_opt('debug_level', debug_level)      # keep sideloading debug level in sync
        return ret

    def on_file_chooser_submit(self, file_path: str, chooser_popup: Widget):
        """ event callback from FileChooserPopup.on_submit() on selection of file.

        :param file_path:       path string of selected file.
        :param chooser_popup:   file chooser popup/container widget.
        """
        if chooser_popup.submit_to != 'current_object':
            super().on_file_chooser_submit(file_path, chooser_popup)    # pass selected file to SideloadingMainAppMixin
            return

        if not os.path.isfile(file_path):
            self.show_message(get_txt("Folders can't be transferred"), title=get_txt("Select Single File"))
            return

        self.change_app_state('current_object', file_path)  # allows also a folder to be transferred
        chooser_popup.dismiss()

    @mainthread
    def on_file_sent(self, response_kwargs: TransferKwargs):
        """ file sent callback event handler.

        :param response_kwargs: optional key 'error' message and 'transferred_bytes'.
        :return:
        """
        self.vpo("GlslTesterApp.on_file_sent", response_kwargs)
        if 'error' in response_kwargs:
            self.show_message(response_kwargs['error'],
                              title="send error for file " + os.path.basename(response_kwargs.get('file_path', "")))
        else:
            self.update_history('current_object', response_kwargs['file_path'])
            self.update_history('current_remote', response_kwargs['remote_ip'])

    def on_request_tasks_clear(self, what: str, _event_kwargs: EventKwargsType) -> bool:
        """ delete messages from request tasks.

        :param what:            what type of entries to be cleared/removed (all/message/file/log).
        :param _event_kwargs:   unused event kwargs.
        :return:                always True for to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_request_tasks_clear", what)
        sh_items = OrderedDict()
        for key, val in self.request_tasks.items():
            if what in ('all', flow_object(val['rt_id'])):
                self.framework_root.del_renderer(val.pop('render_idx', -1))     # remove renderer - mostly already done
            else:
                sh_items[key] = val
        self.request_tasks = sh_items
        return True     # view will be updated by next on_pending_requests timer

    def on_key_press(self, modifiers: str, key_code: str) -> bool:
        """ check key press event for to be handled and processed as command/action. """
        self.vpo("GlslTesterApp.on_key_press", modifiers, key_code)
        if modifiers == '' and key_code in ('home', 'end'):
            self.framework_root.ids.request_tasks_view.scroll_y = 0.0 if key_code == 'end' else 1.0
            return True
        return False

    @mainthread
    def on_message_sent(self, response_kwargs: TransferKwargs):
        """ message sent callback event handler.

        :param response_kwargs: optional key 'error' message and 'transferred_bytes'.
        :return:
        """
        self.vpo("GlslTesterApp.on_message_sent", response_kwargs)
        if 'error' in response_kwargs:
            self.show_message(response_kwargs['error'], title="send message error")
        else:
            self.update_history('current_object', response_kwargs['message'])
            self.update_history('current_remote', response_kwargs['remote_ip'])

    def on_object_send(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ send button pressed handler.

        :param _flow_key:       unused/empty flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                True if new request task could be created, else False.
        """
        obj = self.current_object
        rem = self.current_remote
        kwargs = dict(remote_ip=rem, transferred_bytes=0)

        if os.path.exists(obj):
            flo_obj = 'file'
            kwargs['file_path'] = obj
            kwargs['method_name'] = 'send_file'
            kwargs['response_method'] = 'on_file_sent'
        else:
            flo_obj = 'message'
            obj = datetime.datetime.now().strftime("%X") + " " + obj
            kwargs['message'] = obj
            kwargs['method_name'] = 'send_message'
            kwargs['response_method'] = 'on_message_sent'

        rt_id = id_of_flow('send', flo_obj, obj + '@' + rem)

        self.vpo("GlslTesterApp.on_object_send", rt_id, kwargs)

        if not self.add_request_task(rt_id, kwargs):
            return False

        if self.framework_root.ids.close_on_send.state == 'down' and self.framework_root.ids.tool_box.visible:
            self.change_flow(id_of_flow('toggle', 'tool_box'))

        return True

    @mainthread
    def on_pending_requests(self, response_kwargs: TransferKwargs):
        """ response method callback from transfer service.

        transfer service request handler thread providing is calling this method to pass the status/progress of all
        pending requests (and optional on debug the meanwhile collected log messages).

        This method accomplishes several tasks:

        * add/update request tasks from transfer service requests and logs.
        * polling the pending sideloading requests (and debug messages) from the sideloading server.
        * synchronizing the rendering shaders for the background graphics.

        :param response_kwargs: response kwargs dict with pending requests from transfer service server.
        """
        self.vpo("GlslTesterApp.on_pending_requests", response_kwargs)

        prf = self.pending_requests_frequency
        if 'error' in response_kwargs:
            if prf > 1.02 and CONNECT_ERR_PREFIX in response_kwargs['error']:
                self.change_app_state('pending_requests_frequency', prf - 0.9, send_event=False)
                self.play_sound('error')
            else:
                self.show_message(response_kwargs['error'], title="pending requests error")
        else:
            pending_requests = response_kwargs['pending_requests']
            for req in pending_requests:                    # update progress counters in request task records
                self.request_tasks[req['rt_id']] = req

        if self.sideloading_active:
            self.poll_sideloading_server_requests()

        self.update_request_tasks_recycle_view()

        self.adapt_renderers(prf)

    def on_pending_requests_fetch(self, _flow_key: str, _event_kwargs: EventKwargsType) -> bool:
        """ button event handler for to fetch manually the pending requests from the transfer service server.

        :param _flow_key:       unused/empty flow key.
        :param _event_kwargs:   unused event kwargs.
        :return:                True if new request task could be created, else False.
        """
        self._pending_requests_timer()
        return True

    def on_qr_code_read(self, qr_code: str):
        """ symbols event handler from ZBarCam.

        :param qr_code:         qr code as string (from ZBarCam.symbols[0].data).
        """
        self.change_app_state('current_remote', qr_code)

    def on_resend_prepare(self, rt_id: str, _event_kwargs: EventKwargsType) -> bool:
        """ toggle between display and hide of tool box.

        :param rt_id:           request tasks id (<action>_<object_type>:<object_content>@<remote>).
        :param _event_kwargs:   unused event kwargs.
        :return:                always True for to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_resend_prepare", rt_id)

        obj, rem = flow_key(rt_id).split('@', maxsplit=1)
        if flow_object(rt_id) == 'message':
            obj = obj.split(" ", maxsplit=1)[1]     # remove hour:minute prefix

        self.change_app_state('current_object', obj)
        self.change_app_state('current_remote', rem)

        return True

    def on_sideloading_active(self):
        """ changed sideloading app state event handler for to add/del associated renderer. """
        root = self.framework_root
        self.vpo("GlslTesterApp.on_sideloading_active: app state changed to ", self.sideloading_active, "  root=", root)
        if root:
            if self.sideloading_active:
                self.sideloading_render_idx = self.add_shader(
                    center_pos=lambda: (root.width * 2.0 / 3.0, 0.0), alpha=0.3, tex_col_mix=0.63,
                    tint_ink=lambda: self.flow_path_ink)
            else:
                root.del_renderer(self.sideloading_render_idx)
                self.sideloading_render_idx = -1

    def on_sound_volume(self):
        """ use for to control the shader/renderer intensity. """
        self.framework_root.on_alpha(self, self.sound_volume)

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

    def on_transfer_cancel(self, rt_id: str, _event_kwargs: EventKwargsType) -> bool:
        """ cancel running transfer request task.

        :param rt_id:           request tasks id (<action>_<object_type>:<object_content>@<remote>) to be cancelled.
        :param _event_kwargs:   unused event kwargs.
        :return:                always True for to confirm change of flow id.
        """
        self.vpo("GlslTesterApp.on_transfer_cancel", rt_id, _event_kwargs)
        request_kwargs = dict(method_name='cancel_request', rt_id_to_cancel=rt_id)
        return self.add_request_task(id_of_flow('cancel', 'request', rt_id), request_kwargs)

    def on_vibration_volume(self):
        """ use for to control the shader/renderer color contrast. """
        self.framework_root.on_contrast(self, self.vibration_volume)

    def _pending_requests_restart(self):
        prf = self.pending_requests_frequency
        self.vpo(f"GlslTesterApp.on_pending_requests_frequency/_pending_requests_restart(): frequency={prf}Hz")
        Clock.unschedule(self._pending_requests_timer)
        if prf > self.get_var('pending_requests_frequency_min'):
            Clock.schedule_interval(self._pending_requests_timer, 1 / prf)

    def _pending_requests_timer(self, *_args):
        """ gather pending requests and (in debug mode) log messages of the transfer services. """
        request_kwargs = dict()
        request_kwargs['method_name'] = 'pending_requests'
        request_kwargs['response_method'] = 'on_pending_requests'
        threading.Thread(target=self.request_thread_call, args=(request_kwargs, )).start()

    def poll_sideloading_server_requests(self):
        """ poll sideloading server requests and debug/error log entries and merge them into request tasks. """
        finished_sideloading_client_ips = list()

        for client_ip in self.sideloading_app.client_handlers.keys():
            file_path = self.sideloading_app.file_path
            file_id = os.path.basename(file_path) + "@" + client_ip
            rt_id = id_of_flow('sideloading', 'file', file_id)
            transferred, total = self.sideloading_app.client_progress(client_ip)

            if rt_id in self.request_tasks:
                self.request_tasks[rt_id]['transferred_bytes'] = transferred
            else:
                request_kwargs = dict(rt_id=rt_id, method_name='sideloading_file', client_ip=client_ip,
                                      file_path=file_path, transferred_bytes=transferred, total_bytes=total)
                self.add_request_task(rt_id, request_kwargs, transfer=False)

            if transferred == total:
                finished_sideloading_client_ips.append(client_ip)
                self.framework_root.del_renderer(self.request_tasks[rt_id].pop('render_idx', -1))

        for client_ip in finished_sideloading_client_ips:
            self.update_history('current_remote', client_ip)
            self.sideloading_app.client_handlers.pop(client_ip)

        self.request_tasks.update(self.sideloading_app.fetch_log_entries())

    def request_thread_call(self, request_kwargs: TransferKwargs):
        """ request and wait for response in just started background thread.

        :param request_kwargs:  request kwargs dict.
                                Pass a method name into the optional `'response_method'` key for to get notified
                                when the background-request/transfer is finished/completed.
        """
        pre = "GlslTesterApp.request_thread_call() "
        thread_name = threading.current_thread().name
        method_name = request_kwargs['method_name']
        timeout = None      # adapt for special request tasks, else use None (the system/OS socket default timeout)
        if method_name == 'pending_requests':
            timeout = 0.9 * (1 / (self.pending_requests_frequency or 0.03)) \
                if self.pending_requests_frequency > self.get_var('pending_requests_frequency_min') else 690.0
        elif method_name == 'send_file':
            timeout = 3 * 60 * 60   # wait max. 3h until response get send back, when a (big) file got fully transferred

        self.vpo(f"{pre}start: thread={thread_name} timeout={timeout} req={request_kwargs}")

        with socket.socket() as sock:  # use socket default args: socket.AF_INET, socket.SOCK_STREAM
            response_kwargs = connect_and_request(sock, request_kwargs, timeout=timeout)

        if 'response_method' in request_kwargs:
            self.call_method(request_kwargs['response_method'], response_kwargs)

        self.vpo(f"{pre}end: thread={thread_name} response={response_kwargs}")

    def server_task_center_pos(self, rt_id: str) -> Tuple[float, float]:
        """ determine progress x and y position of the RequestTaskItem instance with the passed request task id.

        :param rt_id:           request task id.
        :return:                center position tuple (x, y) in absolute window coordinates.
        """
        shv = self.framework_root.ids.request_tasks_view
        for shi in shv.children[0].children:
            if shi.data['rt_id'] == rt_id:
                return shi.to_window(shi.progress_x, shi.center_y)
        return 0.0, 0.0

    def update_history(self, app_state_name: str, new_entry: str, change_state: bool = False):
        """ extend or update the app state value history list and optional set also the related app state value.

        :param app_state_name:  name of the app state and prefix of the history list.
        :param new_entry:       new entry for to be added to the history list.
        :param change_state:    pass True to assign the new_entry value to the app state.
        """
        hist_name = app_state_name + '_history'
        history = getattr(self, hist_name)
        if new_entry in history:
            idx = history.index(new_entry)
            history.pop(idx)
        elif len(history) > MAX_HISTORY_LEN:
            history.pop(MAX_HISTORY_LEN)
        history.insert(0, new_entry)
        self.change_app_state(hist_name, history)
        if change_state:
            self.change_app_state(app_state_name, new_entry)

    def update_request_tasks_recycle_view(self):
        """ update recycle view data from request tasks. """
        root = self.framework_root
        rv_data = list()
        for row in self.request_tasks.values():   # iterate through request_tasks for to update recycle view data
            action = flow_action(row['rt_id'])
            # alt. sideloading chars: \u015f and \u0219 (https://www.fileformat.info/info/unicode/font/roboto/grid.htm)
            pre = ">" + row['remote_ip'].split('.')[-1] if action == 'send' \
                else "<" + row['local_ip'].split('.')[-1] if action == 'recv' \
                else "\u0161" + row['client_ip'].split('.')[-1] if action == 'sideloading' \
                else ""
            if 'message' in row:
                text = f"{pre} {row['message']}"
            elif 'transferred_bytes' in row:
                text = f"{pre} {os.path.basename(row['file_path'])}" \
                       f" ({file_transfer_progress(row['transferred_bytes'], row.get('total_bytes', 0))})"
            else:
                text = f"invalid transfer request task item: {row}"
            rv_data.append(dict(text=text, data=row))

            if 'render_idx' in row and (row['transferred_bytes'] == row.get('total_bytes', -1) or 'error' in row):
                root.del_renderer(row.pop('render_idx'))

        root.ids.request_tasks_view.data = rv_data


if __name__ == '__main__':
    GlslTesterApp(app_name='comparty', multi_threading=True).run_app()
