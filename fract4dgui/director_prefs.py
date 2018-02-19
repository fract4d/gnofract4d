import os

from gi.repository import Gtk

class DirectorPrefs:
    # wrapper to show dialog for selecting folder
    # returns selected folder or empty string
    def get_folder(self):
        temp_folder = ""
        dialog = Gtk.FileChooserDialog("Choose directory...",None,Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            temp_folder = dialog.get_filename()
        dialog.destroy()
        return temp_folder

    def create_fct_toggled(self,widget,data=None):
        self.btn_temp_fct.set_sensitive(self.chk_create_fct.get_active())
        self.txt_temp_fct.set_sensitive(self.chk_create_fct.get_active())

    def temp_fct_clicked(self,widget, data=None):
        fold = self.get_folder()
        if fold != "":
            self.txt_temp_fct.set_text(fold)

    def temp_png_clicked(self,widget, data=None):
        fold = self.get_folder()
        if fold != "":
            self.txt_temp_png.set_text(fold)

    def __init__(self,animation,parent):
        self.dialog = Gtk.Dialog("Director preferences...",parent,
                      Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                      (Gtk.STOCK_OK,Gtk.ResponseType.OK,Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL))

        self.animation = animation
        # -----------Temporary directories---------------------
        #self.frm_dirs=Gtk.Frame("Temporary directories selection")
        #self.frm_dirs.set_border_width(10)
        self.tbl_dirs = Gtk.Table(n_rows=3,n_columns=3,homogeneous=False)
        self.tbl_dirs.set_row_spacings(10)
        self.tbl_dirs.set_col_spacings(10)
        self.tbl_dirs.set_border_width(10)

        self.lbl_temp_fct = Gtk.Label(label="Temporary directory for .fct files:")
        self.tbl_dirs.attach(self.lbl_temp_fct,0,1,1,2)

        self.txt_temp_fct = Gtk.Entry()
        self.txt_temp_fct.set_text(self.animation.get_fct_dir())
        self.txt_temp_fct.set_sensitive(False)
        self.tbl_dirs.attach(self.txt_temp_fct,1,2,1,2)

        self.btn_temp_fct = Gtk.Button(label="Browse")
        self.btn_temp_fct.connect("clicked",self.temp_fct_clicked,None)
        self.btn_temp_fct.set_sensitive(False)
        self.tbl_dirs.attach(self.btn_temp_fct,2,3,1,2)

        # this check box goes after (even if it's above above widgets because
        # we connect and change its state here and it change those buttons, so they wouldn't exist
        self.chk_create_fct = Gtk.CheckButton(label="Create temporary .fct files")
        self.chk_create_fct.connect("toggled",self.create_fct_toggled,None)
        self.chk_create_fct.set_active(self.animation.get_fct_enabled())
        self.tbl_dirs.attach(self.chk_create_fct,0,1,0,1)

        self.lbl_temp_png = Gtk.Label(label="Temporary directory for .png files:")
        self.tbl_dirs.attach(self.lbl_temp_png,0,1,2,3)

        self.txt_temp_png = Gtk.Entry()
        self.txt_temp_png.set_text(self.animation.get_png_dir())
        self.tbl_dirs.attach(self.txt_temp_png,1,2,2,3)

        self.btn_temp_png = Gtk.Button(label="Browse")
        self.btn_temp_png.connect("clicked",self.temp_png_clicked,None)
        self.tbl_dirs.attach(self.btn_temp_png,2,3,2,3)

        #self.frm_dirs.add(self.tbl_dirs)
        self.dialog.vbox.pack_start(self.tbl_dirs,False,False,0)
        #self.dialog.vbox.pack_start(self.tbl_main,True,True,0)

    # checking is txt fields valid dirs
    def check_fields(self):
        if self.chk_create_fct.get_active():
            # checking fct dir
            if not os.path.isdir(self.txt_temp_fct.get_text()):
                error_dlg = Gtk.MessageDialog(None,Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                            Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                            "Directory for temporary .fct files is not directory")
                error_dlg.run()
                error_dlg.destroy()
                return False
        if not os.path.isdir(self.txt_temp_png.get_text()):
            error_dlg = Gtk.MessageDialog(None,Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                        Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                        "Directory for temporary .png files is not directory")
            error_dlg.run()
            error_dlg.destroy()
            return False
        return True

    def show(self):
        self.dialog.show_all()
        # nasty, nasty hack to keep dialog running while either it is canceled or
        # valid dirs are entered
        is_ok = False
        write = False
        while is_ok is False:
            response = self.dialog.run()
            if response == Gtk.ResponseType.OK:
                    is_ok = self.check_fields()
                    if is_ok:
                        write = True
            else:
                is_ok = True

        if write:
            self.animation.set_fct_enabled(self.chk_create_fct.get_active())
            if self.chk_create_fct.get_active():
                self.animation.set_fct_dir(self.txt_temp_fct.get_text())
            self.animation.set_png_dir(self.txt_temp_png.get_text())

        self.dialog.destroy()
        return
