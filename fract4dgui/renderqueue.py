# A module which manages a queue of images to render in the background
# and a UI for the same


import copy

import gobject
import gtk

import gtkfractal
import dialog
import preferences

class QueueEntry:
    def __init__(self, f, name, w, h):
        self.f = f
        self.name = name
        self.w = w
        self.h = h
        
# the underlying queue object
class T(gobject.GObject):
    __gsignals__ = {
        'done' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, ()),
        'changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, ()),
        'progress-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_FLOAT,))
        }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.queue = []
        self.current = None
        
    def add(self,f,name,w,h):
        entry = QueueEntry(copy.copy(f),name,w,h)
        self.queue.append(entry)
        self.emit('changed')
        
    def start(self):
        if self.current == None:
            self.next()

    def empty(self):
        return self.queue == []
    
    def next(self):
        if self.empty():
            self.current = None
            self.emit('done')
            return

        entry = self.queue[0]

        self.current = gtkfractal.HighResolution(entry.f.compiler,entry.w,entry.h)
        self.current.set_fractal(entry.f)
        
        self.current.connect('status-changed', self.onImageComplete)
        self.current.connect('progress-changed', self.onProgressChanged)

        self.current.set_nthreads(preferences.userPrefs.getint("general","threads"))
        self.current.draw_image(entry.name)

    def onImageComplete(self, f, status):
        if status == 0:
            self.queue.pop(0)
            self.emit('changed')
            self.next()

    def onProgressChanged(self,f,progress):
        self.emit('progress-changed',progress)
        
# explain our existence to GTK's object system
gobject.type_register(T)

def show(parent, alt_parent, f):
    QueueDialog.show(parent, alt_parent, f)

instance = T()

class CellRendererProgress(gtk.GenericCellRenderer):

    __gproperties__ = {
        "progress": (gobject.TYPE_FLOAT, "Progress", 
                    "Progress (0.0-100.0)", 0.0, 100.0, 0,
                    gobject.PARAM_READWRITE),
    }
                     
    def __init__(self):
        self.__gobject_init__()
        self.progress = 0.0

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def on_render(self, window, widget, background_area,
                  cell_area, expose_area, flags):

        x_offset, y_offset, width, height = self.on_get_size(widget, cell_area)
        widget.style.paint_box(window, gtk.STATE_NORMAL, gtk.SHADOW_IN,
                               None, widget, "",
                               cell_area.x+x_offset, cell_area.y+y_offset,
                               width, height)

        xt = widget.style.xthickness
        xpad = self.get_property("xpad")
        space = (width-2*xt-2*xpad)*(self.progress/100.)

        widget.style.paint_box(window, gtk.STATE_PRELIGHT, gtk.SHADOW_OUT,
                               None, widget, "bar",
                               cell_area.x+x_offset+xt,
                               cell_area.y+y_offset+xt,
                               int(space), height-2*xt)

    def on_get_size(self, widget, cell_area):
        xpad = self.get_property("xpad")
        ypad = self.get_property("ypad")
        if cell_area:
            width = cell_area.width
            height = cell_area.height
            x_offset = xpad
            y_offset = ypad
        else:
            width = self.get_property("width")
            height = self.get_property("height")
            if width == -1: width = 100
            if height == -1: height = 30
            width += xpad*2
            height += ypad*2
            x_offset = 0
            y_offset = 0
        return x_offset, y_offset, width, height

gobject.type_register(CellRendererProgress)

class QueueDialog(dialog.T):
    def show(parent, alt_parent, f):
        dialog.T.reveal(QueueDialog,True, parent, alt_parent, f)
            
    show = staticmethod(show)

    def __init__(self, main_window, f):
        dialog.T.__init__(
            self,
            _("Render Queue"),
            main_window,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.main_window = main_window

        self.q = instance

        self.q.connect('changed', self.onQueueChanged)
        self.q.connect('progress-changed', self.onProgressChanged)
        
        self.controls = gtk.VBox()
        self.store = gtk.ListStore(
            gobject.TYPE_STRING, # name
            gobject.TYPE_STRING, # size
            gobject.TYPE_FLOAT, # % complete
            )

        self.view = gtk.TreeView(self.store)
        column = gtk.TreeViewColumn(
            _('_Name'),gtk.CellRendererText(),text=0)
        self.view.append_column(column)
        column = gtk.TreeViewColumn(
            _('_Size'),gtk.CellRendererText(),text=1)
        self.view.append_column(column)
        column = gtk.TreeViewColumn(
            _('_Progress'),CellRendererProgress(),progress=2)
        self.view.append_column(column)
        
        self.controls.add(self.view)
        self.vbox.add(self.controls)

    def onQueueChanged(self,q):
        self.store.clear()
        for item in self.q.queue:
            self.store.append((item.name,"%dx%d" % (item.w,item.h),0.0))

    def onProgressChanged(self,f,progress):
        iter = self.store.get_iter_first()
        if iter:
            self.store.set_value(iter,2,progress)
    
