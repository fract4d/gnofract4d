# This file contains utility classes and functions used by the GUI
# Many of them 'cover up' differences between pygtk versions - these
# follow the general pattern
#
# try:
#    do new thing
# except:
#    fall back to the 'old way'

import os
import inspect

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib

from . import hig


def input_add(fd, cb):
    return GLib.io_add_watch(fd, GLib.PRIORITY_DEFAULT,
                             GLib.IO_IN | GLib.IO_HUP | GLib.IO_PRI, cb)


def stack_trace():
    stack = inspect.stack()
    str = ""
    for frame in stack[1:]:
        (frame_obj, filename, line, funcname, context, context_index) = frame
        try:
            args = inspect.formatargvalues(*inspect.getargvalues(frame_obj))
        except Exception:
            args = "<unavailable>"

        frame_desc = "%s(%s)\t\t%s(%s)\n" % (filename, line, funcname, args)
        str += frame_desc
    return str


def get_directory_chooser(title, parent):
    chooser = Gtk.FileChooserDialog(
        title=title,
        transient_for=parent,
        action=Gtk.FileChooserAction.SELECT_FOLDER)

    chooser.add_buttons(
        _("_OK"), Gtk.ResponseType.OK,
        _("_Cancel"), Gtk.ResponseType.CANCEL)
    chooser.set_default_response(Gtk.ResponseType.OK)

    return chooser


def set_file_chooser_filename(chooser, name):
    if name:
        chooser.set_current_folder(os.path.abspath(os.path.dirname(name)))
        chooser.set_current_name(os.path.basename(name))


def create_option_menu(items):
    widget = Gtk.ComboBoxText()
    for item in items:
        widget.append_text(item)

    return widget


def set_menu_from_list(menu, items):
    model = Gtk.ListStore(str)
    for item in items:
        model.append((item,))
    menu.set_model(model)


def set_selected(menu, i):
    menu.set_active(int(i))


def get_selected(menu):
    return menu.get_active()


def get_selected_value(menu):
    iter = menu.get_active_iter()
    if not iter:
        return None
    val = menu.get_model().get_value(iter, 0)
    return val


def set_selected_value(menu, val):
    model = menu.get_model()
    i = 0
    iter = model.get_iter_first()
    while iter is not None:
        item = model.get_value(iter, 0)
        if item == val:
            menu.set_active(i)
            return
        iter = model.iter_next(iter)
        i += 1


def create_color(r, g, b):
    return Gdk.RGBA(int(r * 65535), int(g * 65535), int(b * 65535))


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

        self.connect('color-set', self.on_color_set)

    def on_color_set(self, widget):
        self.color_changed(self.get_color())

    def set_color(self, rgb):
        self.color = create_color(rgb[0], rgb[1], rgb[2])
        Gtk.ColorButton.set_rgba(self, self.color)

    def color_changed(self, color):
        self.color = color
        self.changed_cb(
            color.red / 65535.0,
            color.green / 65535.0,
            color.blue / 65535.0,
            self.is_left)
