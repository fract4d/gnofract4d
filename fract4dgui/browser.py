# a browser to examine fractal functions

from gi.repository import Gtk

from . import utils, gtkfractal, browser_model


class BrowserDialog(Gtk.Window):
    RESPONSE_REFRESH = 2

    def __init__(self, main_window, f, type=browser_model.FRACTAL):
        super().__init__(
            title=_("Formula Browser"),
            transient_for=main_window,
            modal=True,
        )

        self.model = browser_model.T(f.compiler)
        self.model.type_changed += self.on_type_changed
        self.model.file_changed += self.on_file_changed
        self.model.formula_changed += self.on_formula_changed

        self.file_list = Gtk.ListStore(str)
        self.formula_list = Gtk.ListStore(str)

        self.file_selection_changed_spec = None
        self.formula_selection_changed_spec = None

        self.f = f
        self.compiler = f.compiler

        self.ir = None
        self.set_size_request(600, 500)
        self.preview = gtkfractal.Preview(self.compiler)
        self.preview.f.auto_tolerance = False

        self.create_panes()

        self.set_type(type)

    def onRefresh(self, *args):
        self.f.refresh()
        self.set_file(self.model.current.fname)  # update text window

    def onApply(self, *args):
        self.model.apply(self.f)

    def onOK(self, *args):
        self.onApply()
        self.quit()

    def set_type_cb(self, optmenu):
        self.set_type(optmenu.get_active())

    def on_type_changed(self):
        self.funcTypeMenu.set_active(int(self.model.current_type))
        try:
            self.set_file(self.f.forms[self.model.current_type].funcFile)
        except IndexError:
            pass
        try:
            self.set_formula(self.f.forms[self.model.current_type].funcName)
        except IndexError:
            pass
        self.populate_file_list()

    def set_type(self, type):
        self.model.set_type(type)

    def create_file_list(self):
        sw = Gtk.ScrolledWindow(has_frame=True)

        self.filetreeview = Gtk.TreeView(
            model=self.file_list,
            tooltip_text=_("A list of files containing fractal formulas"))
        sw.set_child(self.filetreeview)

        column = Gtk.TreeViewColumn('_File', Gtk.CellRendererText(), text=0)
        self.filetreeview.append_column(column)

        return sw

    def populate_file_list(self):
        # find all appropriate files and add to file list
        # first clear files of the current type
        # preventing on_file_changed being called for each deletion
        sel = self.filetreeview.get_selection()
        if self.file_selection_changed_spec:
            sel.disconnect(self.file_selection_changed_spec)
            self.file_selection_changed_spec = None
        self.file_list.clear()

        files = self.model.current.files

        current_iter = None
        index, i = 0, 0
        for fname in files:
            iter = self.file_list.append()
            if fname == self.model.current.fname:
                current_iter = iter
                index = i
            self.file_list.set(iter, 0, fname)
            i += 1

        # re-select current file, if any
        if current_iter:
            self.filetreeview.scroll_to_cell(index)
            sel.unselect_all()
            sel.select_iter(current_iter)
            self.populate_formula_list(self.model.current.fname)
        else:
            self.formula_list.clear()
            self.formula_selection_changed(None)

        self.file_selection_changed_spec = sel.connect(
            'changed', self.file_selection_changed)

    def populate_formula_list(self, fname):
        sel = self.treeview.get_selection()
        if self.formula_selection_changed_spec:
            sel.disconnect(self.formula_selection_changed_spec)
            self.formula_selection_changed_spec = None
        self.formula_list.clear()

        form_names = self.model.current.formulas

        i = 0
        for formula_name in form_names:
            iter = self.formula_list.append()
            self.formula_list.set(iter, 0, formula_name)
            if formula_name == self.model.current.formula:
                self.treeview.get_selection().select_iter(iter)
                self.treeview.scroll_to_cell(i)
                self.set_formula(formula_name)
            i += 1

        self.formula_selection_changed_spec = sel.connect(
            'changed', self.formula_selection_changed)

    def create_formula_list(self):
        sw = Gtk.ScrolledWindow(has_frame=True)

        self.treeview = Gtk.TreeView(
            model=self.formula_list,
            tooltip_text=_("A list of formulas in the selected file"))
        sw.set_child(self.treeview)

        column = Gtk.TreeViewColumn(_('F_ormula'), Gtk.CellRendererText(), text=0)
        self.treeview.append_column(column)

        return sw

    def create_scrolled_textview(self, tip):
        sw = Gtk.ScrolledWindow(has_frame=True)
        textview = Gtk.TextView(tooltip_text=tip, editable=False)
        sw.set_child(textview)
        return (textview, sw)

    def create_panes(self):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, css_classes=["content"])
        self.set_child(content)

        # option menu for choosing Inner/Outer/Fractal
        self.funcTypeMenu = utils.combo_box_text_with_items(
            [_("Fractal Function"),
             _("Outer Coloring Function"),
             _("Inner Coloring Function"),
             _("Transform Function"),
             _("Gradient")],
            _("Which formula of the current fractal to change"))
        self.funcTypeMenu.set_active(int(self.model.current_type))
        self.funcTypeMenu.connect('changed', self.set_type_cb)

        # label for the menu
        hbox = Gtk.Box(css_classes=["component_first"])
        label = Gtk.Label(
            label=_("Function _Type to Modify : "),
            use_underline=True,
            mnemonic_widget=self.funcTypeMenu)
        hbox.append(label)
        hbox.append(self.funcTypeMenu)
        content.append(hbox)

        # 3 panes: files, formulas, formula contents
        panes1 = Gtk.Paned(vexpand=True)
        panes1.set_layout_manager(Gtk.BoxLayout())
        content.append(panes1)

        file_list = self.create_file_list()
        formula_list = self.create_formula_list()

        panes2 = Gtk.Paned(hexpand=True)
        # left-hand pane displays file list
        panes2.set_start_child(file_list)
        # middle is formula list for that file
        panes2.set_end_child(formula_list)
        panes1.set_start_child(panes2)

        # right-hand pane is details of current formula
        notebook = Gtk.Notebook()

        # preview
        label = Gtk.Label(label=_('_Preview'), use_underline=True)
        notebook.append_page(self.preview.widget, label)

        # source
        (self.sourcetext, sw) = self.create_scrolled_textview(
            _("The contents of the currently selected formula file"))

        label = Gtk.Label(label=_('_Source'), use_underline=True)
        notebook.append_page(sw, label)

        # messages
        (self.msgtext, sw) = self.create_scrolled_textview(
            _("Any compiler warnings or errors in the current function"))

        label = Gtk.Label(label=_('_Messages'), use_underline=True)
        notebook.append_page(sw, label)

        panes1.set_end_child(notebook)

        button_box = Gtk.Box(halign=Gtk.Align.END)
        button_box.add_css_class("component_last")
        content.append(button_box)

        refresh_button = Gtk.Button.new_with_mnemonic(label=_("_Refresh"))
        refresh_button.connect("clicked", self.onRefresh)
        button_box.append(refresh_button)

        self.apply_button = Gtk.Button.new_with_mnemonic(label=_("_Apply"))
        self.apply_button.connect("clicked", self.onApply)
        button_box.append(self.apply_button)

        self.ok_button = Gtk.Button.new_with_mnemonic(label=_("_OK"))
        self.ok_button.connect("clicked", self.onOK)
        button_box.append(self.ok_button)

        close_button = Gtk.Button.new_with_mnemonic(label=_("_Close"))
        close_button.connect("clicked", self.quit)
        button_box.append(close_button)

    def load_file(self, fname):
        type = self.model.guess_type(fname)
        self.set_type(type)
        self.set_file(fname)
        self.populate_file_list()

    def file_selection_changed(self, selection):
        self.model.current.formula = None
        (model, iter) = selection.get_selected()
        if iter is None:
            return

        fname = model.get_value(iter, 0)
        self.set_file(fname)

    def set_file(self, fname):
        self.model.set_file(fname)

    def on_file_changed(self):
        text = self.model.get_contents()

        self.display_text(text)
        self.populate_formula_list(self.model.current.fname)
        self.set_apply_sensitivity()

    def clear_selection(self):
        self.set_formula(None)

    def formula_selection_changed(self, selection):
        if not selection:
            self.clear_selection()
            return

        (model, iter) = selection.get_selected()
        if iter is None:
            self.clear_selection()
            return

        form_name = model.get_value(iter, 0)
        self.set_formula(form_name)

    def set_formula(self, form_name):
        self.model.set_formula(form_name)

    def on_formula_changed(self):
        form_name = self.model.current.formula
        file = self.model.current.fname

        if not file:
            return

        formula = self.compiler.get_parsetree(file, form_name)

        if not formula:
            return

        # update location of source buffer
        sourcebuffer = self.sourcetext.get_buffer()
        iter = sourcebuffer.get_iter_at_line(formula.pos - 1)[1]
        self.sourcetext.scroll_to_iter(iter, 0.0, True, 0.0, 0.0)

        # update IR tree
        self.ir = self.compiler.get_formula(file, form_name)

        # update messages
        buffer = self.msgtext.get_buffer()
        msg = ""
        if self.ir.errors:
            msg += _("Errors:\n") + "\n".join(self.ir.errors) + "\n"
        if self.ir.warnings:
            msg += _("Warnings:\n") + "\n".join(self.ir.warnings)
        if msg == "":
            msg = _("No messages")

        buffer.set_text(msg, -1)

        self.set_apply_sensitivity()

    def set_apply_sensitivity(self):
        can_apply = self.model.current.can_apply
        self.apply_button.set_sensitive(can_apply)
        self.ok_button.set_sensitive(can_apply)

        if can_apply:
            self.model.apply(self.preview)
            self.preview.draw_image(False, False)

    def display_text(self, text):
        self.sourcetext.get_buffer().set_text(text, -1)

    def quit(self, *args):
        self.close()
