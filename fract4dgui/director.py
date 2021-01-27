# UI for gathering needed data and storing them in director bean class
# then it calls PNGGeneration, and (if everything was OK) AVIGeneration

# TODO: change default directory when selecting new according to already set item
# (for temp dirs, avi and fct files selections)

import os
import fnmatch
import tempfile
import gi

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, Gio, Gtk, GObject

from fract4d import animation, fractconfig
from . import dialog, hig, PNGGen, AVIGen, DlgAdvOpt, director_prefs, utils


class UserCancelledError(Exception):
    pass


class SanityCheckError(Exception):
    "The type of exception which is thrown when animation sanity checks fail"

    def __init__(self, msg):
        Exception.__init__(self, msg)


class DirectorDialog(dialog.T, hig.MessagePopper):
    RESPONSE_RENDER = 1

    def check_for_keyframe_clash(self, keyframe, fct_dir):
        keydir = os.path.dirname(keyframe)
        if keydir[-1] != "/":
            keydir += "/"

        if fct_dir[-1] != "/":
            fct_dir += "/"
        if keydir == fct_dir:
            raise SanityCheckError(
                _("Keyframe %s is in the temporary .fct directory and could be overwritten. Please change temp directory." % keyframe))

    def check_fct_file_sanity(self):
        # things to check with fct temp dir
        if not self.animation.get_fct_enabled():
            # we're not generating .fct files, so this is superfluous
            return

        # check fct temp dir is set
        if self.animation.get_fct_dir() == "":
            raise SanityCheckError(
                _("Directory for temporary .fct files not set"))

        # check if it is directory
        if not os.path.isdir(self.animation.get_fct_dir()):
            raise SanityCheckError(
                _("Path for temporary .fct files is not a directory"))

        fct_path = self.animation.get_fct_dir()

        # heck if any keyframe fct files are in temp fct dir
        for i in range(self.animation.keyframes_count()):
            keyframe = self.animation.get_keyframe_filename(i)
            self.check_for_keyframe_clash(keyframe, fct_path)

        # check if there are any .fct files in temp fct dir
        has_any = False
        for file in os.listdir(fct_path):
            if fnmatch.fnmatch(file, "*.fct"):
                has_any = True

            if has_any is True:
                response = self.ask_question(
                    _("Directory for temporary .fct files contains other .fct files"),
                    _("These may be overwritten. Proceed?"))
                if response != Gtk.ResponseType.ACCEPT:
                    raise UserCancelledError()
            return

    # throws SanityCheckError if there was a problem
    def check_sanity(self):
        # check if at least two keyframes exist
        if self.animation.keyframes_count() < 2:
            raise SanityCheckError(_("There must be at least two keyframes"))

        # check png temp dir is set
        if self.animation.get_png_dir() == "":
            raise SanityCheckError(
                _("Directory for temporary .png files not set"))

        # check if it is directory
        if not os.path.isdir(self.animation.get_png_dir()):
            raise SanityCheckError(
                _("Path for temporary .png files is not a directory"))

        # check avi file is set
        if self.animation.get_avi_file() == "":
            raise SanityCheckError(_("Output AVI file name not set"))

        self.check_fct_file_sanity()

    # wrapper to show dialog for selecting .fct file
    # returns selected file or empty string
    def get_fct_file(self):
        temp_file = ""
        dialog = utils.FileOpenChooser("Choose keyframe...", self)
        dialog.add_file_filter("gnofract4d files (*.fct)", ["*.fct"])
        dialog.add_file_filter("All files", ["*"])
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            temp_file = dialog.get_filename()
        dialog.destroy()
        return temp_file

    # wrapper to show dialog for selecting .avi file
    # returns selected file or empty string
    def get_avi_file(self):
        temp_file = ""
        dialog = utils.FileSaveChooser("Save AVI file...", self)
        current_file = self.txt_temp_avi.get_text()
        dialog.set_current_name(current_file if current_file else "video.webm")
        dialog.add_file_filter("webm video file (*.webm)", ["*.webm"])
        dialog.add_file_filter("All files", ["*"])
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            temp_file = dialog.get_filename()
        dialog.destroy()
        return temp_file

    # wrapper to show dialog for selecting .cfg file
    # returns selected file or empty string
    def get_cfg_file_save(self):
        temp_file = ""
        dialog = utils.FileSaveChooser("Save animation...", self)
        dialog.set_current_name("animation.fcta")
        dialog.add_file_filter("gnofract4d animation files (*.fcta)", ["*.fcta"])
        dialog.add_file_filter("All files", ["*"])
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            temp_file = dialog.get_filename()
        dialog.destroy()
        return temp_file

    # wrapper to show dialog for selecting .fct file
    # returns selected file or empty string
    def get_cfg_file_open(self):
        temp_file = ""
        dialog = utils.FileOpenChooser("Choose animation...", self)
        dialog.add_file_filter("gnofract4d animation files (*.fcta)", ["*.fcta"])
        dialog.add_file_filter("All files", ["*"])
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            temp_file = dialog.get_filename()
        dialog.destroy()
        return temp_file

    def temp_avi_clicked(self, widget, data=None):
        avi = self.get_avi_file()
        if avi:
            self.txt_temp_avi.set_text(avi)

    def output_width_changed(self, widget, data=None):
        self.animation.set_width(self.spin_width.get_value())

    def output_height_changed(self, widget, data=None):
        self.animation.set_height(self.spin_height.get_value())

    def output_framerate_changed(self, widget, data=None):
        self.animation.set_framerate(self.spin_framerate.get_value())

    def duration_changed(self, widget, data=None):
        if self.current_select == -1:
            return
        self.animation.set_keyframe_duration(
            self.current_select, int(
                self.spin_duration.get_value()))
        self.update_model()

    def stop_changed(self, widget, data=None):
        if self.current_select == -1:
            return
        self.animation.set_keyframe_stop(
            self.current_select, int(
                self.spin_kf_stop.get_value()))
        self.update_model()

    def interpolation_type_changed(self, widget, data=None):
        if self.current_select == -1:
            return
        self.animation.set_keyframe_int(
            self.current_select, int(
                self.cmb_interpolation_type.get_active()))
        self.update_model()

    # point of whole program:)
    # first we generate png files and list, then .avi
    def generate(self, create_avi=True):
        try:
            self.check_sanity()
        except SanityCheckError as exn:
            self.show_error(_("Cannot Generate Animation"), str(exn))
            raise

        png_gen = PNGGen.PNGGeneration(self.animation, self.compiler, self)
        res = png_gen.show()
        if res == 1:
            # user cancelled, but they know that. Stop silently
            return
        elif res != 0:
            # unexpected return code
            return

        if not create_avi:
            return

        avi_gen = AVIGen.AVIGeneration(self.animation, self)
        res = avi_gen.show()
        if res == 1:
            # user cancelled, but they know that. Stop silently
            pass
        elif res == 0:
            # success
            self.show_info(
                _("AVI Generation Complete"),
                _("File is %s." % self.animation.get_avi_file()))

    def generate_clicked(self, widget, data=None):
        self.generate(True)

    def adv_opt_clicked(self, widget, data=None):
        if self.current_select == -1:
            return
        dlg = DlgAdvOpt.DlgAdvOptions(
            self.current_select, self.animation, self)
        dlg.show()

    # before selecting keyframes in list box we must update values of spin
    # boxes in case user typed something in there
    def before_selection(self, selection, data=None, *kwargs):
        self.spin_duration.update()
        self.spin_kf_stop.update()
        return True

    # update right box (duration, stop, interpolation type) when keyframe is
    # selected from list
    def selection_changed(self, widget, data=None):
        (model, it) = self.tv_keyframes.get_selection().get_selected()
        if it is not None:
            # ------getting index of selected row-----------
            index = 0
            it = model.get_iter_first()
            while it is not None:
                if self.tv_keyframes.get_selection().iter_is_selected(it):
                    break
                it = model.iter_next(it)
                index = index + 1
            self.current_select = index
            self.spin_duration.set_value(
                int(self.animation.get_keyframe_duration(index)))
            self.spin_kf_stop.set_value(
                self.animation.get_keyframe_stop(index))
            self.cmb_interpolation_type.set_active(
                self.animation.get_keyframe_int(index))
            return
        else:
            self.spin_duration.set_value(25)
            self.spin_kf_stop.set_value(1)
            self.cmb_interpolation_type.set_active(animation.INT_LINEAR)
            self.current_select = -1

    def update_model(self):
        (model, it) = self.tv_keyframes.get_selection().get_selected()
        if it is not None:
            # ------getting index of selected row-----------
            index = 0
            it = model.get_iter_first()
            while it is not None:
                if self.tv_keyframes.get_selection().iter_is_selected(it):
                    break
                it = model.iter_next(it)
                index = index + 1

            model.set(it, 1, self.animation.get_keyframe_duration(index))
            model.set(it, 2, self.animation.get_keyframe_stop(index))
            int_type = self.animation.get_keyframe_int(index)
            if int_type == animation.INT_LINEAR:
                model.set(it, 3, "Linear")
            elif int_type == animation.INT_LOG:
                model.set(it, 3, "Logarithmic")
            elif int_type == animation.INT_INVLOG:
                model.set(it, 3, "Inverse logarithmic")
            else:
                model.set(it, 3, "Cosine")

    def swap_redblue_clicked(self, widget, data=None):
        self.animation.set_redblue(self.chk_swapRB.get_active())

    def add_from_file(self, widget, data=None):
        file = self.get_fct_file()
        if file != "":
            self.add_keyframe(file)

    def add_from_current(self, widget, data=None):
        (tmp_fd, tmp_name) = tempfile.mkstemp(suffix='.fct')
        with os.fdopen(tmp_fd, 'w') as f:
            self.f.save(f)
        self.add_keyframe(tmp_name)
        return

    def add_keyframe(self, file):
        if file != "":
            # get current seletion
            (model, it) = self.tv_keyframes.get_selection().get_selected()
            if it is None:  # if it's none, just append at the end of the list
                it = model.append([file, 25, 1, "Linear"])
            else:  # append after currently selected
                it = model.insert_after(it, [file, 25, 1, "Linear"])

            # add to bean with default parameters
            if self.current_select != -1:
                self.animation.add_keyframe(
                    file, 25, 1, animation.INT_LINEAR, self.current_select + 1)
            else:
                self.animation.add_keyframe(file, 25, 1, animation.INT_LINEAR)
            # and select newly item
            self.tv_keyframes.get_selection().select_iter(it)
            # set default duration
            self.spin_duration.set_value(25)
            # set default stop
            self.spin_kf_stop.set_value(1)
            # set default interpolation type
            self.cmb_interpolation_type.set_active(animation.INT_LINEAR)

    def remove_keyframe_clicked(self, widget, data=None):
        # is anything selected
        (model, it) = self.tv_keyframes.get_selection().get_selected()
        if it is not None:
            temp_curr = self.current_select
            model.remove(it)
            self.animation.remove_keyframe(temp_curr)

    def updateGUI(self):
        # keyframes
        (model, it) = self.tv_keyframes.get_selection().get_selected()
        model.clear()
        for i in range(self.animation.keyframes_count() - 1, -1, -1):
            filename = self.animation.get_keyframe_filename(i)
            duration = self.animation.get_keyframe_duration(i)
            stopped = self.animation.get_keyframe_stop(i)
            it = model.insert(0, [filename, duration, stopped, ""])
            int_type = self.animation.get_keyframe_int(i)
            if int_type == animation.INT_LINEAR:
                model.set(it, 3, "Linear")
            elif int_type == animation.INT_LOG:
                model.set(it, 3, "Logarithmic")
            elif int_type == animation.INT_INVLOG:
                model.set(it, 3, "Inverse logarithmic")
            else:
                model.set(it, 3, "Cosine")
        # output part
        self.txt_temp_avi.set_text(self.animation.get_avi_file())
        self.spin_width.set_value(self.animation.get_width())
        self.spin_height.set_value(self.animation.get_height())
        self.spin_framerate.set_value(self.animation.get_framerate())
        self.chk_swapRB.set_active(self.animation.get_redblue())

    # loads configuration file, returns 0 on ok, -1 on error (and displays
    # error message)
    def load_configuration(self, file):
        if file == "":
            return -1
        try:
            self.animation.load_animation(file)
        except Exception as err:
            self.show_error(
                _("Cannot load animation"),
                str(err))
            return -1
        # set GUI to reflect changes
        self.updateGUI()
        return 0

    # loads configuration from pickled file
    def load_configuration_clicked(self, *args):
        cfg = self.get_cfg_file_open()
        if cfg != "":
            self.load_configuration(cfg)

    # reset all field to defaults
    def new_configuration_clicked(self, *args):
        self.animation.reset()
        self.updateGUI()

    # save configuration in file
    def save_configuration_clicked(self, *args):
        cfg = self.get_cfg_file_save()
        if cfg != "":
            try:
                self.animation.save_animation(cfg)
            except Exception as err:
                self.show_error(
                    _("Error saving animation"),
                    str(err))

    def preferences_clicked(self, *args):
        dlg = director_prefs.DirectorPrefs(self.animation, self)
        dlg.show()

    # creating window...
    def __init__(self, main_window):
        #pylint: disable=no-member
        dialog.T.__init__(
            self,
            _("Director"),
            main_window,
            (_("_Render"), DirectorDialog.RESPONSE_RENDER,
             _("_Close"), Gtk.ResponseType.CLOSE)
        )

        hig.MessagePopper.__init__(self)
        self.f = main_window.f
        self.compiler = main_window.f.compiler
        self.animation = animation.T(self.compiler, main_window.application.userConfig)

        # main VBox
        self.box_main = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.box_main.set_homogeneous(False)
        # --------------------menu-------------------------------
        accelgroup = Gtk.AccelGroup()
        self.add_accel_group(accelgroup)

        accelerators = [
            (Gdk.KEY_n, self.new_configuration_clicked),
            (Gdk.KEY_o, self.load_configuration_clicked),
            (Gdk.KEY_s, self.save_configuration_clicked),
            (Gdk.KEY_p, self.preferences_clicked),
        ]

        for key, handler in accelerators:
            accelgroup.connect(
                key, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE, handler)

        def add_action(name, handler):
            action = Gio.SimpleAction(name=name)
            action.connect("activate", handler)
            actiongroup.add_action(action)

        actions = [
            ("new", self.new_configuration_clicked),
            ("open", self.load_configuration_clicked),
            ("save", self.save_configuration_clicked),
            ("edit_prefs", self.preferences_clicked),
        ]

        actiongroup = Gio.SimpleActionGroup()
        # SimpleActionGroup.add_action_entries() requires override from PyGObject 3.29.2
        for name, handler in actions:
            add_action(name, handler)
        self.insert_action_group("director", actiongroup)

        menubar = Gtk.MenuBar.new_from_model(
            main_window.application.get_menu_by_id("director_menubar"))
        self.box_main.pack_start(menubar, False, True, 0)

        # -----------creating keyframes popup menu model----------------
        add_action("file_keyframe", self.add_from_file)
        add_action("current_keyframe", self.add_from_current)

        popup_menu = Gio.Menu()
        popup_menu.append("From file", "director.file_keyframe")
        popup_menu.append("From current fractal", "director.current_keyframe")
        # --------------Keyframes box-----------------------------------
        self.frm_kf = Gtk.Frame.new("Keyframes")
        self.frm_kf.set_border_width(10)
        vbox_kfs = Gtk.Box.new(Gtk.Orientation.VERTICAL, 8)
        button_box_kfs = Gtk.ButtonBox()
        button_box_kfs.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        self.sw = Gtk.ScrolledWindow()
        self.sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.sw.set_size_request(-1, 100)
#        filenames=Gtk.ListStore(GObject.TYPE_STRING,
#            GObject.TYPE_STRING)
#        self.tv_keyframes=Gtk.TreeView(filenames)
#        self.tv_column_name = Gtk.TreeViewColumn('Keyframes')
#        self.tv_keyframes.append_column(self.tv_column_name)
#        self.tv_column_duration = Gtk.TreeViewColumn('Duration')
#        self.tv_keyframes.append_column(self.tv_column_duration)
#        self.cell_name = Gtk.CellRendererText()
#        self.tv_column_name.pack_start(self.cell_name, True)
#        self.tv_column_name.add_attribute(self.cell_name, 'text', 0)
#        self.cell_duration = Gtk.CellRendererText()
#        self.tv_column_name.pack_start(self.cell_duration, True)
#        self.tv_column_name.add_attribute(self.cell_duration, 'text', 0)
        filenames = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_UINT,
                                  GObject.TYPE_UINT, GObject.TYPE_STRING)
        self.tv_keyframes = Gtk.TreeView()
        self.tv_keyframes.set_model(filenames)
        column = Gtk.TreeViewColumn(
            'Keyframes', Gtk.CellRendererText(), text=0)
        self.tv_keyframes.append_column(column)

        column = Gtk.TreeViewColumn(
            'Stopped for', Gtk.CellRendererText(), text=2)
        self.tv_keyframes.append_column(column)

        column = Gtk.TreeViewColumn(
            'Transition duration',
            Gtk.CellRendererText(),
            text=1)
        self.tv_keyframes.append_column(column)

        column = Gtk.TreeViewColumn(
            'Interpolation type',
            Gtk.CellRendererText(),
            text=3)
        self.tv_keyframes.append_column(column)

        self.sw.add(self.tv_keyframes)
        self.tv_keyframes.get_selection().connect(
            "changed", self.selection_changed, None)
        self.tv_keyframes.get_selection().set_select_function(self.before_selection, None)
        self.current_select = -1

        self.btn_add_keyframe = Gtk.MenuButton(label="Add", menu_model=popup_menu)

        self.btn_remove_keyframe = Gtk.Button.new_with_label("Remove")
        self.btn_remove_keyframe.connect(
            "clicked", self.remove_keyframe_clicked, None)

        button_box_kfs.pack_start(self.btn_add_keyframe, True, True, 0)
        button_box_kfs.pack_start(self.btn_remove_keyframe, True, True, 0)

        vbox_kfs.pack_start(self.sw, True, True, 0)
        vbox_kfs.pack_start(button_box_kfs, True, True, 10)

        self.frm_kf.add(vbox_kfs)
        self.box_main.pack_start(self.frm_kf, True, True, 0)

        # current keyframe box
        self.current_kf = Gtk.Frame.new("Current Keyframe")
        self.current_kf.set_border_width(10)

        self.box_main.pack_start(self.current_kf, True, True, 0)

        self.tbl_keyframes_right = Gtk.Grid()
        self.tbl_keyframes_right.set_column_homogeneous(True)
        self.tbl_keyframes_right.set_row_homogeneous(True)
        self.tbl_keyframes_right.set_row_spacing(10)
        self.tbl_keyframes_right.set_column_spacing(10)
        self.tbl_keyframes_right.set_border_width(10)

        self.lbl_kf_stop = Gtk.Label(label="Keyframe stopped for:")
        self.tbl_keyframes_right.attach(self.lbl_kf_stop, 0, 0, 1, 1)

        adj_kf_stop = Gtk.Adjustment.new(1, 1, 10000, 1, 10, 0)
        self.spin_kf_stop = Gtk.SpinButton()
        self.spin_kf_stop.set_adjustment(adj_kf_stop)
        self.spin_kf_stop.connect("output", self.stop_changed, None)
        self.tbl_keyframes_right.attach(self.spin_kf_stop, 1, 0, 1, 1)

        self.lbl_duration = Gtk.Label(label="Transition duration:")
        self.tbl_keyframes_right.attach(self.lbl_duration, 0, 1, 1, 1)

        adj_duration = Gtk.Adjustment.new(25, 1, 10000, 1, 10, 0)
        self.spin_duration = Gtk.SpinButton()
        self.spin_duration.set_adjustment(adj_duration)
        self.spin_duration.connect("output", self.duration_changed, None)
        self.tbl_keyframes_right.attach(self.spin_duration, 1, 1, 1, 1)

        self.lbl_int_type = Gtk.Label(label="Interpolation type:")
        self.tbl_keyframes_right.attach(self.lbl_int_type, 0, 2, 1, 1)

        self.cmb_interpolation_type = Gtk.ComboBoxText()  # Gtk.ComboBox()
        self.cmb_interpolation_type.append_text("Linear")
        self.cmb_interpolation_type.append_text("Logarithmic")
        self.cmb_interpolation_type.append_text("Inverse logarithmic")
        self.cmb_interpolation_type.append_text("Cosine")
        self.cmb_interpolation_type.set_active(0)
        self.cmb_interpolation_type.connect(
            "changed", self.interpolation_type_changed, None)
        self.tbl_keyframes_right.attach(
            self.cmb_interpolation_type, 1, 2, 1, 1)

        self.btn_adv_opt = Gtk.Button(label="Advanced options")
        self.btn_adv_opt.connect("clicked", self.adv_opt_clicked, None)
        self.tbl_keyframes_right.attach(self.btn_adv_opt, 0, 3, 2, 1)

        self.current_kf.add(self.tbl_keyframes_right)
        # -------------------------------------------------------------------
        # ----------------------output box-----------------------------------
        self.frm_output = Gtk.Frame.new("Output options")
        self.frm_output.set_border_width(10)

        self.box_output_main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                       homogeneous=True, spacing=10)
        self.box_output_main.set_border_width(10)
        self.box_output_file = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                       homogeneous=False, spacing=10)

        self.lbl_temp_avi = Gtk.Label(label="Resulting video file:")
        self.box_output_file.pack_start(self.lbl_temp_avi, False, False, 10)

        self.txt_temp_avi = Gtk.Entry()
        self.box_output_file.pack_start(self.txt_temp_avi, True, True, 10)

        self.btn_temp_avi = Gtk.Button(label="Browse")
        self.btn_temp_avi.connect("clicked", self.temp_avi_clicked, None)
        self.box_output_file.pack_start(self.btn_temp_avi, True, True, 10)

        self.box_output_main.pack_start(self.box_output_file, True, True, 0)

        self.box_output_res = Gtk.HBox(homogeneous=False, spacing=10)

        self.lbl_res = Gtk.Label(label="Resolution:")
        self.box_output_res.pack_start(self.lbl_res, False, False, 10)

        adj_width = Gtk.Adjustment.new(640, 320, 2048, 10, 100, 0)
        self.spin_width = Gtk.SpinButton()
        self.spin_width.set_adjustment(adj_width)
        self.box_output_res.pack_start(self.spin_width, False, False, 10)

        self.lbl_x = Gtk.Label(label="x")
        self.box_output_res.pack_start(self.lbl_x, False, False, 10)

        adj_height = Gtk.Adjustment.new(480, 240, 1536, 10, 100, 0)
        self.spin_height = Gtk.SpinButton()
        self.spin_height.set_adjustment(adj_height)
        self.box_output_res.pack_start(self.spin_height, False, False, 10)

        self.box_output_main.pack_start(self.box_output_res, True, True, 0)

        self.box_output_framerate = Gtk.HBox(homogeneous=False, spacing=10)

        self.lbl_framerate = Gtk.Label(label="Frame rate:")
        self.box_output_framerate.pack_start(
            self.lbl_framerate, False, False, 10)

        adj_framerate = Gtk.Adjustment.new(25, 5, 100, 1, 5, 0)
        self.spin_framerate = Gtk.SpinButton()
        self.spin_framerate.set_adjustment(adj_framerate)
        self.box_output_framerate.pack_start(
            self.spin_framerate, False, False, 10)

        self.chk_swapRB = Gtk.CheckButton(label="Swap red and blue component")
        self.box_output_framerate.pack_start(self.chk_swapRB, False, False, 50)

        self.box_output_main.pack_start(
            self.box_output_framerate, True, True, 0)

        self.frm_output.add(self.box_output_main)
        self.box_main.pack_start(self.frm_output, False, False, 0)

        # check if video converter can be found
        self.converterpath = fractconfig.T.find_on_path("ffmpeg")
        if not self.converterpath:
            # put a message at the bottom to warn user
            warning_box = Gtk.HBox()
            image = Gtk.Image.new_from_icon_name(
                "dialog-warning", Gtk.IconSize.BUTTON)

            warning_box.pack_start(image, True, True, 0)

            message = Gtk.Label(label=_(
                "ffmpeg utility not found. Without it we can't generate any video but can still save sequences of still images."))

            message.set_line_wrap(True)
            warning_box.pack_start(message, True, True, 0)
            self.box_main.pack_end(warning_box, True, True, 0)

        # initialise default settings
        self.updateGUI()

        # don't connect signals until after settings initialised
        self.spin_height.connect(
            "value-changed",
            self.output_height_changed,
            None)
        self.spin_width.connect(
            "value-changed",
            self.output_width_changed,
            None)
        self.spin_framerate.connect(
            "value-changed", self.output_framerate_changed, None)
        self.chk_swapRB.connect("toggled", self.swap_redblue_clicked, None)

        # --------------showing all-------------------------------
        self.vbox.add(self.box_main)
        self.vbox.show_all()

    def onResponse(self, widget, id):
        if id == Gtk.ResponseType.CLOSE or \
                id == Gtk.ResponseType.NONE or \
                id == Gtk.ResponseType.DELETE_EVENT:
            self.hide()
        elif id == DirectorDialog.RESPONSE_RENDER:
            self.animation.set_avi_file(self.txt_temp_avi.get_text())
            try:
                self.generate(self.converterpath is not None)
            except (SanityCheckError, UserCancelledError):
                # prevent dialog closing if being run
                GObject.signal_stop_emission_by_name(self, "response")
            else:
                self.hide()

    def quit(self, widget, event):
        # GTK 3 popover menu blocks application if showing when dialog is closed
        self.btn_add_keyframe.get_popover().hide()
        return super().quit(widget, event)
