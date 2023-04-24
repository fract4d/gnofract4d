import os

from gi.repository import Gtk, GObject

from . import utils


class DirectorPrefs:
    # wrapper to show dialog for selecting folder
    # returns selected folder or empty string
    def get_folder(self, callback):
        dialog = utils.DirectoryChooser("Choose directory...", self.dialog)

        def response(dialog, response_id):
            temp_folder = dialog.get_filename()
            dialog.destroy()
            if response_id == Gtk.ResponseType.OK and temp_folder:
                callback(temp_folder)
        dialog.connect("response", response)
        dialog.present()

    def create_fct_toggled(self, widget, data=None):
        self.btn_temp_fct.set_sensitive(self.chk_create_fct.get_active())
        self.txt_temp_fct.set_sensitive(self.chk_create_fct.get_active())

    def temp_fct_clicked(self, widget, data=None):
        self.get_folder(self.txt_temp_fct.set_text)

    def temp_png_clicked(self, widget, data=None):
        self.get_folder(self.txt_temp_png.set_text)

    def __init__(self, animation, parent):
        self.dialog = Gtk.Dialog(title="Director preferences...",
                                 transient_for=parent,
                                 modal=True, destroy_with_parent=True)
        self.dialog.add_buttons(_("_OK"), Gtk.ResponseType.OK,
                                _("_Cancel"), Gtk.ResponseType.CANCEL)

        self.animation = animation
        # -----------Temporary directories---------------------
        tbl_dirs = Gtk.Grid(row_spacing=10, column_spacing=10, css_classes=["content"])

        tbl_dirs.attach(
            Gtk.Label(label="Temporary directory for .fct files:"), 0, 1, 1, 1)

        self.txt_temp_fct = Gtk.Entry(text=self.animation.get_fct_dir(), sensitive=False)
        tbl_dirs.attach(self.txt_temp_fct, 1, 1, 1, 1)

        self.btn_temp_fct = Gtk.Button(label="Browse", sensitive=False)
        self.btn_temp_fct.connect("clicked", self.temp_fct_clicked)
        tbl_dirs.attach(self.btn_temp_fct, 2, 1, 1, 1)

        # this check box goes after (even if it's above above widgets because
        # we connect and change its state here and it change those buttons, so
        # they wouldn't exist
        self.chk_create_fct = Gtk.CheckButton(
            label="Create temporary .fct files")
        self.chk_create_fct.connect("toggled", self.create_fct_toggled)
        self.chk_create_fct.set_active(self.animation.get_fct_enabled())
        tbl_dirs.attach(self.chk_create_fct, 0, 0, 1, 1)

        tbl_dirs.attach(
            Gtk.Label(label="Temporary directory for .png files:"), 0, 2, 1, 1)

        self.txt_temp_png = Gtk.Entry(text=self.animation.get_png_dir())
        tbl_dirs.attach(self.txt_temp_png, 1, 2, 1, 1)

        btn_temp_png = Gtk.Button(label="Browse")
        btn_temp_png.connect("clicked", self.temp_png_clicked)
        tbl_dirs.attach(btn_temp_png, 2, 2, 1, 1)

        self.dialog.get_content_area().append(tbl_dirs)

        self.dialog.connect('response', self.onResponse)

    # checking is txt fields valid dirs
    def check_fields(self):
        if self.chk_create_fct.get_active():
            # checking fct dir
            if not os.path.isdir(self.txt_temp_fct.get_text()):
                error_dlg = Gtk.MessageDialog(
                    title="Directory for temporary .fct files is not directory",
                    transient_for=self.dialog,
                    modal=True, destroy_with_parent=True)
                error_dlg.add_buttons(
                    Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
                error_dlg.present()
                return False
        if not os.path.isdir(self.txt_temp_png.get_text()):
            error_dlg = Gtk.MessageDialog(
                title="Directory for temporary .png files is not directory",
                transient_for=self.dialog,
                modal=True, destroy_with_parent=True)
            error_dlg.add_buttons(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
            error_dlg.present()
            return False
        return True

    def onResponse(self, widget, id):
        if id == Gtk.ResponseType.OK and not self.check_fields():
            GObject.signal_stop_emission_by_name(self.dialog, "response")

    def show_dialog(self):
        def response(dialog, response_id):
            self.dialog.destroy()
            if response_id == Gtk.ResponseType.OK:
                self.animation.set_fct_enabled(self.chk_create_fct.get_active())
                if self.chk_create_fct.get_active():
                    self.animation.set_fct_dir(self.txt_temp_fct.get_text())
                self.animation.set_png_dir(self.txt_temp_png.get_text())
        self.dialog.connect("response", response)
        self.dialog.present()


class DlgAdvOptions:
    # Original copyright from DlgAdvOpt.py:
    # Copyright (C) 2006  Branko Kokanovic
    """Dialog for advanced interpolation options for director"""
    def __init__(self, current_kf, animation, parent):
        self.dialog = Gtk.Dialog(
            transient_for=parent,
            title="Keyframe advanced options",
            modal=True,
            destroy_with_parent=True
        )
        self.dialog.add_buttons(_("_OK"), Gtk.ResponseType.OK,
                                _("_Cancel"), Gtk.ResponseType.CANCEL)

        self.current_kf = current_kf
        self.animation = animation

        tbl_main = Gtk.Grid(row_spacing=10, column_spacing=10)
        dirs = animation.get_directions(self.current_kf)
        self.cmbs = []
        for i, plane in enumerate(["XY", "XZ", "XW", "YZ", "YW", "ZW"]):
            tbl_main.attach(
                Gtk.Label(label=f"{plane} angles interpolation direction:"), 0, i, 1, 1)
            cmb = utils.combo_box_text_with_items(
                ["Nearer", "Longer", "Clockwise", "Counterclockwise"])
            cmb.set_active(dirs[i])
            tbl_main.attach(cmb, 1, i, 1, 1)
            self.cmbs.append(cmb)

        self.dialog.get_content_area().append(tbl_main)

    def show_dialog(self):
        def response(dialog, response_id):
            if response_id == Gtk.ResponseType.OK:
                dirs = ([cmb.get_active() for cmb in self.cmbs])
                self.animation.set_directions(self.current_kf, dirs)
            dialog.destroy()
        self.dialog.connect("response", response)
        self.dialog.present()
