#!/usr/bin/env python3

# unit tests for model

from fract4dgui import fourway

import unittest

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gtk


class Test(unittest.TestCase):
    def testCreate(self):
        f = fourway.T("hello", "fourway")
        self.assertTrue(f)

    def testAddToWindow(self):
        w = Gtk.Window()
        f = fourway.T("wibble", "fourway")
        w.add(f)
        w.show()
        Gtk.main_iteration()

    def testMouseButton1(self):
        f = fourway.T("button1", "fourway")
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
