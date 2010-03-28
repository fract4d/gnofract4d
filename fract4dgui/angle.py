# Sort of a widget which controls an angle of the fractal
# I say sort of, because this doesn't actually inherit from gtk.Widget,
# so it's not really a widget. This is because if I attempt to do that
# pygtk crashes. Hence I delegate to a member which actually is a widget
# with some stuff drawn on it - basically an ungodly hack.

import gtk
import gobject
import pango
import math

class T(gobject.GObject):
    __gsignals__ = {
        'value-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_DOUBLE,)),
        'value-slightly-changed' : (
        (gobject.SIGNAL_RUN_FIRST | gobject.SIGNAL_NO_RECURSE),
        gobject.TYPE_NONE, (gobject.TYPE_DOUBLE,))
        }
    two_pi = 2.0 * math.pi
    ptr_radius = 4
    
    def __init__(self,text):
        self.radius = 0
        self.text=text
        
        self.adjustment = gtk.Adjustment(0, -math.pi, math.pi, 0.01, 0.01, 0)

        self.old_value = self.adjustment.get_value()
        
        self.adjustment.connect('value-changed', self.onAdjustmentValueChanged)
                
        gobject.GObject.__init__(self)
        
        self.widget = gtk.DrawingArea()
        self.widget.set_size_request(40,40)

        self.widget.set_events(
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.BUTTON1_MOTION_MASK |
            gtk.gdk.POINTER_MOTION_HINT_MASK |
            gtk.gdk.ENTER_NOTIFY_MASK |
            gtk.gdk.LEAVE_NOTIFY_MASK |                               
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.EXPOSURE_MASK
            )

        self.notice_mouse = False
        self.widget.connect('motion_notify_event', self.onMotionNotify)
        self.widget.connect('button_release_event', self.onButtonRelease)
        self.widget.connect('button_press_event', self.onButtonPress)
        self.widget.connect('expose_event',self.onExpose)

    def set_value(self,val):
        val = math.fmod(val + math.pi, 2.0 * math.pi) - math.pi
        self.adjustment.set_value(val)
        self.widget.queue_draw()
        
    def update_from_mouse(self,x,y):        
        (w,h) = (self.widget.allocation.width, self.widget.allocation.height)
        
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
        dummy = widget.window.get_pointer()
        self.update_from_mouse(event.x, event.y)

    def onButtonRelease(self,widget,event):
        if event.button==1:
            self.notice_mouse = False
            (xc,yc) = (widget.allocation.width//2, widget.allocation.height//2)
            current_value = self.adjustment.get_value()
            if self.old_value != current_value:
                self.old_value = current_value
                self.emit('value-changed',current_value)

        self.widget.set_state(gtk.STATE_NORMAL)

        
    def onButtonPress(self,widget,event):
        if event.button == 1:
            self.notice_mouse = True
            self.update_from_mouse(event.x, event.y)
            self.widget.set_state(gtk.STATE_ACTIVE)

        
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
        
    def onExpose(self,widget,exposeEvent):
        r = exposeEvent.area
        self.redraw_rect(widget,r)
        
    def redraw_rect(self,widget,r):
        style = widget.get_style()
        (w,h) = (widget.allocation.width, widget.allocation.height)
        
        xc = w//2
        yc = h//2
        radius = min(w,h)//2 - 1

        # text
        context = widget.get_pango_context()
        layout = pango.Layout(context)

        # some pygtk versions want 2 args, some want 1. sigh
        try:
            layout.set_text(self.text)
        except TypeError:
            layout.set_text(self.text,len(self.text))

        (text_width, text_height) = layout.get_pixel_size()
        style.paint_layout(
            widget.window,
            widget.state,
            True,
            r,
            widget,
            "",
            xc - text_width//2,
            yc - text_height//2,
            layout)

        # outer circle
        gc = style.fg_gc[widget.state]
        widget.window.draw_arc(
            gc,
            False,
            xc - radius,
            yc - radius,
            radius*2 - 1,
            radius*2 - 1,
            0,
            360 * 64)

        # inner circle indicating current angle
        angle = self.get_current_angle()
        (ptr_xc, ptr_yc) = self.pointer_coords(radius, angle)
        
        widget.window.draw_arc(
            gc,
            True,
            int(xc + ptr_xc - T.ptr_radius),
            int(yc + ptr_yc - T.ptr_radius),
            T.ptr_radius*2 - 1,
            T.ptr_radius*2 - 1,
            0,
            360 * 64)
        
# explain our existence to GTK's object system
gobject.type_register(T)
