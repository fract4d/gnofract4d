# GUI for painting colors onto the fractal

from gi.repository import Gtk

from . import utils


class PainterDialog(utils.Dialog):
    def __init__(self, main_window):
        super().__init__(
            _("Painter"),
            main_window,
            (_("_Close"), Gtk.ResponseType.CLOSE),
            modal=False
        )

        self.f = main_window.f
        self.connect("notify::visible", self.on_visible)
        self.paint_toggle = Gtk.ToggleButton.new_with_label(_("Painting"))
        self.paint_toggle.connect('toggled', self.onChangePaintMode)
        self.csel = Gtk.ColorChooserWidget()
        self.get_content_area().append(self.csel)
        self.get_content_area().append(self.paint_toggle)

    def on_visible(self, *args):
        self.paint_toggle.set_active(self.get_visible())

    def onChangePaintMode(self, *args):
        self.f.set_paint_mode(self.paint_toggle.get_active(), self)

    def onResponse(self, widget, id):
        if id == Gtk.ResponseType.CLOSE or \
                id == Gtk.ResponseType.NONE or \
                id == Gtk.ResponseType.DELETE_EVENT:
            self.set_visible(False)

    def get_current_color(self):
        return self.csel.get_rgba()
