#!/usr/bin/env python3

from fract4d import image


class ImageWrapper(image.T):

    def __init__(self, width, height):
        image.T.__init__(self, xsize=width, ysize=height)

    def get_img(self):
        return self._img
