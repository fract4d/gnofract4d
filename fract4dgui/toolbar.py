# toolbar code. 

import gtk

class T(gtk.Toolbar):
    def __init__(self):
        gtk.Toolbar.__init__(self)

        self.set_tooltips(True)
        self.set_border_width(1)

    def add_space(self):
        self.insert(gtk.SeparatorToolItem(), -1)

    def add_widget(self, widget, tip_text, private_text):
        toolitem = gtk.ToolItem()
        toolitem.add(widget)
        toolitem.set_expand(False)
        toolitem.set_homogeneous(False)
        toolitem.set_tooltip_text(tip_text)
        self.insert(toolitem,-1)

    def add_button(self, title, tip_text, image, cb):
        try:
            toolitem = gtk.ToolButton(image,title)
            self.insert(toolitem,-1)
        except:
            self.append_element(
                gtk.TOOLBAR_CHILD_BUTTON,
                None,
                title,
                tip_text,
                None,
                image,
                cb,
                None)

    def add_stock(self, stock_id, tip_text, cb):
        toolitem = gtk.ToolButton(stock_id)
        toolitem.connect('clicked', cb)
        toolitem.set_tooltip_text(tip_text)
        self.insert(toolitem,-1)

    def add_toggle(self, stock_id, title, tip_text, cb):
        toolitem = gtk.ToggleToolButton(stock_id)
        toolitem.connect('toggled', cb)
        toolitem.set_tooltip_text(tip_text)
        self.insert(toolitem,-1)
