#!/usr/bin/env python3

# unit tests for undo code

import unittest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import undo

class Status:
    def __init__(self):
        self.count = 0
        
class UndoTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def assertUndoStatus(self,undoer,should_undo,should_redo):
        self.assertEqual(undoer.can_undo(),should_undo)
        self.assertEqual(undoer.can_redo(),should_redo)
        self.assertExternalAndInternalStatusMatch(undoer)

    def assertExternalAndInternalStatusMatch(self,undoer):
        self.assertEqual(self.undo_cb_status.count, undoer.can_undo())
        self.assertEqual(self.redo_cb_status.count, undoer.can_redo())
        
    def testCreateUndoRedo(self):
        status = Status()
        self.undo_cb_status = Status()
        self.redo_cb_status = Status()
        
        def inc_status(x):
            status.count += x
            
        def dec_status(x):
            status.count -= x

        def set_undoable(sequence,state):
            #print "undo_status: %s" % state
            self.undo_cb_status.count = state

        def set_redoable(sequence,state):
            #print "redo_status: %s" % state
            self.redo_cb_status.count = state
            
        self.assertEqual(status.count,0)
        self.assertEqual(self.undo_cb_status.count,0)
        self.assertEqual(self.redo_cb_status.count,0)
                
        # create sequence
        undoer = undo.Sequence()
        undoer.connect('can-undo',set_undoable)
        undoer.connect('can-redo',set_redoable)
        
        self.assertEqual(undoer.can_undo(),False)
        self.assertEqual(undoer.can_redo(),False)
        self.assertExternalAndInternalStatusMatch(undoer)
        
        self.assertEqual(undoer.pos,0)
        self.assertEqual(len(undoer.history),0)
        
        # perform an action
        inc_status(1)
        undoer.do(inc_status,1,dec_status,1)
        
        self.assertEqual(status.count,1)
        self.assertUndoStatus(undoer,True,False)
        self.assertEqual(len(undoer.history),1)
        self.assertEqual(undoer.pos,1)

        # undo it
        undoer.undo()

        # check externals
        self.assertEqual(status.count,0)
        self.assertUndoStatus(undoer,False,True)
        
        # check internals
        self.assertEqual(len(undoer.history),1)
        self.assertEqual(undoer.pos,0)
        
        # redo it
        undoer.redo()

        # check externals
        self.assertEqual(status.count,1)
        self.assertUndoStatus(undoer,True,False)
        
        # check internals
        self.assertEqual(len(undoer.history),1)
        self.assertEqual(undoer.pos,1)

    def testUndoAndRedoAreAssociated(self):
        status = Status()

        def inc_status(x):
            status.count += x
            
        def dec_status(x):
            status.count -= x

        def make_status_string(s):
            status.count = s

        def make_status_int(i):
            status.count = i
                    
        self.assertEqual(status.count,0)

        # create sequence
        undoer = undo.Sequence()
        inc_status(1)
        undoer.do(inc_status,1,dec_status,1)
        make_status_string("foo")
        undoer.do(make_status_string, "foo", make_status_int, 1)

        self.assertEqual(status.count,"foo")
        undoer.undo()
        self.assertEqual(status.count,1)
        undoer.undo()
        self.assertEqual(status.count,0)

    def testDoRemovesRedoStack(self):
        status = Status()

        def inc_status(x):
            status.count += x
            
        def dec_status(x):
            status.count -= x
                    
        self.assertEqual(status.count,0)

        # perform 3 actions, undo 2, do 1 again
        undoer = undo.Sequence()
        inc_status(1)
        undoer.do(inc_status,1,dec_status,1)
        inc_status(1)
        undoer.do(inc_status,1,dec_status,1)
        inc_status(1)
        undoer.do(inc_status,1,dec_status,1)
        undoer.undo()
        undoer.undo()
        self.assertEqual(status.count,1)

        inc_status(1)
        undoer.do(inc_status,1,dec_status,1)
        self.assertEqual(len(undoer.history),2)
        self.assertEqual(undoer.can_redo(), False)
        self.assertEqual(status.count,2)

        # undo again, check we're back where we started
        undoer.undo()
        self.assertEqual(status.count,1)
        
    def testInvalidOperationsThrow(self):
        undoer = undo.Sequence()
        self.assertRaises(ValueError,undoer.undo)
        self.assertRaises(ValueError,undoer.redo)
        
def suite():
    return unittest.makeSuite(UndoTest,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
