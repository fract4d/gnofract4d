from gi.repository import GLib, Gtk

from fract4d_compiler import fracttypes, function
from . import utils, fourway


class FractalSettingsTable(Gtk.Grid):
    def __init__(self, f, main_window, param_type, row=0, row_spacing=0):
        super().__init__(column_spacing=10, row_spacing=row_spacing)
        self.f = f
        self.main_window = main_window
        # create widget to fiddle with this fractal's settings
        form = self.f.get_form(param_type)
        formula = form.formula

        if param_type == 0:
            row = self.create_maxiter_widget(row)

        params = formula.symbols.parameters()
        op = formula.symbols.order_of_params()

        keys = sorted(params.keys())
        for name in keys:
            param = params[name]
            if isinstance(param, function.Func):
                self.add_formula_function(row, name, param, form)
            else:
                if param.type == fracttypes.Complex:
                    self.add_complex_formula_setting(
                        row, form, name, param, op[name], param_type)
                    row += 1
                elif param.type == fracttypes.Hyper:
                    suffixes = [" (re)", " (i)", " (j)", " (k)"]
                    for j in range(4):
                        self.add_formula_setting(
                            row + j, form, name, suffixes[j],
                            param, op[name] + j)
                    row += 3
                elif param.type == fracttypes.Color:
                    self.add_formula_setting(
                        row, form, name, "", param, op[name])
                    row += 3
                elif param.type == fracttypes.Gradient:
                    # FIXME
                    pass
                else:
                    self.add_formula_setting(
                        row, form, name, "", param, op[name])
            row += 1

    def add_complex_formula_setting(
            self, i, form, name, param, order, param_type):
        widget = self.make_numeric_entry(form, param, order)
        self.attach(widget, 1, i, 1, 1)

        widget = self.make_numeric_entry(form, param, order + 1)
        self.attach(widget, 1, i + 1, 1, 1)

        name = self.f.param_display_name(name, param)
        tip = self.f.param_tip(name, param)
        fway = fourway.T(name, tip)

        fway.connect('value-changed', self.fourway_released, order, form)
        fway.connect(
                'value-slightly-changed',
                self.main_window.on_drag_param_fourway, order, param_type)

        self.attach(fway, 0, i, 1, 2)

    def add_formula_function(self, i, name, param, form):
        label = Gtk.Label(
            label=self.f.param_display_name(name, param),
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER)
        self.attach(label, 0, i, 1, 1)

        funclist = sorted(form.formula.symbols.available_param_functions(
            param.ret, param.args))
        widget = utils.dropdown_with_items(funclist)

        formula = form.formula

        def set_selected_function():
            try:
                selected_func_name = form.get_func_value(name)
                index = funclist.index(selected_func_name)
            except ValueError:
                # func.cname not in list
                # print "bad cname"
                return

            widget.set_selected(index)

        def set_fractal_function(om, item, f, param, formula):
            index = om.get_selected()
            if index != -1:
                # this shouldn't be necessary but I got weird errors
                # trying to reuse the old funclist
                list = sorted(formula.symbols.available_param_functions(
                    param.ret, param.args))

                fname = list[index]
                f.set_func(param, fname, formula)

        set_selected_function()

        widget.update_function = set_selected_function

        widget.connect('notify::selected-item', set_fractal_function, self.f, param, formula)

        self.attach(widget, 1, i, 1, 1)

    def add_formula_setting(self, i, form, name, part, param, order):
        if param.type == fracttypes.Int:
            if hasattr(param, "enum"):
                widget = self.make_enumerated_widget(
                    i, form, name, part, param, order)
            else:
                widget = self.make_numeric_widget(
                    i, form, name, part, param, order)

        elif param.type == fracttypes.Float or \
                param.type == fracttypes.Complex or \
                param.type == fracttypes.Hyper:

            widget = self.make_numeric_widget(
                i, form, name, part, param, order)
        elif param.type == fracttypes.Bool:
            widget = self.make_bool_widget(form, name, param, order)
        elif param.type == fracttypes.Color:
            widget = self.make_color_widget(i, form, name, param, order)
        elif param.type == fracttypes.Image:
            # skip image params for now
            return
        else:
            raise ValueError("Unsupported parameter type")

        self.attach(widget, 1, i, 1, 1)

    def create_maxiter_widget(self, i):
        widget = Gtk.Entry(activates_default=True)

        def set_entry(*args):
            widget.set_text("%d" % self.f.maxiter)

        def set_fractal(*args):
            try:
                try:
                    i = int(widget.get_text())
                    self.f.set_maxiter(i)
                except ValueError:
                    msg = "Invalid value '%s': must be a number" % \
                          widget.get_text()
                    GLib.idle_add(self.f.warn, msg)
            except Exception as exn:
                print(exn)
            return False

        set_entry(self)

        self.f.connect('parameters-changed', set_entry)
        self.f.connect('iters-changed', set_entry)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect('leave', set_fractal)
        widget.add_controller(focus_controller)

        label = Gtk.Label(
            label="_Max Iterations",
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
            use_underline=True,
            mnemonic_widget=widget)

        self.attach(label, 0, i, 1, 1)
        self.attach(widget, 1, i, 1, 1)
        return i + 1

    def make_numeric_entry(self, form, param, order):
        if param.type == fracttypes.Int:
            fmt = "%d"
        else:
            fmt = "%.17f"

        widget = Gtk.Entry(activates_default=True)

        def set_entry():
            new_value = fmt % form.params[order]
            if widget.get_text() != new_value:
                widget.set_text(new_value)

        def set_fractal(*args):
            try:
                GLib.idle_add(
                    form.set_param, order, widget.get_text())
            except Exception:
                # FIXME: produces too many errors
                msg = f"Invalid value '{widget.get_text()}': must be a number"
                print(msg)
                # GLib.idle_add(f.warn,msg)
            return False

        set_entry()

        widget.update_function = set_entry

        widget.f = self.f
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect('leave', set_fractal)
        widget.add_controller(focus_controller)

        if hasattr(param, "min") and hasattr(param, "max"):
            widget.freeze = False
            # add a slider
            adj = Gtk.Adjustment(
                value=0.0,
                lower=param.min.value, upper=param.max.value,
                step_increment=0.001, page_increment=0.01)

            def set_adj():
                if adj.get_value() != form.params[order]:
                    widget.freeze = True
                    adj.set_value(form.params[order])
                    widget.freeze = False

            set_adj()

            def adj_changed(adjustment, form, order):
                if widget.freeze:
                    return

                GLib.idle_add(
                    form.set_param, order, adjustment.get_value())

            adj.connect('value-changed', adj_changed, form, order)

            hscale = Gtk.Scale(adjustment=adj, draw_value=False)
            hscale.update_function = set_adj
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox.append(widget)
            vbox.append(hscale)
            return vbox

        return widget

    def make_numeric_widget(self, i, form, name, part, param, order):
        widget = self.make_numeric_entry(form, param, order)

        label = Gtk.Label(
            label=self.f.param_display_name(name, param) + part,
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
            mnemonic_widget=widget)
        self.attach(label, 0, i, 1, 1)

        return widget

    def make_bool_widget(self, form, name, param, order):
        widget = Gtk.CheckButton(label=self.f.param_display_name(name, param))

        def set_toggle(*args):
            is_set = form.params[order]
            widget.set_active(is_set)
            if widget.get_active() != is_set:
                widget.set_active(is_set)

        def set_fractal(entry, form, order):
            try:
                GLib.idle_add(form.set_param, order, entry.get_active())
            except Exception as err:
                msg = "error setting bool param: %s" % str(err)
                print(msg)

            return False

        set_toggle(self)

        widget.update_function = set_toggle
        widget.f = self.f
        widget.connect('toggled', set_fractal, form, order)
        return widget

    def make_color_widget(self, i, form, name, param, order):
        label = Gtk.Label(
            label=self.f.param_display_name(name, param),
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER)
        self.attach(label, 0, i, 1, 1)

        def set_fractal(r, g, b, is_left):
            self.f.freeze()
            form.set_param(order, r)
            form.set_param(order + 1, g)
            form.set_param(order + 2, b)
            if self.f.thaw():
                self.f.changed()

        rgba = []
        for j in range(4):
            rgba.append(form.params[order + j])

        color_button = utils.ColorButton(rgba, set_fractal, False)

        def set_selected_value(*args):
            rgba = []
            for j in range(4):
                rgba.append(form.params[order + j])
            color_button.set_color(rgba)

        set_selected_value()

        color_button.update_function = set_selected_value

        return color_button

    def make_enumerated_widget(self, i, form, name, part, param, order):
        widget = utils.combo_box_text_with_items(param.enum.value)

        def set_selected_value(*args):
            try:
                index = form.params[order]
            except ValueError as err:
                print(err)
                return

            widget.set_active(index)

        def set_fractal(entry, form, order):
            new_value = widget.get_active()
            form.set_param(order, new_value)

        set_selected_value(self)

        widget.update_function = set_selected_value

        widget.f = self.f
        widget.connect('changed', set_fractal, form, order)

        label = Gtk.Label(
            label=self.f.param_display_name(name, param),
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
            mnemonic_widget=widget)
        self.attach(label, 0, i, 1, 1)

        return widget

    def fourway_released(self, widget, x, y, order, form):
        form.nudge_param(order, x, y)
