#!/usr/bin/env python3

#unit tests for settings window

import unittest
import copy
import math
import os
import sys

from gi.repository import Gtk
import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')
sys.path.insert(1, "..")

from fract4d import fc, fractal
from . import painter
from . import gtkfractal

class FakeEvent:
    def __init__(self,**kwds):
        self.__dict__.update(kwds)

class Test(unittest.TestCase):
    def setUp(self):
        self.compiler = fc.Compiler()
        self.compiler.add_func_path("../formulas")
        self.compiler.add_func_path("../fract4d")
        
        self.f = gtkfractal.T(self.compiler)
        self.settings = painter.PainterDialog(None,self.f)

    def tearDown(self):
        pass
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def testPaintOnUnknown(self):
        self.assertEqual(True, self.f.paint_mode)
        event = FakeEvent(x=0,y=0,button=1)
        self.f.onButtonPress(self.f.widget,event)
        self.f.onButtonRelease(self.f.widget,event)

        
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
