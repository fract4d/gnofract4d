#!/usr/bin/env python3

# Subclass of fract4d.fractal.T which works with a GUI

import os
import struct
import math
import copy
import cairo
import gi

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GdkPixbuf, GLib

from fract4d_compiler import fracttypes, function
from fract4d import fractal, fract4dc, image, messages

from . import utils, fourway


class Hidden(GObject.GObject):
    """This class implements a fractal which calculates asynchronously
    and is integrated with the GTK main loop"""
    __gsignals__ = {
        'parameters-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, ()),
        'iters-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_INT,)),
        'tolerance-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_FLOAT,)),
        'formula-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, ()),
        'status-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_INT,)),
        'progress-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_FLOAT,)),
        'pointer-moved': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_INT,
                   GObject.TYPE_FLOAT, GObject.TYPE_FLOAT)),
        'stats-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_PYOBJECT,))

    }

    def __init__(self, comp, width, height, total_width=-1, total_height=-1):
        GObject.GObject.__init__(self)

        (self.readfd, self.writefd) = os.pipe()
        self.nthreads = 1

        self.compiler = comp

        self.x = self.y = 0
        self.button = 0
        self.last_progress = 0.0
        self.skip_updates = False
        self.running = False
        self.frozen = False  # if true, don't emit signals

        self.site = fract4dc.fdsite_create(self.writefd)
        self.f = None
        self.try_init_fractal()

        self.input_add(self.readfd, self.onData)

        self.width = width
        self.height = height
        self.image = image.T(
            self.width, self.height, total_width, total_height)

        self.msgbuf = b""

    def try_init_fractal(self):
        f = fractal.T(self.compiler, self.site)
        self.set_fractal(f)
        self.f.compile()

    def set_fractal(self, f):
        if f != self.f:
            if self.f:
                self.interrupt()
                del self.f
            self.f = f

            # take over fractal's changed function
            f.changed = self.changed
            f.formula_changed = self.formula_changed
            f.warn = self.warn
            self.formula_changed()
            self.changed()

    def changed(self, clear_image=True):
        if self.f is None:
            return
        self.f.dirty = True
        self.f.clear_image = clear_image
        self.set_saved(False)
        if not self.frozen:
            self.emit('parameters-changed')

    def formula_changed(self):
        # print "formula changed"
        self.f.dirtyFormula = True
        # if not self.frozen:
        self.emit('formula-changed')

    def set_saved(self, val):
        if self.f is not None:
            self.f.saved = val

    def input_add(self, fd, cb):
        utils.input_add(fd, cb)

    def error(self, msg, err):
        print("Error: %s %s" % (msg, err))

    def warn(self, msg):
        print("Warning: ", msg)

    def update_formula(self):
        if self.f is not None:
            self.f.dirtyFormula = True

    def freeze(self):
        self.frozen = True

    def thaw(self):
        if self.f is None:
            return False

        self.frozen = False
        was_dirty = self.f.dirty
        self.f.clean()
        return was_dirty

    def interrupt(self):
        if self.skip_updates:
            # print "skip recursive interrupt"
            return

        self.skip_updates = True

        fract4dc.interrupt(self.site)

        n = 0
        # wait for stream from worker to flush
        while self.running:
            n += 1
            Gtk.main_iteration()

        self.skip_updates = False

    def copy_f(self):
        return copy.copy(self.f)

    def set_formula(self, fname, formula, index=0):
        self.f.set_formula(fname, formula, index)

    def onData(self, fd, condition):
        self.msgbuf = self.msgbuf + \
            os.read(fd, 8 - len(self.msgbuf))

        if len(self.msgbuf) < 8:
            # print "incomplete message: %s" % list(self.msgbuf)
            return True

        (t, size) = struct.unpack("2i", self.msgbuf)
        self.msgbuf = b""
        bytes = os.read(fd, size)
        if len(bytes) < size:
            print(
                "not enough bytes, got %d instead of %d" %
                (len(bytes), size))
            return True

        m = messages.parse(t, bytes)

        if utils.threads_enabled:
            Gdk.threads_enter()

        # print "msg: %s %d %d %d %d" % (m,p1,p2,p3,p4)
        if t == fract4dc.MESSAGE_TYPE_ITERS:
            if not self.skip_updates:
                self.iters_changed(m.iterations)
        elif t == fract4dc.MESSAGE_TYPE_IMAGE:
            if not self.skip_updates:
                self.image_changed(m.x, m.y, m.w, m.h)
        elif t == fract4dc.MESSAGE_TYPE_PROGRESS:
            if not self.skip_updates:
                progress = m.progress
                # filters out 'backwards' progress which can occur due to
                # threading
                if progress > self.last_progress or progress == 0.0:
                    self.progress_changed(progress)
                    self.last_progress = progress
        elif t == fract4dc.MESSAGE_TYPE_STATUS:
            if m.status == fract4dc.CALC_DONE:  # DONE
                self.running = False
            if not self.skip_updates:
                self.status_changed(m.status)
        elif t == fract4dc.MESSAGE_TYPE_PIXEL:
            # FIXME pixel_changed
            pass
        elif t == fract4dc.MESSAGE_TYPE_TOLERANCE:
            # tolerance changed
            if not self.skip_updates:
                self.tolerance_changed(m.tolerance)
        elif t == fract4dc.MESSAGE_TYPE_STATS:
            if not self.skip_updates:
                self.stats_changed(m)
        else:
            print("Unknown message from fractal thread; %s" % list(bytes))

        if utils.threads_enabled:
            Gdk.threads_leave()
        return True

    def __getattr__(self, name):
        return getattr(self.f, name)

    def params(self):
        return self.f.params

    def get_param(self, n):
        return self.f.get_param(n)

    def set_nthreads(self, n):
        if self.nthreads != n:
            self.nthreads = n
            self.changed()

    def set_auto_deepen(self, deepen):
        if self.f.auto_deepen != deepen:
            self.f.auto_deepen = deepen
            self.changed()

    def set_antialias(self, aa_type):
        if self.f.antialias != aa_type:
            self.f.antialias = aa_type
            self.changed()

    def set_func(self, func, fname, formula):
        self.f.set_func(func, fname, formula)

    def improve_quality(self):
        self.freeze()
        self.set_maxiter(self.f.maxiter * 2)
        self.set_period_tolerance(self.f.period_tolerance / 10.0)
        self.thaw()
        self.changed()

    def reset(self):
        self.f.reset()
        self.changed()

    def loadFctFile(self, file):
        new_f = fractal.T(self.compiler, self.site)
        new_f.warn = self.warn
        new_f.loadFctFile(file)
        self.set_fractal(new_f)
        self.set_saved(True)

    def is_saved(self):
        if self.f is None:
            return True
        return self.f.saved

    def save_image(self, filename):
        self.image.save(filename)

    def progress_changed(self, progress):
        self.emit('progress-changed', progress)

    def status_changed(self, status):
        self.emit('status-changed', status)

    def iters_changed(self, n):
        self.f.maxiter = n
        # don't emit a parameters-changed here to avoid deadlock
        self.emit('iters-changed', n)

    def tolerance_changed(self, tolerance):
        self.f.period_tolerance = tolerance
        self.emit('tolerance-changed', tolerance)

    def image_changed(self, x1, y1, x2, y2):
        pass

    def stats_changed(self, stats):
        self.emit('stats-changed', stats)

    def draw(self, image, width, height, nthreads):
        t = self.f.epsilon_tolerance(width, height)
        if self.f.auto_epsilon:
            self.f.set_named_param("@epsilon", t,
                                   self.f.formula, self.f.initparams)

        self.f.init_pfunc()
        cmap = self.f.get_colormap()
        self.running = True
        try:
            self.f.calc(image, cmap, nthreads, self.site, True)
        except MemoryError:
            pass

    def draw_image(self, aa=None, auto_deepen=None):
        if self.f is None:
            return
        self.interrupt()

        self.f.compile()

        if aa is not None and auto_deepen is not None:
            self.f.antialias = aa
            self.f.auto_deepen = auto_deepen

        self.draw(self.image, self.width, self.height, self.nthreads)

    def set_plane(self, angle1, angle2):
        self.freeze()
        self.reset_angles()
        if angle1 is not None:
            self.set_param(angle1, math.pi / 2)
        if angle2 is not None:
            self.f.set_param(angle2, math.pi / 2)

        if self.thaw():
            self.changed()

    def float_coords(self, x, y):
        return ((x - self.width / 2.0) / self.width,
                (y - self.height / 2.0) / self.width)

    def recenter(self, x, y, zoom):
        dx = (x - self.width / 2.0) / self.width
        dy = (y - self.height / 2.0) / self.width
        self.relocate(dx, dy, zoom)

    def count_colors(self, rect):
        # calculate the number of different colors which appear
        # in the subsection of the image bounded by the rectangle
        xstart, ystart, xend, yend = map(int, rect)
        buf = self.image.image_buffer(0, 0)
        colors = {}
        for y in range(ystart, yend):
            for x in range(xstart, xend):
                offset = (y * self.width + x) * 3
                col = buf[offset:offset + 3].hex()
                colors[col] = 1 + colors.get(col, 0)
        return len(colors)

    def get_func_name(self):
        if self.f is None:
            return _("No fractal loaded")
        return self.f.forms[0].funcName

    def get_saved(self):
        if self.f is None:
            return True
        return self.f.get_saved()

    def serialize(self, compress=False):
        if self.f is None:
            return None
        return self.f.serialize(compress)

    def set_size(self, new_width, new_height):
        self.interrupt()
        if self.width == new_width and self.height == new_height:
            return

        self.width = new_width
        self.height = new_height

        self.image.resize_full(new_width, new_height)
        utils.idle_add(self.changed)


# explain our existence to GTK's object system
GObject.type_register(Hidden)


class HighResolution(Hidden):
    "An invisible GtkFractal which computes in multiple chunks"

    def __init__(self, comp, width, height):
        (tile_width, tile_height) = self.compute_tile_size(width, height)

        Hidden.__init__(self, comp, tile_width, tile_height, width, height)
        self.reset_render()

    def reset_render(self):
        self.tile_list = self.image.get_tile_list()
        self.ntiles = len(self.tile_list)
        self.ncomplete_tiles = 0
        self.last_overall_progress = 0.0

    def compute_tile_size(self, w, h):
        tile_width = w
        tile_height = min(h, 128)
        return (tile_width, tile_height)

    def draw_image(self, name):
        if self.f is None:
            return
        self.interrupt()

        self.f.compile()

        self.f.auto_deepen = False
        self.f.auto_tolerance = False
        self.image.start_save(name)
        self.next_tile()
        return False

    def next_tile(self):
        # work left to do
        (xoff, yoff, w, h) = self.tile_list.pop(0)
        self.image.resize_tile(w, h)
        self.image.set_offset(xoff, yoff)
        self.draw(self.image, w, h, self.nthreads)

    def status_changed(self, status):
        if status == 0:
            # done this chunk
            self.image.save_tile()
            self.ncomplete_tiles += 1
            if len(self.tile_list) > 0:
                self.next_tile()
            else:
                # completely done
                self.image.finish_save()
                self.emit('status-changed', status)
        else:
            self.emit('status-changed', status)

    def progress_changed(self, progress):
        overall_progress = (
            100.0 * self.ncomplete_tiles + progress) / self.ntiles
        if overall_progress > self.last_overall_progress:
            self.emit('progress-changed', overall_progress)
            self.last_overall_progress = overall_progress


class T(Hidden):
    "A visible GtkFractal which responds to user input"
    SELECTION_LINE_WIDTH = 2.0

    def __init__(self, comp, parent=None, width=640, height=480):
        self.parent = parent
        Hidden.__init__(self, comp, width, height)

        self.paint_mode = False

        drawing_area = Gtk.DrawingArea()
        drawing_area.set_events(
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.BUTTON1_MOTION_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.POINTER_MOTION_HINT_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.KEY_PRESS_MASK |
            Gdk.EventMask.KEY_RELEASE_MASK |
            Gdk.EventMask.EXPOSURE_MASK
        )

        self.notice_mouse = False

        drawing_area.connect('motion_notify_event', self.onMotionNotify)
        drawing_area.connect('button_release_event', self.onButtonRelease)
        drawing_area.connect('button_press_event', self.onButtonPress)
        drawing_area.connect('draw', self.redraw_rect)

        self.selection_rect = []

        drawing_area.set_size_request(self.width, self.height)

        self.widget = drawing_area

    def image_changed(self, x1, y1, x2, y2):
        self.widget.queue_draw_area(x1, y1, x2 - x1, y2 - y1)

    def make_numeric_entry(self, form, param, order):
        if param.type == fracttypes.Int:
            fmt = "%d"
        else:
            fmt = "%.17f"

        widget = Gtk.Entry()
        widget.set_activates_default(True)

        def set_entry():
            new_value = fmt % form.params[order]
            if widget.get_text() != new_value:
                widget.set_text(new_value)

        def set_fractal(entry, event, form, order):
            try:
                utils.idle_add(
                    form.set_param, order, entry.get_text())
            except Exception as err:
                # FIXME: produces too many errors
                msg = "Invalid value '%s': must be a number" % \
                      entry.get_text()
                print(msg)
                # utils.idle_add(f.warn,msg)
            return False

        set_entry()

        widget.update_function = set_entry

        widget.f = self
        widget.connect('focus-out-event', set_fractal, form, order)

        if hasattr(param, "min") and hasattr(param, "max"):
            # add a slider
            adj = Gtk.Adjustment(
                value=0.0,
                lower=param.min.value, upper=param.max.value,
                step_increment=0.001, page_increment=0.01)

            def set_adj():
                if adj.get_value() != form.params[order]:
                    adj.set_value(form.params[order])

            set_adj()

            def adj_changed(adjustment, form, order):
                utils.idle_add(
                    form.set_param, order, adjustment.get_value())

            adj.connect('value-changed', adj_changed, form, order)

            hscale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, adj)
            hscale.set_draw_value(False)
            hscale.update_function = set_adj
            vbox = Gtk.VBox()
            vbox.pack_start(widget, True, True, 0)
            vbox.pack_start(hscale, True, True, 0)
            return vbox

        return widget

    def make_numeric_widget(
            self, table, i, form, name, part, param, order):

        label = Gtk.Label.new(self.param_display_name(name, param) + part)
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.CENTER)
        table.attach(label, 0, i, 1, 1)

        widget = self.make_numeric_entry(form, param, order)

        label.set_mnemonic_widget(widget)
        return widget

    def make_bool_widget(self, form, name, param, order):

        widget = Gtk.CheckButton(label=self.param_display_name(name, param))

        def set_toggle(*args):
            is_set = form.params[order]
            widget.set_active(is_set)
            if widget.get_active() != is_set:
                widget.set_active(is_set)

        def set_fractal(entry, form, order):
            try:
                utils.idle_add(form.set_param, order, entry.get_active())
            except Exception as err:
                msg = "error setting bool param: %s" % str(err)
                print(msg)
                #utils.idle_add(f.warn, msg)

            return False

        set_toggle(self)

        widget.update_function = set_toggle
        widget.f = self
        widget.connect('toggled', set_fractal, form, order)
        return widget

    def make_color_widget(
            self, table, i, form, name, param, order):

        label = Gtk.Label.new(self.param_display_name(name, param))
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.CENTER)
        table.attach(label, 0, i, 1, 1)

        def set_fractal(r, g, b, is_left):
            self.freeze()
            form.set_param(order, r)
            form.set_param(order + 1, g)
            form.set_param(order + 2, b)
            if self.thaw():
                self.changed()

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

    def make_enumerated_widget(
            self, table, i, form, name, part, param, order):

        label = Gtk.Label.new(self.param_display_name(name, param))
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.CENTER)
        table.attach(label, 0, i, 1, 1)

        widget = utils.create_option_menu(param.enum.value)

        def set_selected_value(*args):
            try:
                index = form.params[order]
            except ValueError as err:
                print(err)
                return

            utils.set_selected(widget, index)

        def set_fractal(entry, form, order):
            new_value = utils.get_selected(widget)
            form.set_param(order, new_value)

        set_selected_value(self)

        widget.update_function = set_selected_value

        widget.f = self
        widget.connect('changed',
                       set_fractal, form, order)

        label.set_mnemonic_widget(widget)
        return widget

    def add_formula_setting(
            self, table, i, form, name, part, param, order):

        if param.type == fracttypes.Int:
            if hasattr(param, "enum"):
                widget = self.make_enumerated_widget(
                    table, i, form, name, part, param, order)
            else:
                widget = self.make_numeric_widget(
                    table, i, form, name, part, param, order)

        elif param.type == fracttypes.Float or \
                param.type == fracttypes.Complex or \
                param.type == fracttypes.Hyper:

            widget = self.make_numeric_widget(
                table, i, form, name, part, param, order)
        elif param.type == fracttypes.Bool:
            widget = self.make_bool_widget(
                form, name, param, order)
        elif param.type == fracttypes.Color:
            widget = self.make_color_widget(
                table, i, form, name, param, order)
        elif param.type == fracttypes.Image:
            # skip image params for now
            return
        else:
            raise "Unsupported parameter type"

        table.attach(widget, 1, i, 1, 1)

    def add_complex_formula_setting(
            self, table, i, form, name, param, order, param_type):

        widget = self.make_numeric_entry(form, param, order)
        widget.set_hexpand(True)
        table.attach(widget, 1, i, 1, 1)

        widget = self.make_numeric_entry(form, param, order + 1)
        table.attach(widget, 1, i + 1, 1, 1)

        name = self.param_display_name(name, param)
        fway = fourway.T(name)
        tip = self.param_tip(name, param)
        fway.set_tooltip_text(tip)
        fway.set_hexpand(True)

        fway.connect('value-changed', self.fourway_released, order, form)

        if self.parent:
            fway.connect(
                'value-slightly-changed',
                self.parent.on_drag_param_fourway, order, param_type)

        table.attach(fway, 0, i, 1, 2)

    def fourway_released(self, widget, x, y, order, form):
        form.nudge_param(order, x, y)

    def construct_function_menu(self, param, form):
        funclist = sorted(form.formula.symbols.available_param_functions(
            param.ret, param.args))
        return funclist

    def set_nthreads(self, n):
        if self.nthreads != n:
            self.nthreads = n
            self.changed()

    def error(self, msg, err):
        print(self, self.parent)
        if self.parent:
            self.parent.show_error_message(msg, err)
        else:
            print("Error: %s : %s" % (msg, err))

    def warn(self, msg):
        if self.parent:
            self.parent.show_warning(msg)
        else:
            print("Warning: ", msg)

    def add_formula_function(self, table, i, name, param, form):
        label = Gtk.Label.new(self.param_display_name(name, param))
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.CENTER)
        table.attach(label, 0, i, 1, 1)

        funclist = self.construct_function_menu(param, form)
        widget = utils.create_option_menu(funclist)

        formula = form.formula

        def set_selected_function():
            try:
                selected_func_name = form.get_func_value(name)
                index = funclist.index(selected_func_name)
            except ValueError as err:
                # func.cname not in list
                # print "bad cname"
                return

            utils.set_selected(widget, index)

        def set_fractal_function(om, f, param, formula):
            index = utils.get_selected(om)
            if index != -1:
                # this shouldn't be necessary but I got weird errors
                # trying to reuse the old funclist
                list = sorted(formula.symbols.available_param_functions(
                    param.ret, param.args))

                fname = list[index]
                f.set_func(param, fname, formula)

        set_selected_function()

        widget.update_function = set_selected_function

        widget.connect('changed', set_fractal_function, self, param, formula)

        table.attach(widget, 1, i, 1, 1)

    def create_maxiter_widget(self, table, i):
        label = Gtk.Label(label="_Max Iterations")
        label.set_halign(Gtk.Align.END)
        label.set_valign(Gtk.Align.CENTER)
        label.set_use_underline(True)
        table.attach(label, 0, i, 1, 1)

        widget = Gtk.Entry()
        widget.set_activates_default(True)

        def set_entry(*args):
            widget.set_text("%d" % self.f.maxiter)

        def set_fractal(*args):
            try:
                try:
                    i = int(widget.get_text())
                    self.set_maxiter(i)
                except ValueError as err:
                    msg = "Invalid value '%s': must be a number" % \
                          widget.get_text()
                    utils.idle_add(self.warn, msg)
            except Exception as exn:
                print(exn)
            return False

        set_entry(self)

        self.connect('parameters-changed', set_entry)
        self.connect('iters-changed', set_entry)
        widget.connect('focus-out-event', set_fractal)

        label.set_mnemonic_widget(widget)
        table.attach(widget, 1, i, 1, 1)
        return i + 1

    def populate_formula_settings(self, table, param_type, row=0):
        # create widget to fiddle with this fractal's settings
        form = self.f.get_form(param_type)
        formula = form.formula

        if param_type == 0:
            row = self.create_maxiter_widget(table, row)

        params = formula.symbols.parameters()
        op = formula.symbols.order_of_params()

        keys = sorted(params.keys())
        for name in keys:
            param = params[name]
            if isinstance(param, function.Func):
                self.add_formula_function(table, row, name, param, form)
            else:
                if param.type == fracttypes.Complex:
                    self.add_complex_formula_setting(
                        table, row, form, name, param,
                        op[name],
                        param_type)
                    row += 1
                elif param.type == fracttypes.Hyper:
                    suffixes = [" (re)", " (i)", " (j)", " (k)"]
                    for j in range(4):
                        self.add_formula_setting(
                            table, row + j, form, name, suffixes[j],
                            param, op[name] + j)
                    row += 3
                elif param.type == fracttypes.Color:
                    self.add_formula_setting(
                        table, row, form, name, "",
                        param, op[name])
                    row += 3
                elif param.type == fracttypes.Gradient:
                    # FIXME
                    pass
                else:
                    self.add_formula_setting(
                        table, row, form, name, "", param, op[name])
            row += 1
        return table

    def set_size(self, new_width, new_height):
        try:
            Hidden.set_size(self, new_width, new_height)
            self.widget.set_size_request(new_width, new_height)
        except MemoryError as err:
            utils.idle_add(self.warn, str(err))

    def draw_image(self, aa=None, auto_deepen=None):
        try:
            Hidden.draw_image(self, aa, auto_deepen)
        except fracttypes.TranslationError as err:
            advice = _(
                "\nCheck that your compiler settings and formula file are correct.")
            utils.idle_add(self.error,
                           _("Error compiling fractal:"),
                           err.msg + advice)
            return

    def onMotionNotify(self, widget, event):
        x, y = self.float_coords(event.x, event.y)
        self.emit('pointer-moved', self.button, x, y)

        if not self.notice_mouse:
            return

        self.newx, self.newy = event.x, event.y

        dy = int(abs(self.newx - self.x) * float(self.height) / self.width)
        if(self.newy < self.y or (self.newy == self.y and self.newx < self.x)):
            dy = -dy
        self.newy = self.y + dy

        # create a dummy Cairo context to calculate the affected bounding box
        surface = cairo.ImageSurface(cairo.FORMAT_A1, self.width, self.height)
        cairo_ctx = cairo.Context(surface)
        cairo_ctx.set_line_width(T.SELECTION_LINE_WIDTH)
        if self.selection_rect:
            cairo_ctx.rectangle(*self.selection_rect)

        self.selection_rect = [
            int(min(self.x, self.newx)),
            int(min(self.y, self.newy)),
            int(abs(self.newx - self.x)),
            int(abs(self.newy - self.y))]

        cairo_ctx.rectangle(*self.selection_rect)
        x1, y1, x2, y2 = cairo_ctx.stroke_extents()

        self.widget.queue_draw_area(x1, y1, x2 - x1, y2 - y1)

    def onButtonPress(self, widget, event):
        self.x = event.x
        self.y = event.y
        self.newx = self.x
        self.newy = self.y
        self.button = event.button
        if self.button == 1:
            self.notice_mouse = True

    def set_paint_mode(self, isEnabled, colorsel):
        self.paint_mode = isEnabled
        self.paint_color_sel = colorsel

    def get_paint_color(self):
        color = self.paint_color_sel.get_current_color()
        return (color.red / 65535.0, color.green /
                65535.0, color.blue / 65535.0)

    def onPaint(self, x, y):
        # obtain index
        fate = self.image.get_fate(int(x), int(y))
        if not fate:
            return

        index = self.image.get_color_index(int(x), int(y))

        # obtain a color
        (r, g, b) = self.get_paint_color()

        # update colormap
        grad = self.f.get_gradient()

        (is_solid, color_type) = fate
        if color_type == 0x20:
            print("update fate")
            color_type = 1  # FATE_UNKNOWN is treated as INSIDE
        if is_solid:
            self.f.solids[color_type] = (
                int(r * 255.0), int(g * 255.0), int(b * 255.0), 255)
        else:
            i = grad.get_index_at(index)
            if index > grad.segments[i].mid:
                alpha = grad.segments[i].right_color[3]
                grad.segments[i].right_color = [r, g, b, alpha]
            else:
                alpha = grad.segments[i].left_color[3]
                grad.segments[i].left_color = [r, g, b, alpha]

        self.changed(False)

    def filterPaintModeRelease(self, event):
        if self.paint_mode:
            if event.button == 1:
                if self.x == self.newx or self.y == self.newy:
                    self.onPaint(self.newx, self.newy)
                    return True

        return False

    def onButtonRelease(self, widget, event):
        self.widget.queue_draw()
        self.button = 0
        self.notice_mouse = False
        self.selection_rect.clear()
        if self.filterPaintModeRelease(event):
            return

        self.freeze()
        if event.button == 1:
            if self.x == self.newx or self.y == self.newy:
                zoom = 0.5
                x = self.x
                y = self.y
            else:
                zoom = (1 + abs(self.x - self.newx)) / float(self.width)
                x = 0.5 + (self.x + self.newx) / 2.0
                y = 0.5 + (self.y + self.newy) / 2.0

            # with shift held, don't zoom
            if hasattr(event, "state") and event.get_state() & Gdk.ModifierType.SHIFT_MASK:
                zoom = 1.0
            self.recenter(x, y, zoom)

        elif event.button == 2:
            (x, y) = (event.x, event.y)
            zoom = 1.0
            self.recenter(x, y, zoom)
            if self.is4D():
                self.flip_to_julia()

        else:
            if hasattr(event, "state") and event.get_state(
            ) & Gdk.ModifierType.CONTROL_MASK:
                zoom = 20.0
            else:
                zoom = 2.0
            (x, y) = (event.x, event.y)
            self.recenter(x, y, zoom)

        if self.thaw():
            self.changed()

    def redraw_rect(self, widget, cairo_ctx):
        result, r = Gdk.cairo_get_clip_rectangle(cairo_ctx)
        if result:
            x, y, w, h = r.x, r.y, r.width, r.height
        else:
            print("Skipping drawing because entire context clipped")
            return

        try:
            buf = self.image.image_buffer(x, y)
        except MemoryError as err:
            # suppress these errors
            return

        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes(buf),
            GdkPixbuf.Colorspace.RGB,
            False,
            8,
            min(self.width - x, w),
            min(self.height - y, h),
            self.width * 3)
        Gdk.cairo_set_source_pixbuf(cairo_ctx, pixbuf.copy(), x, y)
        cairo_ctx.paint()

        if self.selection_rect:
            cairo_ctx.set_source_rgb(1.0, 1.0, 1.0)
            cairo_ctx.set_line_width(T.SELECTION_LINE_WIDTH)
            cairo_ctx.rectangle(*self.selection_rect)
            cairo_ctx.stroke()


class Preview(T):
    def __init__(self, comp, width=120, height=90):
        T.__init__(self, comp, None, width, height)

    def onButtonRelease(self, widget, event):
        pass

    def error(self, msg, exn):
        # suppress errors from previews
        pass

    def stats_changed(self, s):
        pass


class SubFract(T):
    def __init__(self, comp, width=640, height=480):
        T.__init__(self, comp, None, width, height)
        self.master = None

    def set_master(self, master):
        self.master = master

    def onButtonRelease(self, widget, event):
        self.button = 0
        if self.master:
            self.master.set_fractal(self.copy_f())

    def onMotionNotify(self, widget, event):
        pass

    def error(self, msg, exn):
        # suppress errors from subfracts, if they ever happened
        # it would be too confusing
        pass
