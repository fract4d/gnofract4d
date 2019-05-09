#!/usr/bin/env python3

import math
import io
import copy
import re

from . import testbase

from fract4d import gradient, fract4dc, translate, fractparser
from fract4d.gradient import Blend, ColorMode

wood='''GIMP Gradient
Name: Wood 2
9
0.000000 0.069491 0.138982 1.000000 0.700000 0.400000 1.000000 0.944844 0.616991 0.289137 1.000000 3 0
0.138982 0.208472 0.277963 0.800000 0.522406 0.244813 1.000000 0.928860 0.592934 0.257008 1.000000 3 0
0.277963 0.347454 0.416945 0.820000 0.523444 0.226888 1.000000 0.922120 0.582791 0.243462 1.000000 3 0
0.416945 0.486436 0.555927 0.770000 0.486649 0.203299 1.000000 0.920000 0.579600 0.239200 1.000000 3 0
0.555927 0.609140 0.662354 0.780000 0.491400 0.202800 1.000000 0.903086 0.568944 0.234802 1.000000 4 0
0.662354 0.715568 0.768781 0.810000 0.510300 0.210600 1.000000 0.850329 0.535708 0.221086 1.000000 4 0
0.768781 0.821995 0.875209 0.760000 0.478800 0.197600 1.000000 0.708598 0.446417 0.184235 1.000000 4 0
0.875209 0.928422 0.981636 0.620000 0.390600 0.161200 1.000000 0.000000 0.000000 0.000000 1.000000 4 0
0.981636 0.991653 1.000000 0.000000 0.000000 0.000000 1.000000 0.000000 0.000000 0.000000 0.000000 4 0
'''

class Test(testbase.TestBase):
    def setUp(self):
        self.white = [1.0, 1.0, 1.0, 1.0]
        self.black = [0.0, 0.0, 0.0, 1.0]
        self.grey_33 = [1.0/3.0, 1.0/3.0, 1.0/3.0, 1.0]
        self.mid_grey = [0.5, 0.5, 0.5, 1.0]
        self.grey_66 = [2.0/3.0, 2.0/3.0, 2.0/3.0, 1.0]
        self.red = [1.0, 0.0, 0.0, 1.0]
        self.green = [0.0, 1.0, 0.0, 1.0]
        self.blue = [0.0, 0.0, 1.0, 1.0]
    
    def tearDown(self):
        pass

    def testCreate(self):
        g = gradient.Gradient()

        self.assertEqual(len(g.segments), 1)
        self.assertWellFormedGradient(g)

    def testEquals(self):
        g1 = gradient.Gradient()
        g2 = gradient.Gradient()

        self.assertTrue(g1 == g2) # calls __eq__
        self.assertEqual(g1,g2) # calls __ne__

        g1.segments[0].left_color[0] = 0.7
        self.assertNotEqual(g1,g2)
        
    def checkColorMapAndGradientEquivalent(self,colorlist,maxdiff=0):
        grad = gradient.Gradient()
        grad.load_list(colorlist,maxdiff)

        self.assertWellFormedGradient(grad)
        if maxdiff != 0:
            # don't have any robust metric for how close this will be
            return
        
        cmap = fract4dc.cmap_create(colorlist)
        
        for i in range(1000):
            fi = i / 1000.0
            (r,g,b,a) = grad.get_color_at(fi)
            cmap_color = fract4dc.cmap_lookup(cmap, fi)
            grad_color = (int(r*255.0), int(g*255.0),
                          int(b*255.0), int(a*255.0))
            self.assertNearlyEqual(
                grad_color,
                cmap_color,
                "colorlist(%s) = %s but gradient(%s) = %s" % \
                (fi, cmap_color, fi, grad_color), 1.5)
        return grad

    def checkCGradientAndPyGradientEquivalent(self,grad):
        # We have 2 sets of gradient-drawing code, in C and Python
        # check they calculate the same answer
        self.assertWellFormedGradient(grad)
        cmap = fract4dc.cmap_create_gradient(grad.segments)
        for i in range(1000):
            fi = i / 1000.0
            (r,g,b,a) = grad.get_color_at(fi)
            #print "%d: %.17g, %.17g, %.17g, %.17g" % (i,r,g,b,a)
            cmap_color = fract4dc.cmap_lookup(cmap, fi)
            grad_color = (int(r*255.0), int(g*255.0),
                          int(b*255.0), int(a*255.0))
            self.assertNearlyEqual(
                grad_color,
                cmap_color,
                "colorlist(%s) = %s but gradient(%s) = %s" % \
                (fi, cmap_color, fi, grad_color), 1.5)
        
    def testFromColormap(self):
        # check that creating a gradient from a colormap produces the same
        # output
        colorlist = [(0.0, 255,255,255, 255), (1.0, 0,0,0,255)]
        g = gradient.Gradient()
        g.load_list(colorlist)
        self.assertEqual(len(g.segments),1)
        self.assertEqual(g.segments[0].left_color, self.white)
        self.assertEqual(g.segments[0].right_color, self.black)

        self.checkColorMapAndGradientEquivalent(colorlist)

    def testFromUgr(self):
        pt = fractparser.parser.parse('''blatte10 {
gradient:
  title="blatte10" smooth=no index=0 color=3085069 index=25 color=3216141
  index=56 color=10761236 index=83 color=1408165 index=92 color=4050153
  index=110 color=18018 index=134 color=0 index=213 color=5183243 index=284
  color=11494485 index=358 color=0 index=384 color=144
opacity:
  smooth=no index=0 opacity=255
}
''')
        t = translate.GradientFunc(pt.children[0],"f")
        g = gradient.Gradient()
        g.load_ugr(t)

        self.assertWellFormedGradient(g)
        self.assertEqual(len(g.segments),12)
            
    def testFromColormap2(self):
        # create a longer one
        colorlist = [
            (0.0, 255,0,0, 255),
            (0.5, 0,255,0, 255),
            (1.0, 0, 0, 255, 255)]
        g = gradient.Gradient()
        g.load_list(colorlist)
        self.assertWellFormedGradient(g)
        self.assertEqual(len(g.segments),2)
        self.assertEqual(g.segments[0].left_color, self.red)
        self.assertEqual(g.segments[0].right_color, self.green)
        self.assertEqual(g.segments[1].left, 0.5)
        self.assertEqual(g.segments[1].left_color, self.green)
        self.assertEqual(g.segments[1].right_color, self.blue)

        self.checkColorMapAndGradientEquivalent(colorlist)            
            
    def testFromColormap3(self):
        # create a short, compressible one
        colorlist = [
            (0.0, 0, 0, 0, 255),
            (0.5, 127, 127, 127, 255),
            (1.0, 255, 255, 255, 255)]

        g = gradient.Gradient()
        g.load_list(colorlist)
        self.assertWellFormedGradient(g)
        self.assertEqual(len(g.segments),1)

    def testfromColormap4(self):
        # this should always produce 255 segments
        colorlist = self.colorMapFromFile("maps/4zebbowx.map")
        grad = self.checkColorMapAndGradientEquivalent(colorlist)
        self.assertEqual(len(grad.segments),255)

    def testfromColormapHlsrain(self):
        # this map once caused issues
        colorlist = self.colorMapFromFile("maps/hlsrain5.map")
        grad = self.checkColorMapAndGradientEquivalent(colorlist)

    def testFromColormapCompressible(self):
        colorlist = self.colorMapFromFile("maps/Gallet02.map")
        grad = self.checkColorMapAndGradientEquivalent(colorlist)
        self.assertTrue(len(grad.segments) < 255,"should have been compressed")

    def testFromColormapLossyCompression(self):
        colorlist = self.colorMapFromFile("maps/Gallet02.map")
        grad = self.checkColorMapAndGradientEquivalent(colorlist, 2)
        
    def colorMapFromFile(self, name):
        f = open(name,"r")
        i = 0
        colorlist = []
        rgb_re = re.compile(r'\s*(\d+)\s+(\d+)\s+(\d+)')
        for line in f:
            m = rgb_re.match(line)
            if m != None:
                (r,g,b) = (int(m.group(1)),
                           int(m.group(2)),
                           int(m.group(3)))

                # in case they're over 255 - as some badly-behaved
                # Fractint gradients are 
                [r,g,b] = [min(x,255) for x in [r,g,b]]

                if i == 0:
                    # first color is inside solid color
                    pass 
                else:
                    colorlist.append(((i-1)/255.0,r,g,b,255))
            i += 1

        f.close()
        return colorlist

    def testCopy(self):
        # check that copy.copy() doesn't share state
        g1 = self.create_rgb_gradient()

        s1 = g1.serialize()
        g2 = copy.copy(g1)

        s2 =g2.serialize()
        self.assertEqual(s1,s2)

        g1.segments[0].bmode = gradient.Blend.CURVED

        s3=g2.serialize()
        self.assertEqual(s2,s3)
        
    def testGradientCmap(self):
        g = gradient.Gradient()
        self.checkCGradientAndPyGradientEquivalent(g)

        g.segments[0].mid = 0.2
        self.checkCGradientAndPyGradientEquivalent(g)

        g.segments[0].bmode = gradient.Blend.CURVED
        self.checkCGradientAndPyGradientEquivalent(g)

        g.segments[0].bmode = gradient.Blend.SINE
        self.checkCGradientAndPyGradientEquivalent(g)

        g.segments[0].bmode = gradient.Blend.SPHERE_INCREASING
        self.checkCGradientAndPyGradientEquivalent(g)

        g.segments[0].bmode = gradient.Blend.SPHERE_DECREASING
        self.checkCGradientAndPyGradientEquivalent(g)

        g = self.create_rgb_gradient()
        self.checkCGradientAndPyGradientEquivalent(g)
        
    def create_rgb_gradient(self):
        # make a simple gradient which goes from R -> G -> B
        g = gradient.Gradient()
        g.segments = [
           gradient.Segment(0.0, self.red, 0.333, self.red),
           gradient.Segment(0.333, self.green, 0.667, self.green),
           gradient.Segment(0.667, self.blue, 1.0, self.blue)]
        return g
    
    def testGetSegments(self):
        g = self.create_rgb_gradient()
        self.assertWellFormedGradient(g)
        self.assertEqual(g.get_segment_at(0.0), g.segments[0])
        self.assertEqual(g.get_segment_at(0.5), g.segments[1])
        self.assertEqual(g.get_segment_at(1.0), g.segments[2])

        self.assertEqual(g.get_segment_at(0.333), g.segments[0])
        self.assertEqual(g.get_segment_at(0.667), g.segments[1])
        
        self.assertRaises(IndexError, g.get_segment_at, -1.0)
        self.assertRaises(IndexError, g.get_segment_at, 2.0)

    def testGetSegmentIndexes(self):
        g = self.create_rgb_gradient()
        self.assertWellFormedGradient(g)
        self.assertEqual(g.get_index_at(0.0), 0)
        self.assertEqual(g.get_index_at(0.5), 1)
        self.assertEqual(g.get_index_at(1.0), 2)

        self.assertEqual(g.get_index_at(0.333), 0)
        self.assertEqual(g.get_index_at(0.667), 1)
        
        self.assertRaises(IndexError, g.get_index_at, -1.0)
        self.assertRaises(IndexError, g.get_index_at, 2.0)

    def testLinearSegment(self):
        seg = gradient.Segment(0.0, self.red, 0.333, self.red)
        self.assertEqual(seg.get_linear_factor(0.0, 0.5),0.0)
        self.assertEqual(seg.get_linear_factor(0.5, 0.5),0.5)
        self.assertEqual(seg.get_linear_factor(1.0, 0.5),1.0)

        # middle close to left end
        self.assertEqual(seg.get_linear_factor(0.0, 0.0),0.0)
        self.assertEqual(seg.get_linear_factor(0.5, 0.0),0.75)
        self.assertEqual(seg.get_linear_factor(1.0, 0.0),1.0)

        # middle close to right end
        self.assertEqual(seg.get_linear_factor(0.0, 1.0),0.0)
        self.assertEqual(seg.get_linear_factor(0.5, 1.0),0.25)
        self.assertEqual(seg.get_linear_factor(1.0, 1.0),0.5)

    def testVeryShortSegment(self):
        seg = gradient.Segment(0.0, self.black, 0.0, self.white)
        self.assertEqual(seg.get_color_at(0.0), self.mid_grey)
        self.assertEqual(seg.get_color_at(0.5), self.mid_grey)
        self.assertEqual(seg.get_color_at(1.0), self.mid_grey)
        
    def testGetFlatColors(self):
        g = self.create_rgb_gradient()
        self.assertWellFormedGradient(g)
        self.assertEqual(g.get_color_at(0.0), self.red)
        self.assertEqual(g.get_color_at(0.3), self.red)
        self.assertEqual(g.get_color_at(0.333), self.red)
        self.assertEqual(g.get_color_at(0.334), self.green)
        self.assertEqual(g.get_color_at(0.666), self.green)
        self.assertEqual(g.get_color_at(0.668), self.blue)
        self.assertEqual(g.get_color_at(1.0), self.blue)

    def checkGreyGradient(self, g, midpoint, oracle):
        self.assertWellFormedGradient(g)
        
        for i in range(256):
            x = i * 1.0/256.0
            fx = oracle(x,midpoint)

            self.assertTrue(0.0 <= fx <= 1.0,
                            "dubious value %f for %f" % (fx,x))
            
            col = g.get_color_at(x)
            expected = [fx,fx,fx,1.0]
            self.assertNearlyEqual(col, expected,
                                   "%s != %s for %s (int %s)" % \
                                   (col, expected, x, i))

        # should be 0 at start, 1 at end
        self.assertEqual(g.get_color_at(0.0), [0.0, 0.0, 0.0, 1.0])
        self.assertEqual(g.get_color_at(1.0), [1.0, 1.0, 1.0, 1.0])
                
        # should be halfway at the midpoint
        self.assertEqual(g.get_color_at(midpoint), [0.5, 0.5, 0.5, 1.0])

    def testGreyGradient(self):
        g = gradient.Gradient()

        # linear, central midpoint
        g.segments[0].mid = 0.5
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        # linear, off-center midpoint
        def predict_025_linear(x, dummy):
            if x <= 0.25:
                fx = 0.5 * x/0.25
            else:
                fx = 0.5 + 0.5 * (x-0.25)/0.75
            return fx

        g.segments[0].mid = 0.25
        self.checkGreyGradient(g, 0.25, predict_025_linear)
        
        # curved, central midpoint
        # (curved = linear if midpoint = 0.5)
        g.segments[0].bmode = Blend.CURVED
        g.segments[0].mid = 0.5
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        # curved, non-central midpoint, sharper at the start
        def predict_025_curved(x, dummy):
            if x == 0.0:
                fx = 0.0
            else:
                fx = math.pow(x,math.log(0.5)/math.log(0.25))
            return fx

        g.segments[0].mid = 0.25
        self.checkGreyGradient(g, 0.25, predict_025_curved)

        # TODO: sine, sphere_increasing/decreasing
        
    def testAlphaChannel(self):
        g = gradient.Gradient()
        g.segments[0].left_color[3] = 0.5
        self.assertWellFormedGradient(g)
        for i in range(256):
            x = i * 1.0/256.0
            self.assertEqual(g.get_color_at(x), [x,x,x,0.5+x/2.0])

    def testSaveSegment(self):
        s = gradient.Segment(
            0.0, [0.0, 0.1, 0.2, 0.3],
            0.5, [0.4, 0.5, 0.6, 0.7])
        sio = io.StringIO()
        s.save(sio)
        self.assertEqual(
            "0.000000 0.250000 0.500000 0.000000 0.100000 0.200000 0.300000 0.400000 0.500000 0.600000 0.700000 0 0\n", sio.getvalue())

        s2 = gradient.Segment(
            0.5, [0.4, 0.5, 0.6, 0.7],
            0.8, [0.01, 0.02, 0.03, 0.04])

        self.assertEqual(True,s.left_of(s2))
        self.assertEqual(False,s.left_of(s))
        self.assertEqual(False,s2.left_of(s))

        self.assertEqual(True,s2.right_of(s))
        self.assertEqual(False,s.right_of(s))
        self.assertEqual(False,s.right_of(s2))

        s2.save(sio)
        self.assertEqual(
            """0.000000 0.250000 0.500000 0.000000 0.100000 0.200000 0.300000 0.400000 0.500000 0.600000 0.700000 0 0
0.500000 0.650000 0.800000 0.400000 0.500000 0.600000 0.700000 0.010000 0.020000 0.030000 0.040000 0 0
""", sio.getvalue())

        sio = io.StringIO()
        s.save(sio)
        s2.save(sio,True)

        self.assertEqual(
            """0.000000 0.250000 0.500000 0.000000 0.100000 0.200000 0.300000 0.400000 0.500000 0.600000 0.700000 0 0
+0.650000 0.800000 0.010000 0.020000 0.030000 0.040000 0 0
""", sio.getvalue())
        
    def testSaveMinimal(self):
        g = gradient.Gradient()
        s = io.StringIO()
        g.save(s)
        self.assertEqual(
            s.getvalue(),
            '''GIMP Gradient
1
0.000000 0.500000 1.000000 0.000000 0.000000 0.000000 1.000000 1.000000 1.000000 1.000000 1.000000 0 0
''')

    def testLoadSimple(self):
        g = gradient.Gradient()
        s = io.StringIO(wood)
        g.load(s)
        self.assertEqual(g.name, "Wood 2")
        self.assertEqual(len(g.segments), 9)

        # check round trip
        s2 = io.StringIO()
        g.save(s2)
        self.assertEqual(wood,s2.getvalue())

        g2 = gradient.Gradient()
        s2.seek(0,0)
        g2.load(s2)

        self.assertEqual(g,g2)
        
    def testLoadCompressed(self):
        g = gradient.Gradient()
        s = io.StringIO(wood)
        g.load(s)

        s2 = io.StringIO()
        g.save(s2,True)

        s2.seek(0,0)

        g_from_comp = gradient.Gradient()
        g_from_comp.load(s2)

        self.assertEqual(g,g_from_comp)
        
    def checkBadLoad(self, str):
        g = gradient.Gradient()
        s = io.StringIO(str)
        self.assertRaises(Exception, g.load,s)
        self.assertWellFormedGradient(g)
        
    def testBadLoad(self):        
        bad_files=[
            '''xxx''',
            '''GIMP Gradient''',
            '''GIMP Gradient
17
0.000000 0.500000 1.000000 0.000000 0.000000 0.000000 1.000000 1.000000 1.000000 1.000000 1.000000 0 0
''',
            '''GIMP Gradient
1
0.000000 0.500000 1.000000 0.000000 
''',
            '''GIMP Gradient
1
0.000000 0.500000 1.000000 0.000000 0.000000 0.000000 1.000000 1.000000 1.000000 1.000000 1.000000 foo 0
''']
        for file in bad_files:
            self.checkBadLoad(file)

    def testSetLeft(self):
        g = gradient.Gradient()

        g.add(0)

        # shouldn't be able to move leftmost segment
        self.assertEqual(g.set_left(0, -1.0),0.0)
        self.assertEqual(g.set_left(0,0.2),0.0)

        # should be able to move other one
        self.assertEqual(g.set_left(1,0.4),0.4)
        self.assertEqual(g.set_left(1,0.6),0.6)

        # but no further than midpoints
        self.assertEqual(g.set_left(1,0.2),0.25 + gradient.Segment.EPSILON)
        self.assertEqual(g.set_left(1,0.8),0.75 - gradient.Segment.EPSILON)

    def testSetRight(self):
        g = gradient.Gradient()

        g.add(0)

        # shouldn't be able to move rightmost segment
        self.assertEqual(g.set_right(1, -1.0),1.0)
        self.assertEqual(g.set_right(1,0.2),1.0)

        # should be able to move other one
        self.assertEqual(g.set_right(0,0.4),0.4)
        self.assertEqual(g.set_right(0,0.6),0.6)

        # but no further than midpoints
        self.assertEqual(g.set_right(0,0.2),0.25 + gradient.Segment.EPSILON)
        self.assertEqual(g.set_right(0,0.8),0.75 - gradient.Segment.EPSILON)

    def testSetMiddle(self):
        g = gradient.Gradient()

        # should be able to move 
        self.assertEqual(g.set_middle(0,0.4),0.4)
        self.assertEqual(g.set_middle(0,0.6),0.6)

        # but no further than endpoints
        self.assertEqual(g.set_middle(0,0.0),0.0 + gradient.Segment.EPSILON)
        self.assertEqual(g.set_middle(0,1.0),1.0 - gradient.Segment.EPSILON)
        
    def testAddSegment(self):
        # add some segments, ensure invariants hold and correct
        # outcome occurs.
        g = gradient.Gradient()

        # add a segment at left-hand end
        g.add(0)
        self.assertWellFormedGradient(g)
        self.assertEqual(len(g.segments),2)
        left = g.segments[0]
        right = g.segments[1]
        self.assertEqual(left.right_color, right.left_color)
        self.assertEqual(left.right_color,[0.5,0.5,0.5,1.0])
        self.assertEqual(right.right_color, [1.0, 1.0, 1.0, 1.0])
        self.assertEqual(left.mid, 0.25)
        self.assertEqual(left.right, 0.5)
        self.assertEqual(right.mid, 0.75)
        self.assertEqual(right.right, 1.0)

        # should have no effect on resulting pattern
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)
        
        # add another one
        g.add(0)
        self.assertWellFormedGradient(g)
        self.assertEqual(len(g.segments),3)
        left = g.segments[0]
        right = g.segments[1]
        self.assertEqual(left.right_color, right.left_color)
        self.assertEqual(left.right_color,[0.25,0.25,0.25,1.0])
        self.assertEqual(left.mid, 0.125)
        self.assertEqual(left.right, 0.25)
        self.assertEqual(right.mid, 0.375)
        self.assertEqual(right.right, 0.5)

        # still no effect
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        # one more at the other end
        g.add(len(g.segments)-1)
        self.assertWellFormedGradient(g)
        self.assertEqual(len(g.segments),4)
        left = g.segments[2]
        right = g.segments[3]
        self.assertEqual(left.right_color, right.left_color)
        self.assertEqual(left.right_color,[0.75,0.75,0.75,1.0])
        self.assertEqual(left.mid, 0.625)
        self.assertEqual(left.right, 0.75)
        self.assertEqual(right.mid, 0.875)
        self.assertEqual(right.right, 1.0)

        # still no effect
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

    def three_segments(self):
        # set up 3 equal segments
        return [
            gradient.Segment(0,self.black, 1.0/3.0, self.grey_33),
            gradient.Segment(1.0/3.0,self.grey_33, 2.0/3.0, self.grey_66),
            gradient.Segment(2.0/3.0,self.grey_66, 1.0, self.white)]

    def testRemove(self):
        # test removal of segments
        g = gradient.Gradient()

        # shouldn't be able to remove last segment
        self.assertRaises(gradient.Error, g.remove, 0.0)

        g.segments = self.three_segments()
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        # remove middle one
        g.remove(1)

        self.assertEqual(len(g.segments),2)
        self.assertWellFormedGradient(g)
        self.assertEqual(g.segments[0].right, 0.5)

        # recreate and remove left one
        g.segments = self.three_segments()
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        g.remove(0)
        
        self.assertEqual(len(g.segments),2)
        self.assertWellFormedGradient(g)
        self.assertEqual(g.segments[0].right, 2.0/3.0)

        # recreate and remove right one
        g.segments = self.three_segments()
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        g.remove(2)
        
        self.assertEqual(len(g.segments),2)
        self.assertWellFormedGradient(g)
        self.assertEqual(g.segments[1].left, 1.0/3.0)

    def testRemoveSmooth(self):
        # test removal of segments
        g = gradient.Gradient()

        g.segments = self.three_segments()
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        # remove middle one
        g.remove(1, True)
        
        self.assertEqual(len(g.segments),2)
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)
        self.assertEqual(g.segments[0].right, 0.5)

        # recreate and remove left one
        g.segments = self.three_segments()
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        g.remove(0,True)
        
        self.assertEqual(len(g.segments),2)
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)
        self.assertEqual(g.segments[0].right, 2.0/3.0)

        # recreate and remove right one
        g.segments = self.three_segments()
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)

        g.remove(2,True)
        
        self.assertEqual(len(g.segments),2)
        self.assertWellFormedGradient(g)
        self.checkGreyGradient(g, 0.5, lambda x,mid : x)
        self.assertEqual(g.segments[1].left, 1.0/3.0)

    def testLoadCS(self):
        g = gradient.Gradient()
        f = open("testdata/test.cs","rb")

        g.load_cs(f)
        self.assertEqual(8,len(g.segments))
        self.assertEqual(
            [ 0x1d/255.0 , 0x10/255.0, 0x10/255.0, 1.0],
            g.segments[0].left_color)

        f.seek(0)
        g.load(f)
        f.close()
        
    def testSetColor(self):
        g = gradient.Gradient()
        self.assertEqual(True, g.set_color(0,True,0.2,0.7,0.9))
        self.assertEqual(g.segments[0].left_color, [0.2,0.7,0.9,1.0])
        self.assertEqual(True, g.set_color(0,False,0.3,0.8,0.1))
        self.assertEqual(g.segments[0].right_color, [0.3,0.8,0.1,1.0])

    def testSetColorOutOfBounds(self):
        g = gradient.Gradient()
        self.assertEqual(False, g.set_color(-1,True,0.2,0.7,0.9))
        self.assertEqual(False, g.set_color(7,True,0.2,0.7,0.9))

    def assertNearlyEqual(self,a,b,msg, epsilon=1.0e-12):
        # check that each element is within epsilon of expected value
        for (ra,rb) in zip(a,b):
            d = abs(ra-rb)
            self.assertTrue(d < epsilon,msg)

    def assertWellFormedGradient(self, g):
        # check starts and sends at 0 and 1
        first_seg = g.segments[0]
        last_seg = g.segments[-1]
        self.assertEqual(first_seg.left, 0.0)
        self.assertEqual(last_seg.right, 1.0)

        # check segments line up and types are in range
        previous_seg = g.segments[0]
        for seg in g.segments[1:]:
            # check offsets
            self.assertTrue(0.0 <= seg.left <= 1.0)
            self.assertTrue(0.0 <= seg.right <= 1.0)
            self.assertTrue(
                seg.left <= seg.mid <= seg.right,
                "midpoint %g not between endpoints %g,%g" % \
                (seg.mid, seg.left, seg.right))

            # check colors
            self.assertEqual(len(seg.left_color),4)
            self.assertEqual(len(seg.right_color),4)
            for x in seg.left_color + seg.right_color:
                self.assertTrue(0.0 <= x <= 1.0)

            # check modes
            self.assertTrue(Blend.LINEAR <= seg.bmode <= Blend.SPHERE_DECREASING)
            self.assertTrue(ColorMode.RGB <= seg.cmode <= ColorMode.HSV_CW)

            # check offset chaining
            self.assertTrue(seg.right > seg.left)
            self.assertEqual(seg.left, previous_seg.right)
            previous_seg = seg
