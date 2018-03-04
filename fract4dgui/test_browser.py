#!/usr/bin/env python3

#unit tests for browser window

import unittest
import os
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d import fc, fractal
from fract4dgui import browser

class MockMainWindow:
    def __init__(self):
        self.window = None
        self.compiler = fc.Compiler()
        self.compiler.add_func_path("../formulas")
        self.compiler.add_func_path("../fract4d")

class Test(unittest.TestCase):
    def setUp(self):
        self.mainWindow = MockMainWindow()
        self.f = fractal.T(self.mainWindow.compiler,self)
    
    def tearDown(self):
        browser._model = None
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def testCreate(self):
        b = browser.BrowserDialog(self.mainWindow, self.f)
        self.assertNotEqual(b,None)

    def testSetFormula(self):
        b = browser.BrowserDialog(self.mainWindow, self.f)
        b.set_file('gf4d.frm')
        b.set_formula('Newton')
        self.assertEqual(b.ir.errors,[])

    def testBadFormula(self):
        b = browser.BrowserDialog(self.mainWindow, self.f)
        #print b.model.compiler.path_lists[0]
        b.set_file('test.frm')
        b.set_formula('parse_error')
        self.assertNotEqual(b.ir.errors,[])
        buffer = b.msgtext.get_buffer()
        all_text = buffer.get_text(
            buffer.get_start_iter(),
            buffer.get_end_iter(),
            True)
        self.assertNotEqual(all_text,"")
        self.assertEqual(all_text[0:7],"Errors:")

    def test_init(self):
        b = browser.BrowserDialog(self.mainWindow, self.f)
        m = b.model
        self.assertEqual('gf4d.frm', m.current.fname)
        self.assertEqual('Mandelbrot', m.current.formula)

    def testLoadFormula(self):
        b = browser.BrowserDialog(self.mainWindow, self.f)
        m = b.model
        # load good formula file
        b.load_file("../formulas/fractint.cfrm")
        self.assertEqual('fractint.cfrm', m.current.fname, "failed to load formula")
        # load missing file
        self.assertRaises(OSError, b.load_file, "/no_such_dir/wibble.frm")

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
