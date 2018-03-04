#!/usr/bin/env python3

# unit tests for renderqueue module

import unittest
import sys
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d import fractal, fc, fractconfig
from fract4dgui import preferences, renderqueue

g_comp = fc.Compiler(fractconfig.T(""))
g_comp.add_func_path("../fract4d")
g_comp.add_func_path("../formulas")

userPrefs = preferences.Preferences(fractconfig.T(""))

class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def wait(self):
        Gtk.main()
        
    def quitloop(self,rq):
        Gtk.main_quit()

    def testRQ(self):
        rq = renderqueue.T(userPrefs)
        self.assertEqual(0, len(rq.queue))

        # should be a no-op
        rq.start()

        # add a fractal to generate
        f = fractal.T(g_comp)
        rq.add(f,"rq1.png",100,1536)

        # check it got added
        self.assertEqual(1, len(rq.queue))
        entry = rq.queue[0]
        self.assertEqual("rq1.png", entry.name)
        self.assertEqual(100, entry.w)
        self.assertEqual(1536, entry.h)

        # run
        rq.connect('done', self.quitloop)
        rq.start()
        self.wait()

        self.assertEqual(0, len(rq.queue))
        os.remove("rq1.png")

    def testQueueDialog(self):
        f = fractal.T(g_comp)
        rq = renderqueue.T(userPrefs)
        rq.add(f,"foo.png",124,276)
        rq.add(f,"foo2.png",204,153)
        rq.add(f,"foo3.png",80,40)
        rq.connect('done', self.quitloop)
        rq.start()
        d = renderqueue.QueueDialog(None, f, rq)
        d.show()
        self.wait()
        os.remove("foo.png"); os.remove("foo2.png"); os.remove("foo3.png")

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
