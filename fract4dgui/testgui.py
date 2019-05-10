#!/usr/bin/env python3

# Setup defaults for GUI tests including temp directory for cache

import os.path
import tempfile
import unittest

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from fract4d import fc, fractconfig

class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory(prefix="fract4d_")
        cls.userConfig = fractconfig.T("")
        cls.userConfig.set("general","cache_dir", os.path.join(cls.tmpdir.name,
                           "gnofract4d-cache"))
        cls.userConfig["formula_path"].clear()
        cls.userConfig["map_path"].clear()
        cls.g_comp = fc.Compiler(cls.userConfig)
        cls.g_comp.add_func_path("fract4d")
        cls.g_comp.add_func_path("formulas")

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()
