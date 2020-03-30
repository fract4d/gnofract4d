# GUI for painting colors onto the fractal

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from . import dialog


class PainterDialog(dialog.T):
    def __init__(self, main_window, f):
        dialog.T.__init__(
            self,
            _("Painter"),
            main_window,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
            modal=False
        )

        self.f = f
        self.paint_toggle = Gtk.ToggleButton.new_with_label(_("Painting"))
        self.paint_toggle.connect('toggled', self.onChangePaintMode)
        self.csel = Gtk.ColorSelection()
        self.vbox.add(self.csel)
        self.vbox.add(self.paint_toggle)
        self.vbox.show_all()

    def show(self):
        super().show()
        self.paint_toggle.set_active(True)

    def hide(self):
        super().hide()
        self.paint_toggle.set_active(False)

    def onChangePaintMode(self, *args):
        self.f.set_paint_mode(self.paint_toggle.get_active(), self.csel)

    def onResponse(self, widget, id):
        if id == Gtk.ResponseType.CLOSE or \
                id == Gtk.ResponseType.NONE or \
                id == Gtk.ResponseType.DELETE_EVENT:
            self.hide()
