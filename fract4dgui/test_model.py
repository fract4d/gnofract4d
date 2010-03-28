#!/usr/bin/env python

# unit tests for model

import unittest
import copy
import sys
import StringIO

import gtk

sys.path.insert(1, "..")

import model

from fract4d import fractal,fc,fract4dc

import gtkfractal
import settings
import preferences
import autozoom
import undo

# do compiler setup once
g_comp = fc.Compiler()
g_comp.add_func_path("../formulas")
g_comp.add_func_path("formulas")
g_comp.load_formula_file("gf4d.frm")
g_comp.load_formula_file("gf4d.cfrm")

class EmitCounter:
    def __init__(self):
        self.count = 0
    def onCallback(self,*args):
        self.count += 1
        
class Test(unittest.TestCase):
    def setUp(self):
        global g_comp
        self.compiler = g_comp
        self.f = gtkfractal.T(self.compiler)        
        self.m = model.Model(self.f)
    
    def tearDown(self):
        self.f = self.m = None
        
    def wait(self):
        gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            gtk.main_quit()

    def testCreate(self):
        self.failUnless(self.f)
        self.failUnless(self.m)
        self.assertEqual(self.m.f, self.f)

    def testPreserveYFlip(self):
        f = self.m.f

        self.assertEqual(f.yflip,False)
        f.set_yflip(True)

        self.assertEqual(f.yflip,True)
        
        mag = f.get_param(f.MAGNITUDE)
        f.set_param(f.MAGNITUDE,9.0)

        self.assertEqual(f.yflip,True)
        self.m.undo()
        self.assertEqual(f.yflip,True)
        self.m.redo()
        self.assertEqual(f.yflip,True)

        
    def testUndoChangeParameter(self):
        counter = EmitCounter()
        f = self.m.f

        f.connect('parameters-changed',counter.onCallback)
        
        f.save(StringIO.StringIO(""))
        self.assertEqual(f.saved,True)
        
        mag = f.get_param(f.MAGNITUDE)
        f.set_param(f.MAGNITUDE,9.0)

        self.assertEqual(False, f.saved)
        
        self.assertEqual(counter.count,1)
        self.assertEqual(f.get_param(f.MAGNITUDE),9.0)

        self.m.undo()

        self.assertEqual(f.saved,False)
        self.assertEqual(f.get_param(f.MAGNITUDE),mag)

        self.m.redo()
        self.assertEqual(f.get_param(f.MAGNITUDE),9.0)
        self.assertEqual(f.saved, False)
        
    def testUndoFunctionChange(self):
        counter = EmitCounter()
        f = self.m.f        
        f.connect('parameters-changed',counter.onCallback)

        bailfunc = f.forms[0].get_func_value("@bailfunc")
        self.assertEqual(bailfunc,"cmag")
        
        f.forms[0].set_named_func("@bailfunc","real2")
        self.assertEqual(counter.count,1)
        
        self.assertEqual(f.forms[0].get_func_value("@bailfunc"),"real2")
        
        self.m.undo()
        
        self.assertEqual(f.forms[0].get_func_value("@bailfunc"),bailfunc)

        self.m.redo()
        self.assertEqual(f.forms[0].get_func_value("@bailfunc"),"real2")
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
