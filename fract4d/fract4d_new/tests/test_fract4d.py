#!/usr/bin/env python3

import os.path

from fract4d import fract4dc, image
from fract4d.tests import testbase
from .message_handler import MessageHandler


LOCATION_PARAMS = [
    0.0, 0.0, 0.0, 0.0,
    4.0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0
]
TILE_SIZE = 64

class Test(testbase.ClassSetup):
    def setUp(self):
        self.compiler = Test.g_comp

    def compile_color_mandel(self):
        cf1 = self.compiler.get_formula("gf4d.cfrm", "default", "cf0")
        cf2 = self.compiler.get_formula("gf4d.cfrm", "zero", "cf1")
        f = self.compiler.get_formula("gf4d.frm", "Mandelbrot")

        color_mandel_params = f.symbols.default_params() + \
            cf1.symbols.default_params() + \
            cf2.symbols.default_params()

        return self.compiler.compile_all(f, cf1, cf2, []), color_mandel_params

    def create_mandelbrot_controller(self):
        library_file_path, formula_params = self.compile_color_mandel()

        return fract4dc.create_controller(library_file_path, formula_params, LOCATION_PARAMS)

    def test_calculation_messages_are_handled(self):
        controller = self.create_mandelbrot_controller()
        message_handler = MessageHandler()
        controller.set_message_handler(message_handler)
        color_map = fract4dc.cmap_create([
            (0.0, 0, 0, 0, 255),
            (1 / 256.0, 255, 255, 255, 255),
            (1.0, 255, 255, 255, 255)
        ])
        im = image.T(TILE_SIZE, TILE_SIZE)

        controller.start_calculating(
            params=LOCATION_PARAMS,
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=1,
            cmap=color_map,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=im._img,
        )

        self.assertEqual([1, 0], message_handler.get_statuses_history())
        self.assertEqual((0, 0, TILE_SIZE, TILE_SIZE), message_handler.get_last_image_tile_drawn())
        self.assertEqual(True, message_handler.has_finished())
