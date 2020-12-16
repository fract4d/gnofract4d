#!/usr/bin/env python3

# unit tests for director_prefs module

from unittest.mock import patch

from . import testgui

from gi.repository import Gtk

from fract4dgui import director_prefs
from fract4d import fractal, animation


class Test(testgui.TestCase):
    def setUp(self):
        f = fractal.T(Test.g_comp)
        self.test_animation = animation.T(f.compiler, Test.userConfig)

    def testDirectorPrefsDialog(self):
        parent = Gtk.Window()
        dp = director_prefs.DirectorPrefs(self.test_animation, parent)

        self.assertEqual(dp.chk_create_fct.get_label(), "Create temporary .fct files")

    @patch("gi.repository.Gtk.FileChooserDialog.run")
    @patch("gi.repository.Gtk.FileChooserDialog.get_filename")
    def testGetFolder(self, mock_dialog_get_filename, mock_dialog_run):
        filename = "test_file"
        mock_dialog_get_filename.side_effect = lambda : filename

        parent = Gtk.Window()
        dp = director_prefs.DirectorPrefs(self.test_animation, parent)

        mock_dialog_run.side_effect = lambda : Gtk.ResponseType.OK
        self.assertEqual(dp.get_folder(), filename)

        mock_dialog_run.side_effect = lambda : Gtk.ResponseType.CANCEL
        self.assertEqual(dp.get_folder(), "")
