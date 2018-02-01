# Sort of a widget which controls an angle of the fractal
# I say sort of, because this doesn't actually inherit from Gtk.Widget,
# so it's not really a widget. This is because if I attempt to do that
# pygtk crashes. Hence I delegate to a member which actually is a widget
# with some stuff drawn on it - basically an ungodly hack.

import gi
gi.require_version('Gtk', '3.0') 
from gi.repository import Gtk, Gdk, GObject, Pango
import math

class T(GObject.GObject):
    __gsignals__ = {
        'value-changed' : (
        (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
        None, (GObject.TYPE_DOUBLE,)),
        'value-slightly-changed' : (
        (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
        None, (GObject.TYPE_DOUBLE,))
        }
    two_pi = 2.0 * math.pi
    ptr_radius = 4
    
    def __init__(self,text):
        self.radius = 0
        self.text=text
        
        self.adjustment = Gtk.Adjustment(value=0, lower=-math.pi, upper=math.pi, step_increment=0.01, page_increment=0.01, page_size=0)

        self.old_value = self.adjustment.get_value()
        
        self.adjustment.connect('value-changed', self.onAdjustmentValueChanged)
                
        GObject.GObject.__init__(self)
        
        self.widget = Gtk.DrawingArea()
        self.widget.set_size_request(40,40)

        self.widget.set_events(
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.BUTTON1_MOTION_MASK |
            Gdk.EventMask.POINTER_MOTION_HINT_MASK |
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |                               
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.EXPOSURE_MASK
            )

        self.notice_mouse = False
        self.widget.connect('motion_notify_event', self.onMotionNotify)
        self.widget.connect('button_release_event', self.onButtonRelease)
        self.widget.connect('button_press_event', self.onButtonPress)
        self.widget.connect('draw',self.onDraw)

    def set_value(self,val):
        val = math.fmod(val + math.pi, 2.0 * math.pi) - math.pi
        self.adjustment.set_value(val)
        self.widget.queue_draw()
        
    def update_from_mouse(self,x,y):        
        (w,h) = (self.widget.get_allocated_width(), self.widget.get_allocated_height())
        
        xc = w//2
        yc = h//2

        angle = self.angle_from_xy(x-xc,y-yc)
        self.adjustment.set_value(angle)

    def angle_from_xy(self,x,y):
        angle = math.atan2(y,x)
        #angle = math.fmod(angle,T.two_pi)
        return angle
    
    def onAdjustmentValueChanged(self,adjustment):
        val = adjustment.get_value()
        if val != self.old_value:
            self.widget.queue_draw()
            self.emit('value-slightly-changed', val)
            
    def onMotionNotify(self,widget,event):
        if not self.notice_mouse:
            return
        dummy = widget.get_pointer()
        self.update_from_mouse(event.x, event.y)

    def onButtonRelease(self,widget,event):
        if event.button==1:
            self.notice_mouse = False
            (xc,yc) = (widget.get_allocated_width()//2, widget.get_allocated_height()//2)
            current_value = self.adjustment.get_value()
            if self.old_value != current_value:
                self.old_value = current_value
                self.emit('value-changed',current_value)

        self.widget.set_state(Gtk.StateType.NORMAL)

        
    def onButtonPress(self,widget,event):
        if event.button == 1:
            self.notice_mouse = True
            self.update_from_mouse(event.x, event.y)
            self.widget.set_state(Gtk.StateType.ACTIVE)

        
    def __del__(self):
        #This is truly weird. If I don't have this method, when you use
        # one fourway widget, it fucks up the other. Having this fixes it.
        # *even though it doesn't do anything*. Disturbing.
        pass

    def get_current_angle(self):
        value = self.adjustment.get_value()
        return value

    def pointer_coords(self, radius, angle):
        s = math.sin(angle)
        c = math.cos(angle)

        ptr_xc = c * (radius - T.ptr_radius)
        ptr_yc = s * (radius - T.ptr_radius)
        return (ptr_xc, ptr_yc)
        
    def onDraw(self, widget, cairo_ctx):
        self.redraw_rect(widget, cairo_ctx)
        
    def redraw_rect(self, widget, cairo_ctx):
        style_ctx = widget.get_style_context()
        (w,h) = (widget.get_allocated_width(), widget.get_allocated_height())
        
        xc = w//2
        yc = h//2
        radius = min(w,h)//2 - 1

        # text
        pango_ctx = widget.get_pango_context()
        layout = Pango.Layout(pango_ctx)
        layout.set_text(self.text,len(self.text))
        (text_width, text_height) = layout.get_pixel_size()
        Gtk.render_layout(style_ctx,
            cairo_ctx,
            xc - text_width//2,
            yc - text_height//2,
            layout)
        cairo_ctx.new_path()

        # outer circle
        cairo_ctx.arc(
            xc,
            yc,
            radius - 1,
            0,
            self.two_pi)
        cairo_ctx.set_line_width(1)
        cairo_ctx.stroke()

        # inner circle indicating current angle
        angle = self.get_current_angle()
        (ptr_xc, ptr_yc) = self.pointer_coords(radius - 2, angle)
        
        cairo_ctx.arc(
            int(xc + ptr_xc),
            int(yc + ptr_yc),
            T.ptr_radius,
            0,
            self.two_pi)
        cairo_ctx.fill()
        cairo_ctx.stroke()
        
# explain our existence to GTK's object system
GObject.type_register(T)
