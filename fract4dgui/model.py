# The top-level data structure behind the UI. Corresponds to the MainWindow

from . import gtkfractal
from . import undo
import re

# We eavesdrop on parameter-changed notifications from the gtkfractal
# and use those to compile the history

class Model:
    def __init__(self,f):
        # undo history
        self.seq = undo.Sequence()

        # used to prevent undo/redo from triggering new commands
        self.callback_in_progress = False
        self.f = f
        self.old_f = self.f.serialize()
        self.f.connect('parameters-changed',self.onParametersChanged)

    def block_callbacks(self):
        self.callback_in_progress = True

    def unblock_callbacks(self):
        self.callback_in_progress = False

    def callbacks_allowed(self):
        return not self.callback_in_progress
    
    def onParametersChanged(self,*args):
        if not self.callbacks_allowed():
            return

        #print "before:"
        #print self.dump_history()
        
        current = self.f.serialize()

        def set_fractal(val):
            self.f.freeze()
            #print "redo:", current[:100]
            self.f.deserialize(val)
            if self.f.thaw():
                self.block_callbacks()
                self.f.changed()
                self.unblock_callbacks()
                
        self.seq.do(set_fractal,current,set_fractal,self.old_f)
        self.old_f = current

        #print "after:"
        #print self.dump_history()
        
    def extract_x_from_dump(self,dump):
        "Get (x=number) from file"
        x_re = re.compile(r'x=.*')
        m = x_re.search(dump)
        if m:
            return m.group()
        return "eek"
    
    def dump_history(self):
        i=0
        print("(redo,undo)")
        for he in self.seq.history:
            if i == self.seq.pos:
                print("-->", end=' ')
            else:
                print("   ", end=' ')
            print("(%s,%s)" % \
                  (self.extract_x_from_dump(he.redo_data),
                   self.extract_x_from_dump(he.undo_data)))
            i += 1
        
    def undo(self):
        if self.seq.can_undo():
            #print "before undo:"
            #print self.dump_history()
            self.seq.undo()
            #print "after undo:"
            #print self.dump_history()

    def redo(self):
        if self.seq.can_redo():
            #print "before redo:"
            #print self.dump_history()
            self.seq.redo()
            #print "after redo:"
            #print self.dump_history()
