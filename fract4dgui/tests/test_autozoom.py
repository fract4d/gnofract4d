#!/usr/bin/env python3

from unittest.mock import patch

from . import testgui

from gi.repository import Gdk, Gtk

from fract4dgui import autozoom, gtkfractal


class Test(testgui.TestCase):
    def setUp(self):
        self.f = gtkfractal.T(Test.g_comp)
        self.mw = Gtk.Window()

    @patch("gi.repository.Gtk.Dialog.run")
    def testAutozoom(self, mock_dialog_run):
        mock_dialog_run.side_effect = lambda: Gtk.ResponseType.CLOSE

        azd = autozoom.AutozoomDialog(self.mw, self.f)
        self.assertEqual(azd.minsize_entry.get_text(), "1e-13")
        azd.minsize_entry.set_text("1")
        azd.emit("focus-out-event", Gdk.Event())
        self.assertEqual(azd.minsize, 1)

    def testSelectQuadrant(self):
        azd = autozoom.AutozoomDialog(self.mw, self.f)
        azd.select_quadrant_and_zoom()
