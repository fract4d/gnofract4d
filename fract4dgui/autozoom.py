# whimsical feature to zoom in search of interesting items

import random

from gi.repository import Gtk


class AutozoomDialog(Gtk.Window):
    def __init__(self, main_window, f):
        super().__init__(
            title=_("Autozoom"),
            transient_for=main_window,
            modal=True,
        )

        self.f = f

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(content)

        table = Gtk.Grid(column_spacing=5, row_spacing=5)
        content.append(table)

        close_button = Gtk.Button.new_with_mnemonic(label=_("_Close"))
        close_button.set_halign(Gtk.Align.END)
        close_button.connect("clicked", self.quit)
        content.append(close_button)

        self.connect("close-request", self.quit)

        self.zoombutton = Gtk.ToggleButton(
            label=_("Start _Zooming"),
            tooltip_text=_("Zoom into interesting areas automatically"),
            use_underline=True)
        self.zoombutton.connect('toggled', self.onZoomToggle)
        f.connect('status-changed', self.onStatusChanged)
        table.attach(self.zoombutton, 0, 0, 2, 1)

        self.minsize = 1.0E-13  # FIXME, should calculate this better

        self.minsize_entry = Gtk.Entry(
            tooltip_text=_("Stop zooming when size of fractal is this small"))
        minlabel = Gtk.Label(
            label=_("_Min Size"),
            use_underline=True,
            mnemonic_widget=self.minsize_entry)
        table.attach(minlabel, 0, 1, 1, 1)

        def set_entry(*args):
            self.minsize_entry.set_text("%g" % self.minsize)

        def change_entry(*args):
            m = float(self.minsize_entry.get_text())
            if m != 0.0 and m != self.minsize:
                self.minsize = m
                set_entry()
            return False

        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect('leave', change_entry)
        self.add_controller(focus_controller)

        set_entry()

        table.attach(self.minsize_entry, 1, 1, 1, 1)

    def onZoomToggle(self, *args):
        if self.zoombutton.get_active():
            self.zoombutton.get_child().set_text_with_mnemonic("Stop _Zooming")
            self.select_quadrant_and_zoom()
        else:
            self.zoombutton.get_child().set_text_with_mnemonic("Start _Zooming")

    def select_quadrant_and_zoom(self, *args):
        (wby2, hby2) = (self.f.width / 2, self.f.height / 2)
        (w, h) = (self.f.width, self.f.height)
        regions = [(0, 0, wby2, hby2),  # topleft
                   (wby2, 0, w, hby2),  # topright
                   (0, hby2, wby2, h),   # botleft
                   (wby2, hby2, w, h)]   # botright

        counts = [self.f.count_colors(r) for r in regions]
        m = max(counts)
        i = counts.index(m)

        # some level of randomness
        j = random.randrange(0, 4)
        if float(counts[j]) / counts[i] > 0.75:
            i = j

        # print "counts: %s max %d i %d" % (counts,m,i)

        # centers of each quadrant
        coords = [(1, 1), (3, 1), (1, 3), (3, 3)]

        (x, y) = coords[i]
        self.f.recenter(x * self.f.width / 4, y * self.f.height / 4, 0.75)

    def onStatusChanged(self, f, status_val):
        if status_val == 0:
            # done drawing current fractal.
            if self.zoombutton.get_active():
                if self.f.get_param(self.f.MAGNITUDE) > self.minsize:
                    self.select_quadrant_and_zoom()
                else:
                    self.zoombutton.set_active(False)

    def quit(self, *args):
        self.zoombutton.set_active(False)
        self.close()
