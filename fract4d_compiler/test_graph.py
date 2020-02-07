#!/usr/bin/env python3

# test graph

import unittest

from . import graph

class Test(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNew(self):
        g = graph.T()

    def testAdd(self):
        g = graph.T()
        n = g.newNode()
        self.assertEqual(g.succ(n), [])
        self.assertEqual(g.pred(n), [])

    def testAddEdge(self):
        g = graph.T()
        n = g.newNode()
        n2 = g.newNode()
        g.newEdge(n,n2)
        self.assertEqual(g.succ(n), [n2])
        self.assertEqual(g.pred(n2), [n])

    def testAddTwoEdges(self):
        g = graph.T()
        n = g.newNode()
        n2 = g.newNode()
        n3 = g.newNode()
        g.newEdge(n,n2)
        g.newEdge(n,n3)
        self.assertEqual(g.succ(n), [n2,n3])
        self.assertEqual(g.pred(n2), [n])
        self.assertEqual(g.pred(n3), [n])
        
    def testAddEdgeTwice(self):
        g = graph.T()
        n = g.newNode()
        n2 = g.newNode()
        g.newEdge(n,n2)
        g.newEdge(n,n2)
        self.assertEqual(g.succ(n), [n2])
        self.assertEqual(g.pred(n2), [n])
