#!/usr/bin/env python3

# unit tests for renderqueue module

from unittest.mock import patch
import os.path
import sys

from . import testgui

from gi.repository import Gio, Gtk

from fract4dgui import director, PNGGen, hig
from fract4d import fractal, animation


class Window(Gtk.Window):
    def __init__(self):
        super().__init__()
        this_path = os.path.dirname(sys.modules[__name__].__file__)
        resource = Gio.resource_load(os.path.join(this_path, "../../gnofract4d.gresource"))
        Gio.Resource._register(resource)
        self.menu_builder = Gtk.Builder.new_from_resource("/io/github/fract4d/gtk/menus.ui")

    def get_menu_by_id(self, menuid):
        return self.menu_builder.get_object(menuid)


class Test(testgui.TestCase):
    def setUp(self):
        # ensure any dialog boxes are dismissed without human interaction
        hig.timeout = 250

        application = Window()
        application.userConfig = Test.userConfig
        self.parent = Gtk.Window()
        self.parent.f = fractal.T(Test.g_comp)
        self.parent.application = application

    def testDirectorDialog(self):
        dd = director.DirectorDialog(self.parent)
        dd.show()
        dd.animation.set_png_dir(Test.tmpdir.name)
        dd.animation.set_fct_enabled(False)
        dd.animation.add_keyframe(
            "testdata/director1.fct", 1, 10, animation.INT_LOG)
        dd.animation.add_keyframe(
            "testdata/director2.fct", 1, 10, animation.INT_LOG)

        video_file = os.path.join(Test.tmpdir.name, "video.webm")
        dd.animation.set_avi_file(video_file)
        dd.animation.set_width(320)
        dd.animation.set_height(240)
        dd.generate(dd.converterpath is not None)

        self.assertEqual(
            True,
            os.path.exists(
                os.path.join(
                    Test.tmpdir.name,
                    "image_0000000.png")))
        self.assertEqual(
            True,
            os.path.exists(
                os.path.join(
                    Test.tmpdir.name,
                    "image_0000001.png")))
        if dd.converterpath:
            # only check for video if video converter is installed
            self.assertEqual(True, os.path.exists(video_file))

        dd.destroy()

    @patch("gi.repository.Gtk.FileChooserDialog.run")
    @patch("gi.repository.Gtk.FileChooserDialog.get_filename")
    def testFileChoosers(self, mock_dialog_get_filename, mock_dialog_run):
        filename = "test_file"
        mock_dialog_get_filename.side_effect = lambda: filename

        dd = director.DirectorDialog(self.parent)

        mock_dialog_run.side_effect = lambda: Gtk.ResponseType.OK
        self.assertEqual(dd.get_fct_file(), filename)
        self.assertEqual(dd.get_avi_file(), filename)
        self.assertEqual(dd.get_cfg_file_save(), filename)
        self.assertEqual(dd.get_cfg_file_open(), filename)

        mock_dialog_run.side_effect = lambda: Gtk.ResponseType.CANCEL
        self.assertEqual(dd.get_fct_file(), "")
        self.assertEqual(dd.get_avi_file(), "")
        self.assertEqual(dd.get_cfg_file_save(), "")
        self.assertEqual(dd.get_cfg_file_open(), "")

    def assertRaisesMessage(self, excClass, msg, callable, *args, **kwargs):
        try:
            callable(*args, **kwargs)
        except excClass as exn:
            self.assertEqual(msg, str(exn))
        else:
            if hasattr(excClass, '__name__'):
                excName = excClass.__name__
            else:
                excName = str(excClass)
            raise self.failureException("%s not raised" % excName)

    def testOwnSanity(self):
        # exercise each of the checks in the check_sanity function
        dd = director.DirectorDialog(self.parent)

        dd.animation.add_keyframe(
            "/foo/director1.fct", 1, 10, animation.INT_LOG)
        self.assertRaisesMessage(
            director.SanityCheckError, "There must be at least two keyframes",
            dd.check_sanity)

        dd.animation.add_keyframe(os.path.join(Test.tmpdir.name, "director2.fct"),
                                  1, 10, animation.INT_LOG)
        dd.animation.set_png_dir("")
        self.assertRaisesMessage(
            director.SanityCheckError,
            "Directory for temporary .png files not set",
            dd.check_sanity)

        dd.animation.set_png_dir("fishy")
        self.assertRaisesMessage(
            director.SanityCheckError,
            "Path for temporary .png files is not a directory",
            dd.check_sanity)

        dd.animation.set_png_dir(Test.tmpdir.name)

        self.assertRaisesMessage(
            director.SanityCheckError,
            "Output AVI file name not set",
            dd.check_sanity)

        dd.animation.set_avi_file(os.path.join(Test.tmpdir.name, "foo.avi"))

        dd.animation.set_fct_enabled(True)
        dd.animation.set_fct_dir(Test.tmpdir.name)

        self.assertRaisesMessage(
            director.SanityCheckError,
            f"Keyframe {os.path.join(Test.tmpdir.name, 'director2.fct')} is in"
            " the temporary .fct directory and could be overwritten."
            " Please change temp directory.",
            dd.check_sanity)

    def testKeyframeClash(self):
        dd = director.DirectorDialog(self.parent)

        dd.check_for_keyframe_clash("/a", "/b")

        self.assertRaises(
            director.SanityCheckError,
            dd.check_for_keyframe_clash,
            os.path.join(Test.tmpdir.name, "foo.fct"),
            Test.tmpdir.name)
        self.assertRaises(
            director.SanityCheckError,
            dd.check_for_keyframe_clash,
            os.path.join(Test.tmpdir.name, "foo.fct"),
            Test.tmpdir.name)

    def testPNGGen(self):
        dd = director.DirectorDialog(self.parent)
        dd.animation.add_keyframe(
            "testdata/director1.fct", 1, 10, animation.INT_LOG)
        dd.animation.add_keyframe(
            "testdata/director2.fct", 1, 10, animation.INT_LOG)
        pg = PNGGen.PNGGeneration(dd.animation, Test.g_comp, dd)
        pg.generate_png()

        dd.destroy()
