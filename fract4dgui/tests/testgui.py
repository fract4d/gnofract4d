# Setup defaults for GUI tests including temp directory for cache

from fract4d import fractconfig
from fract4d_compiler import fc
import gi
import os
import tempfile
import unittest

import gettext

os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
gi.require_version('Graphene', '1.0')

from gi.repository import Gtk

Gtk.init()


class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory(prefix="fract4d_")

        import sys
        if sys.platform[:6] == "darwin":
            cls.userConfig = fractconfig.DarwinConfig("")
        else:
            cls.userConfig = fractconfig.T("")

        cls.userConfig.set("general", "cache_dir", os.path.join(cls.tmpdir.name,
                                                                "gnofract4d-cache"))
        cls.userConfig["formula_path"].clear()
        cls.userConfig["map_path"].clear()
        cls.g_comp = fc.Compiler(cls.userConfig)
        cls.g_comp.add_func_path("fract4d")
        cls.g_comp.add_func_path("formulas")
        cls.g_comp.add_func_path("testdata/formulas")

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()
