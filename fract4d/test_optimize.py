#!/usr/bin/env python3

# test graph

import unittest
import sys

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d.instructions import *
from fract4d import optimize

class Test(unittest.TestCase):
    def setUp(self):
        self.o = optimize.T()
        self.a = TempArg("a",Float)
        self.b = TempArg("b",Float)
        self.c = TempArg("c",Float)
        
    def tearDown(self):
        pass

    def testFlowGraph(self):
        insns = [
            Move(ConstFloatArg(1.0),self.a),
            Move(ConstFloatArg(2.0),self.b),
            Binop("*", [self.a, self.b], [self.c])
            ]

        g = optimize.FlowGraph()
        g.build(insns)

        self.assertEqual(g.define[0], [self.a])
        self.assertEqual(g.define[1], [self.b])
        self.assertEqual(g.define[2], [self.c])
        self.assertEqual(g.use[2], [self.a, self.b])

    def assertTreesEqual(self,t1,t2):
        self.assertEqual(t1.__class__, t2.__class__)
        if isinstance(t1,list):
            for (a,b) in zip(t1,t2):
                self.assertTreesEqual(a,b)

        if isinstance(t1,Insn):
            self.assertEqual(t1.format(), t2.format())
            for (s1,s2) in zip(t1.source(),t2.source()):
                self.assertTreesEqual(s1,s2)
            for (d1,d2) in zip(t1.dest(), t2.dest()):
                self.assertTreesEqual(d1,d2)
        
    def testPeephole(self):
        tests = [
            # can't be optimized
            (Binop("*", [ ConstFloatArg(2.0), TempArg("a",Float)], [TempArg("b",Float)]),None),
            (Binop("*", [ TempArg("a",Float), ConstFloatArg(2.0)], [TempArg("b",Float)]),None),
            (Binop("*", [ TempArg("a",Float), TempArg("b",Float)], [TempArg("c",Float)]),None),

            # constant folding
            (Binop("*", [ ConstFloatArg(2.0), ConstFloatArg(2.0)], [TempArg("b",Float)]),
             Move([ConstFloatArg(4.0)], [TempArg("b",Float)])),
            (Binop("-", [ ConstFloatArg(12.0), ConstFloatArg(14.0)], [TempArg("b",Float)]),
             Move([ConstFloatArg(-2.0)], [TempArg("b",Float)])),
            (Binop("+", [ ConstFloatArg(3.0), ConstFloatArg(2.0)], [TempArg("b",Float)]),
             Move([ConstFloatArg(5.0)], [TempArg("b",Float)])),
            (Binop("/", [ ConstFloatArg(2.0), ConstFloatArg(0.2)], [TempArg("b",Float)]),
             Move([ConstFloatArg(10.0)], [TempArg("b",Float)])),

            # multiplication by 1
            (Binop("*", [ ConstFloatArg(1.0), TempArg("a",Float)], [TempArg("c",Float)]),
             Move([TempArg("a",Float)], [TempArg("c",Float)])),
            (Binop("*", [ TempArg("a",Float), ConstFloatArg(1.0)], [TempArg("c",Float)]),
             Move([TempArg("a",Float)], [TempArg("c",Float)])),

            # multiplication by 0
            (Binop("*", [ ConstFloatArg(0.0), TempArg("a",Float)], [TempArg("c",Float)]),
             Move([ConstFloatArg(0.0)], [TempArg("c",Float)])),
            (Binop("*", [ TempArg("a",Float), ConstFloatArg(0.0)], [TempArg("c",Float)]),
             Move([ConstFloatArg(0.0)], [TempArg("c",Float)]))
            
            ]

        (allin, allexp) = ([],[])
        for (input, expected) in tests:
            allin.append(input)
            if expected == None:
                expected = input
            allexp.append(expected)
            out = self.o.peephole_binop(input)
            try:                
                self.assertTreesEqual(out, expected)
            except Exception as exn:
                print("Error comparing trees %s, %s" % (out,expected))
                raise
                            
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

