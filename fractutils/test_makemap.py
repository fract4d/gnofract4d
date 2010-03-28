#!/usr/bin/env python

import unittest
import sys

import makemap

sys.path.append("..")
from fract4d import gradient

class Test(unittest.TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass

    def testAllocate(self):
        mm = makemap.T()

        self.assertEqual(None,mm.root)

    def testAddOnePixel(self):
        mm = makemap.T()
        mm.insertPixel(0,0,0)
        n = mm.root
        self.assertEqual((0,0,0,1), (n.r, n.g, n.b, n.count))

    def testAddOnePixelTwice(self):
        mm = makemap.T()
        mm.insertPixel(0,0,0)
        mm.insertPixel(0,0,0)
        n = mm.root
        self.assertEqual((0,0,0,2), (n.r, n.g, n.b, n.count))

    def testAddTwoPixels(self):
        mm = makemap.T()
        mm.insertPixel(0,0,0)
        mm.insertPixel(0xff,0xff,0xff)
        self.checkTwoPixels(mm)
        
    def testAddTwoPixelsReversed(self):
        mm = makemap.T()
        mm.insertPixel(0xff,0xff,0xff)
        mm.insertPixel(0,0,0)
        self.checkTwoPixels(mm)

    def checkTwoPixels(self,mm):
        n = mm.root
        self.assertEqual((127,127,127,0), (n.r, n.g, n.b, n.count))
        n1 = n.branches[0]
        self.assertEqual((0,0,0,1), (n1.r, n1.g, n1.b, n1.count))
        n2 = n.branches[7]
        self.assertEqual((0xff,0xff,0xff,1), (n2.r, n2.g, n2.b, n2.count))

    def testAddThreePixels(self):
        mm = makemap.T()
        mm.insertPixel(0xff,0xff,0xff)
        mm.insertPixel(0,0,0)
        mm.insertPixel(0xff,0x00,0x00)
        self.checkThreePixels(mm)

    def checkThreePixels(self,mm):
        self.checkTwoPixels(mm)
        n3 = mm.root.branches[4]
        self.assertEqual((0xff,0x00,0x00,1), (n3.r, n3.g, n3.b, n3.count))

    def testAddTwoPixelsToSameBranch(self):
        mm = makemap.T()
        mm.insertPixel(0xff,0xff,0xff)
        mm.insertPixel(0x80,0x80,0x80)
        r = mm.root
        self.assertEqual(False,r.isleaf())
        b = r.branches[7]
        self.assertEqual(False,b.isleaf())

    def testAddTwoVerySimilarPixels(self):
        mm = makemap.T()
        mm.insertPixel(0xff,0xff,0xff)
        mm.insertPixel(0xff,0xff,0xfe)
        r = mm.root
        depth=0
        n = 127
        size = 64
        while not r.branches[7].isleaf():
            self.assertEqual((r.r,r.g,r.b),(n,n,n))
            n = n + size
            size = size / 2
            depth += 1
            r = r.branches[7]
        self.assertEqual(7, depth)
        self.assertEqual(False, r.isleaf())
        self.assertEqual((0xfe,0xfe,0xfe,0), (r.r, r.g, r.b, r.count))
        leaf1 = r.branches[6]
        self.assertEqual((0xff,0xff,0xfe,1),
                         (leaf1.r, leaf1.g, leaf1.b, leaf1.count))
        leaf2 = r.branches[7]
        self.assertEqual((0xff,0xff,0xff,1),
                         (leaf2.r, leaf2.g, leaf2.b, leaf2.count))

        
    def testNode(self):
        n = makemap.Node(0,0,0,0)
        self.assertEqual([None]*8, n.branches)

        self.assertEqual(True, n.isleaf())
        
    def testLoadPicture(self):
        'Load a very simple test image and check correctly parsed'
        mm = makemap.T()
        mm.load(open("test000.png","rb"))

        seq = mm.getdata()
        self.assertEqual(len(seq),10 * 10)
        i = 0
        for pix in seq:
            if i % 10 < 5:
                # left half of image is black
                self.assertEqual(pix,(0,0,0))
            else:
                # right half is white
                self.assertEqual(pix,(255,255,255))
            i+= 1
            
        mm.build()
        r = mm.root
        self.assertEqual(False, r.isleaf())
        blackNode = r.branches[0]
        whiteNode = r.branches[7]
        self.assertEqual(blackNode.count,50)
        self.assertEqual(whiteNode.count,50)

    def testCollapseNode(self):
        mm = makemap.T()
        # 2 black + 1 white pixels
        mm.insertPixel(0xff,0xff,0xff)
        mm.insertPixel(0x00,0x00,0x00)
        mm.insertPixel(0x00,0x00,0x00)

        expected_err = 0xFF**2 * 3
        self.assertEqual(expected_err, mm.get_collapse_error(mm.root))

        candidates = mm.find_collapse_candidates(mm.root,[])
        self.assertEqual(1, len(candidates))
        self.assertEqual(
            [ (expected_err, mm.root)], candidates)

        mm.collapse(mm.root)

        # should have 1 leaf containing all 3 pixels using
        # most popular color
        self.assertEqual(True, mm.root.isleaf())
        self.assertEqual(3, mm.root.count)
        self.assertEqual((0,0,0), (mm.root.r, mm.root.g, mm.root.b))

    def testCollapseNode2(self):
        mm = makemap.T()
        # 2 black, 1 white, 1 dark gray pixels
        mm.insertPixel(0xff,0xff,0xff)
        mm.insertPixel(0x00,0x00,0x00)
        mm.insertPixel(0x00,0x00,0x00)
        mm.insertPixel(0x01,0x01,0x01)

        while True:
            candidates = mm.find_collapse_candidates(mm.root,[])
            self.assertEqual(1, len(candidates))
            (err,c) = candidates[0]
            if c == mm.root:
                break
            
            self.failUnless(err <= 1*3, err)
            mm.collapse(c)

        self.assertEqual(0xFF**2 * 3, err)

    def testReduceColors(self):
        mm = makemap.T()
        self.assertEqual(0,mm.numColors())
        
        # 2 black, 1 white, 1 dark gray pixels
        mm.insertPixel(0xff,0xff,0xff)
        self.assertEqual(1,mm.numColors())
        mm.insertPixel(0x00,0x00,0x00)
        self.assertEqual(2,mm.numColors())
        mm.insertPixel(0x00,0x00,0x00)
        self.assertEqual(2,mm.numColors())
        mm.insertPixel(0x01,0x01,0x01)
        self.assertEqual(3,mm.numColors())

        colors = mm.colors()
        colors.sort()
        self.assertEqual(
            [(0x00,0x00,0x00), (0x01,0x01,0x01), (0xff,0xff,0xff)],
            colors)

        mm.reduceColors(2)
        self.assertEqual(2,mm.numColors())

        colors = mm.colors()
        colors.sort()
        self.assertEqual(
            [(0x00,0x00,0x00), (0xff,0xff,0xff)],
            colors)

    def testReduceColors2(self):
        mm = makemap.T()
        in_colors = []
        for i in xrange(256):
            in_colors.append((i,0,0))
            for j in xrange(i+1):
                mm.insertPixel(i,0,0)
        self.assertEqual(256,mm.numColors())

        mm.reduceColors(255)
        colors = mm.colors()
        colors.sort()
        self.assertEqual(in_colors[1:],colors)

        mm.reduceColors(254)
        colors = mm.colors()
        colors.sort()
        # 0 and 2 are removed
        self.assertEqual([(1,0,0)] + in_colors[3:],colors)

        mm.reduceColors(3)

    def testRealImage(self):
        mm = makemap.T()
        mm.load(open("1453558084_8bb56e8b82_t.jpg"))
        mm.build(100)

        mm.reduceColors(10)

        grad = gradient.Gradient()

        colors = []
        i = 0
        for (r,g,b) in mm.colors():
            colors.append((i/10.0,r,g,b,255))
            i += 1

        grad.load_list(colors)
        grad.save(open("../maps/test.ggr","w"))
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

