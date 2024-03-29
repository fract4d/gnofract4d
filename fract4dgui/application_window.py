# pylint: disable=no-member

import os

from gi.repository import Gdk, Gio, Gtk

from fract4d import fractal, fractconfig, image
from fract4d.options import VERSION
from . import angle, application_widgets, fourway, gtkfractal, hig, settings, utils

TOOLITEM_SIZE = 53


class Actions:
    def get_toggle_actions(self):
        return [
            ("ToolsExplorerAction", self.toggle_explorer, "<Ctrl>e"),
            ("ViewFullScreenAction", self.toggle_full_screen, "F11"),
        ]

    def get_main_actions(self):
        return [
            ("FileOpenAction", self.open, "<Ctrl>o"),
            ("FileSaveAction", self.save, "<Ctrl>s"),
            ("FileSaveAsAction", self.saveas, "<Ctrl><Shift>s"),
            ("FileSaveImageAction", self.save_image, "<Ctrl>i"),
            ("FileSaveHighResImageAction", self.save_hires_image, "<Ctrl><Shift>i"),
            ("FileQuitAction", self.quit, "<Ctrl>q"),

            ("EditFractalSettingsAction", self.settings, "<Ctrl>f"),
            ("EditPreferencesAction", self.preferences, None),

            # View Full Screen is a toggle, see above

            ("ToolsAutozoomAction", self.autozoom, "<Ctrl>a"),
            # explorer is a toggle, see above
            ("ToolsBrowserAction", self.browser, "<Ctrl>b"),
            ("ToolsDirectorAction", self.director, "<Ctrl>d"),
            ("ToolsRandomizeAction", self.randomize_colors, "<Ctrl>r"),
            ("ToolsPainterAction", self.painter, None),

            ("HelpContentsAction", self.contents, "F1"),
            # Command Reference action is win.show-help-overlay
            ("HelpReportBugAction", self.report_bug, None),
            ("HelpAboutAction", self.about, None),

            ("ImproveNow", self.improve_now, None),
        ]

    def get_edit_reset_actions(self):
        return [
            ("EditUndoAction", self.undo, "<Ctrl>z"),
            ("EditRedoAction", self.redo, "<Ctrl><Shift>z"),
            ("EditResetAction", self.reset, "Home"),
            ("EditResetZoomAction", self.reset_zoom, "<Ctrl>Home"),
            ("EditPasteAction", self.paste, "<Ctrl>v"),
        ]

    def get_arrow_actions(self):
        return [
            ("Left", self.on_key_left),
            ("Right", self.on_key_right),
            ("Up", self.on_key_up),
            ("Down", self.on_key_down),
        ]

    def get_fourd_actions(self):
        return [
            ("PlanesXYAction", self.set_xy_plane, "<Ctrl>1"),
            ("PlanesZWAction", self.set_zw_plane, "<Ctrl>2"),
            ("PlanesXZAction", self.set_xz_plane, "<Ctrl>3"),
            ("PlanesXWAction", self.set_xw_plane, "<Ctrl>4"),
            ("PlanesYZAction", self.set_yz_plane, "<Ctrl>5"),
            ("PlanesWYAction", self.set_wy_plane, "<Ctrl>6"),
        ]

    def create_actions(self):
        # Missing override for Gtk.Application.add_action_entries():
        # https://gitlab.gnome.org/GNOME/pygobject/-/issues/426
        # main actions
        main_actions = self.get_main_actions() + self.get_edit_reset_actions()
        Gio.ActionMap.add_action_entries(
            self.application,
            [(name, callback)
             for name, callback, accel in main_actions]
        )
        for name, callback, accel in main_actions:
            self.application.set_accels_for_action(f"app.{name}", [accel])

        # actions with parameters
        Gio.ActionMap.add_action_entries(
            self.application, [(*x, "i") for x in self.get_arrow_actions()])
        for key in [x[0] for x in self.get_arrow_actions()]:
            self.application.set_accels_for_action(
                f"app.{key}(0)",
                [f"{key}"])
            self.application.set_accels_for_action(
                f"app.{key}({int(Gdk.ModifierType.SHIFT_MASK)})",
                [f"<Shift>{key}"])
            self.application.set_accels_for_action(
                f"app.{key}({int(Gdk.ModifierType.CONTROL_MASK)})",
                [f"<Control>{key}"])
            self.application.set_accels_for_action(
                f"app.{key}"
                f"({int(Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK)})",
                [f"<Shift><Control>{key}"])

        # stateful actions
        Gio.ActionMap.add_action_entries(
            self.application,
            [(name, None, None, "false", callback)
             for name, callback, accel in self.get_toggle_actions()]
        )
        for name, callback, accel in self.get_toggle_actions():
            self.application.set_accels_for_action(f"app.{name}", [accel])

        # actions which are only available if we're in 4D mode
        self.fourd_actiongroup = Gio.SimpleActionGroup()
        self.fourd_actiongroup.add_action_entries(
            [(name, callback)
             for name, callback, accel in self.get_fourd_actions()]
        )
        self.insert_action_group("app", self.fourd_actiongroup)
        for name, callback, accel in self.get_fourd_actions():
            self.application.set_accels_for_action(f"app.{name}", [accel])

        self.model.seq.register_callbacks(
            self.application.lookup_action("EditRedoAction").set_enabled,
            self.application.lookup_action("EditUndoAction").set_enabled)


class ApplicationDialogs:
    # pylint: disable=access-member-before-definition
    def get_open_fs(self, compiler):
        if self.open_fs is None:
            self.open_fs = application_widgets.Fract4dOpenChooser(
                self, gtkfractal.Preview(compiler))
        return self.open_fs

    def get_save_as_fs(self):
        if self.saveas_fs is None:
            self.saveas_fs = utils.FileSaveChooser(
                _("Save Parameters"), self, ["*.fct"])
        return self.saveas_fs

    def get_save_image_as_fs(self):
        if self.saveimage_fs is None:
            self.saveimage_fs = utils.FileSaveChooser(
                _("Save Image"), self, image.file_matches())
        return self.saveimage_fs

    def get_save_hires_image_as_fs(self):
        if self.hires_image_fs is None:
            self.hires_image_fs = application_widgets.HiresImageSaveChooser(
                self, image.file_matches())
        return self.hires_image_fs

    def about(self, *args):
        aboutDialog = Gtk.AboutDialog(
            transient_for=self,
            modal=True,
            comments=_("Easy to use fractal image generator supporting multiple"
                       " views of a four‑dimensional object"),
            copyright=_("Copyright © 1999-2021, Edwin Young\n"
                        "All rights reserved.\n"
                        "Distributed under the BSD license."
                        ' See the file "LICENSE" for details.'),
            logo_icon_name="gnofract4d",
            program_name="Gnofract 4D",
            version=VERSION,
            website="https://fract4d.github.io/gnofract4d/",
            website_label="fract4d.github.io/gnofract4d"
        )
        aboutDialog.present()

    def confirm(self, name, call_back):
        'if this file exists, check with user before overwriting it'
        if os.path.exists(name):
            def response(dialog, response_id):
                d.destroy()
                call_back(response_id == Gtk.ResponseType.ACCEPT)
            d = hig.ConfirmationAlert(
                primary=_("File %s already exists. Overwrite?") % name,
                transient_for=self,
                proceed_button=_("Overwrite"))

            d.connect("response", response)
            d.present()
        else:
            call_back(True)

    def show_warning(self, message):
        def response(dialog, response_id):
            dialog.destroy()
        d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                              Gtk.MessageType.WARNING, Gtk.ButtonsType.OK,
                              message)
        d.connect("response", response)
        d.present()

    def show_error_message(self, message, exception=None):
        if exception is None:
            secondary_message = ""
        else:
            if isinstance(exception, EnvironmentError):
                secondary_message = exception.strerror or str(exception) or ""
            else:
                secondary_message = str(exception)

        def response(dialog, response_id):
            dialog.destroy()
        d = hig.ErrorAlert(
            primary=message, secondary=secondary_message, transient_for=self)
        d.connect("response", response)
        d.present()

    def display_help(self, section=None):
        helpfile = fractconfig.T.find_resource("index.html", "help")

        abs_file = os.path.abspath(helpfile)

        if not os.path.isfile(abs_file):
            self.show_error_message(
                _("Can't display help"),
                _("Can't find help file '%s'") % abs_file)
        else:
            if section is None:
                anchor = ""
            else:
                anchor = "#" + section

            url = f"file://{abs_file}{anchor}"
            utils.launch_browser(url, self)


class ApplicationWindow(Gtk.ApplicationWindow, ApplicationDialogs):
    def __init__(self, application):
        Gtk.ApplicationWindow.__init__(
            self,
            application=application,
            default_width=application.userPrefs.getint("main_window", "width"),
            default_height=application.userPrefs.getint("main_window", "height"),
            name="main_window",
            show_menubar=True,
        )

        self.application = application
        self.quit_when_done = False
        self.save_filename = None
        self.compress_saves = True
        self.use_preview = True
        self.normal_display_size = None
        self.normal_window_size = None

        # create these properly later to avoid 'end from FAM server connection'
        # messages
        self.saveas_fs = None
        self.saveimage_fs = None
        self.hires_image_fs = None
        self.open_fs = None

        self.four_d_sensitives = []

        # fractal objects
        self.f = gtkfractal.T(application.compiler, self)
        self.f.freeze()  # create frozen - main prog queues first_draw() to thaw

        self.filename = application_widgets.FractalFilename(self.f)

        self.preview = gtkfractal.Preview(
            application.compiler, TOOLITEM_SIZE, TOOLITEM_SIZE)
        self.preview.widget.set_tooltip_text(_("Preview"))

        theme_provider = Gtk.CssProvider()
        theme_provider.load_from_resource("/io/github/fract4d/gnofract4d.css")
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), theme_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # window
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.vbox)

        self.create_toolbar()
        panes = Gtk.Paned(vexpand=True, resize_end_child=False, shrink_end_child=False)
        self.vbox.append(panes)

        self.statusbar = Gtk.ProgressBar(show_text=True)
        self.vbox.append(self.statusbar)

        try:
            # try to make default image more interesting
            self.f.set_cmap(
                fractconfig.T.find_resource("basic.map", "maps"))
        except Exception:
            pass

        self.fractalWindow = application_widgets.FractalWindow(self.f, application.compiler)
        panes.set_start_child(self.fractalWindow)

        self.settingsPane = settings.SettingsPane(self, self.f)
        panes.set_end_child(self.settingsPane)

    def add_fourway(self, name, tip, axis, is4dsensitive):
        my_fourway = fourway.T(name, tip, axis, TOOLITEM_SIZE)
        self.toolbar.append(my_fourway)

        my_fourway.connect('value-slightly-changed', self.on_drag_fourway)
        my_fourway.connect('value-changed', self.on_release_fourway)

        if is4dsensitive:
            self.four_d_sensitives.append(my_fourway)

    def add_warpmenu(self, tip):
        self.warpmenu = utils.combo_box_text_with_items(["None"], tip)
        self.warpmenu.set_id_column(0)

        def update_warp_param(menu, f):
            param = menu.get_active_id()
            if param == "None":
                param = None

            f.set_warp_param(param)
            self.on_formula_change(f)

        # self.populate_warpmenu(self.f,warpmenu)

        self.f.connect('formula-changed', self.populate_warpmenu)

        self.warpmenu.connect("changed", update_warp_param, self.f)

        self.toolbar.append(self.warpmenu)

    def add_angle(self, name, tip, axis, is4dsensitive):
        my_angle = angle.T(name, tip, axis, round(TOOLITEM_SIZE * 0.75))
        my_angle.connect('value-slightly-changed',
                         self.on_angle_slightly_changed)
        my_angle.connect('value-changed',
                         self.on_angle_changed)

        self.f.connect('parameters-changed',
                       self.update_angle_widget, my_angle)

        self.toolbar.append(my_angle)

        if is4dsensitive:
            self.four_d_sensitives.append(my_angle)

    def create_resolution_menu(self):
        self.resolutions = [
            (320, 240), (640, 480),
            (800, 600), (1024, 768),
            (1280, 800), (1280, 960), (1280, 1024),
            (1400, 1050), (1440, 900),
            (1600, 1200), (1680, 1050),
            (1920, 1200), (2560, 1600), (3840, 2160)]

        res_names = ["%dx%d" % (w, h) for (w, h) in self.resolutions]

        res_menu = utils.dropdown_with_items(res_names, _("Resolution"))

        def set_selected_resolution(prefs):
            res = (w, h) = (prefs.getint("display", "width"),
                            prefs.getint("display", "height"))

            try:
                index = self.resolutions.index(res)
            except ValueError:
                # not found
                self.resolutions.append(res)
                item = "%dx%d" % (w, h)
                res_menu.get_model().append(item)
                index = len(self.resolutions) - 1

            res_menu.set_selected(int(index))

        def set_resolution(*args):
            index = res_menu.get_selected()
            if index != -1:
                (w, h) = self.resolutions[index]
                self.userPrefs.set_size(w, h)
                self.update_subfracts()
            # prevent cursor keys navigating toolbar
            self.set_focus()

        set_selected_resolution(self.application.userPrefs)
        res_menu.connect('notify::selected-item', set_resolution)

        self.application.userPrefs.connect('preferences-changed', set_selected_resolution)

        return res_menu

    def create_toolbar(self):
        self.toolbar = application_widgets.Toolbar()
        # request enough space for toolbar items
        self.vbox.append(self.toolbar)

        # preview
        self.toolbar.add_space()

        self.toolbar.append(self.preview.widget)

        # angles
        self.toolbar.add_space()

        self.add_angle(
            _("xy"), _("Angle in the XY plane"), fractal.T.XYANGLE, False)

        self.add_angle(
            _("xz"), _("Angle in the XZ plane"), fractal.T.XZANGLE, True)

        self.add_angle(
            _("xw"), _("Angle in the XW plane"), fractal.T.XWANGLE, True)

        self.add_angle(
            _("yz"), _("Angle in the YZ plane"), fractal.T.YZANGLE, True)

        self.add_angle(
            _("yw"), _("Angle in the YW plane"), fractal.T.YWANGLE, True)

        self.add_angle(
            _("zw"), _("Angle in the ZW plane"), fractal.T.ZWANGLE, True)

        # fourways
        self.toolbar.add_space()

        self.add_fourway(
            _("pan"),
            _("Pan around the image"), 0, False)
        self.add_fourway(
            _("warp"),
            _("Mutate the image by moving along the other 2 axes"), 2, True)

        self.add_warpmenu(_("Which parameter is being warped"))

        # deepen/resize
        self.toolbar.add_space()

        self.toolbar.add_button(
            "improve_now",
            _("Double the maximum number of iterations and tighten periodicity."
              " This will fill in some black areas but increase drawing time"),
            "app.ImproveNow")

        res_menu = self.create_resolution_menu()

        self.toolbar.append(res_menu)

        # undo/redo
        self.toolbar.add_space()

        self.toolbar.add_button(
            "edit-undo",
            _("Undo the last change"),
            "app.EditUndoAction")

        self.toolbar.add_button(
            "edit-redo",
            _("Redo the last undone change"),
            "app.EditRedoAction")

        # explorer mode widgets
        self.toolbar.add_space()

        self.explorer_toolbar_button = self.toolbar.add_toggle(
            "explorer_mode",
            _("Toggle Explorer Mode"),
            "app.ToolsExplorerAction")

        # explorer weirdness
        self.weirdbox = Gtk.Grid(
            name="weirdbox",
            tooltip_text=_("Weirdness"),
            column_homogeneous=False,
            row_spacing=5)
        # shape
        self.weirdness_adjustment = Gtk.Adjustment.new(
            20.0, 0.0, 100.0, 5.0, 5.0, 0.0)
        weirdness = Gtk.Scale(
            adjustment=self.weirdness_adjustment,
            width_request=120,
            value_pos=Gtk.PositionType.RIGHT)
        shape_label = Gtk.Label(label=_("Shape:"), xalign=0.0)

        self.weirdbox.attach(shape_label, 0, 0, 1, 1)
        self.weirdbox.attach(weirdness, 1, 0, 1, 1)
        # color
        self.color_weirdness_adjustment = Gtk.Adjustment.new(
            20.0, 0.0, 100.0, 5.0, 5.0, 0.0)
        color_weirdness = Gtk.Scale(
            adjustment=self.color_weirdness_adjustment,
            value_pos=Gtk.PositionType.RIGHT)
        color_label = Gtk.Label(label=_("Color:"), xalign=0.0)

        self.weirdbox.attach(color_label, 0, 1, 1, 1)
        self.weirdbox.attach(color_weirdness, 1, 1, 1, 1)

        self.toolbar.append(self.weirdbox)

        def on_weirdness_changed(adjustment):
            self.update_subfracts()

        self.weirdness_adjustment.connect('value-changed', on_weirdness_changed)
        self.color_weirdness_adjustment.connect('value-changed', on_weirdness_changed)
