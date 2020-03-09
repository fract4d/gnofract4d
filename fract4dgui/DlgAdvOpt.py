#!/usr/bin/python

# Copyright (C) 2006  Branko Kokanovic
#
#   DlgAdvOpt.py: dialog for advanced interpolation options for director
#

from gi.repository import Gtk


class DlgAdvOptions:
    def __init__(self, current_kf, animation, parent):
        self.dialog = Gtk.Dialog(
            transient_for=parent,
            title="Keyframe advanced options",
            modal=True,
            destroy_with_parent=True
        )
        self.dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK,
                                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)

        self.current_kf = current_kf
        self.animation = animation

        tbl_main = Gtk.Grid()
        tbl_main.set_row_spacing(10)
        tbl_main.set_column_spacing(10)
        tbl_main.set_property("margin", 10)

        dirs = animation.get_directions(self.current_kf)

        lbl_xy = Gtk.Label(label="XY angles interpolation direction:")
        tbl_main.attach(lbl_xy, 0, 0, 1, 1)
        self.cmb_xy = Gtk.ComboBoxText()
        self.cmb_xy.append_text("Nearer")
        self.cmb_xy.append_text("Longer")
        self.cmb_xy.append_text("Clockwise")
        self.cmb_xy.append_text("Counterclockwise")
        self.cmb_xy.set_active(dirs[0])
        tbl_main.attach(self.cmb_xy, 1, 0, 1, 1)
        lbl_xz = Gtk.Label(label="XZ angles interpolation direction:")
        tbl_main.attach(lbl_xz, 0, 1, 1, 1)
        self.cmb_xz = Gtk.ComboBoxText()
        self.cmb_xz.append_text("Nearer")
        self.cmb_xz.append_text("Longer")
        self.cmb_xz.append_text("Clockwise")
        self.cmb_xz.append_text("Counterclockwise")
        self.cmb_xz.set_active(dirs[1])
        tbl_main.attach(self.cmb_xz, 1, 1, 1, 1)
        lbl_xw = Gtk.Label(label="XW angles interpolation direction:")
        tbl_main.attach(lbl_xw, 0, 2, 1, 1)
        self.cmb_xw = Gtk.ComboBoxText()
        self.cmb_xw.append_text("Nearer")
        self.cmb_xw.append_text("Longer")
        self.cmb_xw.append_text("Clockwise")
        self.cmb_xw.append_text("Counterclockwise")
        self.cmb_xw.set_active(dirs[2])
        tbl_main.attach(self.cmb_xw, 1, 2, 1, 1)
        lbl_yz = Gtk.Label(label="YZ angles interpolation direction:")
        tbl_main.attach(lbl_yz, 0, 3, 1, 1)
        self.cmb_yz = Gtk.ComboBoxText()
        self.cmb_yz.append_text("Nearer")
        self.cmb_yz.append_text("Longer")
        self.cmb_yz.append_text("Clockwise")
        self.cmb_yz.append_text("Counterclockwise")
        self.cmb_yz.set_active(dirs[3])
        tbl_main.attach(self.cmb_yz, 1, 3, 1, 1)
        lbl_yw = Gtk.Label(label="YW angles interpolation direction:")
        tbl_main.attach(lbl_yw, 0, 4, 1, 1)
        self.cmb_yw = Gtk.ComboBoxText()
        self.cmb_yw.append_text("Nearer")
        self.cmb_yw.append_text("Longer")
        self.cmb_yw.append_text("Clockwise")
        self.cmb_yw.append_text("Counterclockwise")
        self.cmb_yw.set_active(dirs[4])
        tbl_main.attach(self.cmb_yw, 1, 4, 1, 1)
        lbl_zw = Gtk.Label(label="ZW angles interpolation direction:")
        tbl_main.attach(lbl_zw, 0, 5, 1, 1)
        self.cmb_zw = Gtk.ComboBoxText()
        self.cmb_zw.append_text("Nearer")
        self.cmb_zw.append_text("Longer")
        self.cmb_zw.append_text("Clockwise")
        self.cmb_zw.append_text("Counterclockwise")
        self.cmb_zw.set_active(dirs[5])
        tbl_main.attach(self.cmb_zw, 1, 5, 1, 1)
        self.dialog.vbox.pack_start(tbl_main, True, True, 0)

    def show(self):
        self.dialog.show_all()
        response = self.dialog.run()
        if response == Gtk.ResponseType.OK:
            dirs = (self.cmb_xy.get_active(), self.cmb_xz.get_active(),
                    self.cmb_xw.get_active(), self.cmb_yz.get_active(),
                    self.cmb_yw.get_active(), self.cmb_zw.get_active())
            self.animation.set_directions(self.current_kf, dirs)

        self.dialog.destroy()
        return
