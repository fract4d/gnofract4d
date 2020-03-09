#!/usr/bin/env python3

# test classes for preferences logic

from fract4d import fractconfig
from fract4dgui import preferences
import unittest

import gi
gi.require_version('Gtk', '3.0')


class CallCounter:
    def __init__(self):
        self.count = 0

    def cb(self, *args):
        self.count += 1


class Test(unittest.TestCase):
    def setUp(self):
        baseconfig = fractconfig.T("test.config")
        self.config = preferences.Preferences(baseconfig)

    def tearDown(self):
        pass

    def testSignals(self):
        counter = CallCounter()

        self.config.connect('preferences-changed', counter.cb)

        # callback should happen
        self.config.set('compiler', 'name', 'cc')
        self.assertEqual(counter.count, 1)

        # no callback, value already set
        self.config.set('compiler', 'name', 'cc')
        self.assertEqual(counter.count, 1)

        # new option, callback called
        self.config.set('compiler', 'foop', 'cc')
        self.assertEqual(counter.count, 2)

    def testInstance(self):
        dummy = preferences.Preferences(fractconfig.T(""))
        self.assertNotEqual(None, dummy)
