#!/usr/bin/env python3

# unit tests for renderqueue module

import os.path

from . import testgui

from gi.repository import Gtk

from fract4dgui import director, PNGGen, hig
from fract4d import fractal, animation

class Test(testgui.TestCase):
    def setUp(self):
        # ensure any dialog boxes are dismissed without human interaction
        hig.timeout = 250

    def tearDown(self):
        pass

    def wait(self):
        Gtk.main()

    def quitloop(self,rq):
        Gtk.main_quit()

    def testDirectorDialog(self):
        f = fractal.T(Test.g_comp)
        parent = Gtk.Window()
        dd = director.DirectorDialog(parent,f,Test.userConfig)
        dd.show()
        dd.animation.set_png_dir(Test.tmpdir.name)
        dd.animation.set_fct_enabled(False)
        dd.animation.add_keyframe("testdata/director1.fct",1,10,animation.INT_LOG)
        dd.animation.add_keyframe("testdata/director2.fct",1,10,animation.INT_LOG)

        video_file = os.path.join(Test.tmpdir.name, "video.webm")
        dd.animation.set_avi_file(video_file)
        dd.animation.set_width(320)
        dd.animation.set_height(240)
        dd.generate(dd.converterpath!=None)
            
        self.assertEqual(True,os.path.exists(os.path.join(Test.tmpdir.name, "image_0000000.png")))
        self.assertEqual(True,os.path.exists(os.path.join(Test.tmpdir.name, "image_0000001.png")))
        if dd.converterpath:
            # only check for video if video converter is installed
            self.assertEqual(True,os.path.exists(video_file))

        dd.destroy()

    def assertRaisesMessage(self, excClass, msg, callable, *args, **kwargs):
        try:
            callable(*args,**kwargs)
        except excClass as exn:
            self.assertEqual(msg,str(exn))
        else:
            if hasattr(excClass,'__name__'): excName = excClass.__name__
            else: excName = str(excClass)
            raise self.failureException("%s not raised" % excName)

    def testOwnSanity(self):
        # exercise each of the checks in the check_sanity function
        f = fractal.T(Test.g_comp)
        dd = director.DirectorDialog(None,f,Test.userConfig)
        
        dd.animation.add_keyframe("/foo/director1.fct",1,10,animation.INT_LOG)
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
            "Keyframe {} is in the temporary .fct directory and could be overwritten. Please change temp directory.".format(os.path.join(Test.tmpdir.name, "director2.fct")),
            dd.check_sanity)
        
    def testKeyframeClash(self):
        f = fractal.T(Test.g_comp)
        dd = director.DirectorDialog(None,f,Test.userConfig)

        dd.check_for_keyframe_clash("/a","/b")
        
        self.assertRaises(
            director.SanityCheckError,
            dd.check_for_keyframe_clash, os.path.join(Test.tmpdir.name, "foo.fct"), Test.tmpdir.name)
        self.assertRaises(
            director.SanityCheckError,
            dd.check_for_keyframe_clash, os.path.join(Test.tmpdir.name, "foo.fct"), Test.tmpdir.name)

    def testPNGGen(self):
        f = fractal.T(Test.g_comp)
        dd = director.DirectorDialog(None,f,Test.userConfig)
        pg = PNGGen.PNGGeneration(dd.animation,Test.g_comp,dd)
        pg.generate_png()
        
        dd.destroy()
