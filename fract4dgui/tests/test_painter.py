# unit tests for settings window

from . import testgui

from gi.repository import Gtk

from fract4dgui import gtkfractal, painter


class FakeEvent:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class Test(testgui.TestCase):
    def setUp(self):
        parent = Gtk.Window()
        self.f = parent.f = gtkfractal.T(Test.g_comp)
        self.settings = painter.PainterDialog(parent)

    def testPaintOnUnknown(self):
        self.settings.show()
        self.assertEqual(True, self.f.paint_mode)
        event = FakeEvent(x=0, y=0, button=1)
        self.f.onButtonPress(self.f.widget, event)
        self.f.onButtonRelease(self.f.widget, event)
        self.settings.hide()
        self.assertEqual(False, self.f.paint_mode)
