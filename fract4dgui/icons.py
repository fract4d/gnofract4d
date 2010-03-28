# our 'quasi-stock' icons

import gobject
import gtk
import utils

from fract4d import fractconfig

_iconfactory = gtk.IconFactory()
_iconfactory.add_default()
    
class StockThing:
    def __init__(self, file, stock_name, title, key):
        global _iconfactory
        self.stock_name = stock_name
        self.title = title
        try:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(
                fractconfig.instance.find_resource(
                    file,
                    'pixmaps',
                    '../pixmaps/gnofract4d'))
            
            self.iconset = gtk.IconSet(self.pixbuf)
            _iconfactory.add(stock_name, self.iconset)

            gtk.stock_add(
                [(stock_name, title, gtk.gdk.CONTROL_MASK, key, "c")])

        except ValueError:
            # can't find it
            self.pixbuf = None
        except gobject.GError:
            self.pixbuf = None
            
explorer = StockThing('explorer_mode.png', 'explore', _('Explorer'), ord('e'))

improve_now = StockThing('improve_now.png', 'improve', _('Deepen'), ord('.'))

mail_to = StockThing('mail-forward.png', 'mail-to', _('_Mail To'), ord('m'))

draw_brush = StockThing('draw-brush.png', 'draw-brush', _('_Painter'), ord('p'))

face_sad = StockThing('face-sad.png', 'face-sad', _('_Report Bug'), ord('b'))

autozoom = StockThing('autozoom.png', 'autozoom', _('_Autozoom'), ord('a'))

randomize = StockThing('randomize_colors.png', 'randomize-colors', _('_Randomize Colors'), ord('r'))

#logo = StockThing('gnofract4d-logo.png', 'logo', _('Logo'), 0)


