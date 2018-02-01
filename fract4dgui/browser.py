#!/usr/bin/env python3

# a browser to examine fractal functions
import string
import os

from gi.repository import GObject
from gi.repository import Gtk

from fract4d import fc, gradient, browser_model

from . import preferences, dialog, utils, gtkfractal, gradientCellRenderer

def stricmp(a,b):
    return cmp(a.lower(),b.lower())

def show(parent, f, type=browser_model.FRACTAL):
    BrowserDialog.show(parent,f,type)

def update(file=None, formula=None):
    browser_model.instance.update(file,formula)

def set_type(type):
    browser_model.instance.set_type(type)

def guess_type(file):
    return browser_model.instance.guess_type(file)

class BrowserDialog(dialog.T):
    RESPONSE_EDIT = 1
    RESPONSE_REFRESH = 2
    RESPONSE_COMPILE = 3
    def __init__(self,main_window,f):
        dialog.T.__init__(
            self,
            _("Formula Browser"),
            main_window,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (#_("Co_mpile"), BrowserDialog.RESPONSE_COMPILE,
             Gtk.STOCK_REFRESH, BrowserDialog.RESPONSE_REFRESH,
             Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY,
             Gtk.STOCK_OK, Gtk.ResponseType.OK,
             Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        self.set_default_response(Gtk.ResponseType.OK)

        self.model = browser_model.instance
        self.model.type_changed += self.on_type_changed
        self.model.file_changed += self.on_file_changed
        self.model.formula_changed += self.on_formula_changed
        
        self.formula_list = Gtk.ListStore(
            GObject.TYPE_STRING)

        self.file_list = Gtk.ListStore(
            GObject.TYPE_STRING, #formname
            GObject.TYPE_STRING,
            GObject.TYPE_INT)

        self.f = f
        self.compiler = f.compiler

        self.ir = None
        self.main_window = main_window
        self.set_size_request(600,500)
        self.preview = gtkfractal.Preview(self.compiler)
        self.preview.f.auto_tolerance = False

        self.create_panes()
        self.on_file_changed()
        
    def show(parent, f, type):
        _browser = dialog.T.reveal(BrowserDialog,True, parent, None, f)
        _browser.set_type(type)
        _browser.populate_file_list()

    show = staticmethod(show)

    def onResponse(self,widget,id):
        if id == Gtk.ResponseType.CLOSE or \
               id == Gtk.ResponseType.NONE or \
               id == Gtk.ResponseType.DELETE_EVENT:
            self.hide()
        elif id == Gtk.ResponseType.APPLY:
            self.onApply()
        elif id == Gtk.ResponseType.OK:
            self.onApply()
            self.hide()
        elif id == BrowserDialog.RESPONSE_REFRESH:
            self.onRefresh()
        else:
            print("unexpected response %d" % id)

    def onRefresh(self):
        self.f.refresh()
        self.set_file(self.model.current.fname) # update text window

    def get_current_text(self):
        buffer = self.sourcetext.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(),
                               buffer.get_end_iter(), False)
        return text

    def onApply(self):
        self.model.apply(self.f)
        
    def set_type_cb(self,optmenu):
        self.set_type(utils.get_selected(optmenu))

    def on_type_changed(self):
        utils.set_selected(self.funcTypeMenu, self.model.current_type)
        self.populate_file_list()
        
    def set_type(self,type):
        self.model.set_type(type)
        
    def create_file_list(self):
        sw = Gtk.ScrolledWindow ()

        sw.set_shadow_type (Gtk.ShadowType.ETCHED_IN)
        sw.set_policy (Gtk.PolicyType.NEVER,
                       Gtk.PolicyType.AUTOMATIC)

        self.filetreeview = Gtk.TreeView.new_with_model(self.file_list)
        self.filetreeview.set_tooltip_text(
            _("A list of files containing fractal formulas"))
        
        sw.add(self.filetreeview)

        renderer = Gtk.CellRendererText ()
        column = Gtk.TreeViewColumn ('_File', renderer, text=0)
        
        self.filetreeview.append_column (column)

        #renderer = gradientCellRenderer.GradientCellRenderer(self.model, self.compiler)
        #column = Gtk.TreeViewColumn (_('_Preview'), renderer)
        #self.filetreeview.append_column (column)

        selection = self.filetreeview.get_selection()
        selection.connect('changed',self.file_selection_changed)
        return sw

    def populate_file_list(self):
        # find all appropriate files and add to file list
        self.file_list.clear()

        files = self.model.current.files
        
        current_iter = None
        index,i = 0,0
        for fname in files:
            iter = self.file_list.append ()
            if fname == self.model.current.fname:
                current_iter = iter
                index = i
            self.file_list.set (iter, 0, fname)
            i += 1
            
        # re-select current file, if any
        if current_iter:
            self.filetreeview.scroll_to_cell(index)
            sel = self.filetreeview.get_selection()
            if sel:
                sel.unselect_all()
                sel.select_iter(current_iter)
                self.populate_formula_list(self.model.current.fname)
        else:
            self.formula_list.clear()
            self.formula_selection_changed(None)
        
    def populate_formula_list(self,fname):
        self.formula_list.clear()

        form_names = self.model.current.formulas

        i = 0
        for formula_name in form_names:
            iter = self.formula_list.append()
            self.formula_list.set(iter,0,formula_name)
            if formula_name == self.model.current.formula:
                self.treeview.get_selection().select_iter(iter)
                self.treeview.scroll_to_cell(i)
                self.set_formula(formula_name)
            i += 1
            
    def create_formula_list(self):
        sw = Gtk.ScrolledWindow ()
        sw.set_shadow_type (Gtk.ShadowType.ETCHED_IN)
        sw.set_policy (Gtk.PolicyType.NEVER,
                       Gtk.PolicyType.AUTOMATIC)

        self.treeview = Gtk.TreeView.new_with_model(self.formula_list)

        self.treeview.set_tooltip_text(
            _("A list of formulas in the selected file"))

        sw.add(self.treeview)

        renderer = Gtk.CellRendererText ()
        column = Gtk.TreeViewColumn (_('F_ormula'), renderer, text=0)
        self.treeview.append_column (column)
        #renderer = gradientCellRenderer.GradientCellRenderer(self.model, self.compiler)
        #column = Gtk.TreeViewColumn (_('_Preview'), renderer)
        #column.add_attribute(renderer, "formname", 0)
        #self.treeview.append_column (column)

        selection = self.treeview.get_selection()
        selection.connect('changed',self.formula_selection_changed)
        return sw

    def create_scrolled_textview(self,tip):
        sw = Gtk.ScrolledWindow ()
        sw.set_shadow_type (Gtk.ShadowType.ETCHED_IN)
        sw.set_policy (Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        textview = Gtk.TextView()
        textview.set_tooltip_text(tip)
        textview.set_editable(False)
        
        sw.add(textview)
        return (textview,sw)

    def create_panes(self):
        # option menu for choosing Inner/Outer/Fractal
        self.funcTypeMenu = utils.create_option_menu(
            [_("Fractal Function"),
             _("Outer Coloring Function"),
             _("Inner Coloring Function"),
             _("Transform Function"),
             _("Gradient")])

        utils.set_selected(self.funcTypeMenu,self.model.current_type)
        
        self.funcTypeMenu.set_tooltip_text(
            _("Which formula of the current fractal to change"))

        self.funcTypeMenu.connect('changed',self.set_type_cb)

        # label for the menu
        hbox = Gtk.HBox()
        label = Gtk.Label(label=_("Function _Type to Modify : "))
        label.set_use_underline(True)
        label.set_mnemonic_widget(self.funcTypeMenu)
        
        hbox.pack_start(label, False, False, 0)
                
        hbox.pack_start(self.funcTypeMenu, True, True, 0)
        self.vbox.pack_start(hbox, False, False, 0)
        
        # 3 panes: files, formulas, formula contents
        panes1 = Gtk.HPaned()
        self.vbox.pack_start(panes1, True, True, 0)
        panes1.set_border_width(5)

        file_list = self.create_file_list()
        formula_list = self.create_formula_list()
        
        panes2 = Gtk.HPaned()
        # left-hand pane displays file list
        panes2.pack1(file_list, True, False)
        # middle is formula list for that file
        panes2.pack2(formula_list, True, False)
        panes1.add1(panes2)

        # right-hand pane is details of current formula
        notebook = Gtk.Notebook()

        # preview
        label = Gtk.Label(label=_('_Preview'))
        label.set_use_underline(True)
        notebook.append_page(self.preview.widget, label)
        
        # source
        (self.sourcetext,sw) = self.create_scrolled_textview(
            _("The contents of the currently selected formula file"))
        
        label = Gtk.Label(label=_('_Source'))
        label.set_use_underline(True)
        notebook.append_page(sw, label)

        # messages
        (self.msgtext, sw) = self.create_scrolled_textview(
            _("Any compiler warnings or errors in the current function"))
        
        label = Gtk.Label(label=_('_Messages'))
        label.set_use_underline(True)
        notebook.append_page(sw, label)

        panes1.add2(notebook)

    def file_selection_changed(self,selection):
        self.model.current.formula = None
        (model,iter) = selection.get_selected()
        if iter == None:
            return
        
        fname = model.get_value(iter,0)
        self.set_file(fname)

    def set_file(self,fname):
        self.model.set_file(fname)

    def on_file_changed(self):
        text = self.model.get_contents()
        
        self.display_text(text)
        self.populate_formula_list(self.model.current.fname)
        self.set_apply_sensitivity()
        
    def clear_selection(self):
        self.set_formula(None)
        
    def formula_selection_changed(self,selection):
        if not selection:
            self.clear_selection()
            return
        
        (model,iter) = selection.get_selected()
        if iter == None:
            self.clear_selection()
            return
        
        form_name = model.get_value(iter,0)
        self.set_formula(form_name)
        
    def set_formula(self,form_name):
        self.model.set_formula(form_name)

    def on_formula_changed(self):
        form_name = self.model.current.formula
        file = self.model.current.fname

        if not file:
            return
        
        formula = self.compiler.get_parsetree(file,form_name)

        if not formula:
            return
        
        #update location of source buffer        
        sourcebuffer = self.sourcetext.get_buffer()
        iter = sourcebuffer.get_iter_at_line(formula.pos-1)
        self.sourcetext.scroll_to_iter(iter,0.0,True,0.0,0.0)

        # update IR tree
        self.ir = self.compiler.get_formula(file,form_name)

        # update messages
        buffer = self.msgtext.get_buffer()
        msg = ""
        if self.ir.errors != []:
            msg += _("Errors:\n") + "\n".join(self.ir.errors) + "\n"
        if self.ir.warnings != []:
            msg += _("Warnings:\n") + "\n".join(self.ir.warnings)
        if msg == "":
            msg = _("No messages")
            
        buffer.set_text(msg,-1)

        self.set_apply_sensitivity()

    def set_apply_sensitivity(self):
        can_apply = self.model.current.can_apply
        self.set_response_sensitive(Gtk.ResponseType.APPLY,can_apply)
        self.set_response_sensitive(Gtk.ResponseType.OK,can_apply)

        if can_apply:
            self.model.apply(self.preview)
            self.preview.draw_image(False, False)
        
    def display_text(self,text):
        self.sourcetext.get_buffer().set_text(text, -1)
