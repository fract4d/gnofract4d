# GUI for user settings

import os
import sys

from gi.repository import Gtk
from gi.repository import GObject

import dialog
import utils

from fract4d import fractconfig

class Preferences(GObject.GObject):
    # A wrapper for the preference data
    __gsignals__ = {
        'preferences-changed' : (
        (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
        None, ()),
        'image-preferences-changed' : (
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

    def set(self,section,key,val):
        self.config.set(section,key,val)

    def get(self,section,key):
        return self.config.get(section,key)

    def getboolean(self,section,key):
        return self.config.getboolean(section,key)

    def getint(self,section,key):
        return self.config.getint(section,key)
    
    def set_size(self,width,height):
        self.config.set_size(width,height)

    def get_list(self,name):
        return self.config.get_list(name)

    def set_list(self,name,list):
        self.config.set_list(name,list)

    def update_list(self,name,new_entry,maxsize):
        return self.config.update_list(name,new_entry,maxsize)

    def remove_all_in_list_section(self,name):
        self.config.remove_all_in_list_section(name)

    def save(self):
        self.config.save()

# explain our existence to GTK's object system
GObject.type_register(Preferences)

userPrefs = Preferences(fractconfig.instance)
    
def show_preferences(parent,f):
    PrefsDialog.show(parent,f)
    
class PrefsDialog(dialog.T):
    def __init__(self,main_window,f):
        global userPrefs
        dialog.T.__init__(
            self,
            _("Gnofract 4D Preferences"),
            main_window,
            Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        self.dirchooser = utils.get_directory_chooser(
            _("Select a Formula Directory"),
            main_window)
        
        self.set_default_response(Gtk.ResponseType.CLOSE)
        self.f = f
        self.notebook = Gtk.Notebook()
        self.vbox.add(self.notebook)
        self.prefs = userPrefs
        self.tips = Gtk.Tooltips()
        self.create_image_options_page()
        self.create_compiler_options_page()
        self.create_general_page()
        self.create_helper_options_page()
        self.create_flickr_page()
        
        self.set_size_request(500,-1)

    def show(parent, f):
        dialog.T.reveal(PrefsDialog, True, parent, None, f)

    show = staticmethod(show)

    def show_error(self,message):
        d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                              Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                              message)
        d.run()
        d.destroy()

    def create_width_entry(self):
        entry = Gtk.Entry()
        self.tips.set_tip(entry,"The image's width in pixels")
        entry.set_activates_default(True)
        
        def set_entry(*args):
            entry.set_text(self.prefs.get("display","width"))

        def set_prefs(*args):
            try:
                height = self.f.height
                try:
                    width = int(entry.get_text())
                except ValueError:
                    Gtk.idle_add(
                        self.show_error,
                        "Invalid value for width: '%s'. Must be an integer" % \
                        entry.get_text())
                    return False

                if self.fix_ratio.get_active():
                    height = int(width * float(height)/self.f.width)

                utils.idle_add(self.prefs.set_size,width, height)
            except Exception as exn:
                print(exn)
            return False
    
        set_entry()
        self.prefs.connect('preferences-changed', set_entry)
        entry.connect('focus-out-event', set_prefs)
        return entry

    def create_height_entry(self):
        entry = Gtk.Entry()
        self.tips.set_tip(entry,"The image's height in pixels")
        entry.set_activates_default(True)
        
        def set_entry(*args):
            entry.set_text(self.prefs.get("display","height"))

        def set_prefs(*args):
            try:
                try:
                    height = int(entry.get_text())
                except ValueError:
                    utils.idle_add(
                        self.show_error,
                        "Invalid value for height: '%s'. Must be an integer" % \
                        entry.get_text())
                    return False

                width = self.f.width
                if self.fix_ratio.get_active():
                    width = int(height * float(self.f.width)/self.f.height)
                self.prefs.set_size(width, height)
            except Exception as exn:
                print(exn)
            return False
        
        set_entry()
        self.prefs.connect('preferences-changed', set_entry)
        entry.connect('focus-out-event', set_prefs)
        return entry

    def create_compiler_entry(self,propname):
        return self.create_option_entry("compiler",propname)
    
    def create_option_entry(self,section,propname):
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        
        def set_entry(*args):
            entry.set_text(self.prefs.get(section,propname))

        def set_prefs(*args):
            try:
                self.prefs.set(section,propname,entry.get_text())
            except Exception as err:
                print(err)
            return False
        
        set_entry()
        self.prefs.connect('preferences-changed',set_entry)
        entry.connect('focus-out-event', set_prefs)
        return entry

    def create_save_compress_widget(self):
        widget = Gtk.CheckButton(_("Compress _Parameter Files"))
        self.tips.set_tip(
            widget,_("Write .fct files in a shorter but unreadable format"))
        widget.set_use_underline(True)
        
        def set_widget(*args):
            widget.set_active(self.prefs.getboolean("general","compress_fct"))

        def set_prefs(*args):
            self.prefs.set("general","compress_fct",str(widget.get_active()))

        set_widget()
        self.prefs.connect('preferences-changed',set_widget)
        widget.connect('toggled',set_prefs)

        return widget

    def create_general_page(self):
        table = Gtk.Table(5,2,False)
        label = Gtk.Label(label=_("_General"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)

        entry = self.create_option_entry("general","threads")
        self.tips.set_tip(entry,_("How many threads to use for calculations"))
        table.attach(entry,1,2,0,1,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        name_label = Gtk.Label(label=_("_Number of threads :"))
        name_label.set_use_underline(True)
        name_label.set_mnemonic_widget(entry)
        table.attach(name_label,0,1,0,1,0,0,2,2)

        save_compress = self.create_save_compress_widget()
        table.attach(save_compress,0,2,1,2,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL,0,2,2)
                
    def create_directory_list(self, section_name):
        self.path_list = Gtk.ListStore(
            GObject.TYPE_STRING)
        
        path_treeview = Gtk.TreeView (self.path_list)

        renderer = Gtk.CellRendererText ()
        column = Gtk.TreeViewColumn (_('_Directory'), renderer, text=0)
        path_treeview.append_column (column)
        path_treeview.set_headers_visible(False)
        
        paths = self.prefs.get_list(section_name)
        for path in paths:
            iter = self.path_list.append()
            self.path_list.set(iter,0,path)

        return path_treeview 

    def update_prefs(self,name, model):
        list = []

        def append_func(m,path,iter,dummy):
            list.append(model.get_value(iter,0))
        
        model.foreach(append_func,None)

        self.prefs.set_list(name,list)
        
    def browse_for_dir(self, widget, name, pathlist):
        self.dirchooser.show_all()
        result = self.dirchooser.run()
        if result == Gtk.ResponseType.OK:
            path = self.dirchooser.get_filename()

            model = pathlist.get_model() 
            iter = model.append()
            
            model.set(iter,0,path)
            self.update_prefs(name, model)
            
        self.dirchooser.hide()

    def remove_dir(self, widget, name, pathlist):
        select = pathlist.get_selection()
        (model, iter) = select.get_selected()

        if iter:
            model.remove(iter)
            self.update_prefs(name, model)
            
    def create_compiler_options_page(self):
        table = Gtk.Table(5,2,False)
        label = Gtk.Label(label=_("_Compiler"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)
                        
        entry = self.create_compiler_entry("name")
        self.tips.set_tip(entry,_("The C compiler to use"))
        table.attach(entry,1,2,0,1,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        name_label = Gtk.Label(label=_("Compi_ler :"))
        name_label.set_use_underline(True)
        name_label.set_mnemonic_widget(entry)
        table.attach(name_label,0,1,0,1,0,0,2,2)
        
        entry = self.create_compiler_entry("options")
        self.tips.set_tip(entry, _("Options to pass to the C compiler"))
        table.attach(entry,1,2,1,2,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        flags_label = Gtk.Label(label=_("Compiler _Flags :"))
        flags_label.set_use_underline(True)
        table.attach(flags_label,0,1,1,2,0,0,2,2)
        flags_label.set_mnemonic_widget(entry)

        sw = Gtk.ScrolledWindow ()
        sw.set_shadow_type (Gtk.ShadowType.ETCHED_IN)
        sw.set_policy (Gtk.PolicyType.NEVER,
                       Gtk.PolicyType.AUTOMATIC)

        form_path_section = "formula_path"

        pathlist = self.create_directory_list(form_path_section)
        self.tips.set_tip(pathlist, _("Directories to search for formulas"))

        sw.add(pathlist)

        table.attach(sw,1,2,2,5,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        pathlist_label = Gtk.Label(label=_("Formula Search _Path :"))
        pathlist_label.set_use_underline(True)
        table.attach(pathlist_label,0,1,2,3,0,0,2,2)
        pathlist_label.set_mnemonic_widget(pathlist)

        add_button = Gtk.Button(None,Gtk.STOCK_ADD)
        add_button.connect('clicked', self.browse_for_dir, form_path_section, pathlist)
        table.attach(add_button,0,1,3,4,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        
        remove_button = Gtk.Button(None, Gtk.STOCK_REMOVE)
        remove_button.connect('clicked', self.remove_dir, form_path_section, pathlist)
        table.attach(remove_button,0,1,4,5,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        
        
    def create_helper_options_page(self):
        table = Gtk.Table(5,2,False)
        label = Gtk.Label(label=_("_Helpers"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)
                        
        entry = self.create_option_entry("helpers","editor")
        self.tips.set_tip(entry,_("The text editor to use for changing formulas"))
        table.attach(entry,1,2,0,1,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        name_label = Gtk.Label(label="_Editor :")
        name_label.set_use_underline(True)
        name_label.set_mnemonic_widget(entry)
        table.attach(name_label,0,1,0,1,0,0,2,2)

        entry = self.create_option_entry("helpers","mailer")
        self.tips.set_tip(entry,_("The command to launch an email editor"))
        table.attach(entry,1,2,1,2,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        name_label = Gtk.Label(label="E_mail :")
        name_label.set_use_underline(True)
        name_label.set_mnemonic_widget(entry)
        table.attach(name_label,0,1,1,2,0,0,2,2)

        entry = self.create_option_entry("helpers","browser")
        self.tips.set_tip(entry,_("The command to launch a web browser"))
        table.attach(entry,1,2,2,3,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        name_label = Gtk.Label(label="_Browser :")
        name_label.set_use_underline(True)
        name_label.set_mnemonic_widget(entry)
        table.attach(name_label,0,1,2,3,0,0,2,2)

    def update_id(self,*args):
        token = self.prefs.get("user_info","flickr_token")
        if token=="":
            # not signed in
            self.token_label.set_text(_("Not signed in"))
        else:
            self.token_label.set_text(_("Signed in"))

        self.signoff.set_sensitive(token != "")

    def do_signoff(self,widget):
        self.prefs.set("user_info","flickr_token","")
        self.prefs.set("user_info","nsid","")
        
    def create_flickr_page(self):
        table = Gtk.Table(5,2,False)
        label = Gtk.Label(label=_("_Flickr"))
        label.set_use_underline(True)
        self.notebook.append_page(table,label)

        self.signoff = Gtk.Button(_("_Sign out from Flickr"))
        self.signoff.connect("clicked",self.do_signoff)

        self.token_label = Gtk.Label(label="")
        table.attach(self.token_label,0,2,0,1,0,0,2,2)

        table.attach(self.signoff,0,1,1,2,0,0,2,2)

        self.prefs.connect('preferences-changed',self.update_id)
        self.update_id()
        
    def create_auto_deepen_widget(self):
        widget = Gtk.CheckButton("Auto _Deepen")
        self.tips.set_tip(widget,"Adjust number of iterations automatically")
        widget.set_use_underline(True)
        
        def set_widget(*args):
            widget.set_active(self.prefs.getboolean("display","autodeepen"))

        def set_prefs(*args):
            self.prefs.set("display","autodeepen",str(widget.get_active()))

        set_widget()
        self.prefs.connect('preferences-changed',set_widget)
        widget.connect('toggled',set_prefs)

        return widget

    def create_auto_tolerance_widget(self):
        widget = Gtk.CheckButton("Auto _Tolerance")
        self.tips.set_tip(widget,"Adjust periodicity tolerance automatically")
        widget.set_use_underline(True)
        
        def set_widget(*args):
            widget.set_active(self.prefs.getboolean("display","autotolerance"))

        def set_prefs(*args):
            self.prefs.set("display","autotolerance",str(widget.get_active()))

        set_widget()
        self.prefs.connect('preferences-changed',set_widget)
        widget.connect('toggled',set_prefs)

        return widget

    def create_antialias_menu(self):
        optMenu = utils.create_option_menu(["None", "Fast", "Best"])

        def set_widget(*args):
            utils.set_selected(optMenu, self.prefs.getint("display","antialias"))

        def set_prefs(*args):
            index = utils.get_selected(optMenu)
            if index != -1:
                self.prefs.set("display","antialias",str(index))

        set_widget()
        self.prefs.connect('preferences-changed',set_widget)
        optMenu.connect('changed',set_prefs)
        return optMenu
    
    def create_image_options_page(self):
        table = Gtk.Table(5,2,False)
        label = Gtk.Label(label="_Image")
        label.set_use_underline(True)
        self.notebook.append_page(table,label)

        wentry = self.create_width_entry()
        table.attach(wentry,1,2,0,1,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        wlabel = Gtk.Label(label="_Width :")
        wlabel.set_mnemonic_widget(wentry)
        wlabel.set_use_underline(True)
        table.attach(wlabel,0,1,0,1,0,0,2,2)

        hentry = self.create_height_entry()
        table.attach(hentry,1,2,1,2,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        hlabel = Gtk.Label(label="_Height :")
        hlabel.set_mnemonic_widget(hentry)
        hlabel.set_use_underline(True)
        table.attach(hlabel,0,1,1,2,0,0,2,2)

        self.fix_ratio = Gtk.CheckButton("Maintain Aspect _Ratio")
        self.tips.set_tip(self.fix_ratio,"Keep the image rectangle the same shape when changing its size")
        self.fix_ratio.set_use_underline(True)
        table.attach(self.fix_ratio,0,2,2,3,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        self.fix_ratio.set_active(True)

        # auto deepening
        self.auto_deepen = self.create_auto_deepen_widget()
        table.attach(self.auto_deepen,0,2,3,4,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)
        
        # auto tolerance
        self.auto_tolerance = self.create_auto_tolerance_widget()
        table.attach(self.auto_tolerance,0,2,4,5,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        # antialiasing
        optMenu = self.create_antialias_menu()
        table.attach(optMenu,1,2,5,6,Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 0, 2, 2)

        aalabel = Gtk.Label(label="_Antialiasing : ")
        aalabel.set_use_underline(True)
        aalabel.set_mnemonic_widget(optMenu)
        table.attach(aalabel,0,1,5,6,0,0,2,2)
        
