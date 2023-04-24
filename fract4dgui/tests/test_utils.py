# unit tests for utils module

import unittest

import gi
gi.require_version('Gtk', '4.0')

from fract4dgui import utils


class Test(unittest.TestCase):
    def testOptionMenu(self):
        om = utils.combo_box_text_with_items(["foo", "bar", "Bazniculate Geometry"])
        om.append_text("fishy")
        om.set_active(3)
        self.assertEqual(3, om.get_active())
