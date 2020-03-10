# utilities to comply with Gnome Human Interface Guidelines.
# these are defined at http://developer.gnome.org/projects/gup/hig/2.0/

from gi.repository import Gtk, GLib


class Alert(Gtk.MessageDialog):
    def __init__(self, **kwds):
        type = kwds.get("type")
        primary_text = kwds.get("primary")
        secondary_text = kwds.get("secondary", "")
        buttontype = kwds.get("buttontype", Gtk.ButtonsType.NONE)
        buttons = kwds.get("buttons", ())
        transient_for = kwds.get("transient_for")
        title = kwds.get("title", "")

        Gtk.MessageDialog.__init__(
            self,
            transient_for=transient_for,
            modal=True,
            destroy_with_parent=True,
            message_type=type,
            title=title,
            text=primary_text,
            buttons=buttontype)

        self.add_buttons(*buttons)
        self.format_secondary_text(secondary_text)

        self.show_all()


class InformationAlert(Alert):
    def __init__(self, **kwds):
        kwds.setdefault("type", Gtk.MessageType.INFO)
        kwds.setdefault("buttons", (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        Alert.__init__(self, **kwds)


class ErrorAlert(Alert):
    FIX = 1

    def __init__(self, **kwds):
        fix_button = kwds.get("fix_button")

        # if optional fix button supplied, add to list of buttons
        buttons = list(kwds.get("buttons", ()))
        if fix_button:
            buttons = [fix_button, ErrorAlert.FIX]
        buttons += [Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT]

        kwds["buttons"] = tuple(buttons)
        kwds.setdefault("type", Gtk.MessageType.ERROR)
        Alert.__init__(self, **kwds)
        self.set_default_response(Gtk.ResponseType.ACCEPT)


class ConfirmationAlert(Alert):
    ALTERNATE = 1

    def __init__(self, **kwds):
        proceed_button = kwds.get("proceed_button", Gtk.STOCK_OK)
        alternate_button = kwds.get("alternate_button")
        cancel_button = kwds.get("cancel_button", Gtk.STOCK_CANCEL)
        # if optional fix button supplied, add to list of buttons
        buttons = list(kwds.get("buttons", ()))
        if alternate_button:
            buttons = [alternate_button, ConfirmationAlert.ALTERNATE]

        buttons += [cancel_button, Gtk.ResponseType.CANCEL,
                    proceed_button, Gtk.ResponseType.ACCEPT]

        kwds["buttons"] = tuple(buttons)
        kwds.setdefault("type", Gtk.MessageType.WARNING)

        Alert.__init__(self, **kwds)

        self.set_default_response(Gtk.ResponseType.CANCEL)


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
        time_period = kwds.get("period", -1)
        if time_period == -1:
            text = "If you don't save, changes will be discarded."
        else:
            text = ("If you don't save, changes from the past %s "
                    "will be discarded.") % _periodText(time_period)

        kwds.setdefault(
            "primary",
            _('Save changes to document "%s" before closing?') %
            document_name)
        kwds.setdefault("secondary", text)
        kwds.setdefault("proceed_button", Gtk.STOCK_SAVE)
        kwds.setdefault("alternate_button", _("_Close without Saving"))

        ConfirmationAlert.__init__(self, **kwds)


# global var for testing purposes. If none-zero, dialog will
# automatically be dismissed after 'timeout' milliseconds
timeout = 0


class MessagePopper:
    "A mixin type for a window which wants to display error messages"

    def __init__(self):
        pass

    def show_error(self, msg, extra_message=""):
        d = ErrorAlert(
            transient_for=self,
            primary=msg,
            secondary=extra_message)

        return self.do(d)

    def show_info(self, msg, extra_message=""):
        d = InformationAlert(
            transient_for=self,
            primary=msg,
            secondary=extra_message)

        return self.do(d)

    def ask_question(self, msg, secondary):
        d = ConfirmationAlert(
            transient_for=self,
            primary=msg,
            secondary=secondary,
            type=Gtk.MessageType.QUESTION,
            proceed_button=Gtk.STOCK_YES,
            cancel_button=Gtk.STOCK_NO)

        return self.do(d)

    def do(self, d):
        if timeout > 0:
            def dismiss():
                d.response(Gtk.ResponseType.ACCEPT)
                return False

            GLib.timeout_add(timeout, dismiss)

        response = d.run()
        d.destroy()
        return response
