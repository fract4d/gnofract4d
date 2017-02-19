# A module which manages a queue of images to render in the background
# and a UI for the same


import copy

from gi.repository import GObject
from gi.repository import Gtk

from . import gtkfractal
from . import dialog
from . import preferences

class QueueEntry:
    def __init__(self, f, name, w, h):
        self.f = f
        self.name = name
        self.w = w
        self.h = h
        
# the underlying queue object
class T(GObject.GObject):
    __gsignals__ = {
        'done' : (
        (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
        None, ()),
        'changed' : (
        (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
        None, ()),
        'progress-changed' : (
        (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
        None, (GObject.TYPE_FLOAT,))
        }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.queue = []
        self.current = None
        
    def add(self,f,name,w,h):
        entry = QueueEntry(copy.copy(f),name,w,h)
        self.queue.append(entry)
        self.emit('changed')
        
    def start(self):
        if self.current == None:
            next(self)

    def empty(self):
        return self.queue == []
    
    def __next__(self):
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
            next(self)

    def onProgressChanged(self,f,progress):
        self.emit('progress-changed',progress)
        
# explain our existence to GTK's object system
GObject.type_register(T)

def show(parent, alt_parent, f):
    QueueDialog.show(parent, alt_parent, f)

instance = T()

class CellRendererProgress(Gtk.GenericCellRenderer):

    __gproperties__ = {
        "progress": (GObject.TYPE_FLOAT, "Progress", 
                    "Progress (0.0-100.0)", 0.0, 100.0, 0,
                    GObject.PARAM_READWRITE),
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
        widget.style.paint_box(window, Gtk.StateType.NORMAL, Gtk.ShadowType.IN,
                               None, widget, "",
                               cell_area.x+x_offset, cell_area.y+y_offset,
                               width, height)

        xt = widget.style.xthickness
        xpad = self.get_property("xpad")
        space = (width-2*xt-2*xpad)*(self.progress/100.)

        widget.style.paint_box(window, Gtk.StateType.PRELIGHT, Gtk.ShadowType.OUT,
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

GObject.type_register(CellRendererProgress)

class QueueDialog(dialog.T):
    def show(parent, alt_parent, f):
        dialog.T.reveal(QueueDialog,True, parent, alt_parent, f)
            
    show = staticmethod(show)

    def __init__(self, main_window, f):
        dialog.T.__init__(
            self,
            _("Render Queue"),
            main_window,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        self.main_window = main_window

        self.q = instance

        self.q.connect('changed', self.onQueueChanged)
        self.q.connect('progress-changed', self.onProgressChanged)
        
        self.controls = Gtk.VBox()
        self.store = Gtk.ListStore(
            GObject.TYPE_STRING, # name
            GObject.TYPE_STRING, # size
            GObject.TYPE_FLOAT, # % complete
            )

        self.view = Gtk.TreeView(self.store)
        column = Gtk.TreeViewColumn(
            _('_Name'),Gtk.CellRendererText(),text=0)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn(
            _('_Size'),Gtk.CellRendererText(),text=1)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn(
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
    
