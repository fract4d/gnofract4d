#!/usr/bin/env python3

import unittest

from ...fract4d_new.image_wrapper import ImageWrapper


TILE_SIZE = 64

class Test(unittest.TestCase):

    def test_get_img(self):
        image_wrapper = ImageWrapper(TILE_SIZE, TILE_SIZE)

        self.assertEqual(hasattr(image_wrapper, 'get_img'), True)
        self.assertTrue(image_wrapper.get_img())
