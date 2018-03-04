#!/usr/bin/env python3

# unit tests for model

import unittest
import math

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import angle

class EmitCounter:
    def __init__(self):
        self.count = 0
    def onCallback(self,*args):
        self.count += 1

class FakeEvent:
    def __init__(self,**kwds):
        self.__dict__.update(kwds)

class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
        
    def wait(self):
        Gtk.main()
        
    def quitloop(self,f,status):
        if status == 0:
            Gtk.main_quit()

    def testCreate(self):
        a = angle.T("hello")
        self.assertTrue(a)
        self.assertEqual(a.adjustment.get_lower(),-math.pi)
        self.assertEqual(a.adjustment.get_upper(),math.pi)
        self.assertEqual(a.adjustment.get_value(),0.0)
        
    def testAngles(self):
        a = angle.T('foo')
        
        self.assertEqual(a.get_current_angle(),0.0)

        a.adjustment.set_value(a.adjustment.get_lower())
        self.assertEqual(a.get_current_angle(),-math.pi)

        a.adjustment.set_value(a.adjustment.get_upper())
        self.assertEqual(a.get_current_angle(), math.pi)

    def testPointerCoords(self):
        a = angle.T('foo')

        # 0 should point right
        self.assertNearlyEqual(
            a.pointer_coords(40, 0.0),
            ((40 - angle.T.ptr_radius),0))

        # so should 2pi
        self.assertNearlyEqual(
            a.pointer_coords(40, 2.0*math.pi),
            ((40 - angle.T.ptr_radius),0))

        # pi = left
        self.assertNearlyEqual(
            a.pointer_coords(40, math.pi),
            (-(40 - angle.T.ptr_radius),0))

        # pi/2 = up
        self.assertNearlyEqual(
            a.pointer_coords(40, math.pi/2.0),
            (0,(40 - angle.T.ptr_radius)))

        # 3pi/2 = down
        self.assertNearlyEqual(
            a.pointer_coords(40, 3.0 * math.pi / 2.0),
            (0,-(40 - angle.T.ptr_radius)))

    def testMouseInteraction(self):
        pass
    
    def assertNearlyEqual(self,a,b):
        # check that each element is within epsilon of expected value
        epsilon = 1.0e-12
        for (ra,rb) in zip(a,b):
            d = abs(ra-rb)
            self.assertTrue(d < epsilon,"%f != %f (by %f)" % (ra,rb,d))

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
