# unit tests for model

import unittest

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from fract4dgui import fourway


class FakeGesture:
    def __init__(self, button=1):
        self.button = button

    def get_current_button(self):
        return self.button

    def get_start_point(self):
        return True, 0, 0

    def set_state(self, state):
        pass


class Test(unittest.TestCase):
    def testCreate(self):
        f = fourway.T("hello", "fourway")
        self.assertTrue(f)

    def testAddToWindow(self):
        w = Gtk.Window()
        f = fourway.T("wibble", "fourway")
        w.set_child(f)
        w.present()

    def testMouseButton1(self):
        f = fourway.T("button1", "fourway")
        gesture = FakeGesture()

        f.onButtonPress(gesture, 1, 1)
        self.assertEqual(f.last_x, 1)

        f.onMotionNotify(gesture, 2, 1)
        self.assertEqual(f.last_x, 2)

        f.onButtonRelease(gesture, 1, 1)
        self.assertEqual(f.last_x, 2)
