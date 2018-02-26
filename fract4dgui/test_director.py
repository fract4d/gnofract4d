#!/usr/bin/env python3

# unit tests for renderqueue module

import os
import sys
import unittest

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

if sys.path[1] != "..": sys.path.insert(1, "..")
from fract4dgui import director, PNGGen, hig
from fract4d import fractal, fc, animation

g_comp = fc.Compiler()
g_comp.add_func_path("../fract4d")
g_comp.add_func_path("../formulas")

class Test(unittest.TestCase):
    def setUp(self):
        # ensure any dialog boxes are dismissed without human interaction
        hig.timeout = 250

    def tearDown(self):
        pass

    def wait(self):
        Gtk.main()

    def quitloop(self,rq):
        Gtk.main_quit()

    def removeIfExists(self,file):
        if os.path.exists(file):
            os.remove(file)
            
    def testDirectorDialog(self):
        self.removeIfExists("video.avi")

        f = fractal.T(g_comp)
        dd=director.DirectorDialog(None,f,"")
        dd.show()
        dd.animation.set_png_dir("./")
        dd.animation.set_fct_enabled(False)
        dd.animation.add_keyframe("../testdata/director1.fct",1,10,animation.INT_LOG)
        dd.animation.add_keyframe("../testdata/director2.fct",1,10,animation.INT_LOG)
        for f in dd.animation.create_list():
            self.removeIfExists(f)

        dd.animation.set_avi_file("./video.avi")
        dd.animation.set_width(320)
        dd.animation.set_height(240)
        dd.generate(True)
            
        self.assertEqual(True,os.path.exists("./image_0000000.png"))
        self.assertEqual(True,os.path.exists("./image_0000001.png"))
        if dd.converterpath:
            # only check for video if video converter is installed
            self.assertEqual(True,os.path.exists("video.avi"))

        dd.destroy()
        os.remove("list")
        os.remove("./image_0000000.png")
        os.remove("./image_0000001.png")

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
        f = fractal.T(g_comp)
        dd=director.DirectorDialog(None,f,"")
        
        dd.animation.add_keyframe("/foo/director1.fct",1,10,animation.INT_LOG)
        self.assertRaisesMessage(
            director.SanityCheckError, "There must be at least two keyframes",
            dd.check_sanity)
        
        dd.animation.add_keyframe("/tmp/director2.fct",1,10,animation.INT_LOG)
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

        dd.animation.set_png_dir("/tmp/")
        
        self.assertRaisesMessage(
            director.SanityCheckError,
            "Output AVI file name not set",
            dd.check_sanity)

        dd.animation.set_avi_file("/tmp/foo.avi")

        dd.animation.set_fct_enabled(True)
        dd.animation.set_fct_dir("/tmp")
        
        self.assertRaisesMessage(
            director.SanityCheckError,
            "Keyframe /tmp/director2.fct is in the temporary .fct directory and could be overwritten. Please change temp directory.",
            dd.check_sanity)
        
    def testKeyframeClash(self):
        f = fractal.T(g_comp)
        dd= director.DirectorDialog(None,f,"")

        dd.check_for_keyframe_clash("/a","/b")
        
        self.assertRaises(
            director.SanityCheckError,
            dd.check_for_keyframe_clash, "/tmp/foo.fct", "/tmp")
        self.assertRaises(
            director.SanityCheckError,
            dd.check_for_keyframe_clash, "/tmp/foo.fct", "/tmp/")

    def testPNGGen(self):
        f = fractal.T(g_comp)
        dd= director.DirectorDialog(None,f,"")
        pg = PNGGen.PNGGeneration(dd.animation,g_comp,dd)
        pg.generate_png()
        
        dd.destroy()

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
