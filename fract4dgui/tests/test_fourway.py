#!/usr/bin/env python3

# unit tests for model

from fract4dgui import fourway

import unittest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk


class EmitCounter:
    def __init__(self):
        self.count = 0

    def onCallback(self, *args):
        self.count += 1


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def wait(self):
        Gtk.main()

    def quitloop(self, f, status):
        if status == 0:
            Gtk.main_quit()

    def testCreate(self):
        f = fourway.T("hello")
        self.assertTrue(f)

    def testAddToWindow(self):
        w = Gtk.Window()
        f = fourway.T("wibble")
        w.add(f)
        w.show()
        Gtk.main_iteration()

    def testMouseButton1(self):
        f = fourway.T("button1")
        event = Gdk.EventButton()
        event.button = 1
        event.x, event.y = 1, 1
        widget = Gtk.Window()
        rectangle = Gdk.Rectangle()
        rectangle.width = 100
        rectangle.height = 100
        widget.size_allocate(rectangle)

        f.onButtonPress(widget, event)
        self.assertEqual(f.last_x, 1)

        event.x = 2
        f.onMotionNotify(widget, event)
        self.assertEqual(f.last_x, 2)

        f.onButtonRelease(widget, event)
        self.assertFalse(f.notice_mouse)
