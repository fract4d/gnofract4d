# utilities to comply with Gnome Human Interface Guidelines.
# these are defined at http://developer.gnome.org/projects/gup/hig/2.0/

import gtk
import xml.sax.saxutils

import utils

class Alert(gtk.Dialog):
    def __init__(self, **kwds):

        image = kwds.get("image")
        primary_text = kwds.get("primary")
        secondary_text= kwds.get("secondary","")
        buttons = kwds.get("buttons",())
        parent = kwds.get("parent")
        flags = kwds.get("flags",0)
        title = kwds.get("title","")

        self.ignore_info = kwds.get("ignore")

        if not isinstance(image,gtk.Image):
            image = gtk.image_new_from_stock(image, gtk.ICON_SIZE_DIALOG)
            
        flags = flags | (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        gtk.Dialog.__init__(self,title,parent,flags,buttons)
        self.set_resizable(False)
        self.set_border_width(6)
        self.set_has_separator(False)

        self.vbox.set_spacing(12)
        
        upper_hbox = gtk.HBox()
        upper_hbox.set_spacing(12)
        upper_hbox.set_border_width(6)

        image.set_alignment(0.5,0.5)
        image.icon_size = gtk.ICON_SIZE_DIALOG
        
        upper_hbox.pack_start(image)
        
        if secondary_text and len(secondary_text) > 0:
            secondary_text = "\n\n" + secondary_text
            secondary_text = xml.sax.saxutils.escape(secondary_text)
        else:
            secondary_text = ""
        label_text = '<span weight="bold" size="larger">%s</span>%s' % \
                     (primary_text, secondary_text)

        label = gtk.Label(label_text)
        label.set_use_markup(True)
        label.set_line_wrap(True)
        
        upper_hbox.pack_start(label)
        
        self.vbox.pack_start(upper_hbox)
        
        if self.ignore_info:
            self.dont_show_again = gtk.CheckButton(_("Don't show this message again"))
            self.vbox.pack_end(self.dont_show_again)
            self.dont_show_again.set_active(self.ignore_info.is_ignore_suggested())

            def on_response(self,*args):
                if self.ignore_info and self.dont_show_again.get_active():
                    self.ignore_info.ignore()
                return False
            
            self.connect("response",on_response)
            
        self.show_all()

    def run(self):
        if self.ignore_info and self.ignore_info.is_ignored():
            return self.ignore_info.response
        return gtk.Dialog.run(self)
        
class InformationAlert(Alert):
    def __init__(self,**kwds):
        kwds.setdefault("image", gtk.STOCK_DIALOG_INFO)
        kwds.setdefault("buttons", (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        Alert.__init__(self, **kwds)

class ErrorAlert(Alert):
    FIX = 1
    def __init__(self, **kwds):
        
        fix_button = kwds.get("fix_button")

        # if optional fix button supplied, add to list of buttons
        buttons = list(kwds.get("buttons",()))
        if fix_button:
            buttons = [ fix_button, ErrorAlert.FIX]
        buttons += [gtk.STOCK_OK, gtk.RESPONSE_ACCEPT]

        kwds["buttons"] = tuple(buttons)
        kwds.setdefault("image", gtk.STOCK_DIALOG_ERROR) 
        Alert.__init__(self, **kwds)
        self.set_default_response(gtk.RESPONSE_ACCEPT)

class ConfirmationAlert(Alert):
    ALTERNATE=1
    def __init__(self, **kwds):

        proceed_button = kwds.get("proceed_button", gtk.STOCK_OK)
        alternate_button = kwds.get("alternate_button")
        cancel_button = kwds.get("cancel_button", gtk.STOCK_CANCEL)
        # if optional fix button supplied, add to list of buttons
        buttons = list(kwds.get("buttons", ()))
        if alternate_button:
            buttons = [ alternate_button, ConfirmationAlert.ALTERNATE]

        buttons += [cancel_button, gtk.RESPONSE_CANCEL,
                    proceed_button, gtk.RESPONSE_ACCEPT]

        kwds["buttons"] = tuple(buttons)
        kwds.setdefault("image", gtk.STOCK_DIALOG_WARNING)

        Alert.__init__(self, **kwds)
        
        self.set_default_response(gtk.RESPONSE_CANCEL)

def _periodText(seconds):
    if seconds > 86400:
        return "%d days" % (seconds // 86400)
    elif seconds > 3600:
        return "%d hours" % (seconds // 3600)
    elif seconds > 60:
        return "%d minutes" % (seconds // 60)
    else:
        return "%d seconds" % seconds
    
class SaveConfirmationAlert(ConfirmationAlert):
    NOSAVE = ConfirmationAlert.ALTERNATE
    def __init__(self, **kwds):
        document_name = kwds["document_name"]
        time_period = kwds.get("period",-1)
        if time_period==-1:
            text = "If you don't save, changes will be discarded."
        else:
            text = ("If you don't save, changes from the past %s " + \
                   "will be discarded.") % _periodText(time_period)

        kwds.setdefault("primary",_('Save changes to document "%s" before closing?') % document_name)
        kwds.setdefault("secondary", text)
        kwds.setdefault("proceed_button", gtk.STOCK_SAVE)
        kwds.setdefault("alternate_button",_("_Close without Saving"))

        ConfirmationAlert.__init__(self,**kwds)


# global var for testing purposes. If none-zero, dialog will
# automatically be dismissed after 'timeout' milliseconds
timeout = 0

class MessagePopper:
    "A mixin type for a window which wants to display error messages"
    def __init__(self):
        pass

    def show_error(self,msg, extra_message=""):
        d = ErrorAlert(
            parent=self,
            primary=msg,
            secondary=extra_message)

        return self.do(d)

    def show_info(self,msg,extra_message = ""):
        d = InformationAlert(
            parent=self,
            primary=msg,
            secondary=extra_message)

        return self.do(d)
        
    def ask_question(self, msg, secondary):
        d = ConfirmationAlert(
            primary=msg,
            secondary=secondary,
            image = gtk.STOCK_DIALOG_QUESTION,
            proceed_button = gtk.STOCK_YES,
            cancel_button = gtk.STOCK_NO)
        
        return self.do(d)

    def do(self,d):
        if timeout > 0:
            def dismiss():
                d.response(gtk.RESPONSE_ACCEPT)
                return False

            utils.timeout_add(timeout,dismiss)
        response = d.run()
        d.destroy()
        return response
