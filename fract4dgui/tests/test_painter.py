# unit tests for settings window

from . import testgui

from gi.repository import Gtk

from fract4dgui import gtkfractal, painter


class FakeGesture:
    def __init__(self, button=1):
        self.button = button

    def get_current_button(self):
        return self.button

    def get_current_event_state(self):
        return 0

    def set_state(self, state):
        pass


class Test(testgui.TestCase):
    def setUp(self):
        super().setUp()
        self.parent = Gtk.Window()
        self.f = self.parent.f = gtkfractal.T(Test.g_comp)

    def testPaintOnUnknown(self):
        painterDialog = painter.PainterDialog(self.parent)
        painterDialog.present()
        self.assertEqual(True, self.f.paint_mode)
        gesture = FakeGesture()
        self.f.onButtonPress(gesture, 0, 0)
        self.f.onButtonRelease(gesture, 0, 0)
        painterDialog.close()
        self.assertEqual(False, self.f.paint_mode)
