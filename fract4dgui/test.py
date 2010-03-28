#!/usr/bin/env python

print "A bunch of windows may appear and vanish again."
print "Do not be alarmed, this is normal."

# suppress annoying message during tests we get otherwise
import warnings
warnings.filterwarnings(
    "ignore",
    ".*UIManager.*",
    DeprecationWarning,
    ".*",
    0)

import unittest
import test_gtkfractal
import test_undo
import test_model
import test_preferences
import test_fourway
import test_angle
import test_hig
import test_browser
import test_main_window
import test_settings
import test_painter
import test_utils
import test_renderqueue
import test_director

def suite():
    tests = (
        test_renderqueue.suite(),
        test_gtkfractal.suite(),
        test_undo.suite(),
        test_model.suite(),
        test_preferences.suite(),
        test_fourway.suite(),
        test_angle.suite(),
        test_hig.suite(),
        test_browser.suite(),
        test_settings.suite(),
        test_painter.suite(),
        test_utils.suite(),
        test_main_window.suite(),
        test_director.suite())
    return unittest.TestSuite(tests)

def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()

