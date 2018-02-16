# GUI for modifying the fractal's settings

import copy

from gi.repository import GObject, Gdk, Gtk

from . import hig
from . import dialog
from . import browser
from . import utils

from .table import Table

from fract4d import browser_model
from fract4d.fc import FormulaTypes

class SettingsPane(Gtk.Box):
    def __init__(self, main_window, f):
        Gtk.Box.__init__(self)
        self.set_orientation(Gtk.Orientation.VERTICAL)

        self.main_window = main_window
        self.f = f
        
        label_box = dialog.make_label_box(self, _("Fractal Settings"))
        self.notebook = Gtk.Notebook()
        self.notebook.set_name("settings_notebook")
        self.pack_start(label_box, False, False, 0)
        self.pack_start(self.notebook, True, True, 0)
        
        self.tables = [None,None,None,None]
        self.selected_transform = None
        
        self.create_formula_parameters_page()
        self.create_outer_page()
        self.create_inner_page()
        self.create_transforms_page()
        self.create_general_page()
        self.create_location_page()
        self.create_colors_page()

        self.notebook.show_all()

    def gradarea_mousedown(self, widget, event):
        pass

    def gradarea_clicked(self, widget, event):
        pos = float(event.x) / widget.get_allocated_width()
        i = self.f.get_gradient().get_index_at(pos)
        self.select_segment(i)
        self.redraw()

    def gradarea_mousemoved(self, widget, event):
        pass
    
    def draw_handle(self, widget, cairo_ctx, midpoint, fill):
        # draw a triangle pointing up, centered on midpoint
        total_height = widget.get_allocated_height()
        colorband_height = total_height - self.grad_handle_height
        cairo_ctx.set_line_width(1.0)
        cairo_ctx.set_source_rgb(0, 0, 0)
        cairo_ctx.move_to(midpoint - 5, total_height)
        cairo_ctx.line_to(midpoint, colorband_height)
        cairo_ctx.line_to(midpoint + 5, total_height)
        cairo_ctx.line_to(midpoint - 5, total_height)
        if fill:
            cairo_ctx.fill()
        else:
            cairo_ctx.stroke()

    def redraw_rect(self, widget, cairo_ctx):
        # draw the color preview bar
        result, r = Gdk.cairo_get_clip_rectangle(cairo_ctx)
        wwidth = widget.get_allocated_width()
        colorband_height = widget.get_allocated_height() - self.grad_handle_height
        
        style_ctx = widget.get_style_context()
        normal_background_color = style_ctx.get_property("background-color", Gtk.StateFlags.NORMAL)
        grad = self.f.get_gradient()

        cairo_ctx.set_line_width(2.0)
        for i in range(r.x, r.x + r.width):
            pos_in_gradient = i / wwidth
            col = grad.get_color_at(pos_in_gradient)
            cairo_ctx.set_source_rgba(col[0], col[1], col[2])
            cairo_ctx.move_to(i, r.y)
            cairo_ctx.line_to(i, min(r.y + r.height, colorband_height))
            cairo_ctx.stroke()

        # draw the handles
        cairo_ctx.set_source_rgba(*normal_background_color)
        cairo_ctx.rectangle(r.x, colorband_height, r.width, self.grad_handle_height)
        cairo_ctx.fill()

        for i in range(len(grad.segments)):
            seg = grad.segments[i]
            
            left = seg.left * wwidth
            mid = seg.mid * wwidth
            right = seg.right * wwidth

            if i == self.selected_segment:
                # draw this chunk selected
                cairo_ctx.set_line_width(2.0)
                cairo_ctx.set_source_rgb(0, 1.0, 1.0)
                cairo_ctx.rectangle(left, colorband_height, right - left, self.grad_handle_height)
                cairo_ctx.fill()

            self.draw_handle(widget, cairo_ctx, left, True)
            self.draw_handle(widget, cairo_ctx, mid, False)

        # draw last handle on the right
        self.draw_handle(widget, cairo_ctx, wwidth, True)

    def redraw(self,*args):
        self.gradarea.queue_draw()

        self.inner_solid_button.set_color(
            utils.floatColorFrom256(self.f.solids[1]))
        self.outer_solid_button.set_color(
            utils.floatColorFrom256(self.f.solids[0]))

    def create_colors_table(self):
        gradbox = Gtk.VBox()

        browse_button = Gtk.Button(label=_("Browse..."))

        browse_button.connect(
            "clicked", self.show_browser, browser_model.GRADIENT)
            
        gradbox.pack_start(browse_button, False, False, 1)
        
        # gradient viewer
        self.grad_handle_height = 8
        
        self.gradarea = Gtk.DrawingArea()

        self.gradarea.add_events(
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.BUTTON1_MOTION_MASK |
            Gdk.EventMask.POINTER_MOTION_HINT_MASK |
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.KEY_PRESS_MASK |
            Gdk.EventMask.KEY_RELEASE_MASK
            )

        self.gradarea.set_size_request(256, 96)
        self.gradarea.connect('draw', self.redraw_rect)
        self.gradarea.connect('button-press-event', self.gradarea_mousedown)
        self.gradarea.connect('button-release-event', self.gradarea_clicked)
        self.gradarea.connect('motion-notify-event', self.gradarea_mousemoved)

        self.f.connect('parameters-changed', self.redraw)
        gradbox.pack_start(self.gradarea, False, False, 1)

        table = Gtk.Table(n_rows=4,n_columns=4, homogeneous=True)
        table.set_property("column-spacing",2)

        grad = self.f.get_gradient()
        self.left_color_button = utils.ColorButton(
            grad.segments[0].left_color, self.color_changed, True)
        self.left_color_button.widget.set_tooltip_text(
            _("Color of segment's left end"))
        
        self.right_color_button = utils.ColorButton(
            grad.segments[0].right_color, self.color_changed, False)
        self.right_color_button.widget.set_tooltip_text(
            _("Color of segment's right end"))

        table.attach(Gtk.Label(label="Left Color:"),
                     0,1,0,1)
        table.attach(self.left_color_button.widget,
                     1,2,0,1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)
        table.attach(Gtk.Label(label="Right Color:"),
                     2,3,0,1)
        table.attach(self.right_color_button.widget,
                     3,4,0,1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)

        self.split_button = Gtk.Button(label=_("Split"))
        self.split_button.connect('clicked', self.split)
        table.attach(self.split_button,
                     0,1,1,2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)

        self.remove_button = Gtk.Button(label=_("Remove"))
        self.remove_button.connect('clicked', self.remove)
        table.attach(self.remove_button,
                     1,2,1,2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)

        self.copy_left_button = Gtk.Button(label=_("<Copy"))
        self.copy_left_button.connect('clicked', self.copy_left)
        table.attach(self.copy_left_button,
                     2,3,1,2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)
        
        self.copy_right_button = Gtk.Button(label=_("Copy>"))
        self.copy_right_button.connect('clicked', self.copy_right)
        table.attach(self.copy_right_button,
                     3,4,1,2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)

        self.inner_solid_button = utils.ColorButton(
            utils.floatColorFrom256(self.f.solids[1]),
            self.solid_color_changed, 1)

        self.outer_solid_button = utils.ColorButton(
            utils.floatColorFrom256(self.f.solids[0]),
            self.solid_color_changed, 0)

        table.attach(Gtk.Label(label="Inner Color:"),
                     0,1,2,3)
        table.attach(self.inner_solid_button.widget,
                     1,2,2,3, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)
        table.attach(Gtk.Label(label="Outer Color:"),
                     2,3,2,3)
        table.attach(self.outer_solid_button.widget,
                     3,4,2,3, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND)

        gradbox.add(table)

        return gradbox

    def copy_left(self,widget):
        i = self.selected_segment
        if i == -1 or i == 0:
            return

        segments = self.f.get_gradient().segments
        segments[i-1].right_color = copy.copy(segments[i].left_color)
        self.f.changed()
        
    def copy_right(self,widget):
        i = self.selected_segment
        segments = self.f.get_gradient().segments
        if i == -1 or i == len(segments)-1:
            return

        segments[i+1].left_color = copy.copy(segments[i].right_color)
        self.f.changed()

    def split(self, widget):
        i = self.selected_segment
        if i == -1:
            return
        self.f.get_gradient().add(i)
        self.f.changed()

    def remove(self, widget):
        i = self.selected_segment
        grad = self.f.get_gradient()
        if i == -1 or len(grad.segments)==1:
            return
        grad.remove(i, True)
        if self.selected_segment > 0:
            self.selected_segment -= 1
        self.f.changed()
        
    def solid_color_changed(self, r, g, b, index):
        self.f.set_solid(
            index,
            utils.color256FromFloat(r,g,b, self.f.solids[index]))
        
    def color_changed(self,r,g,b, is_left):
        #print "color changed", r, g, b, is_left
        self.f.get_gradient().set_color(
            self.selected_segment,
            is_left,
            r,g,b)

        self.redraw()

    def select_segment(self,i):
        self.selected_segment = i
        
        if i == -1:
            self.left_color_button.set_color([0.5,0.5,0.5,1])
            self.right_color_button.set_color([0.5,0.5,0.5,1])
        else:
            grad = self.f.get_gradient()
            self.left_color_button.set_color(grad.segments[i].left_color)
            self.right_color_button.set_color(grad.segments[i].right_color)
        # buttons should be sensitive if selection is good
        self.left_color_button.set_sensitive(i!= -1)
        self.right_color_button.set_sensitive(i!= -1)
        self.split_button.set_sensitive(i != -1)
        self.remove_button.set_sensitive(i != -1)
        self.copy_right_button.set_sensitive(i != -1)
        self.copy_left_button.set_sensitive(i != -1)

    def create_colors_page(self):
        table = self.create_colors_table()
        label = Gtk.Label(label=_("_Colors"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)
        self.select_segment(-1)

    def create_location_page(self):
        table = self.create_location_table()
        label = Gtk.Label(label=_("_Location"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)
        
    def create_location_table(self):
        table = Gtk.Table(n_rows=5,n_columns=2,homogeneous=False)
        self.create_param_entry(table,0,_("_X :"), self.f.XCENTER)
        self.create_param_entry(table,1,_("_Y :"), self.f.YCENTER)
        self.create_param_entry(table,2,_("_Z :"), self.f.ZCENTER)
        self.create_param_entry(table,3,_("_W :"), self.f.WCENTER)
        self.create_param_entry(table,4,_("_Size :"), self.f.MAGNITUDE)
        self.create_param_entry(table,5,_("XY (_1):"), self.f.XYANGLE)
        self.create_param_entry(table,6,_("XZ (_2):"), self.f.XZANGLE)
        self.create_param_entry(table,7,_("XW (_3):"), self.f.XWANGLE)
        self.create_param_entry(table,8,_("YZ (_4):"), self.f.YZANGLE)
        self.create_param_entry(table,9,_("YW (_5):"), self.f.YWANGLE)
        self.create_param_entry(table,10,_("ZW (_6):"), self.f.ZWANGLE)
        
        return table
    
    def create_general_page(self):
        table = Gtk.Table(n_rows=5,n_columns=2,homogeneous=False)
        label = Gtk.Label(label=_("_General"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)
        yflip_widget = self.create_yflip_widget()
        table.attach(yflip_widget,0,2,0,1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        periodicity_widget = self.create_periodicity_widget()
        table.attach(periodicity_widget,0,2,1,2,
                     Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        self.create_tolerance_entry(table, 2, _("_Tolerance"))

    def create_tolerance_entry(self, table, row, text):
        label = Gtk.Label(label=text)
        label.set_use_underline(True)
        
        label.set_justify(Gtk.Justification.RIGHT)
        table.attach(label,0,1,row,row+1,0,0,2,2)
        
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        table.attach(entry,1,2,row,row+1,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        label.set_mnemonic_widget(entry)
        
        def set_entry(f,*args):
            try:
                current = float(entry.get_text())
                if current != f.period_tolerance:
                    #print "update entry to %.17f" % f.period_tolerance
                    entry.set_text("%.17f" % f.period_tolerance)
            except ValueError as err:
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
        entry.connect('focus-out-event', set_fractal)

    def create_yflip_widget(self):
        widget = Gtk.CheckButton(label=_("Flip Y Axis"))
        widget.set_use_underline(True)
        widget.set_tooltip_text(
            _("If set, Y axis increases down the screen, otherwise up the screen"))
        
        def set_widget(*args):
            widget.set_active(self.f.yflip)

        def set_fractal(*args):
            self.f.set_yflip(widget.get_active())

        set_widget()
        self.f.connect('parameters-changed',set_widget)
        widget.connect('toggled',set_fractal)

        return widget

    def create_periodicity_widget(self):
        widget = Gtk.CheckButton(label=_("Periodicity Checking"))
        widget.set_use_underline(True)
        widget.set_tooltip_text(
            _("Try to speed up calculations by looking for loops. Can cause incorrect images with some functions, though."))
        
        def set_widget(*args):
            widget.set_active(self.f.periodicity)

        def set_fractal(*args):
            self.f.set_periodicity(widget.get_active())

        set_widget()
        self.f.connect('parameters-changed',set_widget)
        widget.connect('toggled',set_fractal)

        return widget

    def add_notebook_page(self,page,text):
        label = Gtk.Label(label=text)
        label.set_use_underline(True)
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame.add(page)
        self.notebook.append_page(frame,label)
        
    def remove_transform(self,*args):
        if self.selected_transform is None:
            return

        self.f.remove_transform(self.selected_transform)
        
    def create_transforms_page(self):
        vbox = Gtk.VBox()
        table = Table(5,2,False)
        vbox.pack_start(table, True, True, 0)

        self.transform_store = Gtk.ListStore(GObject.TYPE_STRING, object)
        def set_store(*args):
            self.transform_store.clear()
            for transform in self.f.transforms:
                self.transform_store.append((transform.funcName,transform))

        set_store()

        self.f.connect('formula-changed', set_store)

        self.transform_view = Gtk.TreeView(model=self.transform_store)
        self.transform_view.set_headers_visible(False)
        self.transform_view.set_size_request(150,250)
        renderer = Gtk.CellRendererText ()
        column = Gtk.TreeViewColumn ('_Transforms', renderer, text=0)
        
        self.transform_view.append_column (column)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.transform_view)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        table.attach(
            sw, 0, 1, 0, 4,
            0, 0, 2, 2)

        add_button = Gtk.Button.new_from_stock(Gtk.STOCK_ADD)
        add_button.connect(
            'clicked', self.show_browser, browser_model.TRANSFORM)

        table.attach(
            add_button, 1,2,0,1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        remove_button = Gtk.Button.new_from_stock(Gtk.STOCK_REMOVE)
        remove_button.connect(
            'clicked', self.remove_transform)

        table.attach(
            remove_button, 1,2,1,2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        
        selection = self.transform_view.get_selection()
        selection.connect('changed',self.transform_selection_changed,vbox)

        self.add_notebook_page(vbox,_("T_ransforms"))

        self.create_transform_widget_table(vbox)

    def transform_selection_changed(self,selection, parent):
        (model,iter) = selection.get_selected()
        if iter is None:
            self.selected_transform = None
        else:
            transform = model.get_value(iter,1)
            # this is bogus. How do I get the index into the list in a less
            # stupid way?
            i = 0
            for t in self.f.transforms:
                if t == transform:
                    self.selected_transform = i
                    break
                i += 1

        self.update_transform_parameters(parent)

    def create_browsable_name(self, table, param_type, typename, tip):
        label = Gtk.Label(label=self.f.forms[param_type].funcName)
        def set_label(*args):
            label.set_text(self.f.forms[param_type].funcName)
            
        self.f.connect('parameters-changed',set_label)

        hbox = Gtk.HBox(homogeneous=False, spacing=1)
        hbox.pack_start(label, True, True, 0)

        button = Gtk.Button(label=_("_Browse..."))
        button.set_use_underline(True)
        button.set_tooltip_text(tip)
        button.connect('clicked', self.show_browser, param_type)
        hbox.pack_start(button, True, True, 0)

        typelabel = Gtk.Label(label=typename)
        typelabel.set_alignment(1.0,0.0)
        table.add(typelabel,0, Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL,0,2,2)
        table.add(hbox, 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL ,0,2,2)

    def update_formula_text(self, f, textview,formindex):
        text = f.forms[formindex].text()
        textview.get_buffer().set_text(text, -1)

    def change_formula(self,button,buffer,formindex,formtype):
        buftext = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(),
            include_hidden_chars=False)

        if buftext == '':
            #print "no text"
            return

        if buftext == self.f.forms[formtype].text():
            #print "not changed"
            return
        
        #print "text is '%s'" % buftext
        (fileName, formName) = self.f.compiler.add_inline_formula(
            buftext, formtype)
        #print "%s#%s" % (fileName, formName)
        try:
            self.f.set_formula(fileName, formName,formindex)
        except Exception as exn:
            self.show_error_message(
                _("Errors in formula"),
                exn)

    def show_error_message(self,message,exception=None):
        if exception is None:
            secondary_message = ""
        else:
            if isinstance(exception,EnvironmentError):
                secondary_message = exception.strerror or str(exception) or ""
            else:
                secondary_message = str(exception)

        d = hig.ErrorAlert(
            primary=message,
            secondary=secondary_message,
            parent=self.main_window.window)
        d.run()
        d.destroy()

    def create_formula_text_area(self,parent,formindex,formtype):
        sw = Gtk.ScrolledWindow ()
        sw.set_shadow_type (Gtk.ShadowType.ETCHED_IN)
        sw.set_policy (Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        textview = Gtk.TextView()

        sw.add(textview)
        parent.pack_start(sw, True, True, 2)

        self.f.connect(
            'formula-changed', self.update_formula_text, textview, formindex)

        apply = Gtk.Button(label=_("Apply Formula Changes"))
        apply.connect(
            'clicked',
            self.change_formula,
            textview.get_buffer(),
            formindex,
            formtype)

        parent.pack_end(apply, False, False, 1)
        self.update_formula_text(self.f, textview, formindex)

    def create_formula_parameters_page(self):
        vbox = Gtk.VBox()
        formbox = Gtk.VBox()
        self.create_formula_widget_table(
            formbox,
            0,
            _("Formula"),
            _("Browse available fractal functions"))
        
        vbox.pack_start(formbox, False, False, 0)
        self.create_formula_text_area(vbox,0,FormulaTypes.FRACTAL)
        self.add_notebook_page(vbox, _("Formula"))

    def create_outer_page(self):
        vbox = Gtk.VBox()
        formbox = Gtk.VBox()
        self.create_formula_widget_table(
            formbox,
            1,
            _("Coloring Method"),
            _("Browse available coloring functions"))

        vbox.pack_start(formbox, False, False, 0)
        self.create_formula_text_area(vbox,1,FormulaTypes.COLORFUNC)
        self.add_notebook_page(vbox,_("Outer"))
        
    def create_inner_page(self):
        vbox = Gtk.VBox()
        formbox = Gtk.VBox()
        self.create_formula_widget_table(
            formbox,
            2,
            _("Coloring Method"),
            _("Browse available coloring functions"))

        vbox.pack_start(formbox, False, False, 0)
        self.create_formula_text_area(vbox,2,FormulaTypes.COLORFUNC)
        self.add_notebook_page(vbox, _("Inner"))

    def update_transform_parameters(self, parent, *args):
        widget = self.tables[3]
        if widget is not None:
            try:
                parent.remove(self.tables[3])
            except AttributeError:
                pass

        if self.selected_transform is not None:
            self.tables[3] = Table(5,2,False)
            self.f.populate_formula_settings(
                self.tables[3],
                self.selected_transform+3)

            self.tables[3].show_all()
            parent.pack_start(self.tables[3], True, True, 0)

    def create_transform_widget_table(self,parent):
        self.tables[3] = None
                    
        self.update_transform_parameters(parent)

        self.f.connect(
            'formula-changed', self.update_transform_parameters, parent)
        self.f.connect(
            'parameters-changed', self.update_all_widgets, lambda: self.tables[3])
        
    def create_formula_widget_table(self,parent,param_type,typename,tip):
        self.tables[param_type] = None
        
        def update_formula_parameters(*args):
            widget = self.tables[param_type]
            if widget is not None:
                try:
                    parent.remove(self.tables[param_type])
                except AttributeError:
                    pass

            table = Table(5,2,False)
            self.create_browsable_name(table, param_type, typename, tip)
            
            self.f.populate_formula_settings(
                table,
                param_type, 1)
            
            table.show_all()
            parent.pack_start(table, True, True, 0)
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
        else:
            container = container

        if container is None:
            return

        for widget in container.get_children():
            try:
                widget.update_function()
            except AttributeError:
                pass
            if isinstance(widget, Gtk.Container):
                self.update_all_widgets(fractal,widget) # recurse

    def show_browser(self,button,type):
        browser.show(self.main_window, self.f, type)
        
    def create_param_entry(self,table, row, text, param):
        label = Gtk.Label(label=text)
        label.set_use_underline(True)
        
        label.set_justify(Gtk.Justification.RIGHT)
        table.attach(label,0,1,row,row+1,0,0,2,2)
        
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        table.attach(entry,1,2,row,row+1,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        label.set_mnemonic_widget(entry)
        
        def set_entry(f):
            try:
                current = float(entry.get_text())
                if current != f.get_param(param):
                    entry.set_text("%.17f" % f.get_param(param))
            except ValueError as err:
                # current was set to something that isn't a float
                entry.set_text("%.17f" % f.get_param(param))

        def set_fractal(*args):
            try:
                self.f.set_param(param,entry.get_text())
            except Exception as exn:
                print(exn)
            return False
        
        set_entry(self.f)
        self.f.connect('parameters-changed', set_entry)
        entry.connect('focus-out-event', set_fractal)
