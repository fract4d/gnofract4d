# unit tests for renderqueue module

from unittest.mock import patch
import os.path
import sys

from . import testgui

from gi.repository import Gio, GLib, Gtk

from fract4dgui import director, PNGGen, hig, utils
from fract4d import fractal, animation


class MockFileChooser:
    def __init__(self, filepath):
        self.filepath = filepath

    def get_path(self):
        return self.filepath


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
        super().setUp()
        # ensure any dialog boxes are dismissed without human interaction
        hig.timeout = 250

        application = Window()
        application.userConfig = Test.userConfig
        self.parent = Gtk.Window()
        self.parent.f = fractal.T(Test.g_comp)
        self.parent.application = application

    def testDirectorDialog(self):
        dd = director.DirectorDialog(self.parent)
        dd.present()
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
        loop = GLib.MainLoop()

        def stop_loop(*args):
            print("stop_loop")
            loop.quit()
        dd.connect("notify::visible", stop_loop)
        loop.run()

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

    @patch("gi.repository.Gtk.FileChooserDialog.connect")
    @patch("gi.repository.Gtk.FileChooserDialog.get_file")
    def testFileChoosers(self, mock_dialog_get_file, mock_dialog_connect):
        filename = "test_file"
        mock_dialog_get_file.side_effect = lambda: MockFileChooser(filename)
        mock_dialog_connect.side_effect = \
            lambda signal, response: \
            response(utils.FileOpenChooser("test", None), Gtk.ResponseType.OK)

        dd = director.DirectorDialog(self.parent)

        def callback1(temp_file):
            self.assertEqual(temp_file, filename)
        dd.get_fct_file(callback1)
        dd.get_avi_file(callback1)
        #  dd.get_cfg_file_save()
        dd.get_cfg_file_open(callback1)

        def callback2(temp_file):
            self.fail("FileOpenChooser called callback on CANCEL")
        mock_dialog_connect.side_effect = \
            lambda signal, response: \
            response(utils.FileOpenChooser("test", None), Gtk.ResponseType.CANCEL)
        dd.get_fct_file(callback2)
        dd.get_avi_file(callback2)
        #  dd.get_cfg_file_save()
        dd.get_cfg_file_open(callback2)
        dd.close()

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
