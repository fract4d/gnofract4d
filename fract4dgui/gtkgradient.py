import gtk
from . import dialog
from . import utils
import random

from fract4d import gradient

def show_gradients(parent,f):
    GradientDialog.show(parent,f)
    
class GradientDialog(dialog.T):
    def __init__(self,main_window,f):
        global userPrefs
        dialog.T.__init__(
            self,
            _("Gradients"),
            main_window,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        
        self.set_size_request(300, 320)

        self.f = f
        self.grad=gradient.Gradient()

        self.mousedown = False
        self.origmpos = self.startmpos = 0

        self.cur = -1 # no segment selected 
        #self.create_gradient_dialog()

    def show(parent,f,grad):
        dialog.T.reveal(GradientDialog,False, parent, None, f,grad)
        
    show = staticmethod(show)
    
    def create_gradient_dialog(self):
        hData = self.grad.getDataFromHandle(self.grad.cur)
        HSVCo = gradient.RGBtoHSV(hData.col)
    
        ###GRADIENT PREVIEW###
        self.gradarea=gtk.DrawingArea()
        self.gradarea.set_size_request(256, 64)
        self.gradarea.connect('realize', self.gradarea_realized)
        self.gradarea.connect('expose_event', self.gradarea_expose)

        self.gradarea.add_events(
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.POINTER_MOTION_MASK)
        
        self.gradarea.connect('button-press-event', self.gradarea_mousedown)
        self.gradarea.connect('button-release-event', self.gradarea_clicked)
        self.gradarea.connect('motion-notify-event', self.gradarea_mousemoved)
        gradareaBox = gtk.HBox(False, 0)
        
        ###CONTEXT MENU###
        menu_items = ( 
            ( "/_Insert", "<control>I", self.add_handle, 0 ),
            ( "/_Delete", "<control>D", self.rem_handle, 0 ),
            ( "/_Coloring Mode",        None,            None,        0, "<Branch>"    ),
            ( "/Coloring Mode/_RGB",     "<control>R",    self.cmode,    0                 ),
            ( "/Coloring Mode/_HSV",    "<control>H",    self.cmode,    1                 ),
            ( "/_Blending Mode",        None,            None,        0, "<Branch>"    ),
            ( "/Blending Mode/_Linear",    "<control>L",    self.bmode,    0                ),
            ( "/Blending Mode/_Sinusoidal",    None,        self.bmode,    1                ),
            ( "/Blending Mode/Curved _Increasing",None,    self.bmode,    2                ),
            ( "/Blending Mode/Curved _Decreasing",None,    self.bmode,    3                ),
            ( "/Debug",        None,            self.printstuff,    0 )
            )
        
        accel_group = gtk.AccelGroup()
        self.item_factory= gtk.ItemFactory(gtk.Menu, "<gradients>", accel_group)
        self.item_factory.create_items(menu_items)
        self.add_accel_group(accel_group)
        self.menu=self.item_factory.get_widget("<gradients>")
        
        ###COLOR SELECTION###
        if gtk.pygtk_version[0] >= 2 and gtk.pygtk_version[1] >= 4:
            lblCsel = gtk.Label("Color:")
            self.csel = gtk.ColorButton(
                    utils.create_color(hData.col[0], hData.col[1], hData.col[2]))
            self.csel.connect('color-set', self.colorchanged)
            self.colorbutton = True
        else:
            self.csel = gtk.Button("Color...")
            self.csel.connect('clicked', self.cbutton_clicked)
            self.csel_dialog = gtk.ColorSelectionDialog("Select a Color")
            self.csel_dialog.colorsel.set_current_color(
                    utils.create_color(hData.col[0], hData.col[1], hData.col[2]))

            self.csel_dialog.ok_button.connect('clicked', self.cdialog_response)
            self.colorbutton = False
        synccolsB = gtk.Button("Sync Colors")
        synccolsB.connect('clicked', self.sync_colors)
            
        CSelBox = gtk.HBox(False, 0)
        
        ###ALTERNATION CONTROL###
        lblAlternate = gtk.Label(_("Alternation:"))
        alternate    = gtk.SpinButton(gtk.Adjustment(self.grad.getAlt(), 0, .5, 0.01, .5, 0.0))
        alternate.set_digits(3)
        alternate.connect('value-changed', self.alternate_changed)
        
        AlternateBox = gtk.HBox(False, 0)
        
        ###POSITION CONTROL###
        lblPos    = gtk.Label(_("Position:"))
        self.pos = gtk.SpinButton(gtk.Adjustment(hData.pos, 0, 1, 0.01, 0.1, 0.0))
        self.pos.set_digits(2)
        self.pos.connect('value-changed', self.pos_changed)
        
        PosBox = gtk.HBox(False, 0)
        
        ###RANDOMIZE BUTTON###
        randomize = gtk.Button(_("Randomize"))
        randomize.connect('clicked', self.randomize)
        randBox = gtk.HBox(False, 0)
        
        ###OFFSET CONTROL###
        lblOffset = gtk.Label(_("Offset:"))
        lblOffsetBox = gtk.HBox(False, 0)
        
        offset=gtk.HScale(gtk.Adjustment(self.grad.getOffset(), 0, 1, 0.001, 0.01, 0.0))
        offset.set_digits(3)
        offset.connect('value-changed', self.offset_changed)
        
        ####################
        ###WIDGET PACKING###
        ####################
        self.vbox.set_homogeneous(0)
        gradareaBox.pack_start(self.gradarea, 1, 0, 10)
        self.vbox.pack_start(gradareaBox, 0, 0, 5)
        
        if self.colorbutton: CSelBox.pack_start(lblCsel, 0, 0, 10)
        CSelBox.pack_start(self.csel, 0, 0, 10)
        CSelBox.pack_end(synccolsB, 0, 0, 10)
        self.vbox.pack_start(CSelBox, 0, 0, 5)
        
        PosBox.pack_start(lblPos, 0, 0, 10)
        PosBox.pack_start(self.pos, 0, 0, 10)
        self.vbox.pack_start(PosBox, 0, 0, 5)
        
        AlternateBox.pack_start(lblAlternate, 0, 0, 10)
        AlternateBox.pack_start(alternate, 0, 0, 10)
        self.vbox.pack_start(AlternateBox, 0, 0, 5)
        
        lblOffsetBox.pack_start(lblOffset, 0, 0, 5)
        self.vbox.pack_start(lblOffsetBox, 0, 0, 5)
        self.vbox.pack_start(offset, 0, 0, 5)
        
        randBox.pack_start(randomize, 1, 0, 10)
        self.vbox.pack_start(randBox, 0, 0, 5)
        
    def offset_changed(self, widget):
        if self.grad.getOffset() != widget.get_value():
            self.grad.setOffset(1-widget.get_value())
            self.grad.compute()
            self.gradarea.queue_draw()
            self.f.colorlist=self.grad.clist
            self.f.changed(False)
    
    def colourchanged(self, widget):
        color = widget.get_color()
        seg, side = self.grad.getSegFromHandle(self.grad.cur)

        if side == 'left':
            seg.left.col = [colour.red/256, colour.green/256, colour.blue/256]
        else:
            seg.right.col = [colour.red/256, colour.green/256, colour.blue/256]
        self.grad.compute()
        self.gradarea.queue_draw()
        self.f.colorlist=self.grad.clist
        self.f.changed(False)
    
    #The backwards-compatible button was clicked
    def cbutton_clicked(self, widget):
        self.csel_dialog.show()
    def cdialog_response(self, widget):
        colour = self.csel_dialog.colorsel.get_current_color()
        seg, side = self.grad.getSegFromHandle(self.grad.cur)
        if side == 'left':
            seg.left.col = [colour.red/256, colour.green/256, colour.blue/256]
        else:
            seg.right.col = [colour.red/256, colour.green/256, colour.blue/256]
        self.grad.compute()
        self.gradarea.queue_draw()
        self.f.colorlist=self.grad.clist
        self.f.changed(False)
        
        self.csel_dialog.hide()
        
        return False
        
    ###Each handle is comprised of two handles, whose colours can be set independently.
    ###This function finds the other handle and sets it to the current handle's colour.
    def sync_colours(self, widget):
        if self.grad.cur % 2 == 0: #The handle is the first in its segment
            if self.grad.cur > 0:
                self.grad.segments[self.grad.cur/2-1].right.col = self.grad.getDataFromHandle(self.grad.cur).col
            else:
                self.grad.segments[-1].right.col = self.grad.getDataFromHandle(self.grad.cur).col
        else:
            if self.grad.cur < len(self.grad.segments)*2:
                self.grad.segments[self.grad.cur/2+1].left.col = self.grad.getDataFromHandle(self.grad.cur).col
            else:
                self.grad.segments[0].left.col = self.grad.getDataFromHandle(self.grad.cur).col
                
        self.grad.compute()
        self.gradarea.queue_draw()
        self.f.colorlist=self.grad.clist
        self.f.changed(False)
    
    ###ALTERNATION CHANGED###
    def alternate_changed(self, widget):
        if self.grad.getAlt() != widget.get_value():
            self.grad.setAlt(widget.get_value())
            self.grad.compute()
            self.gradarea.queue_draw()
            self.f.colorlist = self.grad.clist
            self.f.changed(False)
    
    ###POSITION CHANGED###
    def pos_changed(self, widget):
        if self.grad.getDataFromHandle(self.grad.cur).pos != widget.get_value():
            self.grad.move(self.grad.cur, widget.get_value()-self.grad.getDataFromHandle(self.grad.cur).pos)
            widget.set_value(self.grad.getDataFromHandle(self.grad.cur).pos)
            
            self.grad.compute()
            self.gradarea.queue_draw()
            self.f.colorlist = self.grad.clist
            self.f.changed(False)
    
    
    ###INIT FOR GRADIENT PREVIEW###
    def gradarea_realized(self, widget):
        self.gradcol= widget.get_colormap().alloc_color(
            "#FFFFFFFFFFFF", True, True)
        self.gradgc = widget.window.new_gc( foreground=self.gradcol,
                                            background=self.gradcol,
                                            fill=gtk.gdk.SOLID)
                                
        widget.window.draw_rectangle(widget.style.white_gc,
                                True,
                                0, 0,
                                widget.allocation.width,
                                widget.allocation.height)
        return True
        
    def gradarea_expose(self, widget, event):
        #Assume some other process has compute()ed the gradient
        
        ##Draw the gradient itself##
        for col in self.grad.clist:
            self.gradcol = widget.get_colormap().alloc_color(col[1]*255,col[2]*255,col[3]*255, True, True)
            self.gradgc.set_foreground(self.gradcol)
            widget.window.draw_line(self.gradgc,
                                    col[0]*self.grad.num+4, 0,
                                    col[0]*self.grad.num+4, 56)
        
        
        ##Draw some handles##                        
        for seg in self.grad.segments:
            s_lpos = (seg.left.pos+(1-self.grad.offset)) * self.grad.num
            s_rpos = (seg.right.pos+(1-self.grad.offset)) * self.grad.num
            
            if s_lpos > self.grad.num:
                s_lpos -= self.grad.num
            elif s_lpos < 0:
                s_lpos += self.grad.num
            if s_rpos > self.grad.num:
                s_rpos -= self.grad.num
            elif s_rpos < 0:
                s_rpos += self.grad.num
            
            s_lpos += 4
            s_rpos += 4
            
            wgc=widget.style.white_gc
            bgc=widget.style.black_gc
            
            index=self.grad.segments.index(seg)
            
            #A vast ugliness that should draw the selected handle with a white centre.
            #The problem is that each handle is really two handles - the second handle
            #of the left-hand segment and the first of the right.
            #The first two branches deal with handles in the middle, whilst the second
            #two deal with those at the edges. The other is a case for where neither
            #of the handles in a segment should be highlighted.            
            if self.grad.cur/2.0 == index or (self.grad.cur+1)/2.0 == index:
                self.draw_handle(widget.window, int(s_lpos), wgc, bgc)
                self.draw_handle(widget.window, int(s_rpos), bgc, bgc)
            elif (self.grad.cur-1)/2.0 == index:
                self.draw_handle(widget.window, int(s_lpos), bgc, bgc)
                self.draw_handle(widget.window, int(s_rpos), wgc, bgc)
            elif (self.grad.cur-1)/2.0 == len(self.grad.segments)-1.0 and index == 0:
                self.draw_handle(widget.window, int(s_lpos), wgc, bgc)
                self.draw_handle(widget.window, int(s_rpos), bgc, bgc)
            elif self.grad.cur == 0 and index == len(self.grad.segments)/2.0:
                self.draw_handle(widget.window, int(s_lpos), bgc, bgc)
                self.draw_handle(widget.window, int(s_rpos), wgc, bgc)
            else:
                self.draw_handle(widget.window, int(s_lpos), bgc, bgc)
                self.draw_handle(widget.window, int(s_rpos), bgc, bgc)
            
        return False
    
    def gradarea_mousedown(self, widget, event):
        if self.mousedown == False and event.button == 1:
            x=event.x/self.grad.num
            x-=1-self.grad.offset
            if x < 0:
                x+=1
        
            seg = self.grad.getSegAt(x)
            relx = x - seg.left.pos
        
            if relx < (seg.right.pos-seg.left.pos)/2:
                self.grad.cur=self.grad.segments.index(seg)*2
            else:
                self.grad.cur=self.grad.segments.index(seg)*2+1
                
            hData = self.grad.getDataFromHandle(self.grad.cur)
            
            if self.colourbutton == True:
                self.csel.set_color(
                        utils.create_color(hData.col[0],hData.col[1],hData.col[2]))
            else:
                self.csel_dialog.colorsel.set_current_color(
                        utils.create_color(hData.col[0],hData.col[1],hData.col[2]))
                
            self.pos.set_value(hData.pos)
                
            self.gradarea.queue_draw()
        
        if event.button == 1:
            self.mousedown = True
            self.origmpos = self.startmpos = event.x
        elif event.button == 3:
            self.mousepos = event.x #We can't pass this as callback data, because things're screwed. If this isn't true, please tell!
            #self.item_factory.popup(int(event.x), int(event.y), event.button)
            self.menu.popup(None, None, None, event.button, event.time)
        
        return False
    
    def gradarea_clicked(self, widget, event):
        self.mousedown = False
        if self.startmpos != event.x:
            self.grad.compute()
            self.gradarea.queue_draw()
            self.f.colorlist=self.grad.getCList()
            self.f.changed(False)
        
        return False
        
    def gradarea_mousemoved(self, widget, event):
        if self.mousedown:
            self.grad.move(self.grad.cur, (event.x - self.origmpos)/self.grad.num)
            
            self.origmpos = event.x
            self.grad.compute()
            self.gradarea.queue_draw()
    
    def add_handle(self, action, widget):
        self.grad.add(self.mousepos/self.grad.num)
        self.gradarea.queue_draw()    
        
    def rem_handle(self, action, widget):
        self.grad.remove(self.grad.cur)
        self.grad.cur = 0
        self.gradarea.queue_draw()
        
    def cmode(self, action, widget):
        seg, side = self.grad.getSegFromHandle(self.grad.cur)

        if action == 0:
            seg.cmode = 'RGB'
        else:
            seg.cmode = 'HSV'
        self.grad.compute()
        self.gradarea.queue_draw()
        self.f.colorlist=self.grad.getCList()
        self.f.changed(False)
        
    def bmode(self, action, widget):
        seg, side = self.grad.getSegFromHandle(self.grad.cur)
        
        if action == 0:
            seg.bmode = 'Linear'
        elif action == 1:
            seg.bmode = 'Sinusoidal'
        elif action == 2:
            seg.bmode = 'CurvedI'
        else:
            seg.bmode = 'CurvedD'
        self.grad.compute()
        self.gradarea.queue_draw()
        self.f.colorlist=self.grad.getCList()
        self.f.changed(False)
    
    def printstuff(self, action, widget):
        for seg in self.grad.segments:
            print([seg.left.pos, seg.left.col], [seg.right.pos, seg.right.col])
            
    def randomize(self, widget):
        oldcol = [random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)]
        oldpos = i = 0
        poslist = []
        
        for seg in self.grad.segments:
            poslist.append(random.random())
        poslist.sort()
        
        for seg in self.grad.segments:
            seg.left.pos = oldpos
            seg.left.col = oldcol
            
            seg.right.pos = oldpos = poslist[i]
            seg.right.col = oldcol = [random.randint(0, 255),random.randint(0, 255),random.randint(0, 255)]
            i+=1
            
        seg.right.pos = 1
        seg.right.col = self.grad.segments[0].left.col
        
        self.grad.compute()
        self.gradarea.queue_draw()
        self.f.colorlist=self.grad.getCList()
        self.f.changed(False)
        
        return False
    
    def draw_handle(self, drawable, pos, fill, outline):
        for y in range(8):
            drawable.draw_line(fill, pos-y/2, y+56, pos+y/2, y+56)
        
        lpos = pos + 3.5
        rpos = pos - 3.5
        
        drawable.draw_line(outline, pos, 56, lpos, 63);
        drawable.draw_line(outline, pos, 56, rpos, 63);
        drawable.draw_line(outline, lpos, 63, rpos, 63);

