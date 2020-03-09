#!/usr/bin/env python3

# unit tests for model

from fract4dgui import fourway
from gi.repository import Gtk
import unittest

import gi
gi.require_version('Gtk', '3.0')


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
