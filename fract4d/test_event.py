#!/usr/bin/env python3

import unittest

import testbase

import event


class Foo:
    def __init__(self):
        self.x = event.T()
        self.x()
    def y(self):
        self.x()
        
class Test(testbase.TestBase):
    def testCreate(self):
        e = event.T()
        self.assertEqual([], e.targets)
        
    def testAdd(self):
        e = event.T()
        def foo():
            pass
        e += foo
        self.assertEqual([foo],e.targets)

    def testCall(self):
        results = []
        def call(arg):
            results.append(arg)

        e = event.T()
        e += call
        e(2)
        self.assertEqual([2],results)

        e += call
        e("fish")
        self.assertEqual([2,"fish","fish"], results)

    def testFoo(self):
        f = Foo()
        f.x()
        f.y()
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

