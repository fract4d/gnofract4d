import copy

from gi.repository import GLib, Gtk, Graphene

from fract4d_compiler import fracttypes, function
from . import browser, browser_model, utils, fourway


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
            xalign=1.0,
        )
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
            xalign=1.0,
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
            xalign=1.0,
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
            xalign=1.0,
        )
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
            xalign=1.0,
            mnemonic_widget=widget)
        self.attach(label, 0, i, 1, 1)

        return widget

    def fourway_released(self, widget, x, y, order, form):
        form.nudge_param(order, x, y)


class ColorSettingsTable(Gtk.Box):
    def __init__(self, f, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.f = f
        self.main_window = main_window
        self.selected_segment = -1

        browse_button = Gtk.Button(label=_("Browse..."))
        browse_button.connect(
            "clicked", self.show_browser, browser_model.GRADIENT)

        self.append(browse_button)

        self.gradarea = GradientViewer(self.f, self.selected_segment)

        event_controller_gesture = Gtk.GestureDrag()
        self.gradarea.add_controller(event_controller_gesture)

        event_controller_gesture.connect("drag_begin", self.gradarea_mousedown)
        event_controller_gesture.connect("drag_update", self.gradarea_mousemoved)
        event_controller_gesture.connect("drag_end", self.gradarea_clicked)

        self.f.connect('parameters-changed', self.redraw)
        self.append(self.gradarea)

        table = Gtk.Grid(
            column_homogeneous=True,
            column_spacing=10,
            row_spacing=50,
            margin_top=30)

        grad = self.f.get_gradient()
        self.left_color_button = utils.ColorButton(
            grad.segments[0].left_color, self.color_changed, True)
        self.left_color_button.set_tooltip_text(
            _("Color of segment's left end"))

        self.right_color_button = utils.ColorButton(
            grad.segments[0].right_color, self.color_changed, False)
        self.right_color_button.set_tooltip_text(
            _("Color of segment's right end"))

        table.attach(Gtk.Label(label="Left Color:"), 0, 0, 1, 1)
        table.attach(self.left_color_button, 1, 0, 1, 1)
        table.attach(Gtk.Label(label="Right Color:"), 2, 0, 1, 1)
        table.attach(self.right_color_button, 3, 0, 1, 1)

        self.split_button = Gtk.Button(label=_("Split"))
        self.split_button.connect('clicked', self.split)
        table.attach(self.split_button, 0, 1, 1, 1)

        self.remove_button = Gtk.Button(label=_("Remove"))
        self.remove_button.connect('clicked', self.remove)
        table.attach(self.remove_button, 1, 1, 1, 1)

        self.copy_left_button = Gtk.Button(label=_("<Copy"))
        self.copy_left_button.connect('clicked', self.copy_left)
        table.attach(self.copy_left_button, 2, 1, 1, 1)

        self.copy_right_button = Gtk.Button(label=_("Copy>"))
        self.copy_right_button.connect('clicked', self.copy_right)
        table.attach(self.copy_right_button, 3, 1, 1, 1)

        self.inner_solid_button = utils.ColorButton(
            utils.floatColorFrom256(self.f.solids[1]),
            self.solid_color_changed, 1)

        self.outer_solid_button = utils.ColorButton(
            utils.floatColorFrom256(self.f.solids[0]),
            self.solid_color_changed, 0)

        table.attach(Gtk.Label(label="Inner Color:"), 0, 2, 1, 1)
        table.attach(self.inner_solid_button, 1, 2, 1, 1)
        table.attach(Gtk.Label(label="Outer Color:"), 2, 2, 1, 1)
        table.attach(self.outer_solid_button, 3, 2, 1, 1)

        self.edit_online_button = Gtk.Button(label=_("Edit Gradient Online"))
        self.edit_online_button.connect('clicked', self.edit_online)
        table.attach(self.edit_online_button, 0, 3, 4, 1)

        self.append(table)

        self.select_segment(-1)

    def gradarea_mousedown(self, gesture, start_x, start_y):
        pass

    def gradarea_clicked(self, gesture, offset_x, offset_y):
        current, x, y = gesture.get_point()
        pos = float(x) / self.gradarea.get_allocated_width()
        i = self.f.get_gradient().get_index_at(pos)
        self.select_segment(i)
        self.redraw()

    def gradarea_mousemoved(self, gesture, offset_x, offset_yt):
        pass

    def redraw(self, *args):
        self.gradarea.queue_draw()

        self.inner_solid_button.set_color(
            utils.floatColorFrom256(self.f.solids[1]))
        self.outer_solid_button.set_color(
            utils.floatColorFrom256(self.f.solids[0]))

        self.edit_online_button.set_sensitive(
            self.f.get_gradient().is_coolorable())

    def edit_online(self, widget):
        grad = self.f.get_gradient()
        url = grad.get_coolor_url()
        # print(url)
        utils.launch_browser(
            url,
            self.main_window)

    def copy_left(self, widget):
        i = self.selected_segment
        if i == -1 or i == 0:
            return

        segments = self.f.get_gradient().segments
        segments[i - 1].right_color = copy.copy(segments[i].left_color)
        self.f.changed()

    def copy_right(self, widget):
        i = self.selected_segment
        segments = self.f.get_gradient().segments
        if i == -1 or i == len(segments) - 1:
            return

        segments[i + 1].left_color = copy.copy(segments[i].right_color)
        self.f.changed()

    def split(self, widget):
        i = self.selected_segment
        if i == -1:
            return
        self.f.get_gradient().add(i)
        self.f.changed()

    def remove(self, widget):
        i = self.selected_segment
        grad = self.f.get_gradient()
        if i == -1 or len(grad.segments) == 1:
            return
        grad.remove(i, True)
        if self.selected_segment > 0:
            self.selected_segment -= 1
        self.f.changed()

    def solid_color_changed(self, r, g, b, index):
        self.f.set_solid(
            index,
            utils.color256FromFloat(r, g, b, self.f.solids[index]))

    def color_changed(self, r, g, b, is_left):
        # print "color changed", r, g, b, is_left
        self.f.get_gradient().set_color(
            self.selected_segment,
            is_left,
            r, g, b)

        self.f.changed()
        self.redraw()

    def select_segment(self, i):
        self.selected_segment = i

        if i == -1:
            self.left_color_button.set_color([0.5, 0.5, 0.5, 1])
            self.right_color_button.set_color([0.5, 0.5, 0.5, 1])
        else:
            grad = self.f.get_gradient()
            self.left_color_button.set_color(grad.segments[i].left_color)
            self.right_color_button.set_color(grad.segments[i].right_color)
        # buttons should be sensitive if selection is good
        self.left_color_button.set_sensitive(i != -1)
        self.right_color_button.set_sensitive(i != -1)
        self.split_button.set_sensitive(i != -1)
        self.remove_button.set_sensitive(i != -1)
        self.copy_right_button.set_sensitive(i != -1)
        self.copy_left_button.set_sensitive(i != -1)

    def show_browser(self, button, type):
        dialog = browser.BrowserDialog(self.main_window, self.f, type)
        dialog.present()


class GradientViewer(Gtk.Widget):
    def __init__(self, f, selected_segment):
        super().__init__(width_request=256, height_request=96)

        self.f = f
        self.selected_segment = selected_segment

        self.grad_handle_height = 8

    def draw_handle(self, total_height, cairo_ctx, midpoint, fill):
        # draw a triangle pointing up, centered on midpoint
        colorband_height = total_height - self.grad_handle_height
        cairo_ctx.set_line_width(1.0)
        cairo_ctx.set_source_rgb(0, 0, 0)
        cairo_ctx.move_to(midpoint - 5, total_height)
        cairo_ctx.line_to(midpoint, colorband_height)
        cairo_ctx.line_to(midpoint + 5, total_height)
        cairo_ctx.line_to(midpoint - 5, total_height)
        if fill:
            cairo_ctx.fill()
        else:
            cairo_ctx.stroke()

    def do_snapshot(self, s):
        # draw the color preview bar
        x, y = 0, 0
        w, h = self.get_width(), self.get_height()
        rect = Graphene.Rect()
        rect.init(0, 0, w, h)
        cairo_ctx = s.append_cairo(rect)

        colorband_height = h - self.grad_handle_height

        grad = self.f.get_gradient()

        cairo_ctx.set_line_width(2.0)
        for i in range(x, x + w):
            pos_in_gradient = i / w
            col = grad.get_color_at(pos_in_gradient)
            cairo_ctx.set_source_rgba(col[0], col[1], col[2])
            cairo_ctx.move_to(i, y)
            cairo_ctx.line_to(i, min(y + h, colorband_height))
            cairo_ctx.stroke()

        # draw the handles
        cairo_ctx.rectangle(
            x,
            colorband_height,
            w,
            self.grad_handle_height)
        cairo_ctx.fill()

        for i in range(len(grad.segments)):
            seg = grad.segments[i]

            left = seg.left * w
            mid = seg.mid * w
            right = seg.right * w

            if i == self.selected_segment:
                # draw this chunk selected
                cairo_ctx.set_line_width(2.0)
                cairo_ctx.set_source_rgb(0, 1.0, 1.0)
                cairo_ctx.rectangle(
                    left,
                    colorband_height,
                    right - left,
                    self.grad_handle_height)
                cairo_ctx.fill()

            self.draw_handle(h, cairo_ctx, left, True)
            self.draw_handle(h, cairo_ctx, mid, False)

        # draw last handle on the right
        self.draw_handle(h, cairo_ctx, w, True)
