#!/usr/bin/env python

import unittest
import math

import testbase

import fc
import fractal
import fract4dc
import image

from test_fractalsite import FractalSite

# centralized to speed up tests
g_comp = fc.Compiler()
g_comp.add_func_path("../formulas")
g_comp.load_formula_file("gf4d.frm")
g_comp.load_formula_file("gf4d.cfrm")
g_comp.load_formula_file("test.frm")

def sum(l):
    x = 0
    for a in l:
        x += a
    return x

class Test(testbase.TestBase):
    def setUp(self):
        global g_comp
        self.compiler = g_comp

        self.f = fractal.T(self.compiler)
        self.f.render_type = 2
        self.f.set_formula("test.frm", "test_hypersphere")
        self.f.compile()

        handle = fract4dc.pf_load(self.f.outputfile)
        self.pfunc = fract4dc.pf_create(handle)
        self.cmap = fract4dc.cmap_create_gradient(self.f.get_gradient().segments)
        (r,g,b,a) = self.f.solids[0]
        fract4dc.cmap_set_solid(self.cmap,0,r,g,b,a)
        (r,g,b,a) = self.f.solids[1]
        fract4dc.cmap_set_solid(self.cmap,1,r,g,b,a)

        initparams = self.f.all_params()
        fract4dc.pf_init(self.pfunc,self.f.params,initparams)

        self.im = image.T(40,30)
        siteobj = FractalSite()
        
        self.fw = fract4dc.fw_create(
            1,self.pfunc,self.cmap,self.im._img,self.f.site)

        self.ff = fract4dc.ff_create(
            [0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            2,
            100,
            0,
            1,
            self.pfunc,
            self.cmap,
            0,
            1,
            2, # 3D
            self.im._img,
            self.f.site,
            self.fw,
            False,
            1.0E-9)

    def tearDown(self):
        pass

    def testHyperSphereFormula(self):
        # check that a formula consisting of a simple 2.0-radius hypersphere
        # can be effectively ray-traced
        (iter,fate,dist,solid) = fract4dc.pf_calc(self.pfunc, [0.0, 0.0, 0.0, 0.0], 100)
        self.assertEqual(fate,32) # should be inside
        
        (iter,fate,dist,solid) = fract4dc.pf_calc(self.pfunc, [-2.5, 0.0, 0.0, 0.0], 100)
        self.assertEqual(fate,0) # should be outside

    def intersect_sphere(self, eye, look):
        # closed form for where we should intersect the hypersphere
        # based on http://stevehollasch.com/thesis/chapter5.html

        # v = sphere.center - ray.origin
        v = [ a - b for (a,b) in zip([0,0,0,0], eye)]

        bb = sum([a*b for (a,b) in zip(v,look)])

        rad = bb * bb - sum([a * b for (a,b) in zip(v,v)]) + 4.0

        if rad < 0:
            # no intersection
            return (False, None)

        rad = math.sqrt(rad)
        t2 = bb - rad
        t1 = bb + rad

        # set t1 to smallest non-negative value (nearest point)
        if t1 < 0 or (t2 > 0 and t2 < t1):
            t1 = t2

        if t1 < 0:
            return (False, None) # sphere behind eye

        t1_ray = [t1 * a for a in look]
        intersection = [a+b for (a,b) in zip(eye,t1_ray)]
        
        return (True, intersection)

    def testLookVector(self):
        # check that looking at different points in screen works

        # top-left corner
        look = fract4dc.ff_look_vector(self.ff,0,0)
        big_look = [(-19.5/40) * 4.0, (14.5/30)*3.0, 40.0, 0.0]
        mag = math.sqrt(sum([x*x for x in big_look]))
        exp_look = tuple([x/mag for x in big_look])
        self.assertNearlyEqual(look, exp_look)

        # center of the screen (betwen pixels)
        look = fract4dc.ff_look_vector(self.ff,19.5,14.5)
        big_look = [0, 0, 40.0, 0.0]
        mag = math.sqrt(sum([x*x for x in big_look]))
        exp_look = tuple([x/mag for x in big_look])
        self.assertNearlyEqual(look, exp_look)

        # root finding experiments

        # going straight ahead, root should be at -2.0
        eye = [0,0,-40.0,0]
        (is_hit,root) = fract4dc.fw_find_root(self.fw, eye ,look)
        lookfor = [0.0, 0.0, -2.0, 0.0]
        self.assertEqual(is_hit, True)
        self.assertNearlyEqual(root, lookfor, 1.0e-10)

        # check each pixel against closed-form results
        for y in xrange(0,30):
            for x in xrange(0,40):
                look = fract4dc.ff_look_vector(self.ff,x,y)
                (is_hit,root) = fract4dc.fw_find_root(self.fw, [0,0,-40.0,0],look)
                (should_be_hit, real_root) = self.intersect_sphere(eye,look)
                self.assertEqual(is_hit, should_be_hit)
                if is_hit:
                    self.assertNearlyEqual(root, real_root,1e-10)

    def testDraw(self):
        fract4dc.calc(
            params = self.f.params,
            antialias = self.f.antialias,
            maxiter=self.f.maxiter,
            yflip=self.f.yflip,
            periodicity=self.f.periodicity,
            pfo=self.pfunc,
            cmap=self.cmap,
            auto_deepen=self.f.auto_deepen,
            nthreads=1,
            render_type=2, # 3D
            image=self.im._img,
            site=self.f.site)

        self.im.save("hs.tga")
        
    def testDrawMBrot(self):
        self.f.set_formula("gf4d.frm", "Mandelbrot")
        self.f.compile()
        im = image.T(80,60)
        self.f.draw(im)
        im.save("mb.tga")
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

