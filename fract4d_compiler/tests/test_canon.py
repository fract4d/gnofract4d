#!/usr/bin/env python3

# unit tests for canon module

import copy
import pickle

from fract4d.tests import testbase
from fract4d_compiler import ir, absyn, canon, fsymbol
from fract4d_compiler.fracttypes import *

class CanonTest(testbase.TestBase):
    def setUp(self):
        self.fakeNode = absyn.Empty(0)
        self.canon = canon.T(fsymbol.T())
    def tearDown(self):
        pass

    # convenience methods to make quick trees for testing
    def eseq(self,stms, exp):
        return ir.ESeq(stms, exp, self.fakeNode, Int)
    def seq(self,stms):
        return ir.Seq(stms,self.fakeNode)
    def var(self,name="a"):
        return ir.Var(name,self.fakeNode, Int)
    def const(self,value=0):
        return ir.Const(value, self.fakeNode, Int)
    def binop(self,stms,op="+"):
        return ir.Binop(op,stms,self.fakeNode, Int)
    def move(self,dest,exp):
        return ir.Move(dest, exp, self.fakeNode, Int)
    def cjump(self,e1,e2,trueDest="trueDest",falseDest="falseDest"):
        return ir.CJump(">", e1, e2, trueDest, falseDest, self.fakeNode)
    def jump(self,dest):
        return ir.Jump(dest,self.fakeNode)
    def cast(self, e, type):
        return ir.Cast(e,self.fakeNode, type)
    def label(self,name):
        return ir.Label(name,self.fakeNode)

    def testPickle(self):
        pickle.dumps(self.canon,True)

    def testEmptyTree(self):
        self.assertEqual(self.canon.linearize(None),None)

    def testBinop(self):
        # binop with no eseqs
        tree = self.binop([self.var(), self.const()])
        ltree = self.canon.linearize(tree)
        self.assertTreesEqual("",tree, ltree)
        self.assertESeqsNotNested(ltree,1)

    def testLHBinop(self):
        # left-hand eseq
        tree = self.binop([self.eseq([self.move(self.var(),self.const())],
                                      self.var("b")),
                           self.const()])

        ltree = self.canon.linearize(tree)
        self.assertTrue(isinstance(ltree,ir.ESeq) and \
                        isinstance(ltree.children[0],ir.Move) and \
                        isinstance(ltree.children[1],ir.Binop) and \
                        isinstance(ltree.children[1].children[0],ir.Var))
        self.assertESeqsNotNested(ltree,1)

        # nested left-hand eseq
        tree = self.binop([self.eseq([self.move(self.var(),self.const())],
                                      self.var("b")),
                           self.const()])

        tree = self.binop([tree,self.const()])

        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

    def testRHBinop(self):
        # right-hand eseq
        tree = self.binop([self.var("a"),
                           self.eseq([self.move(self.var("b"),self.const())],
                                                self.var("b"))])
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)
        self.assertTrue(isinstance(ltree.children[0].children[0], ir.Var) and \
                        ltree.children[0].children[0].name == \
                        ltree.children[2].children[0].name)

        # commuting right-hand eseq
        tree = self.binop([self.const(4),
                           self.eseq([self.move(self.var("b"),self.const())],
                                                self.var("b"))])
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)
        self.assertTrue(isinstance(ltree.children[1].children[0],ir.Const))

    def testNestRHBinop(self):
        # nested right-hand eseq
        tree = self.binop([self.var("a"),
                           self.eseq([self.move(self.var("b"),self.const())],
                                                self.var("b"))])
        tree = self.binop([self.const(),tree])

        # what we ought to produce
        exptree = self.eseq([self.move(self.var("t__0"), self.var()),
                             self.move(self.var("b"),self.const())],
                            self.binop([self.const(),
                                        self.binop([self.var("t__0"),
                                                    self.var("b")])]))
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)
        self.assertTreesEqual("",ltree,exptree)

    def testBothSidesBinop(self):
        tree = self.binop([self.var("a"),
                           self.eseq([self.move(self.var("b"),self.const())],
                                                self.var("b"))])
        tree2 = copy.deepcopy(tree)
        tree = self.binop([tree, tree2])
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

    def testESeq(self):
        tree = self.eseq([self.var("a")], self.var("b"))
        ltree = self.canon.linearize(tree)
        self.assertTreesEqual("",tree,ltree)
        self.assertESeqsNotNested(ltree,1)

        tree = self.eseq([self.eseq([self.var("a")], self.var("b"))], self.var("c"))
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

        tree2 = self.eseq([self.var("a")], self.eseq([self.var("b")], self.var("c")))
        ltree2 = self.canon.linearize(tree2)
        self.assertESeqsNotNested(ltree2,1)
        self.assertTreesEqual("",ltree, ltree2)

    def testSeq(self):
        tree = self.seq([self.var("a"),self.var("b")])
        ltree = self.canon.linearize(tree)
        self.assertTreesEqual("",tree,ltree)
        self.assertESeqsNotNested(ltree,1)

        tree = self.seq([self.seq([self.var("a"), self.var("b")]), self.var("c")])
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

        tree2 = self.seq([self.var("a"), self.seq([self.var("b"), self.var("c")])])
        ltree2 = self.canon.linearize(tree2)
        self.assertESeqsNotNested(ltree2,1)
        self.assertTreesEqual("",ltree, ltree2)

    def testCJump(self):
        tree = self.cjump(self.var(), self.var())
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)
        self.assertTreesEqual("",tree, ltree)

    def testCJumpWithLHESeq(self):
        tree = self.cjump(self.eseq([self.move(self.var("a"),self.const())],
                                    self.var("b")),
                          self.var("c"))
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

    def testCJumpWithRHESeq(self):
        # commutes
        tree = self.cjump(self.const(),
                          self.eseq([self.move(self.var("a"),self.const())],
                                    self.var("b")))
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

        # doesn't commute
        tree = self.cjump(self.var("c"),
                          self.eseq([self.move(self.var("a"),self.const())],
                                    self.var("b")))
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

    def testBothSidesCJump(self):
        tree = self.cjump(self.eseq([self.move(self.var("a"),self.const())],
                                    self.var("b")),
                          self.eseq([self.move(self.var("a"),self.const())],
                                    self.var("b")))
        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

    def testCast(self):
        tree = self.cast(self.eseq([self.const(4)], self.var()), Float)

        ltree = self.canon.linearize(tree)
        self.assertESeqsNotNested(ltree,1)

    def testBasicBlocks(self):
        # no jumps or labels
        seq = self.seq([self.var(), self.var("b"), self.var("c")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlockIsWellFormed(blocks[0],"t__start","t__end")
        trace = self.canon.schedule_trace(blocks,"t__end")
        self.assertValidTrace(trace)

        # starts with a label
        seq = self.seq([self.label("t__1"),self.var()])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlockIsWellFormed(blocks[0],"t__1","t__end")

        # just a label
        seq = self.seq([self.label("t__1")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlockIsWellFormed(blocks[0],"t__1","t__end")

        # just a jump
        seq = self.seq([self.jump("d__1")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlockIsWellFormed(blocks[0],"t__start","d__1")

        # empty seq
        seq = self.seq([])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertEqual(blocks,[])

        # jump midway
        seq = self.seq([self.var("a"),self.jump("d__1"),self.var("b")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlocksAreWellFormed(blocks)
        self.assertEqual(len(blocks),2)

        # cjump midway
        seq = self.seq([self.var("a"),self.cjump(self.var(),self.var()),self.var("b")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlocksAreWellFormed(blocks)
        self.assertEqual(len(blocks),2)

        # label midway
        seq = self.seq([self.var("a"), self.label("x"), self.var("b")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlocksAreWellFormed(blocks)
        self.assertEqual(len(blocks),2)

        # starts with a jump and ends with label
        seq = self.seq([self.jump("d"),self.var("a"), self.label("x")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlocksAreWellFormed(blocks)
        self.assertEqual(len(blocks),3)

        # jump to next stm
        seq = self.seq([self.jump("d"),self.label("d")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        self.assertBlocksAreWellFormed(blocks)
        self.assertEqual(len(blocks),2)

    def testTraceScheduling(self):
        # cjump followed by falsedest
        seq = self.seq([self.var("a"),
                        self.cjump(self.var(),self.var(),"t__end","t__0"),
                        self.label("t__0"),
                        self.var("b")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        trace = self.canon.schedule_trace(blocks,"t__end")
        self.assertValidTrace(trace)

        # cjump followed by truedest
        seq = self.seq([self.var("a"),
                        self.cjump(self.var(),self.var(),"t__0","t__end"),
                        self.label("t__0"),
                        self.var("b")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        trace = self.canon.schedule_trace(blocks,"t__end")
        self.assertValidTrace(trace)
        self.assertEqual(trace[2].op,"<=")

        # cjump followed by neither
        seq = self.seq([self.label("start"),
                        self.cjump(self.var(),self.var(),"start","t__end"),
                        self.label("foo"),
                        self.const()])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        trace = self.canon.schedule_trace(blocks,"t__end")
        self.assertValidTrace(trace)

        # two mingled traces
        seq = self.seq([self.cjump(self.const(), self.const(),"a1","b1"),
                        self.label("a1"), self.var("a1"),self.jump("a2"),
                        self.label("b1"), self.var("b1"),self.jump("b2"),
                        self.label("a2"), self.var("a2"),self.jump("t__end"),
                        self.label("b2"), self.var("b2"),self.jump("t__end")])
        blocks = self.canon.basic_blocks(seq, "t__start", "t__end")
        trace = self.canon.schedule_trace(blocks,"t__end")
        self.assertValidTrace(trace)
        self.assertTrue(trace[2].name == "b1" and \
                        trace[3].name == "b1" and \
                        trace[4].name == "b2")
        self.assertTrue(trace[7].name == "a1" and \
                        trace[8].name == "a1" and \
                        trace[9].name == "a2")

    def test_canonicalize(self):
        # check overall driver works ok
        seq = self.seq([self.cjump(self.const(), self.const(),"a1","b1"),
                        self.label("a1"), self.var("a1"),self.jump("a2"),
                        self.label("b1"), self.var("b1"),self.jump("b2"),
                        self.label("a2"), self.var("a2"),self.jump("t__end"),
                        self.label("b2"), self.var("b2"),self.jump("t__end")])

        trace = self.canon.canonicalize(seq,"t__start","t__end")
        self.assertValidTrace(trace)

    def printAllBlocks(self,blocks):
        for b in blocks:
            for stm in b: print(stm.pretty(), end=' ')
            print()

#     def assertValidTrace(self,trace):
#         # must have each cjump followed by false case
#         expecting = None
#         for stm in trace:
#             if expecting != None:
#                 self.failUnless(isinstance(stm,ir.Label))
#                 self.assertEqual(stm.name,expecting)
#                 expecting = None
#             elif isinstance(stm, ir.CJump):
#                 expecting = stm.falseDest


#     def assertESeqsNotNested(self,t,parentAllowsESeq):
#         'check that no ESeqs are left below other nodes'
#         if isinstance(t,ir.ESeq):
#             if parentAllowsESeq:
#                 for child in t.children:
#                     self.assertESeqsNotNested(child,0)
#             else:
#                 self.fail("tree not well-formed after linearize")
#         else:
#             for child in t.children:
#                 self.assertESeqsNotNested(child,0)

#     def assertTreesEqual(self, t1, t2):
#         self.failUnless(
#             t1.pretty() == t2.pretty(),
#             ("%s, %s should be equivalent" % (t1.pretty(), t2.pretty())))
