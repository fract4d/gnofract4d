#!/usr/bin/env python3

#unit tests for settings window

import unittest
import copy
import math
import os
import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d import fc, fractal
from fract4dgui import settings
from fract4dgui import gtkfractal

class Test(unittest.TestCase):
    def setUp(self):
        self.compiler = fc.Compiler()
        self.compiler.add_func_path("../formulas")
        self.compiler.add_func_path("../fract4d")
        
        self.f = gtkfractal.T(self.compiler)
        self.settings = settings.SettingsPane(None,self.f)
        
    def tearDown(self):
        pass
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def search_for_named_widget(self, page, label_name):
        for child in page.get_children():
            if isinstance(child, Gtk.Label):
                this_label_name = child.get_text()
                #print this_label_name
                if this_label_name == label_name:
                    entry = child.get_mnemonic_widget()
                    self.assertNotEqual(entry, None,
                                        "all widgets should have mnemonics")
                    self.assertEqual(isinstance(entry,Gtk.Entry),True)
                    return entry
            elif isinstance(child, Gtk.Container):
                widget = self.search_for_named_widget(child,label_name)
                if widget:
                    return widget
        
    def get_param_entry(self, page_name, label_name):
        'Find and return an entry widget on the settings dialog'
        notebook = self.settings.notebook
        i = 0
        page = notebook.get_nth_page(0)
        while page != None:
            this_page_name = notebook.get_tab_label_text(page)
            if this_page_name == page_name:
                widget = self.search_for_named_widget(page,label_name)
                self.assertNotEqual(
                    widget, None,
                    "Page doesn't contain widget '%s'" % label_name)
                return widget
            i += 1
            page = notebook.get_nth_page(i)
            
        self.fail("Can't find page %s" % page_name)

    def get_first_transform(self):
        iter = self.settings.transform_store.get_iter_first()
        if iter == None:
            return None
        val = self.settings.transform_store.get(iter,0)[0]
        return val
    
    def testFractalChangeUpdatesSettings(self):
        self.f.set_param(self.f.MAGNITUDE, 2000.0)
        widget = self.get_param_entry(_("Location"), _("Size :"))
        self.assertEqual(widget.get_text(),"2000.00000000000000000")

        self.f.forms[0].set_named_param("@bailout", 578.0)
        self.assertEqual(
            self.f.forms[0].get_named_param_value("@bailout"), 578.0)
        
        widget = self.get_param_entry(_("Formula"), _("Bailout"))
        self.assertEqual(widget.get_text(),"578.00000000000000000")

        self.assertEqual(None, self.get_first_transform())
        self.f.append_transform("gf4d.uxf","Inverse")
        
        self.assertEqual("Inverse", self.get_first_transform())

    def testPages(self):
        notebook = self.settings.notebook
        n = notebook.get_n_pages()
        i = 0
        pagelist = []
        exp_pagelist = [
            _("Formula"), _("Outer"), _("Inner"),
            _("Transforms"), _("General"), _("Location"),
            _("Colors")]
        
        while i < n:
            page = notebook.get_nth_page(i)
            title = notebook.get_tab_label_text(page)
            pagelist.append(title)
            i += 1

        self.assertEqual(exp_pagelist, pagelist)

    def testColorsPage(self):
        gradarea = self.settings.gradarea
            
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
