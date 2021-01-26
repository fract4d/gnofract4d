# toolbar code

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class T(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, margin=5, spacing=1)

    @staticmethod
    def button_args(icon_name, tip_text, action):
        icon = Gtk.Image(icon_name=icon_name, icon_size=Gtk.IconSize.LARGE_TOOLBAR, margin=5)
        return dict(
            action_name=action, image=icon, relief=Gtk.ReliefStyle.NONE, tooltip_text=tip_text)

    def add_space(self):
        self.add(Gtk.Separator(
            orientation=Gtk.Orientation.VERTICAL, margin_start=5, margin_end=5))

    def add_widget(self, widget, tip_text, private_text, expand=False):
        box = Gtk.Box(hexpand=expand, tooltip_text=tip_text)
        box.add(widget)
        self.add(box)

    def add_button(self, icon_name, tip_text, action):
        self.add(Gtk.Button(**self.button_args(icon_name, tip_text, action)))

    def add_toggle(self, icon_name, tip_text, action):
        toolitem = Gtk.ToggleButton(**self.button_args(icon_name, tip_text, action))
        self.add(toolitem)
        return toolitem
