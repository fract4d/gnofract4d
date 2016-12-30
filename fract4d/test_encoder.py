#!/usr/bin/env python3

# test video encoding functionality

import unittest
import sys

import encoder
import animation, fractal, fc

# centralized to speed up tests
g_comp = fc.Compiler()
g_comp.add_func_path("../formulas")
g_comp.load_formula_file("gf4d.frm")
g_comp.load_formula_file("test.frm")
g_comp.load_formula_file("gf4d.cfrm")

class Test(unittest.TestCase):
    def setUp(self):
        self.encoder = encoder.T()

    def tearDown(self):
        pass

    def testDefault(self):
        pass
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

