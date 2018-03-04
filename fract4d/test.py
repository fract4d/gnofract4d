#!/usr/bin/env python3

import unittest
import test_fractlexer
import test_fractparser
import test_fracttypes
import test_symbol
import test_translate
import test_canon
import test_codegen
import test_fc
import test_fract4d
import test_fctutils
import test_fractal
import test_3d
import test_gradient
import test_preprocessor
import test_graph
import test_optimize
import test_image
import test_colorizer
import test_animation
import test_fractconfig
import test_options
import test_cache
import test_browser_model
import test_formsettings
import test_ffloat
import test_absyn
import test_event


def suite():
    return unittest.TestSuite((
    test_fractlexer.suite(),
    test_fractparser.suite(),
    test_fracttypes.suite(),
    test_symbol.suite(),
    test_translate.suite(),
    test_canon.suite(),
    test_codegen.suite(),
    test_fc.suite(),
    test_fract4d.suite(),
    test_fctutils.suite(),
    test_fractal.suite(),
    test_3d.suite(),
    test_gradient.suite(),
    test_preprocessor.suite(),
    test_graph.suite(),
    test_optimize.suite(),
    test_image.suite(),
    test_colorizer.suite(),
    test_animation.suite(),
    test_fractconfig.suite(),
    test_options.suite(),
    test_cache.suite(),
    test_browser_model.suite(),
    test_formsettings.suite(),
    test_ffloat.suite(),
    test_absyn.suite(),
    test_event.suite()
    ))

def main():
    unittest.main(defaultTest='suite')

if __name__ == '__main__':
    main()
