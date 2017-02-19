# GUI for painting colors onto the fractal

import gtk

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
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.main_window = main_window
        self.f = f
        self.paint_toggle = gtk.ToggleButton(_("Painting"))
        self.paint_toggle.set_active(True)
        self.paint_toggle.connect('toggled',self.onChangePaintMode)
        self.csel = gtk.ColorSelection()
        self.vbox.add(self.csel)
        self.vbox.add(self.paint_toggle)
        self.vbox.show_all()
        self.onChangePaintMode()
        
    def onChangePaintMode(self,*args):
        self.f.set_paint_mode(self.paint_toggle.get_active(), self.csel)
        
    def onResponse(self,widget,id):
        if id == gtk.RESPONSE_CLOSE or \
               id == gtk.RESPONSE_NONE or \
               id == gtk.RESPONSE_DELETE_EVENT:
            self.hide()
            self.f.set_paint_mode(False,None) 
