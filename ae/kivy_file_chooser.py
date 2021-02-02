"""
extended kivy file chooser widget
=================================

This ae namespace portion provides the :class:`FileChooserPopup` widget (`chooser_popup`) which is embedding Kivy's
:class:`~kivy.uix.filechooser.FileChooser` class in a dropdown window (:class:`~ae.kivy_app.FlowDropDown`), and
extending it with a path selector and a button for to switch between list and icon view.


file chooser dropdown usage
---------------------------

The :class:`FileChooserPopup` widget can be used like any :class:`Kivy DropDown widget <kivy.uix.dropdown.DropDown>` -
see the python and kv lang examples in the doc strings of the :mod:`~kivy.uix.dropdown` module. Additionally all the
features of the :class:`~ae.kivy_app.FlowDropDown` like e.g. the
:attr:`~ae.kivy_dyn_chi.DynamicChildrenBehavior.child_data_maps` are available.

Alternatively (and without the need to explicitly instantiate the file chooser dropdown widget) you simply have to
:meth:`change the application flow <ae.gui_app.change_flow>` to `id_of_flow('open', 'file_chooser')` for to open this
file chooser (see also :ref:`application flow`)::

    main_app.change_flow(id_of_flow('open', 'file_chooser'),
                         **update_tap_kwargs(open_button))

The variable `open_button` in this example represents a button widget instance that opens the file chooser dropdown (and
to which the file chooser gets attached to).

If the file chooser has multiple usages in the app, then the :attr:`~FileChooserPopup.submit_to` string property can be
used for to distribute the selected file path to the correct usage/process::

    main_app.change_flow(id_of_flow('open', 'file_chooser'),
                         **update_tap_kwargs(open_button,
                                             popup_kwargs=dict(submit_to=submit_to_str_or_callable))

`submit_to_str_or_callable` can be either a string or a callable. If you pass a callable then :class:`FileChooserPopup`
will call it if the user has selected a file (by double clicking on a file name) with two arguments: the file path of
the selected file and the dropdown widget instance::

    def submit_to_callable(file_path: str, chooser_popup: Widget):

Passing a string to `submit_to` (or if it get not specified at all) the hard-coded `on_file_chooser_submit` event
handler callback method of your main app instance will be executed with the same two arguments::

    def on_file_chooser_submit(self, file_path: str, chooser_popup: Widget):
        if chooser_popup.submit_to == 'usage1':
            usage1_object_or_process.file_path = file_path
            chooser_popup.dismiss()
        elif chooser_popup.submit_to == 'usage2':
            ...

This file chooser is providing all common OS and user paths as well as app specific paths that are maintained in the
:data:`~ae.paths.PATH_PLACEHOLDERS` dict. The keys of this dict will be displayed as shortcut path names instead of the
full path strings. Additionally translation texts can be provided for the shortcut path names for to display them in the
language selected by the app user.

By adding the list `file_chooser_paths` to the `:ref:`app state variables` of your app, this file chooser widget will
automatically maintain and keep the last/historical path selections of the file chooser persistent between app runs.

For to record and remember the last selected path add also the app state `file_chooser_initial_path` to the
`:ref:`app state variables` of your app.
"""
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty

from ae.kivy_app import FlowDropDown


__version__ = '0.1.0'


Builder.load_string('''\
<FileChooserPopup>
    do_scroll_x: True
    do_scroll_y: False
    on_initial_path: app.main_app.change_app_state('file_chooser_initial_path', self.initial_path)
    BoxLayout:
        size_hint_y: None
        height: app.app_states['font_size'] * 1.8
        padding: '3sp'
        spacing: '9sp'
        FlowButton:
            tap_flow_id: id_of_flow('select', 'file_chooser_path', root.initial_path)
            tap_kwargs: update_tap_kwargs(self)
            text: path_name(root.initial_path) and _(path_name(root.initial_path)) or root.initial_path
            text_size: self.width, None
            halign: 'center'
            shorten: True
            shorten_from: 'left'
            relief_square_inner_colors: relief_colors((1, 1, 0))
            relief_square_inner_lines: int(sp(6))
        FlowToggler:
            tap_flow_id: id_of_flow('toggle', 'file_chooser_view')
            tap_kwargs: update_tap_kwargs(self)
            icon_name: chooser_widget.view_mode + "_view"
            on_state: chooser_widget.view_mode = 'icon' if self.state == 'down' else 'list'
            size_hint_x: None
            width: self.height
    FileChooser:
        id: chooser_widget
        path: root.initial_path
        size_hint_y: None
        height: root.attach_to.top * 0.96 if root.attach_to else Window.height - app.main_app.font_size * 3.9
        dirselect: True
        on_submit:
            (root.submit_to if callable(root.submit_to) else app.main_app.on_file_chooser_submit)(args[1][0], root)
        on_entry_added: app.on_file_chooser_entry_added(args[1])
        on_subentry_to_entry: app.on_file_chooser_entry_added(args[1])
        FileChooserListLayout
        FileChooserIconLayout

<FileChooserPathSelectPopup>
    paths:
        [norm_path(path) for path in set(list(PATH_PLACEHOLDERS.values()) + app.app_states['file_chooser_paths']) \
        if os.path.exists(norm_path(path)) and os.path.isdir(norm_path(path))]
    on_paths: app.main_app.change_app_state('file_chooser_paths', list(self.paths))
    on_select: self.attach_to.parent.parent.parent.initial_path = args[1]
    child_data_maps:
        [dict(cls='FlowButton', kwargs=dict( \
        text=_(path_name(path)) + (" (" + path + ")" if app.landscape else "") if path_name(path) else path, \
        tap_flow_id=id_of_flow('change', 'file_chooser_path', path), \
        on_release=lambda btn: self.select(flow_key(btn.tap_flow_id)))) \
        for path in self.paths]
''')


class FileChooserPopup(FlowDropDown):
    """ file chooser drop down container. """
    initial_path = StringProperty()
    submit_to = StringProperty()


class FileChooserPathSelectPopup(FlowDropDown):
    """ file chooser path selector dropdown. """
    paths = ListProperty()
