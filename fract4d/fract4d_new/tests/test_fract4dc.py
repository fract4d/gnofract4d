#!/usr/bin/env python3

from fract4d.tests import testbase as Testbase

from fract4d import fract4dc as Fract4dc

from .helpers.mandelbrot_compiled_formula import MandelbrotCompiledFormula
from .helpers.shared_constants import COLOR_MAP, LOCATION_PARAMS


class Test(Testbase.ClassSetup):

    def test_create_controller(self):
        mandelbrot_compiled_formula = MandelbrotCompiledFormula(self.g_comp)

        controller = Fract4dc.create_controller(mandelbrot_compiled_formula.get_library_path(),
                                                mandelbrot_compiled_formula.get_formula_params(),
                                                LOCATION_PARAMS)

        self.assertTrue(controller)
        #self.assertEqual('Controller', type(controller).__name__)

    def test_create_color_map(self):

        color_map = Fract4dc.cmap_create(COLOR_MAP)

        self.assertTrue(color_map)
        #self.assertEqual('PyCapsule', type(color_map).__name__)
