
from gi.repository import Gtk
from gi.repository import GObject

class HistoryEntry:
    def __init__(self,redo,redo_data,undo,undo_data):
        self.undo_action = undo
        self.undo_data = undo_data
        self.redo_action = redo
        self.redo_data = redo_data

    def undo(self):
        self.undo_action(self.undo_data)

    def redo(self):
        self.redo_action(self.redo_data)
        
class Sequence(GObject.GObject):
    __gsignals__ = {
        'can-undo' : (
        GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_BOOLEAN,)),
        'can-redo' : (
        GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_BOOLEAN,))
        }
    
    def __init__(self):
        GObject.GObject.__init__(self)
        self.pos = 0 # the position after the current item
        self.history = []

    def can_undo(self):
        return self.pos > 0

    def can_redo(self):
        return self.pos < len(self.history)

    def send_signals(self):        
        self.emit('can-undo', self.can_undo())
        self.emit('can-redo', self.can_redo())
        
    def do(self,redo_action,redo_data,undo_action,undo_data):
        # replace everything from here on with the new item
        if self.pos < len(self.history):
            undo_action = self.history[self.pos].undo_action 
            undo_data = self.history[self.pos].undo_data 

        del self.history[self.pos:]
        self.history.append(
            HistoryEntry(redo_action,redo_data,undo_action,undo_data))
        self.pos = len(self.history)

        self.send_signals()
        
    def undo(self):
        if not self.can_undo():
            raise ValueError("Can't Undo at start of sequence")
        self.pos -= 1
        self.history[self.pos].undo()
        self.send_signals()

    def redo(self):
        if not self.can_redo():
            raise ValueError("Can't Redo at end of sequence")
        self.history[self.pos].redo()
        self.pos += 1
        
        self.send_signals()

    def make_undo_sensitive(self,widget):
        # make this widget only be sensitive if we can undo

        def set_sensitivity(sequence,can_undo):
            widget.set_sensitive(can_undo)
        
        self.connect('can-undo',set_sensitivity)
        self.emit('can-undo', self.can_undo())

    def make_redo_sensitive(self,widget):
        # make this widget only be sensitive if we can undo

        def set_sensitivity(sequence,can_redo):
            widget.set_sensitive(can_redo)
        
        self.connect('can-redo',set_sensitivity)
        self.emit('can-redo', self.can_redo())

GObject.type_register(Sequence)
