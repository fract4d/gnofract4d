#!/usr/bin/env python3

import unittest

import testbase

from fract4d import ffloat
from fract4d.ffloat import Float, PrecisionError

if ffloat.has_bigmath:
    import gmpy2

save_has_bigmath = ffloat.has_bigmath

class NoBigMathTest(testbase.TestBase):
    def setUp(self):
        ffloat.has_bigmath = False

    def tearDown(self):
        ffloat.has_bigmath = save_has_bigmath
        
    def testCreate(self):
        f = Float(0.0) 
        self.assertEqual(type(f), float)
        self.assertEqual(0.0, f)

    def testCreateWithValue(self):
        f = Float(-1.0e40) 
        self.assertEqual(type(f), float)
        self.assertEqual(-1.0e40, f)

    def testCreateWithDefaultPrecision(self):
        self.assertRaises(PrecisionError, Float, 1.0, 128)

    def testCreateNumberWhichNeedsHighPrecision(self):
        f = Float("1.012345678901234567890123456789", 64)
        self.assertEqual("1.0123456789012346", "%.17g" % f)

class BigMathTest(testbase.TestBase):
    def testCreateWithHighPrecision(self):
        f = Float(1.0,128)
        self.assertEqual(128, f.getprec())
        self.assertEqual(f, gmpy.mpf(1.0,128))
        

    def testCreateNumberWhichNeedsHighPrecision(self):
        f = Float("1.012345678901234567890123456789", 128)
        self.assertEqual("1.012345678901234567890123456789", "%s" % f)
        
def suite():
    s = unittest.makeSuite(NoBigMathTest,'test')
    if save_has_bigmath:
        s.addTest(unittest.makeSuite(BigMathTest, 'test'))
    return s

if __name__ == '__main__':
    unittest.main(defaultTest='suite')


