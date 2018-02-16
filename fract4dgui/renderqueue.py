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

class CellRendererProgress(Gtk.CellRendererProgress):
    def __init__(self):
        Gtk.CellRendererProgress.__init__(self)
        self.set_property("text", "Progress")

class QueueDialog(dialog.T):
    def __init__(self, main_window, f, renderQueue):
        dialog.T.__init__(
            self,
            _("Render Queue"),
            main_window,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        )

        self.q = renderQueue

        self.q.connect('changed', self.onQueueChanged)
        self.q.connect('progress-changed', self.onProgressChanged)
        
        self.controls = Gtk.VBox()
        self.store = Gtk.ListStore(
            GObject.TYPE_STRING, # name
            GObject.TYPE_STRING, # size
            GObject.TYPE_FLOAT, # % complete
            )

        self.view = Gtk.TreeView.new_with_model(self.store)
        column = Gtk.TreeViewColumn(
            _('_Name'),Gtk.CellRendererText(),text=0)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn(
            _('_Size'),Gtk.CellRendererText(),text=1)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn(
            _('_Progress'),CellRendererProgress(),value=2)
        self.view.append_column(column)
        
        self.controls.add(self.view)
        self.vbox.add(self.controls)
        self.vbox.show_all()

    def onQueueChanged(self,q):
        self.store.clear()
        for item in self.q.queue:
            self.store.append((item.name,"%dx%d" % (item.w,item.h),0.0))

    def onProgressChanged(self,f,progress):
        iter = self.store.get_iter_first()
        if iter:
            self.store.set_value(iter,2,progress)
    
