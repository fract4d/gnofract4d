#!/usr/bin/env python3

# unit tests for renderqueue module

import os

from . import testgui

from gi.repository import Gtk

from fract4d import fractal
from fract4dgui import preferences, renderqueue

class Test(testgui.TestCase):
    @classmethod
    def setUpClass(cls):
        testgui.TestCase.setUpClass()
        cls.userPrefs = preferences.Preferences(testgui.TestCase.userConfig)

    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def wait(self):
        Gtk.main()
        
    def quitloop(self,rq):
        Gtk.main_quit()

    def testRQ(self):
        rq = renderqueue.T(Test.userPrefs)
        self.assertEqual(0, len(rq.queue))

        # should be a no-op
        rq.start()

        # add a fractal to generate
        f = fractal.T(Test.g_comp)
        png_file1 = os.path.join(Test.tmpdir.name, "rq1.png")
        rq.add(f,png_file1,100,1536)

        # check it got added
        self.assertEqual(1, len(rq.queue))
        entry = rq.queue[0]
        self.assertEqual(png_file1, entry.name)
        self.assertEqual(100, entry.w)
        self.assertEqual(1536, entry.h)

        # run
        rq.connect('done', self.quitloop)
        rq.start()
        self.wait()

        self.assertEqual(0, len(rq.queue))

    def testQueueDialog(self):
        f = fractal.T(Test.g_comp)
        rq = renderqueue.T(Test.userPrefs)
        png_file2 = os.path.join(Test.tmpdir.name, "foo2.png")
        png_file3 = os.path.join(Test.tmpdir.name, "foo3.png")
        rq.add(f,png_file2,204,153)
        rq.add(f,png_file3,80,40)
        rq.connect('done', self.quitloop)
        rq.start()
        parent = Gtk.Window()
        d = renderqueue.QueueDialog(parent, f, rq)
        d.show()
        self.wait()
