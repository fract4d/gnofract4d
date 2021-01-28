import os
import re

from gi.repository import Gtk

from . import gtkfractal

re_ends_with_num = re.compile(r'\d+\Z')
re_cleanup = re.compile(r'[\s\(\)]+')


class FractalWindow(Gtk.ScrolledWindow):
    def __init__(self, f, compiler):
        super().__init__()
        self.f = f

        self.subfracts = [
            gtkfractal.SubFract(compiler, f.width // 4, f.height // 4, f)
            for i in range(12)
        ]

        ftable = Gtk.Grid()
        ftable.attach(f.widget, 1, 1, 2, 2)

        for i, x, y in [(0, 0, 0),
                        (1, 1, 0),
                        (2, 2, 0),
                        (3, 3, 0),

                        (4, 0, 1),
                        (5, 3, 1),
                        (6, 0, 2),
                        (7, 3, 2),

                        (8, 0, 3),
                        (9, 1, 3),
                        (10, 2, 3),
                        (11, 3, 3),
                        ]:
            ftable.attach(self.subfracts[i].widget, x, y, 1, 1)

        self.add(ftable)
        self.get_child().set_shadow_type(Gtk.ShadowType.NONE)

    def hide_subfracts(self):
        for f in self.subfracts:
            f.widget.hide()

    def set_subfract_size(self, width, height):
        for f in self.subfracts:
            f.set_size(width, height)

    def update_subfracts(self, weirdness, color, aa, auto_deepen):
        for f in self.subfracts:
            f.interrupt()
            f.freeze()
            f.set_fractal(self.f.copy_f())
            f.mutate(weirdness, color)
            f.thaw()
            f.draw_image(aa, auto_deepen)

    def interrupt(self):
        for f in self.subfracts:
            f.interrupt()


class FractalFilename:
    def __init__(self, f):
        self.f = f
        self.filename = None

    def set_filename(self, filename):
        self.filename = filename

    def base_filename(self, extension):
        if self.filename is None:
            base_name = self.f.get_func_name()
            base_name = re_cleanup.sub("_", base_name) + extension
        else:
            base_name = self.filename
        return base_name

    def image_save_filename(self, fctname, extension=".png"):
        (base, ext) = os.path.splitext(fctname)
        return base + extension

    def display_filename(self):
        if self.filename is None:
            return _("(Untitled %s)") % self.f.get_func_name()
        else:
            return self.filename

    def default_save_filename(self, extension=".fct"):
        base_name = self.base_filename(extension)

        # need to gather a filename
        (base, ext) = os.path.splitext(base_name)
        base = re_ends_with_num.sub("", base)

        save_filename = base + extension
        i = 2
        while True:
            if not os.path.exists(save_filename):
                break
            save_filename = base + ("%03d" % i) + extension
            i += 1
        return save_filename

    def default_image_filename(self, extension=".png"):
        base_name = self.base_filename(extension)

        return self.image_save_filename(base_name)
