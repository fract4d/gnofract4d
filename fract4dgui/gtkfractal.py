#!/usr/bin/env python3

# Subclass of fract4d.fractal.T which works with a GUI

import sys
import os
import struct
import math
import copy
import random

import gtk
import gobject

from fract4d import fractal,fract4dc,fracttypes, image, messages

from . import utils, fourway
from .gtkio import gtkio

class Hidden(gobject.GObject):
    """This class implements a fractal which calculates asynchronously
    and is integrated with the GTK main loop"""
    __gsignals__ = {
        'parameters-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, ()),
        'iters-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'tolerance-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_FLOAT,)),    
        'formula-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, ()),
        'status-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'progress-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_FLOAT,)),
        'pointer-moved' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_INT,
                            gobject.TYPE_FLOAT, gobject.TYPE_FLOAT)),
        'stats-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
            
        }

    def __init__(self,comp,width,height,total_width=-1,total_height=-1):
        gobject.GObject.__init__(self)

        if 'win' == sys.platform[:3]:
            (self.readfd, self.writefd) = fract4dc.pipe()
        else:
            # This is the line that was screwing Windows up.. changed to be run only on Linux, for Windows, we want to do this in fract4dc..
            (self.readfd, self.writefd) = os.pipe()
        self.nthreads = 1

        self.compiler = comp

        self.x = self.y = 0
        self.button = 0
        self.last_progress = 0.0
        self.skip_updates = False
        self.running = False
        self.frozen = False # if true, don't emit signals

        self.site = fract4dc.fdsite_create(self.writefd)
        self.f = None
        self.try_init_fractal()

        self.input_add(self.readfd, self.onData)
        
        self.width = width
        self.height = height
        self.image = image.T(
            self.width,self.height,total_width,total_height)

        self.msgbuf = ""
        self.io_subsys = gtkio();

    def try_init_fractal(self):
        f = fractal.T(self.compiler,self.site)
        self.set_fractal(f)
        self.f.compile()

    def set_fractal(self,f):
        if f != self.f:
            if self.f:
                self.interrupt()
                del self.f
            self.f = f

            # take over fractal's changed function
            f.changed = self.changed
            f.formula_changed = self.formula_changed
            f.warn = self.warn
            self.formula_changed()
            self.changed()

    def changed(self,clear_image=True):
        if self.f == None:
            return
        self.f.dirty=True
        self.f.clear_image = clear_image
        self.set_saved(False)
        if not self.frozen:
            self.emit('parameters-changed')
        
    def formula_changed(self):
        #print "formula changed"
        self.f.dirtyFormula = True
        #if not self.frozen:
        self.emit('formula-changed')
            
    def set_saved(self,val):
        if self.f != None:
            self.f.saved = val
        
    def input_add(self,fd,cb):
        utils.input_add(fd,cb)

    def error(self,msg,err):
        print("Error: %s %s" % (msg,err))
        
    def warn(self,msg):
        print("Warning: ", msg)

    def update_formula(self):
        if self.f != None:
            self.f.dirtyFormula = True
        
    def freeze(self):
        self.frozen = True
        
    def thaw(self):
        if self.f == None:
            return False
        
        self.frozen = False
        was_dirty = self.f.dirty
        self.f.clean()
        return was_dirty

    def interrupt(self):
        if self.skip_updates:
            #print "skip recursive interrupt"
            return
        
        self.skip_updates = True
        
        fract4dc.interrupt(self.site)

        n = 0
        # wait for stream from worker to flush
        while self.running:
            n += 1
            gtk.main_iteration(True)

        self.skip_updates = False

    def copy_f(self):
        return copy.copy(self.f)

    def set_formula(self, fname, formula,index=0):
        self.f.set_formula(fname, formula,index)

    def onData(self,fd,condition):
        self.msgbuf = self.msgbuf + self.io_subsys.read(fd, 8 - len(self.msgbuf))

        if len(self.msgbuf) < 8:            
            #print "incomplete message: %s" % list(self.msgbuf)
            return True

        (t,size) = struct.unpack("2i",self.msgbuf)
        self.msgbuf = ""
        bytes = self.io_subsys.read(fd,size)
        if len(bytes) < size:
            print("not enough bytes, got %d instead of %d" % (len(bytes),size))
            return True

        m = messages.parse(t,bytes)

        if utils.threads_enabled:
            gtk.gdk.threads_enter()    

        #print "msg: %s %d %d %d %d" % (m,p1,p2,p3,p4)
        if t == fract4dc.MESSAGE_TYPE_ITERS:
            if not self.skip_updates: self.iters_changed(m.iterations)
        elif t == fract4dc.MESSAGE_TYPE_IMAGE:
            if not self.skip_updates: self.image_changed(m.x, m.y, m.w, m.h)
        elif t == fract4dc.MESSAGE_TYPE_PROGRESS:
            if not self.skip_updates:
                progress = m.progress
                # filters out 'backwards' progress which can occur due to threading
                if progress > self.last_progress or progress == 0.0:
                    self.progress_changed(progress)
                    self.last_progress = progress
        elif t == fract4dc.MESSAGE_TYPE_STATUS:
            if m.status == fract4dc.CALC_DONE: # DONE
                self.running = False
            if not self.skip_updates: self.status_changed(m.status)
        elif t == fract4dc.MESSAGE_TYPE_PIXEL:
            # FIXME pixel_changed
            pass
        elif t == fract4dc.MESSAGE_TYPE_TOLERANCE:
            # tolerance changed
            if not self.skip_updates: self.tolerance_changed(m.tolerance)
        elif t == fract4dc.MESSAGE_TYPE_STATS:
            if not self.skip_updates: self.stats_changed(m)
        else:
            print("Unknown message from fractal thread; %s" % list(bytes))

        if utils.threads_enabled:
            gtk.gdk.threads_leave()
        return True
    
    def __getattr__(self,name):
        return getattr(self.f,name)

    def params(self):
        return self.f.params
    
    def get_param(self,n):
        return self.f.get_param(n)
    
    def set_nthreads(self, n):
        if self.nthreads != n:
            self.nthreads = n
            self.changed()
            
    def set_auto_deepen(self,deepen):
        if self.f.auto_deepen != deepen:
            self.f.auto_deepen = deepen
            self.changed()
            
    def set_antialias(self,aa_type):
        if self.f.antialias != aa_type:
            self.f.antialias = aa_type
            self.changed()
        
    def set_func(self,func,fname,formula):
        self.f.set_func(func,fname,formula)
        
    def improve_quality(self):
        self.freeze()
        self.set_maxiter(self.f.maxiter*2)
        self.set_period_tolerance(self.f.period_tolerance / 10.0)
        self.thaw()
        self.changed()

    def reset(self):
        self.f.reset()
        self.changed()

    def loadFctFile(self,file):
        new_f = fractal.T(self.compiler,self.site)
        new_f.warn = self.warn
        new_f.loadFctFile(file)
        self.set_fractal(new_f)
        self.set_saved(True)

    def is_saved(self):
        if self.f == None:
            return True
        return self.f.saved
    
    def save_image(self,filename):
        self.image.save(filename)
        
    def progress_changed(self,progress):
        self.emit('progress-changed',progress)
        
    def status_changed(self,status):
        self.emit('status-changed',status)
        
    def iters_changed(self,n):
        self.f.maxiter = n
        # don't emit a parameters-changed here to avoid deadlock
        self.emit('iters-changed',n)
        
    def tolerance_changed(self,tolerance):
        self.f.period_tolerance = tolerance
        self.emit('tolerance-changed', tolerance)

    def image_changed(self,x1,y1,x2,y2):
        pass 

    def stats_changed(self,stats):
        self.emit('stats-changed', stats)

    def draw(self,image,width,height,nthreads):
        t = self.f.epsilon_tolerance(width,height)
        if self.f.auto_epsilon:
            self.f.set_named_param("@epsilon",t,
                                   self.f.formula, self.f.initparams)

        self.f.init_pfunc()
        cmap = self.f.get_colormap()
        self.running = True
        try:
            self.f.calc(image,cmap, nthreads, self.site, True)            
        except MemoryError:
            pass
        
    def draw_image(self,aa=None,auto_deepen=None):
        if self.f == None:
            return
        self.interrupt()

        self.f.compile()

        if aa != None and auto_deepen != None:
            self.f.antialias = aa
            self.f.auto_deepen = auto_deepen

        self.draw(self.image,self.width,self.height,self.nthreads)

    def set_plane(self,angle1,angle2):
        self.freeze()
        self.reset_angles()
        if angle1 != None:
            self.set_param(angle1,math.pi/2)
        if angle2 != None:
            self.f.set_param(angle2,math.pi/2)
            
        if self.thaw():
            self.changed()

    def float_coords(self,x,y):
        return ((x - self.width/2.0)/self.width,
                (y - self.height/2.0)/self.width)
    
    def recenter(self,x,y,zoom):
        dx = (x - self.width/2.0)/self.width
        dy = (y - self.height/2.0)/self.width                
        self.relocate(dx,dy,zoom)
        
    def count_colors(self,rect):
        # calculate the number of different colors which appear
        # in the subsection of the image bounded by the rectangle
        (xstart,ystart,xend,yend) = rect
        buf = self.image.image_buffer(0,0)
        colors = {}
        for y in range(ystart,yend):
            for x in range(xstart,xend):
                offset = (y*self.width+x)*3
                col = buf[offset:offset+3]
                colors[col] = 1 + colors.get(col,0)
        return len(colors)

    def get_func_name(self):
        if self.f == None:
            return _("No fractal loaded")
        return self.f.forms[0].funcName

    def get_saved(self):
        if self.f == None:
            return True
        return self.f.get_saved()

    def serialize(self,compress=False):
        if self.f == None:
            return None
        return self.f.serialize(compress)

    def set_size(self, new_width, new_height):
        self.interrupt()
        if self.width == new_width and self.height == new_height :
            return
        
        self.width = new_width
        self.height = new_height

        self.image.resize_full(new_width, new_height)
        utils.idle_add(self.changed)

# explain our existence to GTK's object system
gobject.type_register(Hidden)

class HighResolution(Hidden):
    "An invisible GtkFractal which computes in multiple chunks"
    def __init__(self,comp,width,height):
        (tile_width, tile_height) = self.compute_tile_size(width,height)

        Hidden.__init__(self,comp,tile_width, tile_height, width,height)
        self.reset_render()

    def reset_render(self):
        self.tile_list = self.image.get_tile_list()
        self.ntiles = len(self.tile_list)
        self.ncomplete_tiles = 0
        self.last_overall_progress = 0.0
        
    def compute_tile_size(self,w,h):
        tile_width = w
        tile_height = min(h,128)
        return (tile_width, tile_height)

    def draw_image(self,name):
        if self.f == None:
            return
        self.interrupt()

        self.f.compile()
        
        self.f.auto_deepen = False
        self.f.auto_tolerance = False
        self.image.start_save(name)
        self.next_tile()
        return False

    def next_tile(self):
        # work left to do
        (xoff,yoff,w,h) = self.tile_list.pop(0)
        self.image.resize_tile(w,h)
        self.image.set_offset(xoff,yoff)        
        self.draw(self.image,w,h,self.nthreads)
        
    def status_changed(self,status):
        if status == 0:
            # done this chunk
            self.image.save_tile()
            self.ncomplete_tiles += 1
            if len(self.tile_list) > 0:
                self.next_tile()
            else:
                # completely done
                self.image.finish_save()
                self.emit('status-changed',status)
        else:
            self.emit('status-changed',status)

    def progress_changed(self,progress):
        overall_progress = (100.0*self.ncomplete_tiles + progress)/self.ntiles
        if overall_progress > self.last_overall_progress:
            self.emit('progress-changed',overall_progress)
            self.last_overall_progress = overall_progress

class T(Hidden):
    "A visible GtkFractal which responds to user input"
    def __init__(self,comp,parent=None,width=640,height=480):
        self.parent = parent
        Hidden.__init__(self,comp,width,height)

        self.paint_mode = False
                
        drawing_area = gtk.DrawingArea()
        drawing_area.set_events(
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.BUTTON1_MOTION_MASK |
            gtk.gdk.POINTER_MOTION_MASK |
            gtk.gdk.POINTER_MOTION_HINT_MASK |
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.KEY_PRESS_MASK |
            gtk.gdk.KEY_RELEASE_MASK |
            gtk.gdk.EXPOSURE_MASK
            )

        self.notice_mouse = False

        drawing_area.connect('motion_notify_event', self.onMotionNotify)
        drawing_area.connect('button_release_event', self.onButtonRelease)
        drawing_area.connect('button_press_event', self.onButtonPress)
        drawing_area.connect('expose_event',self.onExpose)

        c = utils.get_rgb_colormap()
        
        drawing_area.set_colormap(c)        
        drawing_area.set_size_request(self.width,self.height)

        self.widget = drawing_area

    def image_changed(self,x1,y1,x2,y2):
        self.redraw_rect(x1,y1,x2-x1,y2-y1)

#    def changed(self):
#        Hidden.changed(self)
#        try:
#            widget = self.widget
#        except Exception, e:
#            return
#        self.widget.queue_draw_area(0, 0, self.width, self.height)
#        #self.expose()

    def make_numeric_entry(self, form, param, order):
        param_type = form.paramtypes[order]

        if param.type == fracttypes.Int:
            fmt = "%d"
        else:
            fmt = "%.17f"

        widget = gtk.Entry()
        widget.set_activates_default(True)

        def set_entry():
            new_value = fmt % form.params[order]
            if widget.get_text() != new_value:
                widget.set_text(new_value)

        def set_fractal(entry,event,form,order):
            try:
                utils.idle_add(
                    form.set_param,order,entry.get_text())
            except Exception as err:
                # FIXME: produces too many errors
                msg = "Invalid value '%s': must be a number" % \
                      entry.get_text()
                print(msg)
                #utils.idle_add(f.warn,msg)
            return False

        set_entry()

        widget.set_data("update_function", set_entry)

        widget.f = self
        widget.connect('focus-out-event',
                       set_fractal,form,order)
        
        if hasattr(param, "min") and hasattr(param, "max"):
            # add a slider
            adj = gtk.Adjustment(
                0.0,param.min.value, param.max.value,
                0.001, 
                0.01)

            def set_adj():
                if adj.value != form.params[order]:
                    adj.set_value(form.params[order])

            set_adj()
            def adj_changed(adjustment,form,order):
                utils.idle_add(
                    form.set_param, order, adjustment.value)

            adj.connect('value-changed', adj_changed, form, order)

            hscale = gtk.HScale(adj)
            hscale.set_draw_value(False)
            hscale.set_update_policy(gtk.UPDATE_DELAYED)
            hscale.set_data("update_function",set_adj)
            vbox = gtk.VBox()
            vbox.pack_start(widget)
            vbox.pack_start(hscale)
            return vbox

        return widget

    def make_numeric_widget(
        self, table, i, form, name, part, param, order):
    
        label = gtk.Label(self.param_display_name(name,param)+part)
        label.set_alignment(1.0, 0.0)
        table.attach(label,0,1,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)

        widget = self.make_numeric_entry(
            form, param, order)

        label.set_mnemonic_widget(widget)
        return widget
    
    def make_bool_widget(self, form, name, param, order):

        widget = gtk.CheckButton(self.param_display_name(name,param))

        def set_toggle(*args):
            is_set = form.params[order]
            widget.set_active(is_set)
            if widget.get_active() != is_set:
                widget.set_active(is_set)

        def set_fractal(entry,form,order):
            try:
                utils.idle_add(form.set_param,order,entry.get_active())
            except Exception as err:
                msg = "error setting bool param: %s" % str(err)
                print(msg)
                utils.idle_add(f.warn,msg)

            return False

        set_toggle(self)

        widget.set_data("update_function", set_toggle)
        widget.f = self
        widget.connect('toggled', set_fractal, form, order)
        return widget

    def make_color_widget(
        self, table, i, form, name, param, order):

        label = gtk.Label(self.param_display_name(name,param))
        label.set_alignment(1.0, 0.0)
        table.attach(label,0,1,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)

        def set_fractal(r, g, b, is_left):
            self.freeze()
            form.set_param(order, r)
            form.set_param(order+1, g)
            form.set_param(order+2, b)
            if self.thaw():
                self.changed()
                

        rgba = []
        for j in range(4):
            rgba.append(form.params[order+j])

        # do we need to keep this ref?
        color_button = utils.ColorButton(rgba, set_fractal, False)

        def set_selected_value(*args):
            rgba = []
            for j in range(4):
                rgba.append(form.params[order+j])
            color_button.set_color(rgba)
            
        set_selected_value()
        
        color_button.widget.set_data("update_function", set_selected_value)

        return color_button.widget

    def make_enumerated_widget(
        self, table, i, form, name, part, param, order):

        label = gtk.Label(self.param_display_name(name,param))
        label.set_alignment(1.0, 0.0)
        table.attach(label,0,1,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)

        widget = utils.create_option_menu(param.enum.value)

        def set_selected_value(*args):
            try:
                index = form.params[order]
            except ValueError as err:
                print(err)
                return

            utils.set_selected(widget, index)
            
        def set_fractal(entry,form,order):
            new_value = utils.get_selected(widget)
            form.set_param(order, new_value)
            
        set_selected_value(self)

        widget.set_data("update_function", set_selected_value)

        widget.f = self
        widget.connect('changed',
                       set_fractal,form,order)

        label.set_mnemonic_widget(widget)
        return widget

    def add_formula_setting(
        self,table,i,form,name,part,param,order):
        
        if param.type == fracttypes.Int:
            if hasattr(param,"enum"):
                widget = self.make_enumerated_widget(
                    table, i,form,name,part,param,order)
            else:
                widget = self.make_numeric_widget(
                    table, i,form,name,part,param,order)
                
        elif param.type == fracttypes.Float or \
             param.type == fracttypes.Complex or \
             param.type == fracttypes.Hyper:

            widget = self.make_numeric_widget(
                table, i, form, name,part,param,order)
        elif param.type == fracttypes.Bool:
            widget = self.make_bool_widget(
                form, name,param,order)
        elif param.type == fracttypes.Color:
            widget = self.make_color_widget(
                table,i,form,name,param,order)
        elif param.type == fracttypes.Image:
            # skip image params for now
            return
        else:
            raise "Unsupported parameter type"

        table.attach(widget,1,2,i,i+1,gtk.EXPAND | gtk.FILL ,0,0,0)


    def add_complex_formula_setting(
        self,table,i,form,name,param,order,param_type):
        
        widget = self.make_numeric_entry(
                form,param,order)

        table.attach(widget,1,2,i,i+1,gtk.EXPAND | gtk.FILL ,0,0,0)

        widget = self.make_numeric_entry(
                form,param,order+1)

        table.attach(widget,1,2,i+1,i+2,gtk.EXPAND | gtk.FILL ,0,0,0)

        name = self.param_display_name(name,param)
        fway = fourway.T(name)
        tip = self.param_tip(name,param)
        fway.widget.set_tooltip_text(tip)
        
        fway.connect('value-changed',self.fourway_released, order, form)

        if self.parent:
            fway.connect(
                'value-slightly-changed',
                self.parent.on_drag_param_fourway, order, param_type)
        
        table.attach(fway.widget,0,1,i,i+2, gtk.EXPAND|gtk.FILL,0, 0,0)

    def fourway_released(self,widget,x,y,order,form):
        form.nudge_param(order, x,y)

    def construct_function_menu(self,param,form):
        funclist = form.formula.symbols.available_param_functions(
            param.ret,param.args)
        funclist.sort()
        return funclist
    
    def set_nthreads(self, n):
        if self.nthreads != n:
            self.nthreads = n
            self.changed()
    
    def error(self,msg,err):
        print(self, self.parent)
        if self.parent:
            self.parent.show_error_message(msg, err)
        else:
            print("Error: %s : %s" % (msg,err))
        
    def warn(self,msg):
        if self.parent:
            self.parent.show_warning(msg)
        else:
            print("Warning: ", msg)

    def add_formula_function(self,table,i,name,param,form):
        label = gtk.Label(self.param_display_name(name,param))
        label.set_alignment(1.0, 0.0)
        table.attach(label,0,1,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)

        funclist = self.construct_function_menu(param,form)
        widget = utils.create_option_menu(funclist)

        formula = form.formula
        def set_selected_function():
            try:
                selected_func_name = form.get_func_value(name)
                index = funclist.index(selected_func_name)
            except ValueError as err:
                # func.cname not in list
                #print "bad cname"
                return
            
            utils.set_selected(widget, index)
            
        def set_fractal_function(om,f,param,formula):
            index = utils.get_selected(om)
            if index != -1:
                # this shouldn't be necessary but I got weird errors
                # trying to reuse the old funclist
                list = formula.symbols.available_param_functions(
                    param.ret,param.args)
                list.sort()

                fname = list[index]
                f.set_func(param,fname,formula)
                
        set_selected_function()

        widget.set_data("update_function", set_selected_function)

        widget.connect('changed',set_fractal_function,self,param,formula)
        
        table.attach(widget,1,2,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)

    def create_maxiter_widget(self,table,i):
        label = gtk.Label("_Max Iterations")
        label.set_alignment(1.0, 0.0)
        label.set_use_underline(True)
        table.attach(label,0,1,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)

        widget = gtk.Entry()
        widget.set_activates_default(True)
        
        def set_entry(*args):
            widget.set_text("%d" % self.f.maxiter)

        def set_fractal(*args):
            try:
                try:
                    i = int(widget.get_text())
                    self.set_maxiter(i)
                except ValueError as err:
                    msg = "Invalid value '%s': must be a number" % \
                          widget.get_text()
                    utils.idle_add(self.warn, msg)
            except Exception as exn:
                print(exn)
            return False

        set_entry(self)

        self.connect('parameters-changed', set_entry)
        self.connect('iters-changed', set_entry)
        widget.connect('focus-out-event',set_fractal)

        label.set_mnemonic_widget(widget)
        table.attach(widget,1,2,i,i+1,gtk.EXPAND | gtk.FILL,0,0,0)
        return i+1

    def populate_formula_settings(self, table, param_type, row=0):
        # create widget to fiddle with this fractal's settings
        form = self.f.get_form(param_type)
        formula = form.formula
        
        if param_type == 0:
            row = self.create_maxiter_widget(table,row)
            
        params = formula.symbols.parameters()
        op = formula.symbols.order_of_params()

        keys = list(params.keys())
        keys.sort()
        for name in keys:
            param = params[name]
            if isinstance(param,fracttypes.Func):
                self.add_formula_function(table,row,name,param,form)
            else:
                if param.type == fracttypes.Complex:
                    self.add_complex_formula_setting(
                        table,row,form,name,param,
                        op[name],
                        param_type)
                    row+= 1
                elif param.type == fracttypes.Hyper:
                    suffixes = [" (re)", " (i)", " (j)", " (k)"]
                    for j in range(4):
                        self.add_formula_setting(
                            table,row+j,form,name,suffixes[j],
                            param,op[name]+j)
                    row += 3
                elif param.type == fracttypes.Color:
                    self.add_formula_setting(
                        table,row, form, name,"",
                        param,op[name])
                    row += 3
                elif param.type == fracttypes.Gradient:
                    # FIXME
                    pass
                else:
                    self.add_formula_setting(
                        table,row,form,name,"",param,op[name])
            row += 1
        return table

    def set_size(self, new_width, new_height):
        try:
            Hidden.set_size(self,new_width, new_height)
            self.widget.set_size_request(new_width,new_height)
        except MemoryError as err:
            utils.idle_add(self.warn,str(err))
                    
    def draw_image(self,aa=None,auto_deepen=None):
        try:
            Hidden.draw_image(self,aa,auto_deepen)
        except fracttypes.TranslationError as err:
            advice = _("\nCheck that your compiler settings and formula file are correct.")
            utils.idle_add(self.error,
                           _("Error compiling fractal:"),
                           err.msg + advice)
            return

    def onExpose(self,widget,exposeEvent):
        r = exposeEvent.area
        self.redraw_rect(r.x,r.y,r.width,r.height)

    def onMotionNotify(self,widget,event):
        (x,y) = self.float_coords(event.x, event.y)
        self.emit('pointer-moved', self.button, x, y)

        if not self.notice_mouse:
            return

        self.redraw_rect(0,0,self.width,self.height)
        (self.newx,self.newy) = (event.x, event.y)

        dummy = widget.window.get_pointer()

        dy = int(abs(self.newx - self.x) * float(self.height)/self.width)
        if(self.newy < self.y or (self.newy == self.y and self.newx < self.x)):
            dy = -dy
        self.newy = self.y + dy;

        widget.window.draw_rectangle(
            self.widget.get_style().white_gc,
            False,
            int(min(self.x,self.newx)),
            int(min(self.y,self.newy)),
            int(abs(self.newx-self.x)),
            int(abs(self.newy-self.y)));

    def onButtonPress(self,widget,event):
        self.x = event.x
        self.y = event.y
        self.newx = self.x
        self.newy = self.y
        self.button = event.button
        if self.button == 1:
            self.notice_mouse = True
        
    def set_paint_mode(self,isEnabled, colorsel):
        self.paint_mode = isEnabled
        self.paint_color_sel = colorsel
        
    def get_paint_color(self):
        color = self.paint_color_sel.get_current_color() 
        return (color.red/65535.0, color.green/65535.0, color.blue/65535.0)
    
    def onPaint(self,x,y):
        # obtain index
        fate = self.image.get_fate(int(x), int(y))
        if not fate:
            return

        index = self.image.get_color_index(int(x), int(y))
        
        # obtain a color
        (r,g,b) = self.get_paint_color()
        
        # update colormap
        grad = self.f.get_gradient()

        (is_solid, color) = fate
        if is_solid:
            self.f.solids[color] = (int(r*255.0),int(g*255.0),int(b*255.0),255)
        else:
            i = grad.get_index_at(index)
            if index > grad.segments[i].mid:
                alpha = grad.segments[i].right_color[3]
                grad.segments[i].right_color = [r, g, b, alpha]
            else:
                alpha = grad.segments[i].left_color[3]
                grad.segments[i].left_color = [r, g, b, alpha]

        self.changed(False)

    def filterPaintModeRelease(self,event):
        if self.paint_mode:
            if event.button == 1:
                if self.x == self.newx or self.y == self.newy:
                    self.onPaint(self.newx, self.newy)
                    return True
        
        return False
    
    def onButtonRelease(self,widget,event):
        self.redraw_rect(0,0,self.width,self.height)
        self.button = 0
        self.notice_mouse = False
        if self.filterPaintModeRelease(event):
            return
        
        self.freeze()
        if event.button == 1:
            if self.x == self.newx or self.y == self.newy:
                zoom=0.5
                x = self.x
                y = self.y
            else:
                zoom= (1+abs(self.x - self.newx))/float(self.width)
                x = 0.5 + (self.x + self.newx)/2.0;
                y = 0.5 + (self.y + self.newy)/2.0;

            # with shift held, don't zoom
            if hasattr(event,"state") and event.state & gtk.gdk.SHIFT_MASK:
                zoom = 1.0
            self.recenter(x,y,zoom)
            
        elif event.button == 2:
            (x,y) = (event.x, event.y)
            zoom = 1.0
            self.recenter(x,y,zoom)
            if self.is4D():
                self.flip_to_julia()
            
        else:
            if hasattr(event,"state") and event.state & gtk.gdk.CONTROL_MASK:
                zoom = 20.0
            else:
                zoom = 2.0
            (x,y) = (event.x, event.y)
            self.recenter(x,y,zoom)

        if self.thaw():
            self.changed()

    def redraw_rect(self,x,y,w,h):
        # check to see if part of the rect is out-of-bounds, and clip if so
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x+w > self.width:
            w = self.width-x
        if y+h > self.height:
            h = self.height-y

        if x >= self.width or y >= self.height or w < 1 or h < 1:
            # nothing to do
            return
        
        gc = self.widget.get_style().white_gc

        try:
            buf = self.image.image_buffer(x,y)
        except MemoryError as err:
            # suppress these errors
            return
        
        if self.widget.window:
            self.widget.window.draw_rgb_image(
                gc,
                x, y,
                min(self.width-x,w),
                min(self.height-y,h),
                gtk.gdk.RGB_DITHER_NONE,
                buf,
                self.width*3)

class Preview(T):
    def __init__(self,comp,width=120,height=90):
        T.__init__(self,comp,None,width,height)

    def onButtonRelease(self,widget,event):
        pass

    def error(self,msg,exn):
        # suppress errors from previews
        pass
    
    def stats_changed(self,s):
        pass

class SubFract(T):
    def __init__(self,comp,width=640,height=480):
        T.__init__(self,comp,None,width,height)
        self.master = None
        
    def set_master(self,master):
        self.master = master
        
    def onButtonRelease(self,widget,event):
        self.button = 0
        if self.master:
            self.master.set_fractal(self.copy_f())

    def onMotionNotify(self, widget, event):
        pass

    def error(self,msg,exn):
        # suppress errors from subfracts, if they ever happened
        # it would be too confusing
        pass
