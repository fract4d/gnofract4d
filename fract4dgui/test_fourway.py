#!/usr/bin/env python3

# unit tests for model

import unittest

import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
from gi.repository import GObject

import fourway

class EmitCounter:
    def __init__(self):
        self.count = 0
    def onCallback(self,*args):
        self.count += 1
        
class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def testCreate(self):
        f = fourway.T("hello")
        self.assertTrue(f)
        
    def testAddToWindow(self):
        w = Gtk.Window()
        f = fourway.T("wibble")
        w.add(f.widget)
        w.show()
        Gtk.main_iteration()

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
