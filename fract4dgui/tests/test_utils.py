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
