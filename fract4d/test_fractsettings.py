#!/usr/bin/env python3

import unittest

import fractsettings

class ProduceAnything:
    def __getattr__(self,name):
        return name + "val"

class FakeParent:
    def __init__(self):
        self.changes = 0
    def changed(self):
        self.changes += 1

class Test(unittest.TestCase):
    def testCreate(self):
        s = fractsettings.T(None)

    def testSetAndGet(self):
        s = fractsettings.T(ProduceAnything())
        s.x = 10.0
        self.assertEqual(10.0, s.x)
        self.assertEqual(10.0, s.__dict__.get("x"))

    def testGetMissingUsesFallback(self):
        s = fractsettings.T(ProduceAnything())
        self.assertEqual("xval", s.x)
        self.assertEqual(None, s.__dict__.get("x"))

    def testSetRaisesChanged(self):
        p = FakeParent()
        s = fractsettings.T(ProduceAnything(),p)
        s.x = 10.0
        self.assertEqual(1, p.changes)

        # don't call changed, it hasn't 
        s.x = 10.0
        self.assertEqual(1, p.changes)
            
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

