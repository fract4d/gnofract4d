from . import testgui

from gi.repository import Graphene, Gtk

from fract4dgui import settings_widgets, gtkfractal


class Test(testgui.TestCase):
    def setUp(self):
        super().setUp()
        self.window = Gtk.Window()
        self.f = gtkfractal.T(Test.g_comp)
        self.window.set_child(self.f.widget)
        self.window.present()

    def tearDown(self):
        self.window.destroy()
        self.f = None

    def testParamSettings(self):
        self.f.set_formula("test.frm", "test_func")
        self.f.set_outer("test.cfrm", "flat")

        table = settings_widgets.FractalSettingsTable(self.f, self.window, 0)

        children = [x for x in table]
        names = [x.get_text() for x in children if isinstance(x, Gtk.Label)]

        self.assertEqual(names[0], "Max Iterations")
        self.assertEqual(names[1], "Bailfunc")
        self.assertEqual(names[2], "Bailout")
        self.assertEqual(names[3], "Param with min and max")
        self.assertEqual(names[4], "Myfunc")

        table = settings_widgets.FractalSettingsTable(self.f, self.window, 1)

        children = [x for x in table]
        names = [x.get_text() for x in children if isinstance(x, Gtk.Label)]

        self.assertEqual(
            names,
            ["Color Density", "Color Offset", "Transfer Function",
             "Col", "Ep", "I", "Mycolorfunc", "Myfunc", "Val",
             "Val2 (re)", "Val2 (i)", "Val2 (j)", "Val2 (k)"])

    def testIntParamSetting(self):
        self.f.set_formula("test.frm", "fn_with_intparam")

        settings_widgets.FractalSettingsTable(self.f, self.window, 0)

    def testAllSettingsTypes(self):
        self.f.set_formula("test.frm", "test_all_types")
        self.window.on_drag_param_fourway = lambda widget, dx, dy, order, param_type: widget

        settings_widgets.FractalSettingsTable(self.f, self.window, 0)

    def testGradientViewerDrawHandle(self):
        gradarea = settings_widgets.GradientViewer(self.f, -1)
        s = Gtk.Snapshot.new()
        rect = Graphene.Rect()
        rect.init(0, 0, 100, 100)
        ct = s.append_cairo(rect)
        gradarea.draw_handle(96, ct, 10, None)
        gradarea.draw_handle(96, ct, 10, True)

    def testGradientViewerDoSnapshot(self):
        gradarea = settings_widgets.GradientViewer(self.f, -1)
        gradarea.do_snapshot(Gtk.Snapshot.new())

    def testSelectedSegment(self):
        table = settings_widgets.ColorSettingsTable(self.f, self.window)
        table.copy_left(None)
        table.copy_right(None)
        table.split(None)
        table.remove(None)
