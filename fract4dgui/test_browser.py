#!/usr/bin/env python

#unit tests for browser window

import unittest
import copy
import math
import os
import sys

import gtk
import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')
sys.path.insert(1, "..")

from fract4d import fc, fractal, browser_model
import browser


class Test(unittest.TestCase):
    def setUp(self):
        self.compiler = fc.instance
        self.compiler.add_func_path("../formulas")
        self.compiler.add_func_path("../fract4d")
        
        self.f = fractal.T(self.compiler,self)
    
    def tearDown(self):
        browser._model = None
        
    def wait(self):
        gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            gtk.main_quit()

    def testCreate(self):        
        b = browser.BrowserDialog(None,self.f)
        self.assertNotEqual(b,None)

    def testLoadFormula(self):
        b = browser.BrowserDialog(None,self.f)
        b.set_file('gf4d.frm')
        b.set_formula('Newton')
        self.assertEqual(b.ir.errors,[])

    def testBadFormula(self):
        b = browser.BrowserDialog(None,self.f)
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

    def test_update(self):
        b = browser.BrowserDialog(None,self.f)
        b = browser.update(None)
        m = browser_model.instance
        self.assertEqual(None, m.current.fname)
        self.assertEqual(None, m.current.formula)


def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
