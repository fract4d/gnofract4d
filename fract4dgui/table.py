
import gtk

class Table(gtk.Table):
    def __init__(self,rows=1,cols=1,homogeneous=False):
        self.__gobject_init__()
        gtk.Table.__init__(self,rows,cols,homogeneous)
        self.nextrow=0
        self.set_col_spacing(0,10)

    def add(
        self,
        widget,col,
        xoptions=gtk.EXPAND|gtk.FILL,yoptions=gtk.EXPAND|gtk.FILL,
        xpadding=0, ypadding=0):
        self.attach(
            widget,col,col+1,self.nextrow,self.nextrow+1,
            xoptions,yoptions,xpadding,ypadding)

    def next():
        self.nextrow += 1
