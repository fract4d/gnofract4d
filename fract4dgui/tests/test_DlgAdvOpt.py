#!/usr/bin/env python3

from unittest.mock import patch

from . import testgui

from gi.repository import Gtk

from fract4dgui import DlgAdvOpt
from fract4d import fractal, animation


class Test(testgui.TestCase):
    def setUp(self):
        f = fractal.T(Test.g_comp)
        self.test_animation = animation.T(f.compiler, Test.userConfig)

    @patch("gi.repository.Gtk.Dialog.run")
    def testDlgAdvOptions(self, mock_dialog_run):
        mock_dialog_run.side_effect = lambda: Gtk.ResponseType.OK

        parent = Gtk.Window()
        self.test_animation.add_keyframe(
            "testdata/director1.fct", 1, 10, animation.INT_LOG)
        dao = DlgAdvOpt.DlgAdvOptions(0, self.test_animation, parent)
        dao.show()
        self.assertTrue(dao.animation.keyframes[0].flags)
