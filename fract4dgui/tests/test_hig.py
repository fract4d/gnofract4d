#!/usr/bin/env python3

from fract4dgui import hig
from gi.repository import Gtk, GLib
import unittest
import gettext
import os

import gi
gi.require_version('Gtk', '3.0')


os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

Gtk.init()
toplevel = Gtk.Window()


class MockDialog(Gtk.MessageDialog, hig.MessagePopper):
    def __init__(self):
        Gtk.MessageDialog.__init__(
            self,
            text="Title",
            transient_for=toplevel)
        hig.MessagePopper.__init__(self)


class Test(unittest.TestCase):
    def setUp(self):
        hig.timeout = 0

    def tearDown(self):
        pass

    def wait(self):
        Gtk.main()

    def quitloop(self, f, status):
        if status == 0:
            Gtk.main_quit()

    def testCreate(self):
        d = hig.Alert(
            transient_for=toplevel,
            type=Gtk.MessageType.INFO,
            primary="Hello!")
        self.assertNotEqual(d, None)

        self.runAndDismiss(d)

        d = hig.Alert(
            transient_for=toplevel,
            type=Gtk.MessageType.ERROR,
            primary="Oh no!",
            secondary="A terrible thing has happened")

        self.runAndDismiss(d)

    def testInformation(self):
        d = hig.InformationAlert(
            transient_for=toplevel,
            primary="Your zipper is undone",
            secondary="This might be considered unsightly.")

        self.runAndDismiss(d)

    def testError(self):
        d = hig.ErrorAlert(
            transient_for=toplevel,
            primary="You don't want to do it like that",
            secondary="Chaos will ensue.")

        self.runAndDismiss(d)

        d = hig.ErrorAlert(
            transient_for=toplevel,
            primary="Could not destroy universe",
            secondary="Destructor ray malfunctioned.",
            fix_button="Try again")

        self.runAndDismiss(d)

    def testConfirm(self):
        d = hig.ConfirmationAlert(
            transient_for=toplevel,
            primary="Do you really want to hurt me?",
            secondary="Do you really want to make me cry?")

        self.runAndDismiss(d)

        d = hig.ConfirmationAlert(
            transient_for=toplevel,
            primary="Convert sub-meson structure?",
            secondary="The process is agonizingly painful and could result in permanent damage to the space-time continuum",
            proceed_button="Convert",
            alternate_button="Go Fishing")

        self.runAndDismiss(d)

    def runAndDismiss(self, d):
        def dismiss():
            d.response(Gtk.ResponseType.ACCEPT)
            return False

        # increase timeout to see what dialogs look like
        GLib.timeout_add(10, dismiss)

        d.run()
        d.destroy()

    def testPeriodText(self):
        self.assertEqual(hig._periodText(86400 * 3.5), "3 days")
        self.assertEqual(hig._periodText(3600 * 17.2), "17 hours")
        self.assertEqual(hig._periodText(60 * 17), "17 minutes")
        self.assertEqual(hig._periodText(23), "23 seconds")

    def testSaveConfirm(self):
        d = hig.SaveConfirmationAlert(
            transient_for=toplevel,
            document_name="Wombat.doc")

        self.runAndDismiss(d)

        d = hig.SaveConfirmationAlert(
            transient_for=toplevel,
            document_name="Wombat.doc",
            period=791)

        self.runAndDismiss(d)

    def testMessagePopper(self):
        dd = MockDialog()
        self.assertEqual(0, hig.timeout)

        hig.timeout = 300

        dd.show_error("Hello", "A catastrophe has occurred")
        dd.ask_question("Eh?", "Speak into t'trumpet!")
