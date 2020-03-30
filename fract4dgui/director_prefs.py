import os
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class DirectorPrefs:
    # wrapper to show dialog for selecting folder
    # returns selected folder or empty string
    def get_folder(self):
        temp_folder = ""
        dialog = Gtk.FileChooserDialog(title="Choose directory...",
                                       transient_for=self.dialog,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            temp_folder = dialog.get_filename()
        dialog.destroy()
        return temp_folder

    def create_fct_toggled(self, widget, data=None):
        self.btn_temp_fct.set_sensitive(self.chk_create_fct.get_active())
        self.txt_temp_fct.set_sensitive(self.chk_create_fct.get_active())

    def temp_fct_clicked(self, widget, data=None):
        fold = self.get_folder()
        if fold:
            self.txt_temp_fct.set_text(fold)

    def temp_png_clicked(self, widget, data=None):
        fold = self.get_folder()
        if fold:
            self.txt_temp_png.set_text(fold)

    def __init__(self, animation, parent):
        self.dialog = Gtk.Dialog(title="Director preferences...",
                                 transient_for=parent,
                                 modal=True, destroy_with_parent=True)
        self.dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.animation = animation
        # -----------Temporary directories---------------------
        #self.frm_dirs=Gtk.Frame("Temporary directories selection")
        # self.frm_dirs.set_border_width(10)
        tbl_dirs = Gtk.Grid()
        tbl_dirs.set_row_spacing(10)
        tbl_dirs.set_column_spacing(10)
        tbl_dirs.set_property("margin", 10)

        lbl_temp_fct = Gtk.Label(label="Temporary directory for .fct files:")
        tbl_dirs.attach(lbl_temp_fct, 0, 1, 1, 1)

        self.txt_temp_fct = Gtk.Entry()
        self.txt_temp_fct.set_text(self.animation.get_fct_dir())
        self.txt_temp_fct.set_sensitive(False)
        tbl_dirs.attach(self.txt_temp_fct, 1, 1, 1, 1)

        self.btn_temp_fct = Gtk.Button(label="Browse")
        self.btn_temp_fct.connect("clicked", self.temp_fct_clicked, None)
        self.btn_temp_fct.set_sensitive(False)
        tbl_dirs.attach(self.btn_temp_fct, 2, 1, 1, 1)

        # this check box goes after (even if it's above above widgets because
        # we connect and change its state here and it change those buttons, so
        # they wouldn't exist
        self.chk_create_fct = Gtk.CheckButton(
            label="Create temporary .fct files")
        self.chk_create_fct.connect("toggled", self.create_fct_toggled, None)
        self.chk_create_fct.set_active(self.animation.get_fct_enabled())
        tbl_dirs.attach(self.chk_create_fct, 0, 0, 1, 1)

        lbl_temp_png = Gtk.Label(label="Temporary directory for .png files:")
        tbl_dirs.attach(lbl_temp_png, 0, 2, 1, 1)

        self.txt_temp_png = Gtk.Entry()
        self.txt_temp_png.set_text(self.animation.get_png_dir())
        tbl_dirs.attach(self.txt_temp_png, 1, 2, 1, 1)

        btn_temp_png = Gtk.Button(label="Browse")
        btn_temp_png.connect("clicked", self.temp_png_clicked, None)
        tbl_dirs.attach(btn_temp_png, 2, 2, 1, 1)

        # self.frm_dirs.add(tbl_dirs)
        self.dialog.vbox.pack_start(tbl_dirs, False, False, 0)
        # self.dialog.vbox.pack_start(self.tbl_main,True,True,0)

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
                error_dlg.run()
                error_dlg.destroy()
                return False
        if not os.path.isdir(self.txt_temp_png.get_text()):
            error_dlg = Gtk.MessageDialog(
                title="Directory for temporary .png files is not directory",
                transient_for=self.dialog,
                modal=True, destroy_with_parent=True)
            error_dlg.add_buttons(Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
            error_dlg.run()
            error_dlg.destroy()
            return False
        return True

    def onResponse(self, widget, id):
        if id == Gtk.ResponseType.OK and not self.check_fields():
            GObject.signal_stop_emission_by_name(self.dialog, "response")

    def show(self):
        self.dialog.show_all()
        response = self.dialog.run()
        if response == Gtk.ResponseType.OK:
            self.animation.set_fct_enabled(self.chk_create_fct.get_active())
            if self.chk_create_fct.get_active():
                self.animation.set_fct_dir(self.txt_temp_fct.get_text())
            self.animation.set_png_dir(self.txt_temp_png.get_text())

        self.dialog.destroy()
