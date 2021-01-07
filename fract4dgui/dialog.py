# superclass for dialogs

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


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
