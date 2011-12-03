# This file contains utility classes and functions used by the GUI
# Many of them 'cover up' differences between pygtk versions - these
# follow the general pattern
#
# try:
#    do new thing
# except:
#    fall back to the 'old way'

import os
import sys
import inspect

import gtk
import gobject

try:
	from fract4d import fract4dcgmp as fract4dc
except ImportError, err:
    from fract4d import fract4dc

threads_enabled = False
break_new_things = False

def force_throwback():
    """Used for unit testing the 'old style' code - make the new stuff break
    even if it would normally work. Call this to revert to pygtk 2.0 style"""
    global break_new_things
    break_new_things = True

def unforce_throwback():
    global break_new_things
    break_new_things = False
    
def _throwback():
    if break_new_things: raise AttributeError("Forcing use of old code")
    
def threads_enter():
    if threads_enabled:
        gtk.gdk.threads_enter()

def threads_leave():
    if threads_enabled:
        gtk.gdk.threads_leave()

def idle_wrapper(callable, *args):
    threads_enter()
    callable(*args)
    threads_leave()

def idle_add(callable, *args):
    """A wrapper around gtk.idle_add which wraps the callback in
    threads_enter/threads_leave if required"""
    try:
        _throwback()
        gobject.idle_add(idle_wrapper, callable, *args)
    except AttributeError:
        gtk.idle_add(idle_wrapper, callable, *args)

def timeout_add(time,callable):
    try:
        _throwback()
        gobject.timeout_add(time,callable)
    except AttributeError:
        gtk.timeout_add(time,callable)

if 'win' != sys.platform[:3]:
    def input_add(fd,cb):
        try:
            _throwback()
            return gobject.io_add_watch(fd, gobject.IO_IN | gobject.IO_HUP, cb)
        except AttributeError, err:
            return gtk.input_add(fd, gtk.gdk.INPUT_READ, cb)
else:
    def input_add(fd, cb):
        # fd = %i; cb = %o
        return fract4dc.io_add_watch(fd, gobject.IO_IN | gobject.IO_HUP, cb)

def find_in_path(exe):
    # find an executable along PATH env var
    pathstring = os.environ["PATH"]
    if pathstring == None or pathstring == "":
        return None
    paths = pathstring.split(":")
    for path in paths:
        full_path = os.path.join(path,exe)
        if os.path.exists(full_path):
            return full_path
    return None
    
def stack_trace():
    stack = inspect.stack()
    str = ""
    for frame in stack[1:]:
        (frame_obj, filename, line, funcname, context, context_index) = frame
        try:
            args = inspect.formatargvalues(*inspect.getargvalues(frame_obj))
        except Exception:
            args = "<unavailable>"
        
        frame_desc = "%s(%s)\t\t%s(%s)\n" % (filename, line, funcname, args)
        str += frame_desc
    return str
    
def get_rgb_colormap():
    # work around a difference between pygtk versions
    if hasattr(gtk.gdk,'rgb_get_colormap'):
        c = gtk.gdk.rgb_get_colormap()
    else:
        c = gtk.gdk.rgb_get_cmap()
    return c

def get_directory_chooser(title,parent):
    try:
        _throwback()
        chooser = gtk.FileChooserDialog(
            title, parent, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

        return chooser
    except:
        return gtk.FileSelection(title)
    
def get_file_chooser_extra_widget(chooser):
    try:
        _throwback()
        return chooser.get_extra_widget()
    except:
        return chooser.action_area.get_children()[0]

def set_file_chooser_filename(chooser,name):
    try:
        _throwback()
        if name:
            chooser.set_current_folder(os.path.abspath(os.path.dirname(name)))
            chooser.set_current_name(os.path.basename(name))
    except:
        pass
    
def create_option_menu(items):
    try:
        _throwback()
        widget = gtk.combo_box_new_text()
        for item in items:
            widget.append_text(item)
        
    except Exception, exn:
        widget = gtk.OptionMenu()
        widget.item_list = items # for get_selected_value
        menu = gtk.Menu()
        for item in items:
            mi = gtk.MenuItem(item)
            menu.append(mi)
        widget.set_menu(menu)
        
    return widget

def set_menu_from_list(menu, items):
    try:
        _throwback()
        model = gtk.ListStore(gobject.TYPE_STRING)
        for item in items:
            model.append((item,))
        menu.set_model(model)
    except:
        menu.item_list = items
        submenu = menu.get_menu()
        for child in submenu.get_children():
            submenu.remove(child)

        for item in items:
            mi = gtk.MenuItem(item)
            submenu.append(mi)
        
def add_menu_item(menu, item):
    try:
        _throwback()
        menu.append_text(item)
    except:
        menu.get_menu().append(gtk.MenuItem(item))

def set_selected(menu, i):
    try:
        _throwback()
        menu.set_active(int(i))
    except:
        menu.set_history(int(i))
        
def get_selected(menu):
    try:
        _throwback()
        return menu.get_active()
    except:
        return menu.get_history()

def get_selected_value(menu):
    try:
        _throwback()
        iter = menu.get_active_iter()
        if not iter:
            return None
        val = menu.get_model().get_value(iter,0)
        return val
    except:
        return menu.item_list[menu.get_history()]

def set_selected_value(menu,val):
    try:
        _throwback()
        model = menu.get_model()
        i = 0
        iter = model.get_iter_first()
        while iter != None:
            item = model.get_value(iter,0)
            if item == val:
                menu.set_active(i)
                return
            iter = model.iter_next(iter)
            i += 1
        
    except:
        i = menu.item_list.index(val)
        menu.set_history(i)

def create_color(r,g,b):
    # multiply up to match range expected by gtk
    try:
        _throwback()
        return gtk.gdk.Color(int(r*65535),int(g*65535),int(b*65535))
    except Exception, exn:
        # old gtk doesn't have direct color constructor
        return gtk.gdk.color_parse(
            "#%04X%04X%04X" % (int(r*65535),int(g*65535),int(b*65535)))

def floatColorFrom256(rgba):
    return [ rgba[0]/255.0, rgba[1]/255.0, rgba[2]/255.0, rgba[3]/255.0]

def color256FromFloat(r,g,b,color):
    return (int(r*255), int(g*255), int(b*255), color[3])

def launch_browser(prefs, url, window):
    browser = prefs.get("helpers","browser")
    cmd = browser % ('"' + url + '" &')
    try:
        os.system(cmd)
    except Exception, err:
        d = hig.ErrorAlert(
            primary=_("Error launching browser"),
            secondary=_("Try modifying your preferences or copy the URL manually to a browser window.\n") + \
            str(err),
            parent=window) 
        d.run()
        d.destroy()

class ColorButton:
    def __init__(self,rgb, changed_cb, is_left):
        self.area = None
        self.set_color(rgb)
        self.changed_cb = changed_cb
        self.is_left = is_left
        try:
            _throwback()
            self.widget = gtk.ColorButton(self.color)

            def color_set(widget):
                color = widget.get_color()
                self.color_changed(color)

            self.widget.connect('color-set', self.on_color_set)
        except:
            # This GTK is too old to support ColorButton directly, fake one
            self.widget = gtk.Button()
            self.area = gtk.DrawingArea()
            self.area.set_size_request(16,10)
            self.widget.add(self.area)
            self.area.connect('expose_event', self.on_expose_event)
            self.csel_dialog = gtk.ColorSelectionDialog(_("Select a Color"))

            self.widget.connect('clicked', self.run_colorsel)

    def on_color_set(self, widget):
        self.color_changed(widget.get_color())

    def set_color(self, rgb):
        self.color = create_color(rgb[0], rgb[1], rgb[2])
    
        try:
            _throwback()
            self.widget.set_color(self.color)
        except:
            #print "sc", self.area, rgb
            if self.area:
                self.area_expose(
                    self.area,
                    0,0,
                    self.area.allocation.width,self.area.allocation.height)

    def on_expose_event(self, widget, event):
        r = event.area
        self.area_expose(widget, r.x, r.y, r.width, r.height)
        
    def area_expose(self, widget, x, y, w, h):
        if not widget.window:
            return
        gc = widget.window.new_gc(fill=gtk.gdk.SOLID)
        self.color = widget.get_colormap().alloc_color(
            self.color.red, self.color.green, self.color.blue)
        gc.set_foreground(self.color)
        widget.window.draw_rectangle(gc, True, x, y, w, h)

    def run_colorsel(self, widget):
        dlg = self.csel_dialog
        dlg.colorsel.set_current_color(self.color)
        result = dlg.run()
        if result == gtk.RESPONSE_OK:
            self.color = dlg.colorsel.get_current_color()
            self.color_changed(self.color)
        self.csel_dialog.hide()

    def set_sensitive(self,x):
        self.widget.set_sensitive(x)
        
    def color_changed(self,color):
        self.color = color     
        self.changed_cb(
            color.red/65535.0,
            color.green/65535.0,
            color.blue/65535.0,
            self.is_left)

        
