#!/usr/bin/env python3

# high-level unit tests for main window

import unittest
import os

import testgui

from gi.repository import Gtk

from fract4d import fractal
from fract4dgui import main_window

class WrapMainWindow(main_window.MainWindow):
    def __init__(self, config):
        self.errors = []
        main_window.MainWindow.__init__(self, config, ['../formulas'])

    def show_error_message(self,message,exception):
        self.errors.append((message,exception))
        
class Test(testgui.TestCase):
    def setUp(self):
        self.mw = WrapMainWindow(Test.userConfig)
        self.assertEqual(self.mw.filename, None, "shouldn't have a filename")
        
    def tearDown(self):
        os.system("killall realyelp > /dev/null 2>&1")
        os.system("killall yelp > /dev/null 2>&1")
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def testLoad(self):
        # load good file
        fn_good = "../testdata/test.fct"
        result = self.mw.load(fn_good)
        self.assertTrue(result, "load failed")
        self.assertEqual(self.mw.filename, fn_good)

        # load bad file
        fn_bad = "test_main_window.py"
        result = self.mw.load(fn_bad)
        self.assertEqual(result, False, "load of bad file succeeded")
        # filename shouldn't change
        self.assertEqual(self.mw.filename, fn_good)
        self.assertEqual(
            self.mw.errors[0][0], "Error opening test_main_window.py")

        # load missing file
        fn_bad = "wibble.fct"
        result = self.mw.load(fn_bad)
        self.assertEqual(result, False, "load of missing file succeeded")
        # filename shouldn't change
        self.assertEqual(self.mw.filename, fn_good)
        self.assertEqual(
            self.mw.errors[1][0], "Error opening wibble.fct")

    def testSave(self):
        # load good file
        fn_good = "../testdata/test.fct"
        result = self.mw.load(fn_good)
        self.assertTrue(result, "load failed")

        # save again
        mytest_file = os.path.join(Test.tmpdir.name, "mytest.fct")
        result = self.mw.save_file(mytest_file)
        self.assertEqual(result, True, "save file failed")
        self.assertEqual(self.mw.filename, mytest_file)

        # fail to save to bad location
        result = self.mw.save_file("/no_such_dir/mytest.fct")
        self.assertEqual(result, False, "save file to bad location succeeded")
        self.assertEqual(self.mw.filename, mytest_file)
        self.assertEqual(
            self.mw.errors[0][0],
            "Error saving to file /no_such_dir/mytest.fct")

    def testSaveImage(self):
        # load good file
        fn_good = "../testdata/test.fct"
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
        result = self.mw.load("../testdata/collapsar.fct")
        self.assertTrue(result, "load failed")

        self.mw.update_preview(self.mw.f, False)
        fct1 = self.mw.f.serialize()
        fct2 = self.mw.preview.f.serialize()

        self.assertEqual(fct1, fct2)
        
    def testDialogs(self):
        self.mw.settings(None,None)
        self.mw.contents(None,None)
        self.mw.painter(None,None)
        
    def testFileDialogs(self):
        self.mw.get_save_as_fs()
        self.mw.get_save_image_as_fs()
        self.mw.get_save_hires_image_as_fs()
        self.mw.get_open_fs()
        
    def testExplorer(self):
        self.mw.load("../testdata/nexus.fct")
        self.mw.set_explorer_state(True)
        self.mw.update_subfracts()
        sub3_file = os.path.join(Test.tmpdir.name, "sub3.fct")
        with open(sub3_file, "w") as fh:
                self.mw.subfracts[3].save(fh,False)
        
        self.mw.subfracts[3].onButtonRelease(None,None)
        main_file = os.path.join(Test.tmpdir.name, "main.fct")
        with open(main_file, "w") as fh:
                self.mw.f.save(fh,False)
        
        self.assertEqual(self.mw.subfracts[3].serialize(),
                         self.mw.f.serialize())
            
        self.mw.set_explorer_state(False)

    def testPlanes(self):
        self.mw.set_xz_plane(None,None)
        
    def testRandomize(self):
        self.mw.randomize_colors(8,None)

    def testDefaultFilenames(self):
        self.assertEqual("Mandelbrot.fct", self.mw.default_save_filename())
        self.assertEqual("Mandelbrot.png", self.mw.default_save_filename(".png"))
        self.assertEqual("Mandelbrot.png", self.mw.default_image_filename())
        
        self.mw.load("../testdata/elfglow.fct")
        self.assertEqual("../testdata/elfglow002.fct", self.mw.default_save_filename())
        self.assertEqual(
            "../testdata/elfglow.png",
            self.mw.image_save_filename("../testdata/elfglow.fct"))

    def testCantFindDefault(self):
        old_default = fractal.T.DEFAULT_FORMULA_FILE
        fractal.T.DEFAULT_FORMULA_FILE = "no_such_file.frm"
        try:
            self.assertRaises(IOError, WrapMainWindow, Test.userConfig)
        finally:
            fractal.T.DEFAULT_FORMULA_FILE = old_default


def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
