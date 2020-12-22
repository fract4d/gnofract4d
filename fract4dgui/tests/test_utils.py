#!/usr/bin/env python3

# unit tests for utils module

import unittest

from fract4dgui import utils


class Test(unittest.TestCase):
    def testOptionMenu(self):
        om = utils.create_option_menu(["foo", "bar", "Bazniculate Geometry"])
        om.append_text("fishy")
        om.set_active(3)
        self.assertEqual(3, om.get_active())

        utils.set_menu_from_list(om, ["hello", "world"])
        om.set_active(1)
        item1 = utils.get_selected_value(om)
        self.assertEqual("world", item1)

        utils.set_selected_value(om, "hello")
        i = om.get_active()
        self.assertEqual(0, i)

        utils.set_selected_value(om, "world")
        i = om.get_active()
        self.assertEqual(1, i)
