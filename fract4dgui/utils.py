# This file contains utility classes and functions used across the GUI

import os

from gi.repository import Gtk, Gdk, Gio, GLib

from . import hig


class BaseChooser(Gtk.FileChooserDialog):
    def __init__(self, title, parent, action, ok_label):
        super().__init__(
            title=title,
            transient_for=parent,
            action=action)

        self.add_buttons(
            ok_label, Gtk.ResponseType.OK,
            _("_Cancel"), Gtk.ResponseType.CANCEL)
        self.set_default_response(Gtk.ResponseType.OK)

    def add_file_filter(self, name, patterns):
        """User-selectable file filter"""
        file_filter = Gtk.FileFilter()
        file_filter.set_name(name)
        for pattern in patterns:
            file_filter.add_pattern(pattern)
        self.add_filter(file_filter)
        return file_filter


class DirectoryChooser(BaseChooser):
    def __init__(self, title, parent):
        super().__init__(title, parent, Gtk.FileChooserAction.SELECT_FOLDER, _("_OK"))


class FileOpenChooser(BaseChooser):
    def __init__(self, title, parent):
        super().__init__(title, parent, Gtk.FileChooserAction.OPEN, _("_Open"))


class FileSaveChooser(BaseChooser):
    def __init__(self, title, parent, patterns=[]):
        super().__init__(title, parent, Gtk.FileChooserAction.SAVE, _("_Save"))

        # Current file filter
        file_filter = Gtk.FileFilter()
        for pattern in patterns:
            file_filter.add_pattern(pattern)
        self.set_filter(file_filter)

    def set_filename(self, name):
        if name:
            self.set_current_folder(os.path.abspath(os.path.dirname(name)))
            self.set_current_name(os.path.basename(name))


def combo_box_text_with_items(items, tip=None):
    widget = Gtk.ComboBoxText(tooltip_text=tip)
    for item in items:
        widget.append_text(item)

    return widget


def floatColorFrom256(rgba):
    return [rgba[0] / 255.0, rgba[1] / 255.0, rgba[2] / 255.0, rgba[3] / 255.0]


def color256FromFloat(r, g, b, color):
    return (int(r * 255), int(g * 255), int(b * 255), color[3])


def launch_browser(url, window):
    try:
        Gio.AppInfo.launch_default_for_uri(url)
    except GLib.Error as err:
        d = hig.ErrorAlert(
            primary=_("Error launching browser"),
            secondary=_(f"Try copying the URL '{url}' manually to a browser window.\n"
                        f"{err.message}"),
            transient_for=window)
        d.run()
        d.destroy()


class ColorButton(Gtk.ColorButton):
    def __init__(self, rgb, changed_cb, is_left):
        Gtk.ColorButton.__init__(self)
        self.set_color(rgb)
        self.changed_cb = changed_cb
        self.is_left = is_left
        self.set_property("show-editor", True)
        self.connect('color-set', self.on_color_set)

    def on_color_set(self, widget):
        self.color_changed(self.get_color())

    def set_color(self, rgb):
        self.color = Gdk.RGBA(rgb[0], rgb[1], rgb[2], 1.0)
        Gtk.ColorButton.set_rgba(self, self.color)

    def color_changed(self, color):
        # get_color() returns each component in the range 0-65535. Normalize to float 0-1.0
        self.color = Gdk.RGBA(color.red / 65535.0,
                              color.green / 65535.0, color.blue / 65535.0, 1.0)
        self.changed_cb(self.color.red, self.color.green,
                        self.color.blue, self.is_left)


class Dialog(Gtk.Dialog):
    def __init__(self, title=None, parent=None, buttons=None, modal=Gtk.DialogFlags.MODAL):
        super().__init__(
            title=title,
            transient_for=parent,
            modal=modal,
            destroy_with_parent=Gtk.DialogFlags.DESTROY_WITH_PARENT)

        if buttons:
            self.add_buttons(*buttons)

        self.set_default_response(Gtk.ResponseType.CLOSE)
        self.connect('response', self.onResponse)
        self.connect('delete-event', self.quit)

    def onResponse(self, widget, id):
        if id == Gtk.ResponseType.CLOSE or \
                id == Gtk.ResponseType.NONE or \
                id == Gtk.ResponseType.DELETE_EVENT:
            self.hide()
        else:
            print("unexpected response %d" % id)

    def quit(self, widget, event):
        self.hide()
        return True
