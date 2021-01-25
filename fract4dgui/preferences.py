# GUI for user settings

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib

from . import dialog, utils


class Preferences(GObject.GObject):
    # A wrapper for the preference data
    __gsignals__ = {
        'preferences-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, ()),
        'image-preferences-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, ()),

    }

    def __init__(self, config):
        GObject.GObject.__init__(self)
        self.config = config
        self.config.changed = self.changed

    def changed(self, section):
        self.emit('preferences-changed')
        if self.config.image_changed_sections.get(section, False):
            self.emit('image-preferences-changed')

    def set(self, section, key, val):
        self.config.set(section, key, val)

    def get(self, section, key):
        return self.config.get(section, key)

    def getboolean(self, section, key):
        return self.config.getboolean(section, key)

    def getint(self, section, key):
        return self.config.getint(section, key)

    def set_size(self, width, height):
        self.config.set_size(width, height)

    def set_main_window_size(self, width, height):
        self.config.set_main_window_size(width, height)

    def get_list(self, name):
        return self.config.get_list(name)

    def set_list(self, name, list):
        self.config.set_list(name, list)

    def remove_all_in_list_section(self, name):
        self.config.remove_all_in_list_section(name)

    def save(self):
        self.config.save()


# explain our existence to GTK's object system
GObject.type_register(Preferences)


class PrefsDialog(dialog.T):
    def __init__(self, main_window, f, userPrefs):
        # pylint: disable=no-member
        dialog.T.__init__(
            self,
            _("Gnofract 4D Preferences"),
            main_window,
            (_("_Close"), Gtk.ResponseType.CLOSE)
        )

        self.dirchooser = utils.get_directory_chooser(
            _("Select a Formula Directory"),
            self)

        self.f = f
        self.notebook = Gtk.Notebook(vexpand=True)
        self.vbox.add(self.notebook)
        self.prefs = userPrefs
        self.create_image_options_page()
        self.create_compiler_options_page()
        self.create_general_page()
        self.create_helper_options_page()
        self.vbox.show_all()

        self.set_size_request(500, -1)

    def show_error(self, message):
        d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                              Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                              message)
        d.run()
        d.destroy()

    def create_width_entry(self):
        entry = Gtk.Entry(
            tooltip_text="The image's width in pixels", activates_default=True)

        def set_entry(*args):
            entry.set_text(self.prefs.get("display", "width"))

        def set_prefs(*args):
            try:
                height = self.f.height
                try:
                    width = int(entry.get_text())
                except ValueError:
                    GLib.idle_add(
                        self.show_error,
                        "Invalid value for width: '%s'. Must be an integer" %
                        entry.get_text())
                    return False

                if self.fix_ratio.get_active():
                    height = int(width * float(height) / self.f.width)

                GLib.idle_add(self.prefs.set_size, width, height)
            except Exception as exn:
                print(exn)
            return False

        set_entry()
        self.prefs.connect('preferences-changed', set_entry)
        entry.connect('focus-out-event', set_prefs)
        return entry

    def create_height_entry(self):
        entry = Gtk.Entry(
            tooltip_text="The image's height in pixels", activates_default=True)

        def set_entry(*args):
            entry.set_text(self.prefs.get("display", "height"))

        def set_prefs(*args):
            try:
                try:
                    height = int(entry.get_text())
                except ValueError:
                    GLib.idle_add(
                        self.show_error,
                        "Invalid value for height: '%s'. Must be an integer" %
                        entry.get_text())
                    return False

                width = self.f.width
                if self.fix_ratio.get_active():
                    width = int(height * float(self.f.width) / self.f.height)
                self.prefs.set_size(width, height)
            except Exception as exn:
                print(exn)
            return False

        set_entry()
        self.prefs.connect('preferences-changed', set_entry)
        entry.connect('focus-out-event', set_prefs)
        return entry

    def create_compiler_entry(self, propname, **properties):
        return self.create_option_entry("compiler", propname, **properties)

    def create_option_entry(self, section, propname, **properties):
        entry = Gtk.Entry(activates_default=True, **properties)

        def set_entry(*args):
            entry.set_text(self.prefs.get(section, propname))

        def set_prefs(*args):
            try:
                self.prefs.set(section, propname, entry.get_text())
            except Exception as err:
                print(err)
            return False

        set_entry()
        self.prefs.connect('preferences-changed', set_entry)
        entry.connect('focus-out-event', set_prefs)
        return entry

    def create_save_compress_widget(self):
        widget = Gtk.CheckButton(
            label=_("Compress _Parameter Files"),
            tooltip_text=_("Write .fct files in a shorter but unreadable format"),
            use_underline=True)

        def set_widget(*args):
            widget.set_active(self.prefs.getboolean("general", "compress_fct"))

        def set_prefs(*args):
            self.prefs.set("general", "compress_fct", str(widget.get_active()))

        set_widget()
        self.prefs.connect('preferences-changed', set_widget)
        widget.connect('toggled', set_prefs)

        return widget

    def create_general_page(self):
        table = Gtk.Grid(column_spacing=5, row_spacing=5, column_homogeneous=False)
        label = Gtk.Label(label=_("_General"), use_underline=True)
        self.notebook.append_page(table, label)

        entry = self.create_option_entry(
            "general", "threads", tooltip_text=_("How many threads to use for calculations"))
        name_label = Gtk.Label(
            label=_("_Number of threads :"), mnemonic_widget=entry, use_underline=True)

        cache_entry = self.create_option_entry(
            "general", "cache_dir", hexpand=True,
            tooltip_text=_("Restart program to use new directory"))
        cache_label = Gtk.Label(label=_("Cache directory :"))

        table.attach(name_label, 0, 0, 1, 1)
        table.attach(entry, 1, 0, 1, 1)

        table.attach(self.create_save_compress_widget(), 0, 1, 2, 1)

        table.attach(cache_label, 0, 2, 1, 1)
        table.attach(cache_entry, 1, 2, 1, 1)

    def create_formula_directory_list(self, section_name):
        path_list = Gtk.ListStore(str)

        path_treeview = Gtk.TreeView(
            model=path_list, headers_visible=False,
            tooltip_text=_("Directories to search for formulas"))

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_('_Directory'), renderer, text=0)
        path_treeview.append_column(column)

        for path in self.prefs.get_list(section_name):
            path_list.append([path])

        return path_treeview

    def update_prefs(self, name, model):
        self.prefs.set_list(name, [row[0] for row in model])

    def browse_for_dir(self, widget, name, pathlist):
        self.dirchooser.show_all()
        result = self.dirchooser.run()
        if result == Gtk.ResponseType.OK:
            path = self.dirchooser.get_filename()

            model = pathlist.get_model()
            iter = model.append()

            model.set(iter, 0, path)
            self.update_prefs(name, model)

        self.dirchooser.hide()

    def remove_dir(self, widget, name, pathlist):
        select = pathlist.get_selection()
        (model, iter) = select.get_selected()

        if iter:
            model.remove(iter)
            self.update_prefs(name, model)

    def create_compiler_options_page(self):
        table = Gtk.Grid(column_spacing=5, row_spacing=5)
        label = Gtk.Label(label=_("_Compiler"), use_underline=True)
        self.notebook.append_page(table, label)

        entry = self.create_compiler_entry(
            "name", hexpand=True, tooltip_text=_("The C compiler to use"))
        table.attach(entry, 1, 0, 1, 1)

        name_label = Gtk.Label(
            label=_("Compi_ler :"), mnemonic_widget=entry, use_underline=True)
        table.attach(name_label, 0, 0, 1, 1)

        entry = self.create_compiler_entry(
            "options", tooltip_text=_("Options to pass to the C compiler"))
        table.attach(entry, 1, 1, 1, 1)

        flags_label = Gtk.Label(
            label=_("Compiler _Flags :"), mnemonic_widget=entry, use_underline=True)
        table.attach(flags_label, 0, 1, 1, 1)

        sw = Gtk.ScrolledWindow(
            shadow_type=Gtk.ShadowType.ETCHED_IN,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            vexpand=True)
        form_path_section = "formula_path"
        pathlist = self.create_formula_directory_list(form_path_section)
        sw.add(pathlist)
        table.attach(sw, 1, 2, 1, 3)

        pathlist_label = Gtk.Label(
            label=_("Formula Search _Path :"),
            mnemonic_widget=pathlist,
            use_underline=True,
            vexpand=True)
        table.attach(pathlist_label, 0, 2, 1, 1)

        add_button = Gtk.Button(label="Add")
        add_button.connect(
            'clicked',
            self.browse_for_dir,
            form_path_section,
            pathlist)
        table.attach(add_button, 0, 3, 1, 1)

        remove_button = Gtk.Button(label="Remove")
        remove_button.connect(
            'clicked',
            self.remove_dir,
            form_path_section,
            pathlist)
        table.attach(remove_button, 0, 4, 1, 1)

    def create_helper_options_page(self):
        table = Gtk.Grid(column_homogeneous=False, column_spacing=5, row_spacing=5)
        label = Gtk.Label(label=_("_Helpers"), use_underline=True)
        self.notebook.append_page(table, label)

        entry = self.create_option_entry(
            "helpers", "editor", hexpand=True,
            tooltip_text=_("The text editor to use for changing formulas"))
        table.attach(entry, 1, 0, 1, 1)

        name_label = Gtk.Label(label="_Editor :", mnemonic_widget=entry, use_underline=True)
        table.attach(name_label, 0, 0, 1, 1)

    def create_auto_deepen_widget(self):
        widget = Gtk.CheckButton(
            label="Auto _Deepen", use_underline=True,
            tooltip_text="Adjust number of iterations automatically")

        def set_widget(*args):
            widget.set_active(self.prefs.getboolean("display", "autodeepen"))

        def set_prefs(*args):
            self.prefs.set("display", "autodeepen", str(widget.get_active()))

        set_widget()
        self.prefs.connect('preferences-changed', set_widget)
        widget.connect('toggled', set_prefs)

        return widget

    def create_auto_tolerance_widget(self):
        widget = Gtk.CheckButton(
            label="Auto _Tolerance",
            tooltip_text="Adjust periodicity tolerance automatically",
            use_underline=True)

        def set_widget(*args):
            widget.set_active(
                self.prefs.getboolean(
                    "display", "autotolerance"))

        def set_prefs(*args):
            self.prefs.set(
                "display", "autotolerance", str(
                    widget.get_active()))

        set_widget()
        self.prefs.connect('preferences-changed', set_widget)
        widget.connect('toggled', set_prefs)

        return widget

    def create_antialias_menu(self):
        optMenu = utils.create_option_menu(["None", "Fast", "Best"])

        def set_widget(*args):
            optMenu.set_active(self.prefs.getint("display", "antialias"))

        def set_prefs(*args):
            index = optMenu.get_active()
            if index != -1:
                self.prefs.set("display", "antialias", str(index))

        set_widget()
        self.prefs.connect('preferences-changed', set_widget)
        optMenu.connect('changed', set_prefs)
        return optMenu

    def create_image_options_page(self):
        table = Gtk.Grid(column_spacing=5, row_spacing=5)
        label = Gtk.Label(label="_Image", use_underline=True)
        self.notebook.append_page(table, label)

        wentry = self.create_width_entry()
        table.attach(wentry, 1, 0, 1, 1)

        wlabel = Gtk.Label(label="_Width :", mnemonic_widget=wentry, use_underline=True)
        table.attach(wlabel, 0, 0, 1, 1)

        hentry = self.create_height_entry()
        table.attach(hentry, 1, 1, 1, 1)

        hlabel = Gtk.Label(label="_Height :", mnemonic_widget=hentry, use_underline=True)
        table.attach(hlabel, 0, 1, 1, 1)

        self.fix_ratio = Gtk.CheckButton(
            label="Maintain Aspect _Ratio", 
            tooltip_text="Keep the image rectangle the same shape when changing its size",
            use_underline=True,
            active=True)
        table.attach(self.fix_ratio, 0, 2, 2, 1)

        # auto deepening
        self.auto_deepen = self.create_auto_deepen_widget()
        table.attach(self.auto_deepen, 0, 3, 2, 1)

        # auto tolerance
        self.auto_tolerance = self.create_auto_tolerance_widget()
        table.attach(self.auto_tolerance, 0, 4, 2, 1)

        # antialiasing
        optMenu = self.create_antialias_menu()
        table.attach(optMenu, 1, 5, 1, 1)

        aalabel = Gtk.Label(
            label="_Antialiasing : ", mnemonic_widget=optMenu, use_underline=True)
        table.attach(aalabel, 0, 5, 1, 1)
