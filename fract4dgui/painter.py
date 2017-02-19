# GUI for painting colors onto the fractal

from gi.repository import Gtk

from . import dialog
from . import browser
from . import utils

def show(parent,f):
    PainterDialog.show(parent,f)

class PainterDialog(dialog.T):
    def show(parent, f):
        dialog.T.reveal(PainterDialog, True, parent, None, f)

    show = staticmethod(show)
    
    def __init__(self,main_window,f):
        dialog.T.__init__(
            self,
            _("Painter"),
            main_window,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        self.main_window = main_window
        self.f = f
        self.paint_toggle = Gtk.ToggleButton(_("Painting"))
        self.paint_toggle.set_active(True)
        self.paint_toggle.connect('toggled',self.onChangePaintMode)
        self.csel = Gtk.ColorSelection()
        self.vbox.add(self.csel)
        self.vbox.add(self.paint_toggle)
        self.vbox.show_all()
        self.onChangePaintMode()
        
    def onChangePaintMode(self,*args):
        self.f.set_paint_mode(self.paint_toggle.get_active(), self.csel)
        
    def onResponse(self,widget,id):
        if id == Gtk.ResponseType.CLOSE or \
               id == Gtk.ResponseType.NONE or \
               id == Gtk.ResponseType.DELETE_EVENT:
            self.hide()
            self.f.set_paint_mode(False,None) 
