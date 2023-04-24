# unit tests for director_prefs module

from unittest.mock import patch

from . import testgui

from gi.repository import Gtk

from fract4dgui import director_dialogs, utils
from fract4d import fractal, animation


class MockFileChooser:
    def __init__(self, filepath):
        self.filepath = filepath

    def get_path(self):
        return self.filepath


class Test(testgui.TestCase):
    def setUp(self):
        super().setUp()
        f = fractal.T(Test.g_comp)
        self.test_animation = animation.T(f.compiler, Test.userConfig)

    def testDirectorPrefsDialog(self):
        parent = Gtk.Window()
        dp = director_dialogs.DirectorPrefs(self.test_animation, parent)

        self.assertEqual(dp.chk_create_fct.get_label(), "Create temporary .fct files")

    @patch("gi.repository.Gtk.FileChooserDialog.connect")
    @patch("gi.repository.Gtk.FileChooserDialog.get_file")
    def testGetFolder(self, mock_dialog_get_file, mock_dialog_connect):
        filename = "test_file"
        mock_dialog_get_file.side_effect = lambda: MockFileChooser(filename)
        mock_dialog_connect.side_effect = \
            lambda signal, response: \
            response(utils.DirectoryChooser("test", None), Gtk.ResponseType.OK)

        parent = Gtk.Window()
        dp = director_dialogs.DirectorPrefs(self.test_animation, parent)

        def callback1(temp_file):
            self.assertEqual(temp_file, filename)
        dp.get_folder(callback1)

        def callback2(temp_file):
            self.fail("DirectorPrefs called callback on CANCEL")
        mock_dialog_connect.side_effect = \
            lambda signal, response: \
            response(utils.DirectoryChooser("test", None), Gtk.ResponseType.CANCEL)
        dp.get_folder(callback2)

    def testDlgAdvOptions(self):
        parent = Gtk.Window()
        self.test_animation.add_keyframe(
            "testdata/director1.fct", 1, 10, animation.INT_LOG)
        dao = director_dialogs.DlgAdvOptions(0, self.test_animation, parent)
        dao.show_dialog()
        self.assertTrue(dao.animation.keyframes[0].flags)
