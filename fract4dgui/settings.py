# GUI for modifying the fractal's settings

from gi.repository import Gtk

from fract4d_compiler.fc import FormulaTypes

from . import hig, browser, browser_model, settings_widgets


class SettingsPane(Gtk.Box):
    def __init__(self, main_window, f):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, visible=False)

        self.main_window = main_window
        self.f = f

        label_box = self.make_label_box(_("Fractal Settings"))
        self.notebook = Gtk.Notebook(name="settings_notebook", vexpand=True)
        self.append(label_box)
        self.append(self.notebook)

        self.tables = [None, None, None, None]
        self.selected_transform = None

        self.create_formula_parameters_page()
        self.create_outer_page()
        self.create_inner_page()
        self.create_transforms_page()
        self.create_general_page()
        self.create_location_page()
        self.create_colors_page()

    def make_label_box(self, title):
        label_box = Gtk.Box(name="settings_label_box")
        label_box.append(Gtk.Label(label=title, xalign=0.0, hexpand=True))
        close = Gtk.Button(label=_("Close"))
        label_box.append(close)

        close.connect('clicked', lambda x: self.set_visible(False))
        return label_box

    def create_colors_page(self):
        table = settings_widgets.ColorSettingsTable(self.f, self.main_window)
        label = Gtk.Label(label=_("_Colors"), use_underline=True)
        self.notebook.append_page(table, label)

    def create_location_page(self):
        table = self.create_location_table()
        label = Gtk.Label(label=_("_Location"), use_underline=True)
        self.notebook.append_page(table, label)

    def create_location_table(self):
        table = Gtk.Grid(row_spacing=5)
        self.create_param_entry(table, 0, _("_X :"), self.f.XCENTER)
        self.create_param_entry(table, 1, _("_Y :"), self.f.YCENTER)
        self.create_param_entry(table, 2, _("_Z :"), self.f.ZCENTER)
        self.create_param_entry(table, 3, _("_W :"), self.f.WCENTER)
        self.create_param_entry(table, 4, _("_Size :"), self.f.MAGNITUDE)
        self.create_param_entry(table, 5, _("XY (_1):"), self.f.XYANGLE)
        self.create_param_entry(table, 6, _("XZ (_2):"), self.f.XZANGLE)
        self.create_param_entry(table, 7, _("XW (_3):"), self.f.XWANGLE)
        self.create_param_entry(table, 8, _("YZ (_4):"), self.f.YZANGLE)
        self.create_param_entry(table, 9, _("YW (_5):"), self.f.YWANGLE)
        self.create_param_entry(table, 10, _("ZW (_6):"), self.f.ZWANGLE)

        return table

    def create_general_page(self):
        table = Gtk.Grid(column_spacing=5, row_spacing=5)
        label = Gtk.Label(label=_("_General"), use_underline=True)
        self.notebook.append_page(table, label)
        table.attach(self.create_yflip_widget(), 0, 0, 2, 1)
        table.attach(self.create_periodicity_widget(), 0, 1, 2, 1)
        self.create_tolerance_entry(table, 2, _("_Tolerance"))

    def create_tolerance_entry(self, table, row, text):
        entry = Gtk.Entry(activates_default=True)
        label = Gtk.Label(label=text, mnemonic_widget=entry, use_underline=True)
        table.attach(label, 0, row, 1, 1)
        table.attach(entry, 1, row, 1, 1)

        def set_entry(f, *args):
            try:
                current = float(entry.get_text())
                if current != f.period_tolerance:
                    # print "update entry to %.17f" % f.period_tolerance
                    entry.set_text("%.17f" % f.period_tolerance)
            except ValueError:
                # current was set to something that isn't a float
                entry.set_text("%.17f" % f.period_tolerance)

        def set_fractal(*args):
            try:
                self.f.set_period_tolerance(float(entry.get_text()))
            except Exception as exn:
                print(exn)
            return False

        set_entry(self.f)
        self.f.connect('parameters-changed', set_entry)
        self.f.connect('tolerance-changed', set_entry)
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect('leave', set_fractal)
        entry.add_controller(focus_controller)

    def create_yflip_widget(self):
        widget = Gtk.CheckButton(
            label=_("Flip Y Axis"),
            use_underline=True,
            tooltip_text=_("If set, Y axis increases down the screen,"
                           " otherwise up the screen"))

        def set_widget(*args):
            widget.set_active(self.f.yflip)

        def set_fractal(*args):
            self.f.set_yflip(widget.get_active())

        set_widget()
        self.f.connect('parameters-changed', set_widget)
        widget.connect('toggled', set_fractal)

        return widget

    def create_periodicity_widget(self):
        widget = Gtk.CheckButton(
            label=_("Periodicity Checking"),
            use_underline=True,
            tooltip_text=_("Try to speed up calculations by looking for loops."
                           " Can cause incorrect images with some functions, though."))

        def set_widget(*args):
            widget.set_active(self.f.periodicity)

        def set_fractal(*args):
            self.f.set_periodicity(widget.get_active())

        set_widget()
        self.f.connect('parameters-changed', set_widget)
        widget.connect('toggled', set_fractal)

        return widget

    def add_notebook_page(self, page, text):
        label = Gtk.Label(label=text, use_underline=True)
        frame = Gtk.Frame()
        frame.set_child(page)
        self.notebook.append_page(frame, label)

    def remove_transform(self, *args):
        if self.selected_transform is None:
            return

        self.f.remove_transform(self.selected_transform)

    def create_transforms_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        table = Gtk.Box(spacing=10)
        vbox.append(table)

        self.transform_store = Gtk.ListStore(str, object)

        def set_store(*args):
            self.transform_store.clear()
            for transform in self.f.transforms:
                self.transform_store.append((transform.funcName, transform))

        set_store()

        self.f.connect('formula-changed', set_store)

        self.transform_view = Gtk.TreeView(
            model=self.transform_store,
            headers_visible=False,
            hexpand=True,
            height_request=250)
        column = Gtk.TreeViewColumn('_Transforms', Gtk.CellRendererText(), text=0)
        self.transform_view.append_column(column)

        sw = Gtk.ScrolledWindow(min_content_height=200)
        sw.set_child(self.transform_view)
        table.append(sw)

        add_button = Gtk.Button(label="Add", valign=Gtk.Align.CENTER)
        add_button.connect(
            'clicked', self.show_browser, browser_model.TRANSFORM)
        remove_button = Gtk.Button(label="Remove", valign=Gtk.Align.CENTER)
        remove_button.connect(
            'clicked', self.remove_transform)
        buttonbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)
        buttonbox.append(add_button)
        buttonbox.append(remove_button)
        table.append(buttonbox)

        selection = self.transform_view.get_selection()
        selection.connect('changed', self.transform_selection_changed, vbox)

        self.add_notebook_page(vbox, _("T_ransforms"))

        self.create_transform_widget_table(vbox)

    def transform_selection_changed(self, selection, parent):
        (model, iter) = selection.get_selected()
        if iter is None:
            self.selected_transform = None
        else:
            transform = model.get_value(iter, 1)
            # this is bogus. How do I get the index into the list in a less
            # stupid way?
            i = 0
            for t in self.f.transforms:
                if t == transform:
                    self.selected_transform = i
                    break
                i += 1
            else:
                self.selected_transform = None
                return
        self.update_transform_parameters(parent)

    def create_browsable_name(self, table, param_type, typename, tip):
        label = Gtk.Label(label=self.f.forms[param_type].funcName, hexpand=True)

        def set_label(*args):
            label.set_text(self.f.forms[param_type].funcName)

        self.f.connect('parameters-changed', set_label)

        button = Gtk.Button(
            label=_("_Browse..."),
            use_underline=True,
            tooltip_text=tip)
        button.connect('clicked', self.show_browser, param_type)

        typelabel = Gtk.Label(label=typename, xalign=1.0)

        table.attach(typelabel, 0, 0, 1, 1)
        table.attach(label, 1, 0, 1, 1)
        table.attach(button, 2, 0, 1, 1)

    def update_formula_text(self, f, textview, formindex):
        text = f.forms[formindex].text()
        textview.get_buffer().set_text(text, -1)

    def change_formula(self, button, buffer, formindex, formtype):
        buftext = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(),
            include_hidden_chars=False)

        if buftext == '':
            # print "no text"
            return

        if buftext == self.f.forms[formtype].text():
            # print "not changed"
            return

        # print "text is '%s'" % buftext
        (fileName, formName) = self.f.compiler.add_inline_formula(
            buftext, formtype)
        # print "%s#%s" % (fileName, formName)
        try:
            self.f.set_formula(fileName, formName, formindex)
        except Exception as exn:
            self.show_error_message(
                _("Errors in formula"),
                exn)

    def show_error_message(self, message, exception=None):
        if exception is None:
            secondary_message = ""
        else:
            if isinstance(exception, EnvironmentError):
                secondary_message = exception.strerror or str(exception) or ""
            else:
                secondary_message = str(exception)

        def response(dialog, response_id):
            dialog.destroy()
        d = hig.ErrorAlert(
            primary=message,
            secondary=secondary_message,
            transient_for=self.main_window)
        d.connect("response", response)
        d.present()

    def create_formula_text_area(self, parent, formindex, formtype):
        sw = Gtk.ScrolledWindow(vexpand=True)
        textview = Gtk.TextView()
        sw.set_child(textview)
        parent.append(sw)

        self.f.connect(
            'formula-changed', self.update_formula_text, textview, formindex)

        apply = Gtk.Button(label=_("Apply Formula Changes"))
        apply.connect(
            'clicked',
            self.change_formula,
            textview.get_buffer(),
            formindex,
            formtype)

        parent.append(apply)
        self.update_formula_text(self.f, textview, formindex)

    def create_formula_parameters_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        formbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.create_formula_widget_table(
            formbox,
            0,
            _("Formula"),
            _("Browse available fractal functions"))

        vbox.append(formbox)
        self.create_formula_text_area(vbox, 0, FormulaTypes.FRACTAL)
        sw = Gtk.ScrolledWindow(overlay_scrolling=False)
        sw.set_child(vbox)
        self.add_notebook_page(sw, _("Formula"))

    def create_outer_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        formbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.create_formula_widget_table(
            formbox,
            1,
            _("Coloring Method"),
            _("Browse available coloring functions"))

        vbox.append(formbox)
        self.create_formula_text_area(vbox, 1, FormulaTypes.COLORFUNC)
        sw = Gtk.ScrolledWindow(overlay_scrolling=False)
        sw.set_child(vbox)
        self.add_notebook_page(sw, _("Outer"))

    def create_inner_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        formbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.create_formula_widget_table(
            formbox,
            2,
            _("Coloring Method"),
            _("Browse available coloring functions"))

        vbox.append(formbox)
        self.create_formula_text_area(vbox, 2, FormulaTypes.COLORFUNC)
        sw = Gtk.ScrolledWindow(overlay_scrolling=False)
        sw.set_child(vbox)
        self.add_notebook_page(sw, _("Inner"))

    def update_transform_parameters(self, parent, *args):
        widget = self.tables[3]
        if widget is not None:
            try:
                parent.remove(self.tables[3])
            except AttributeError:
                pass

        if self.selected_transform is not None:
            self.tables[3] = settings_widgets.FractalSettingsTable(
                self.f,
                self.main_window,
                self.selected_transform + 3)

            parent.append(self.tables[3])

    def create_transform_widget_table(self, parent):
        self.tables[3] = None

        self.update_transform_parameters(parent)

        self.f.connect(
            'formula-changed', self.update_transform_parameters, parent)
        self.f.connect(
            'parameters-changed', self.update_all_widgets, lambda: self.tables[3])

    def create_formula_widget_table(self, parent, param_type, typename, tip):
        self.tables[param_type] = None

        def update_formula_parameters(*args):
            widget = self.tables[param_type]
            if widget is not None:
                try:
                    parent.remove(self.tables[param_type])
                except AttributeError:
                    pass

            table = settings_widgets.FractalSettingsTable(
                self.f,
                self.main_window,
                param_type,
                row=1,
                row_spacing=5)
            self.create_browsable_name(table, param_type, typename, tip)

            parent.append(table)
            self.tables[param_type] = table
        update_formula_parameters()

        self.f.connect('formula-changed', update_formula_parameters)
        self.f.connect(
            'parameters-changed',
            self.update_all_widgets, lambda: self.tables[param_type])

    def update_all_widgets(self, fractal, container):
        # weird hack. We need to change the set of widgets when
        # the formula changes and change the values of the widgets
        # when the parameters change. When I connected the widgets
        # directly to the fractal's parameters-changed signal they
        # would still get signalled even after they were obsolete.
        # This works around that problem

        if hasattr(container, "__call__"):
            container = container()

        if container is None:
            return

        for widget in container:
            try:
                widget.update_function()
            except AttributeError:
                pass
            if widget.get_first_child():
                self.update_all_widgets(fractal, widget)  # recurse

    def show_browser(self, button, type):
        dialog = browser.BrowserDialog(self.main_window, self.f, type)
        dialog.present()

    def create_param_entry(self, table, row, text, param):
        label = Gtk.Label(
            label=text,
            xalign=1.0,
            justify=Gtk.Justification.RIGHT,
            margin_end=5,
            use_underline=True)
        table.attach(label, 0, row, 1, 1)

        entry = Gtk.Entry(activates_default=True, hexpand=True)
        table.attach(entry, 1, row, 1, 1)
        label.set_mnemonic_widget(entry)

        def set_entry(f):
            try:
                current = float(entry.get_text())
                if current != f.get_param(param):
                    entry.set_text("%.17f" % f.get_param(param))
            except ValueError:
                # current was set to something that isn't a float
                entry.set_text("%.17f" % f.get_param(param))

        def set_fractal(*args):
            try:
                self.f.set_param(param, entry.get_text())
            except Exception as exn:
                print(f"SettingsPane.create_param_entry set_fractal: {exn}")
            return False

        set_entry(self.f)
        self.f.connect('parameters-changed', set_entry)
        entry.connect('changed', set_fractal)
