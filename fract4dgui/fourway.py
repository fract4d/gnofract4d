# A widget which controls 2 linear dimensions of the fractal

from gi.repository import Gtk, GObject, Graphene, Pango


class T(Gtk.Widget):
    __gsignals__ = {
        'value-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_INT, GObject.TYPE_INT)),
        'value-slightly-changed': (
            (GObject.SignalFlags.RUN_FIRST | GObject.SignalFlags.NO_RECURSE),
            None, (GObject.TYPE_INT, GObject.TYPE_INT))
    }

    def __init__(self, text, tip, axis=None, size=53):
        self.axis = axis
        self.button = 0
        self.radius = 0
        self.last_x = 0
        self.last_y = 0
        self.text = text
        super().__init__(
            tooltip_text=tip, width_request=size, height_request=size)

        event_controller_gesture = Gtk.GestureDrag()
        self.add_controller(event_controller_gesture)

        event_controller_gesture.connect("drag_begin", self.onButtonPress)
        event_controller_gesture.connect("drag_update", self.onMotionNotify)
        event_controller_gesture.connect("drag_end", self.onButtonRelease)

    def update_from_mouse(self, x, y):
        dx = self.last_x - x
        dy = self.last_y - y
        if dx or dy:
            self.emit('value-slightly-changed', dx, dy)
            self.last_x = x
            self.last_y = y

    def onMotionNotify(self, gesture, offset_x, offset_y):
        active, start_x, start_y = gesture.get_start_point()
        self.update_from_mouse(start_x + offset_x, start_y + offset_y)

    def onButtonRelease(self, gesture, offset_x, offset_y):
        (xc, yc) = (self.get_allocated_width() // 2,
                    self.get_allocated_height() // 2)
        dx = xc - self.last_x
        dy = yc - self.last_y
        if dx or dy:
            self.emit('value-changed', dx, dy)

    def onButtonPress(self, gesture, start_x, start_y):
        self.last_x = self.get_allocated_width() / 2
        self.last_y = self.get_allocated_height() / 2
        self.update_from_mouse(start_x, start_y)

    def do_snapshot(self, s):
        w, h = self.get_width(), self.get_height()
        rect = Graphene.Rect()
        rect.init(0, 0, w, h)
        color = self.get_style_context().get_color()

        cairo_ctx = s.append_cairo(rect)
        cairo_ctx.set_source_rgb(color.red, color.blue, color.green)

        xc = w // 2
        yc = h // 2

        def triangle(points):
            cairo_ctx.move_to(*points[0])
            cairo_ctx.line_to(*points[1])
            cairo_ctx.line_to(*points[2])
            cairo_ctx.line_to(*points[0])
            cairo_ctx.fill()
            cairo_ctx.stroke()

        th = 8
        tw = 6

        # Triangle pointing left
        points = [
            (1, yc),
            (1 + th, yc - tw),
            (1 + th, yc + tw)]
        triangle(points)

        # pointing right
        points = [
            (w - 2, yc),
            (w - 2 - th, yc - tw),
            (w - 2 - th, yc + tw)]
        triangle(points)

        # pointing up
        points = [
            (xc, 1),
            (xc - tw, th),
            (xc + tw, th)]
        triangle(points)

        # pointing down
        points = [
            (xc, h - 2),
            (xc - tw, h - 2 - th),
            (xc + tw, h - 2 - th)]
        triangle(points)

        pango_ctx = self.get_pango_context()
        layout = Pango.Layout(pango_ctx)

        try:
            drawtext = self.text
        except AttributeError:
            print("fourway has no text")
            return

        while True:
            layout.set_text(drawtext, len(drawtext))

            text_width, text_height = layout.get_pixel_size()
            # truncate text if it's too long
            if text_width < (w - th * 2) or len(drawtext) < 3:
                break
            drawtext = drawtext[:-1]

        point = Graphene.Point()
        point.init(xc - text_width // 2, yc - text_height // 2)
        s.translate(point)

        s.append_layout(layout, color)
