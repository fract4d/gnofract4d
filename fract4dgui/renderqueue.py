# A module which manages a queue of images to render in the background
# and a UI for the same


import copy

from gi.repository import Gtk, GObject

from . import dialog, gtkfractal


class QueueEntry:
    def __init__(self, f, name, w, h):
        self.f = f
        self.name = name
        self.w = w
        self.h = h

# the underlying queue object


class T(GObject.GObject):
    __gsignals__ = {
        'done': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, ()),
        'changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, ()),
        'progress-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_FLOAT,))
    }

    def __init__(self, userPrefs):
        GObject.GObject.__init__(self)
        self.userPrefs = userPrefs
        self.queue = []
        self.current = None

    def add(self, f, name, w, h):
        entry = QueueEntry(copy.copy(f), name, w, h)
        self.queue.append(entry)
        self.emit('changed')

    def start(self):
        if self.current is None:
            next(self)

    def empty(self):
        return self.queue == []

    def __next__(self):
        if self.empty():
            self.current = None
            self.emit('done')
            return

        entry = self.queue[0]

        self.current = gtkfractal.HighResolution(
            entry.f.compiler, entry.w, entry.h)
        self.current.set_fractal(entry.f)

        self.current.connect('status-changed', self.onImageComplete)
        self.current.connect('progress-changed', self.onProgressChanged)

        self.current.set_nthreads(self.userPrefs.getint("general", "threads"))
        self.current.draw_image(entry.name)

    def onImageComplete(self, f, status):
        if status == 0:
            self.queue.pop(0)
            self.emit('changed')
            next(self)

    def onProgressChanged(self, f, progress):
        self.emit('progress-changed', progress)


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
        self.q.connect('done', self.onQueueDone)

        self.store = Gtk.ListStore(
            str,  # name
            str,  # size
            float  # % complete
        )

        self.view = Gtk.TreeView.new_with_model(self.store)
        column = Gtk.TreeViewColumn(
            _('_Name'), Gtk.CellRendererText(), text=0)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn(
            _('_Size'), Gtk.CellRendererText(), text=1)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn(
            _('_Progress'), CellRendererProgress(), value=2)
        self.view.append_column(column)

        self.vbox.add(self.view)

    def onQueueChanged(self, q):
        self.store.clear()
        for item in self.q.queue:
            self.store.append((item.name, "%dx%d" % (item.w, item.h), 0.0))

    def onProgressChanged(self, f, progress):
        iter = self.store.get_iter_first()
        if iter:
            self.store.set_value(iter, 2, progress)

    def onQueueDone(self, q):
        self.hide()

    def show(self):
        Gtk.Dialog.show(self)
        self.vbox.show_all()
