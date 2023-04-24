# A widget which controls an angle of the fractal

import math

from gi.repository import Gtk, GObject, Graphene, Pango


class T(Gtk.Widget):
    __gsignals__ = {
        'value-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_DOUBLE,)),
        'value-slightly-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_DOUBLE,))
    }
    two_pi = 2.0 * math.pi
    ptr_radius = 4

    def __init__(self, text, tip, axis, size):
        self.axis = axis
        self.radius = 0
        self.text = text

        self.adjustment = Gtk.Adjustment(
            value=0,
            lower=-math.pi,
            upper=math.pi,
            step_increment=0.01,
            page_increment=0.01,
            page_size=0)

        self.old_value = self.adjustment.get_value()

        self.adjustment.connect('value-changed', self.onAdjustmentValueChanged)

        super().__init__(
            tooltip_text=tip, width_request=size, height_request=size)

        event_controller_gesture = Gtk.GestureDrag()
        self.add_controller(event_controller_gesture)

        event_controller_gesture.connect("drag_begin", self.onButtonPress)
        event_controller_gesture.connect("drag_update", self.onMotionNotify)
        event_controller_gesture.connect("drag_end", self.onButtonRelease)

    def set_value(self, val):
        val = math.fmod(val + math.pi, 2.0 * math.pi) - math.pi
        self.adjustment.set_value(val)
        self.queue_draw()

    def update_from_mouse(self, x, y):
        (w, h) = (self.get_allocated_width(), self.get_allocated_height())

        xc = w // 2
        yc = h // 2

        angle = self.angle_from_xy(x - xc, y - yc)
        self.adjustment.set_value(angle)

    def angle_from_xy(self, x, y):
        angle = math.atan2(y, x)
        return angle

    def onAdjustmentValueChanged(self, adjustment):
        val = adjustment.get_value()
        if val != self.old_value:
            self.queue_draw()
            self.emit('value-slightly-changed', val)

    def onMotionNotify(self, gesture, offset_x, offset_y):
        active, start_x, start_y = gesture.get_start_point()
        self.update_from_mouse(start_x + offset_x, start_y + offset_y)

    def onButtonRelease(self, gesture, offset_x, offset_y):
        current_value = self.adjustment.get_value()
        if self.old_value != current_value:
            self.old_value = current_value
            self.emit('value-changed', current_value)
        self.set_state_flags(Gtk.StateFlags.NORMAL, True)

    def onButtonPress(self, gesture, start_x, start_y):
        self.update_from_mouse(start_x, start_y)
        self.set_state_flags(Gtk.StateFlags.ACTIVE, True)

    def get_current_angle(self):
        value = self.adjustment.get_value()
        return value

    def pointer_coords(self, radius, angle):
        s = math.sin(angle)
        c = math.cos(angle)

        ptr_xc = c * (radius - T.ptr_radius)
        ptr_yc = s * (radius - T.ptr_radius)
        return (ptr_xc, ptr_yc)

    def do_snapshot(self, s):
        w, h = self.get_width(), self.get_height()
        rect = Graphene.Rect()
        rect.init(0, 0, w, h)
        color = self.get_style_context().get_color()

        cairo_ctx = s.append_cairo(rect)
        cairo_ctx.set_source_rgb(color.red, color.blue, color.green)

        xc = w // 2
        yc = h // 2
        radius = min(w, h) // 2 - 1

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

        # text
        pango_ctx = self.get_pango_context()
        layout = Pango.Layout(pango_ctx)
        layout.set_text(self.text, len(self.text))
        (text_width, text_height) = layout.get_pixel_size()

        point = Graphene.Point()
        point.init(xc - text_width // 2, yc - text_height // 2)
        s.translate(point)

        s.append_layout(layout, color)
