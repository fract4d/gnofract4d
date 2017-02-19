#!/usr/bin/env python3

# unit tests for utils module

import unittest
import sys
import os
import subprocess
import warnings

import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk

sys.path.insert(1, "..")
sys.path.insert(1, "../fract4d")

import utils
import gtkfractal

from fract4d import fc

# centralized to speed up tests
g_comp = fc.Compiler()
g_comp.add_func_path("../fract4d")
g_comp.add_func_path("../formulas")


class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

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

    def on_update_preview(self, chooser, preview):
        filename = chooser.get_preview_filename()
        try:
            preview.loadFctFile(open(filename))
            preview.draw_image(False, False)
            active=True
        except Exception as err:
            active=False
        chooser.set_preview_widget_active(active)
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def runAndDismiss(self,d, time=1):
        def dismiss():
            d.response(Gtk.ResponseType.ACCEPT)
            d.hide()
            return False

        # increase timeout to see what dialogs look like
        utils.timeout_add(10 * time,dismiss)
        r = d.run()
        d.destroy()


def suite():
    s = unittest.makeSuite(Test,'test')
    return s

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
