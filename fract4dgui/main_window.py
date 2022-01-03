# main window

import math

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gio, GLib, Gtk

from fract4d import fractconfig
from fract4d_compiler import fc, fracttypes
from .application_window import Actions, ApplicationWindow
from . import (model, preferences, autozoom, browser, utils, hig, painter,
               renderqueue, director)

STATUS = [_("Done"),
          _("Calculating"),
          _("Deepening (%d iterations)"),
          _("Antialiasing"),
          _("Paused"),
          _("Reducing Periodicity Tolerance")]


class Application(Gtk.Application):
    def __init__(self, options, userConfig):
        super().__init__(application_id="io.github.fract4d")
        self.mainWindow = None
        self.options = options
        self.userConfig = userConfig

        resource = Gio.resource_load(
            fractconfig.T.find_resource("gnofract4d.gresource", ""))
        Gio.resources_register(resource)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.userPrefs = preferences.Preferences(self.userConfig)
        self.compiler = fc.Compiler(self.userConfig)
        for path in self.options.extra_paths:
            self.compiler.add_func_path(path)

    def do_activate(self):
        if not self.mainWindow:
            self.mainWindow = MainWindow(self)
            self.mainWindow.apply_options(self.options)
            GLib.idle_add(self.mainWindow.first_draw)

        self.mainWindow.present()


class MainWindow(Actions, ApplicationWindow):
    def __init__(self, application):
        ApplicationWindow.__init__(self, application)
        self.compiler = application.compiler
        self.userPrefs = application.userPrefs

        self.model = model.Model(self.f)
        self.renderQueue = renderqueue.T(self.userPrefs)

        self.directorDialog = director.DirectorDialog(self)
        self.painterDialog = painter.PainterDialog(self)
        self.renderqueueDialog = renderqueue.QueueDialog(self)

        self.update_subfract_visibility(False)
        self.populate_warpmenu(self.f)
        self.update_image_prefs(self.userPrefs)

        self.f.set_saved(True)

        self.create_actions()

        self.f.connect('parameters-changed', self.on_fractal_change)
        self.f.connect('formula-changed', self.on_formula_change)
        self.f.connect('progress_changed', self.progress_changed)
        self.f.connect('status_changed', self.status_changed)
        self.f.connect('stats-changed', self.stats_changed)

        self.f.connect('parameters-changed', self.update_preview)
        self.f.connect('pointer-moved', self.update_preview_on_pointer)

        self.connect('delete-event', self.quit)
        self.connect('window-state-event', self.on_window_state_event)

        self.userPrefs.connect('image-preferences-changed', self.on_prefs_changed)

    def update_subfract_visibility(self, visible):
        if visible:
            self.fractalWindow.show_all()
            self.weirdbox.show_all()
        else:
            self.fractalWindow.hide_subfracts()
            self.weirdbox.hide()

        self.show_subfracts = visible
        self.update_image_prefs(self.userPrefs)

    def update_subfracts(self):
        if not self.show_subfracts:
            return

        self.fractalWindow.update_subfracts(
            self.weirdness_adjustment.get_value() / 100.0,
            self.color_weirdness_adjustment.get_value() / 100.0,
            self.userPrefs.getint("display", "antialias"),
            self.userPrefs.getboolean("display", "autodeepen"))

    def on_formula_change(self, f):
        is4d = f.is4D()
        for widget in self.four_d_sensitives:
            widget.set_sensitive(is4d)
        for name in self.fourd_actiongroup.list_actions():
            self.application.lookup_action(name).set_enabled(is4d)

    def draw_image(self):
        nt = self.userPrefs.getint("general", "threads")
        self.f.set_nthreads(nt)

        self.f.draw_image()

    def update_compiler_prefs(self, prefs):
        # update compiler
        self.compiler.update_from_prefs(prefs)

        if self.f:
            self.f.update_formula()

    def update_image_prefs(self, prefs):
        (w, h) = (prefs.getint("display", "width"),
                  prefs.getint("display", "height"))
        if self.show_subfracts:
            w = w // 2
            h = h // 2
            self.fractalWindow.set_subfract_size(w // 2, h // 2)
            w += 2
            h += 2
        self.f.set_size(w, h)

        self.f.set_antialias(
            prefs.getint("display", "antialias"))
        self.f.set_auto_deepen(
            prefs.getboolean("display", "autodeepen"))
        self.f.set_auto_tolerance(
            prefs.getboolean("display", "autotolerance"))
        self.f.set_continuous_zoom(prefs.getboolean("display", "continuouszoom"))

    def on_prefs_changed(self, prefs):
        self.f.freeze()
        self.update_compiler_prefs(prefs)
        self.update_image_prefs(prefs)
        if self.f.thaw():
            self.draw_image()

    def on_window_state_event(self, widget, event):
        if not event.new_window_state & Gdk.WindowState.FULLSCREEN and \
                self.normal_window_size:
            self.resize(*self.normal_window_size)
            self.normal_window_size = None

    def set_window_title(self):
        title = self.filename.display_filename()
        if not self.f.get_saved():
            title += "*"

        self.set_title(title)

    def first_draw(self):
        self.on_fractal_change()
        self.f.thaw()

    def on_fractal_change(self, *args):
        self.draw_image()
        self.set_window_title()
        self.update_subfracts()

    def set_filename(self, name):
        self.filename.set_filename(name)
        self.set_window_title()

    def nudge(self, x, y, state):
        axis = 0
        if state & Gdk.ModifierType.SHIFT_MASK:
            axis = 2
        if state & Gdk.ModifierType.CONTROL_MASK:
            x *= 10.0
            y *= 10.0
        self.f.nudge(x, y, axis)

    def on_key_left(self, action, parameter):
        self.nudge(-1, 0, parameter.unpack())

    def on_key_right(self, action, parameter):
        self.nudge(1, 0, parameter.unpack())

    def on_key_up(self, action, parameter):
        self.nudge(0, -1, parameter.unpack())

    def on_key_down(self, action, parameter):
        self.nudge(0, 1, parameter.unpack())

    def progress_changed(self, f, progress):
        self.statusbar.set_fraction(progress / 100.0)

    def stats_changed(self, f, stats):
        self.statusbar.set_tooltip_text(stats.show())

    def status_changed(self, f, status):
        if status == 2:
            # deepening
            text = STATUS[status] % self.f.maxiter
        elif status == 0:
            # done
            text = STATUS[status]
            if self.save_filename:
                self.save_image_file(self.save_filename)
            if self.quit_when_done:
                self.f.set_saved(True)
                self.quit(None, None)

        else:
            text = STATUS[status]

        self.statusbar.set_text(text)

    def save_hires_image(self, *args):
        """Add the current fractal to the render queue."""
        save_filename = self.filename.default_image_filename(".png")

        fs = self.get_save_hires_image_as_fs()
        fs.set_filename(save_filename)
        fs.show_all()

        name = None
        while True:
            result = fs.run()
            if result == Gtk.ResponseType.OK:
                name = fs.get_filename()
            else:
                break

            if name and self.confirm(name):
                self.add_to_queue(name, *fs.get_hires_dimensions())
                break
        fs.hide()

    def director(self, *args):
        """Display the Director (animation) window."""
        self.directorDialog.show()

    def browser(self, *args):
        """Display formula browser."""
        dialog = browser.BrowserDialog(self, self.f)
        dialog.run()
        dialog.destroy()

    def randomize_colors(self, *args):
        """Create a new random color scheme."""
        self.f.make_random_colors(8)

    def painter(self, *args):
        self.painterDialog.show()

    def add_to_queue(self, name, w, h):
        self.renderqueueDialog.show()
        self.renderQueue.add(self.f.f, name, w, h)
        self.renderQueue.start()

    def toggle_explorer(self, action, parameter):
        """Enter (or leave) Explorer mode."""
        state = action.get_state() == GLib.Variant("b", False)
        self.set_explorer_state(state)

    def toggle_full_screen(self, action, parameter):
        """Switch main window to/from full-screen."""
        to_full = action.get_state() == GLib.Variant("b", False)
        if to_full:
            if not self.normal_window_size:
                self.normal_window_size = self.get_size()

            if not self.normal_display_size:
                self.normal_display_size = (
                    self.userPrefs.getint("display", "width"),
                    self.userPrefs.getint("display", "height"))

            self.fullscreen()
            self.set_show_menubar(False)
            self.toolbar.hide()
            self.statusbar.hide()
            self.fractalWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

            display = self.get_display()
            monitor = display.get_monitor_at_window(self.get_window())
            geometry = monitor.get_geometry()
            self.userPrefs.set_size(geometry.width, geometry.height)

        else:
            if self.normal_display_size:
                self.userPrefs.set_size(*self.normal_display_size)
                self.normal_display_size = None
            self.fractalWindow.set_policy(
                Gtk.PolicyType.AUTOMATIC,
                Gtk.PolicyType.AUTOMATIC)
            self.set_show_menubar(True)
            self.toolbar.show()
            self.statusbar.show()
            self.unfullscreen()

        self.fullscreen_action.set_state(GLib.Variant("b", to_full))

    def update_preview(self, f, flip2julia=False):
        if self.use_preview:
            self.preview.set_fractal(f.copy_f())
            self.draw_preview()

    def update_preview_on_pointer(self, f, button, x, y):
        if self.use_preview and button == 2:
            self.preview.set_fractal(f.copy_f())
            self.preview.relocate(x, y, 1.0)
            self.preview.flip_to_julia()
            self.draw_preview()

    def draw_preview(self):
        auto_deepen = self.userPrefs.getboolean("display", "autodeepen")
        self.preview.draw_image(False, auto_deepen)

    def improve_now(self, *args):
        self.f.improve_quality()

    def set_explorer_state(self, active):
        self.explorer_action.set_state(GLib.Variant("b", active))
        self.update_subfract_visibility(active)

    def update_angle_widget(self, f, widget):
        widget.set_value(f.get_param(widget.axis))

    def on_angle_slightly_changed(self, widget, val):
        self.preview.set_param(widget.axis, val)
        angle_in_degrees = "%.2f" % (float(val) * 180.0 / math.pi)
        self.statusbar.set_text(angle_in_degrees)
        self.draw_preview()

    def on_angle_changed(self, widget, val):
        self.f.set_param(widget.axis, val)

    def on_drag_fourway(self, widget, dx, dy):
        self.preview.nudge(dx / 10.0, dy / 10.0, widget.axis)
        self.draw_preview()

    def on_drag_param_fourway(self, widget, dx, dy, order, param_type):
        try:
            self.preview.nudge_param(order, param_type, dx, dy)
        except Exception as err:
            print(param_type)
            print(err)
            raise
        self.draw_preview()

    def on_release_fourway(self, widget, dx, dy):
        self.f.nudge(dx / 10.0, dy / 10.0, widget.axis)

    def populate_warpmenu(self, f):
        params = f.forms[0].params_of_type(fracttypes.Complex, True)
        if params == []:
            self.warpmenu.hide()
        else:
            self.warpmenu.remove_all()
            for entry in ["None"] + params:
                self.warpmenu.append_text(entry)
            p = f.warp_param
            if p is None:
                p = "None"
            self.warpmenu.set_active_id(p)
            self.warpmenu.show()

    def save_file(self, file):
        try:
            comp = self.userPrefs.getboolean("general", "compress_fct")
            with open(file, 'w') as fileHandle:
                self.f.save(fileHandle, compress=comp)
            self.set_filename(file)
            return True
        except Exception as err:
            self.show_error_message(
                _("Error saving to file %s") % file, err)
            return False

    def save(self, *args):
        """Save the current parameters."""
        if self.filename.filename is None:
            self.saveas()
        else:
            self.save_file(self.filename.filename)

    def saveas(self, *args):
        """Save the current parameters into a new file."""
        save_filename = self.filename.default_save_filename()

        fs = self.get_save_as_fs()
        fs.set_filename(save_filename)
        fs.show_all()

        name = None
        while True:
            result = fs.run()
            if result == Gtk.ResponseType.OK:
                name = fs.get_filename()
            else:
                break

            if name and self.confirm(name):
                if self.save_file(name):
                    break

        fs.hide()

    def save_image(self, *args):
        """Save the current image to a file."""
        save_filename = self.filename.default_image_filename(".png")

        fs = self.get_save_image_as_fs()
        fs.set_filename(save_filename)
        fs.show_all()

        name = None
        while True:
            result = fs.run()
            if result == Gtk.ResponseType.OK:
                name = fs.get_filename()
            else:
                break

            if name and self.confirm(name):
                try:
                    self.save_image_file(name)
                    break
                except Exception as err:
                    self.show_error_message(
                        _("Error saving image %s") % name, err)
        fs.hide()

    def save_image_file(self, filename):
        try:
            self.f.save_image(filename)
            return True
        except Exception as err:
            self.show_error_message(
                _("Error saving image to file %s") % filename, err)
            return False

    def settings(self, *args):
        """Show fractal settings controls."""
        self.settingsPane.show()

    def preferences(self, *args):
        """Change current preferences."""
        dialog = preferences.PrefsDialog(self, self.f, self.userPrefs)
        dialog.run()
        dialog.destroy()

    def undo(self, *args):
        """Undo the last operation."""
        self.model.undo()

    def redo(self, *args):
        """Redo an operation after undoing it."""
        self.model.redo()

    def paste(self, *args):
        """Paste (can be used to update colors)."""

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text = clipboard.wait_for_text()
        if text is None:
            return

        grad = self.f.get_gradient()
        grad.load_from_url(text)
        self.f.set_gradient(grad)
        self.f.changed()

    def reset(self, *args):
        """Reset all numeric parameters to their defaults."""
        self.f.reset()

    def reset_zoom(self, *args):
        """Reset zoom to default level."""
        self.f.reset_zoom()

    def set_xy_plane(self, *args):
        """Reset rotation to show the XY (Mandelbrot) plane."""
        # left = +x, down = +y
        self.f.set_plane(None, None)

    def set_xz_plane(self, *args):
        """Reset rotation to show the XZ (Oblate) plane."""
        # left = +x, down = +z
        self.f.set_plane(None, self.f.YZANGLE)

    def set_xw_plane(self, *args):
        """Reset rotation to show the XW (Parabolic) plane."""
        # left =+x, down = +w
        self.f.set_plane(None, self.f.YWANGLE)

    def set_zw_plane(self, *args):
        """Reset rotation to show the ZW (Julia) plane."""
        # left = +z, down = +w
        self.f.set_plane(self.f.XZANGLE, self.f.YWANGLE)

    def set_yz_plane(self, *args):
        """Reset rotation to show the YZ (Elliptic) plane."""
        # left = +z, down = +y
        self.f.set_plane(self.f.XZANGLE, None)

    def set_wy_plane(self, *args):
        """Reset rotation to show the WY (Rectangular) plane."""
        # left =+w, down = +y
        self.f.set_plane(self.f.XWANGLE, None)

    def autozoom(self, *args):
        """Display AutoZoom dialog."""
        dialog = autozoom.AutozoomDialog(self, self.f)
        dialog.run()
        dialog.destroy()

    def contents(self, *args):
        """Show help file contents page."""
        self.display_help()

    def report_bug(self, *args):
        url = "https://github.com/fract4d/gnofract4d/issues"
        utils.launch_browser(url, self)

    def open(self, *args):
        """Open a parameter or formula file."""
        fs = self.get_open_fs(self.compiler)
        fs.show_all()

        while True:
            result = fs.run()
            if result == Gtk.ResponseType.OK:
                if self.load(fs.get_filename()):
                    break
            else:
                break

        fs.hide()

    def load(self, file):
        try:
            if fc.FormulaTypes.isFormula(file):
                self.load_formula(file)
                return True
            with open(file) as fh:
                self.f.loadFctFile(fh)
            self.set_filename(file)
            return True
        except Exception as err:
            self.show_error_message(_("Error opening %s") % file, err)
            return False

    def load_formula(self, file):
        try:
            self.compiler.load_formula_file(file)
            dialog = browser.BrowserDialog(self, self.f)
            dialog.load_file(file)
            dialog.run()
            dialog.destroy()

            return True
        except Exception as err:
            self.show_error_message(_("Error opening %s") % file, err)
            return False

    def check_save_fractal(self):
        "Prompt user to save if necessary. Return whether to quit"
        while not self.f.is_saved():
            d = hig.SaveConfirmationAlert(
                document_name=self.filename.display_filename(),
                transient_for=self)

            response = d.run()
            d.destroy()
            if response == Gtk.ResponseType.ACCEPT:
                self.save(None)
            elif response == Gtk.ResponseType.CANCEL \
                    or response == Gtk.ResponseType.DELETE_EVENT:
                return False
            elif response == hig.SaveConfirmationAlert.NOSAVE:
                break

        while not self.renderQueue.empty():
            d = hig.ConfirmationAlert(
                primary=_("Render queue still processing."),
                secondary=_("If you proceed, queued images will not be saved"),
                proceed_button=_("Close anyway"),
                transient_for=self)

            response = d.run()
            d.destroy()
            if response == Gtk.ResponseType.ACCEPT:
                break
            elif response == Gtk.ResponseType.CANCEL:
                return False
            else:
                break
        return True

    def quit(self, action, widget=None):
        """Quit Gnofract 4D."""
        self.f.interrupt()
        self.fractalWindow.interrupt()
        if not self.check_save_fractal():
            # user doesn't want to quit after all
            return True

        try:
            self.userPrefs.set_main_window_size(*self.get_size())
            self.userPrefs.save()
            del self.f
            for f in self.fractalWindow.subfracts:
                del f
            self.compiler.clear_cache()
        finally:
            self.application.quit()

    def apply_options(self, opts):
        "Deal with opts gathered from cmd-line"
        width = opts.width or self.userPrefs.getint("display", "width")
        height = opts.height or self.userPrefs.getint("display", "height")

        self.quit_when_done = opts.quit_when_done
        self.save_filename = opts.save_filename
        self.use_preview = opts.preview

        if opts.paramfile:
            self.load(opts.paramfile)

        self.f.apply_options(opts)
        self.update_preview(self.f)

        if opts.trace:
            self.f.set_compiler_option("trace", opts.trace)
            self.f.compile()

        if opts.tracez:
            self.f.set_compiler_option("tracez", opts.tracez)
            self.f.compile()

        if opts.explore:
            self.set_explorer_state(True)

        self.f.set_size(width, height)
