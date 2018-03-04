#!/usr/bin/env python3

# unit tests for utils module

import unittest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import utils

class Test(unittest.TestCase):
    def testOptionMenu(self):
        om = utils.create_option_menu(["foo","bar","Bazniculate Geometry"])
        utils.add_menu_item(om,"fishy")
        utils.set_selected(om,3)
        self.assertEqual(3, utils.get_selected(om))

        utils.set_menu_from_list(om, ["hello","world"])
        utils.set_selected(om,1)
        item1 = utils.get_selected_value(om)
        self.assertEqual("world",item1)

        utils.set_selected_value(om,"hello")
        i = utils.get_selected(om)
        self.assertEqual(0,i)

        utils.set_selected_value(om,"world")
        i = utils.get_selected(om)
        self.assertEqual(1,i)
        
    def testCreateColor(self):
        cyan = utils.create_color(0.0,1.0,1.0)
        self.assertEqual(cyan.red,0)
        self.assertEqual(cyan.green,65535)
        self.assertEqual(cyan.blue,65535)


def suite():
    s = unittest.makeSuite(Test,'test')
    return s

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
