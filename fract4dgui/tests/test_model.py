#!/usr/bin/env python3

# unit tests for model

import io

from . import testgui

from gi.repository import Gtk

from fract4dgui import model, gtkfractal

class EmitCounter:
    def __init__(self):
        self.count = 0
    def onCallback(self,*args):
        self.count += 1
        
class Test(testgui.TestCase):
    def setUp(self):
        Test.g_comp.add_func_path("formulas")
        Test.g_comp.load_formula_file("gf4d.frm")
        Test.g_comp.load_formula_file("gf4d.cfrm")
        self.f = gtkfractal.T(Test.g_comp)
        self.m = model.Model(self.f)
    
    def tearDown(self):
        self.f = self.m = None
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def testCreate(self):
        self.assertTrue(self.f)
        self.assertTrue(self.m)
        self.assertEqual(self.m.f, self.f)

    def testPreserveYFlip(self):
        f = self.m.f

        self.assertEqual(f.yflip,False)
        f.set_yflip(True)

        self.assertEqual(f.yflip,True)
        
        f.get_param(f.MAGNITUDE)
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
        
        f.save(io.StringIO(""))
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
