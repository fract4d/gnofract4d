#!/usr/bin/env python3

from fract4d.tests import testbase as Testbase

from fract4d import fract4dc as Fract4dc

from ...fract4d_new.image_wrapper import ImageWrapper
from .helpers.mandelbrot_compiled_formula import MandelbrotCompiledFormula
from .helpers.mock_message_handler import MockMessageHandler
from .helpers.shared_constants import COLOR_MAP, LOCATION_PARAMS, TILE_SIZE


class Test(Testbase.ClassSetup):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mandelbrot_compiled_formula = MandelbrotCompiledFormula(cls.g_comp)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        del cls.mandelbrot_compiled_formula

    def setUp(self):
        library_path = self.mandelbrot_compiled_formula.get_library_path()
        formula_params = self.mandelbrot_compiled_formula.get_formula_params()
        self.controller = Fract4dc.create_controller(library_path, formula_params, LOCATION_PARAMS)

    def tearDown(self):
        del self.controller

    def test_set_message_handler(self):
        message_handler = MockMessageHandler()

        try:
            self.controller.set_message_handler(message_handler)
        except Exception: # pylint: disable=broad-except
            self.fail("set_message_handler() raised Exception")

    def test_start_calculating(self):
        message_handler = MockMessageHandler()
        self.controller.set_message_handler(message_handler)
        color_map = Fract4dc.cmap_create(COLOR_MAP)
        image = ImageWrapper(TILE_SIZE, TILE_SIZE).get_img()

        initial_statuses_history = message_handler.get_statuses_history().copy()
        self.controller.start_calculating(
            params=LOCATION_PARAMS,
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=1,
            cmap=color_map,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=image,
        )
        first_status = message_handler.get_statuses_history()[0]

        self.assertEqual(0, len(initial_statuses_history))
        self.assertEqual(1, first_status)

    def test_stop_calculating(self):
        message_handler = MockMessageHandler()
        self.controller.set_message_handler(message_handler)
        color_map = Fract4dc.cmap_create(COLOR_MAP)
        image = ImageWrapper(TILE_SIZE, TILE_SIZE).get_img()

        initial_statuses_history = message_handler.get_statuses_history().copy()
        self.controller.start_calculating(
            params=LOCATION_PARAMS,
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=1,
            cmap=color_map,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=image,
        )
        first_status = message_handler.get_statuses_history()[0]
        self.controller.stop_calculating()
        last_status = message_handler.get_statuses_history()[-1]

        self.assertEqual(0, len(initial_statuses_history))
        self.assertEqual(1, first_status)
        self.assertEqual(0, last_status)
