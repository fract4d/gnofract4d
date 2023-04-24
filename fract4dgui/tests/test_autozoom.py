from . import testgui

from gi.repository import Gtk

from fract4dgui import autozoom, gtkfractal


class Test(testgui.TestCase):
    def setUp(self):
        super().setUp()
        self.f = gtkfractal.T(Test.g_comp)
        self.mw = Gtk.Window()

    def testAutozoom(self):
        azd = autozoom.AutozoomDialog(self.mw, self.f)
        self.assertEqual(azd.minsize_entry.get_text(), "1e-13")
        azd.minsize_entry.set_text("1")
        azd.observe_controllers()[0].emit("leave")
        self.assertEqual(azd.minsize, 1)

    def testSelectQuadrant(self):
        azd = autozoom.AutozoomDialog(self.mw, self.f)
        azd.select_quadrant_and_zoom()
