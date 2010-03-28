# superclass for dialogs

import gtk
import new

_dialogs = {}

def make_container(title):
    label_box = gtk.HBox()
    label = gtk.Label('<span weight="bold">%s</span>' % title)
    label.set_use_markup(True)
    label_box.pack_start(label, False, False)
    close = gtk.Button(None, gtk.STOCK_CLOSE)
    label_box.pack_end(close, False, False)
    frame = gtk.VBox()
    frame.pack_start(label_box, False, False, 1)

    close.connect('clicked', lambda x : frame.hide())
    return frame

class T(gtk.Dialog):
    def __init__(self,title=None,parent=None,flags=0,buttons=None):
        gtk.Dialog.__init__(self,title,parent,flags,buttons)

        self.set_default_response(gtk.RESPONSE_CLOSE)
        self.connect('response',self.onResponse)

        self.connect('destroy-event', self.clear_global)
        self.connect('delete-event', self.clear_global)

    def clear_global(self,*args):
        global _dialogs
        _dialogs[self.__class__] = None
    
    def reveal(type, dialog_mode, parent, alt_parent, *args):
        global _dialogs
        if not _dialogs.get(type):
            _dialogs[type] = type(parent, *args)
        if dialog_mode:
            _dialogs[type].show_all()
            _dialogs[type].present()
        else:
            if not hasattr(alt_parent, "dialogs"):
                alt_parent.dialogs = {}
            container = alt_parent.dialogs.get(type)
            if not container:                
                dialog = _dialogs[type]
                box = dialog.controls
                title = dialog.get_title()
                container = make_container(title)
                box.reparent(container)
                alt_parent.pack_start(container,True,True,0)
                alt_parent.dialogs[type] = container

            container.show_all()
            _dialogs[type].hide()
        
        return _dialogs[type]
    
    reveal = staticmethod(reveal)

    def onResponse(self,widget,id):
        if id == gtk.RESPONSE_CLOSE or \
               id == gtk.RESPONSE_NONE or \
               id == gtk.RESPONSE_DELETE_EVENT:
            self.hide()
        else:
            print "unexpected response %d" % id

def get(type):
    global _dialogs
    return _dialogs.get(type)
