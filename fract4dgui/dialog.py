# superclass for dialogs

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def make_label_box(parent, title):
    label_box = Gtk.HBox()
    label_box.set_name('dialog_label_box')
    label = Gtk.Label(label=title)
    label_box.pack_start(label, False, False, 0)
    close = Gtk.Button.new_with_label("Close")
    label_box.pack_end(close, False, False, 0)
    label_box.show_all()

    close.connect('clicked', lambda x: parent.hide())
    return label_box


class T(Gtk.Dialog):
    def __init__(self, title=None, parent=None, buttons=None, modal=Gtk.DialogFlags.MODAL):
        Gtk.Dialog.__init__(self,
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
