#!/usr/bin/python

# Copyright (C) 2006  Branko Kokanovic
#
#   DlgAdvOpt.py: dialog for advanced interpolation options for director
#

from gi.repository import Gtk

from . import utils


class DlgAdvOptions:
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

        tbl_main = Gtk.Grid(row_spacing=10, column_spacing=10, margin=10)
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

        self.dialog.vbox.pack_start(tbl_main, True, True, 0)

    def show(self):
        self.dialog.show_all()
        response = self.dialog.run()
        if response == Gtk.ResponseType.OK:
            dirs = ([cmb.get_active() for cmb in self.cmbs])
            self.animation.set_directions(self.current_kf, dirs)

        self.dialog.destroy()
        return
