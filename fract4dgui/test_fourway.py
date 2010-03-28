#!/usr/bin/env python

# unit tests for model

import unittest

import gtk
import gobject

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
        gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            gtk.main_quit()

    def testCreate(self):
        f = fourway.T("hello")
        self.failUnless(f)
        
    def testAddToWindow(self):
        w = gtk.Window()
        f = fourway.T("wibble")
        w.add(f.widget)
        w.show()
        gtk.main_iteration()

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
