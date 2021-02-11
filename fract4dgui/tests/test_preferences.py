# test classes for preferences logic

from . import testgui

from fract4d import fractconfig
from fract4dgui import gtkfractal, preferences

import gettext
gettext.install('gnofract4d')

from gi.repository import Gtk


class CallCounter:
    def __init__(self):
        self.count = 0

    def cb(self, *args):
        self.count += 1


class Test(testgui.TestCase):
    def testSignals(self):
        baseconfig = fractconfig.T("test.config")
        config = preferences.Preferences(baseconfig)

        counter = CallCounter()

        config.connect('preferences-changed', counter.cb)

        # callback should happen
        config.set('compiler', 'name', 'cc')
        self.assertEqual(counter.count, 1)

        # no callback, value already set
        config.set('compiler', 'name', 'cc')
        self.assertEqual(counter.count, 1)

        # new option, callback called
        config.set('compiler', 'foop', 'cc')
        self.assertEqual(counter.count, 2)

    def testInstance(self):
        dummy = preferences.Preferences(fractconfig.T(""))
        self.assertNotEqual(None, dummy)

    def testPrefsDialog(self):
        parent = Gtk.Window()
        f = gtkfractal.T(Test.g_comp, parent)
        pd = preferences.PrefsDialog(parent, f, preferences.Preferences(Test.userConfig))
        self.assertEqual(pd.f, f)
