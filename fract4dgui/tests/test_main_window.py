# high-level unit tests for main window

import os
import sys
import tempfile
from unittest.mock import patch

from . import testgui

from gi.repository import Gio, GLib, Gtk
import pytest

from fract4d import fractal, options
from fract4d_compiler import fc
from fract4dgui import main_window, preferences


class Application(Gtk.Application):
    def __init__(self, config):
        super().__init__()
        self.userConfig = config
        self.userPrefs = preferences.Preferences(config)
        self.compiler = fc.Compiler(config)
        self.compiler.add_func_path('formulas')
        this_path = os.path.dirname(sys.modules[__name__].__file__)
        resource = Gio.resource_load(os.path.join(this_path, "../../gnofract4d.gresource"))
        Gio.Resource._register(resource)
        self.menu_builder = Gtk.Builder.new_from_resource("/io/github/fract4d/gtk/menus.ui")

    def get_menu_by_id(self, menuid):
        return self.menu_builder.get_object(menuid)


class WrapMainWindow(main_window.MainWindow):
    def __init__(self, config):
        self.errors = []
        main_window.MainWindow.__init__(self, Application(config))

    def show_error_message(self, message, exception):
        self.errors.append((message, exception))


class MockMainWindow:
    @classmethod
    def first_draw(cls):
        pass

    @classmethod
    def present(cls):
        pass

    def apply_options(self):
        pass


class TestApplication(testgui.TestCase):
    @patch("fract4dgui.main_window.MainWindow")
    def testApplication(self, mock_mainwindow):
        mock_mainwindow.return_value = MockMainWindow
        opts = options.Arguments().parse_args(["--path", "formulas"])
        app = main_window.Application(opts, TestApplication.userConfig)
        app.run()


class Test(testgui.TestCase):
    def setUp(self):
        super().setUp()
        self.mw = WrapMainWindow(Test.userConfig)
        self.assertEqual(self.mw.filename.filename, None, "shouldn't have a filename")

    def testApplyOptions(self):
        opts = options.Arguments().parse_args(
            ["--width", "123", "--explorer", "--quit"])
        self.mw.apply_options(opts)
        self.assertEqual(self.mw.f.width, 123)

    def testLoad(self):
        # load good file
        fn_good = "testdata/test.fct"
        result = self.mw.load(fn_good)
        self.assertTrue(result, "load failed")
        self.assertEqual(self.mw.filename.filename, fn_good)

        # load bad file
        fn_bad = "test_main_window.py"
        result = self.mw.load(fn_bad)
        self.assertEqual(result, False, "load of bad file succeeded")
        # filename shouldn't change
        self.assertEqual(self.mw.filename.filename, fn_good)
        self.assertEqual(
            self.mw.errors[0][0], "Error opening test_main_window.py")

        # load missing file
        fn_bad = "wibble.fct"
        result = self.mw.load(fn_bad)
        self.assertEqual(result, False, "load of missing file succeeded")
        # filename shouldn't change
        self.assertEqual(self.mw.filename.filename, fn_good)
        self.assertEqual(
            self.mw.errors[1][0], "Error opening wibble.fct")

    def testSave(self):
        # load good file
        fn_good = "testdata/test.fct"
        result = self.mw.load(fn_good)
        self.assertTrue(result, "load failed")

        # save again
        mytest_file = os.path.join(Test.tmpdir.name, "mytest.fct")
        result = self.mw.save_file(mytest_file)
        self.assertEqual(result, True, "save file failed")
        self.assertEqual(self.mw.filename.filename, mytest_file)

        # fail to save to bad location
        result = self.mw.save_file("/no_such_dir/mytest.fct")
        self.assertEqual(result, False, "save file to bad location succeeded")
        self.assertEqual(self.mw.filename.filename, mytest_file)
        self.assertEqual(
            self.mw.errors[0][0],
            "Error saving to file /no_such_dir/mytest.fct")

    def testSaveImage(self):
        # load good file
        fn_good = "testdata/test.fct"
        result = self.mw.load(fn_good)
        self.assertTrue(result, "load failed")

        # save to a bad place
        result = self.mw.save_image_file("/no_such_dir/mybad.jpg")
        self.assertEqual(False, result)
        self.assertEqual(self.mw.errors[0][0],
                         "Error saving image to file /no_such_dir/mybad.jpg")

        # save wrong image type
        result = self.mw.save_image_file("mybad.gif")
        self.assertEqual(False, result)
        self.assertEqual(self.mw.errors[1][0],
                         "Error saving image to file mybad.gif")

        # save successfully
        myimage_file = os.path.join(Test.tmpdir.name, "mygood.png")
        result = self.mw.save_image_file(myimage_file)
        self.assertEqual(True, result)
        self.assertEqual(True, os.path.isfile(myimage_file))

    def testPreview(self):
        'Check for problem where preview differs from main image'
        result = self.mw.load("testdata/collapsar.fct")
        self.assertTrue(result, "load failed")

        self.mw.update_preview(self.mw.f, False)
        fct1 = self.mw.f.serialize()
        fct2 = self.mw.preview.f.serialize()

        self.assertEqual(fct1, fct2)

    @patch("gi.repository.Gtk.Dialog.run")
    def testAbout(self, mock_dialog_run):
        mock_dialog_run.side_effect = lambda: Gtk.ResponseType.OK

        self.mw.about()

    def testDialogs(self):
        self.mw.settings(None, None)
        self.mw.painter(None, None)

    @pytest.mark.skipif(Gio.AppInfo.get_default_for_uri_scheme("http") is None,
                        reason="No web browser found")
    def testHelp(self):
        self.mw.contents(None, None)

    def testFileDialogs(self):
        self.mw.get_save_as_fs()
        self.mw.get_save_image_as_fs()
        self.mw.get_save_hires_image_as_fs()
        self.mw.get_open_fs(self.g_comp)

    def testExplorer(self):
        self.mw.load("testdata/nexus.fct")
        self.mw.set_explorer_state(True)
        self.mw.update_subfracts()
        sub3_file = os.path.join(Test.tmpdir.name, "sub3.fct")
        with open(sub3_file, "w") as fh:
            self.mw.fractalWindow.subfracts[3].save(fh, False)

        self.mw.fractalWindow.subfracts[3].onButtonRelease(None, None)
        main_file = os.path.join(Test.tmpdir.name, "main.fct")
        with open(main_file, "w") as fh:
            self.mw.f.save(fh, False)

        self.assertEqual(self.mw.fractalWindow.subfracts[3].serialize(),
                         self.mw.f.serialize())

        self.mw.set_explorer_state(False)

    def testPlanes(self):
        self.mw.set_xz_plane(None, None)

    def testRandomize(self):
        self.mw.randomize_colors(8, None)

    def testDefaultFilenames(self):
        self.assertEqual("Mandelbrot.fct", self.mw.filename.default_save_filename())
        self.assertEqual(
            "Mandelbrot.png",
            self.mw.filename.default_save_filename(".png"))
        self.assertEqual("Mandelbrot.png", self.mw.filename.default_image_filename())

        self.mw.load("testdata/elfglow.fct")
        self.assertEqual(
            "testdata/elfglow002.fct",
            self.mw.filename.default_save_filename())
        self.assertEqual(
            "testdata/elfglow.png",
            self.mw.filename.image_save_filename("testdata/elfglow.fct"))

    def testCantFindDefault(self):
        old_default = fractal.T.DEFAULT_FORMULA_FILE
        fractal.T.DEFAULT_FORMULA_FILE = "no_such_file.frm"
        try:
            self.assertRaises(IOError, WrapMainWindow, Test.userConfig)
        finally:
            fractal.T.DEFAULT_FORMULA_FILE = old_default

    def testToggleFullScreen(self):
        action = Gio.SimpleAction.new_stateful(
            "ViewFullScreenAction", None, GLib.Variant("b", False))
        self.mw.toggle_full_screen(action, None, None)
        self.assertTrue(
            self.mw.application.lookup_action("ViewFullScreenAction").get_state().unpack())
        action.set_state(GLib.Variant("b", True))
        self.mw.toggle_full_screen(action, None, None)
        self.assertFalse(
            self.mw.application.lookup_action("ViewFullScreenAction").get_state().unpack())

    def testQuit(self):
        tmpdir = tempfile.TemporaryDirectory(prefix="testQuit_")
        self.mw.application.userConfig.file = os.path.join(tmpdir.name, "testquit.config")
        self.mw.quit(None)
        tmpdir.cleanup()
