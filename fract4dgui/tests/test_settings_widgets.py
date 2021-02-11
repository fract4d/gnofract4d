from . import testgui

from gi.repository import Gtk

from fract4dgui import settings_widgets, gtkfractal


class Test(testgui.TestCase):
    def setUp(self):
        self.window = Gtk.Window()
        self.f = gtkfractal.T(Test.g_comp)
        self.window.add(self.f.widget)
        self.f.widget.realize()

    def tearDown(self):
        self.window.destroy()
        self.f = None

    def testParamSettings(self):
        self.f.set_formula("test.frm", "test_func")
        self.f.set_outer("test.cfrm", "flat")

        table = settings_widgets.FractalSettingsTable(self.f, self.window, 0)

        children = table.get_children()
        list.reverse(children)

        names = [x.get_text() for x in children if isinstance(x, Gtk.Label)]

        self.assertEqual(names[0], "Max Iterations")
        self.assertEqual(names[1], "Bailfunc")
        self.assertEqual(names[2], "Bailout")
        self.assertEqual(names[3], "Param with min and max")
        self.assertEqual(names[4], "Myfunc")

        table = settings_widgets.FractalSettingsTable(self.f, self.window, 1)

        children = table.get_children()
        list.reverse(children)

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
