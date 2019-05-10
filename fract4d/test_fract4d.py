#!/usr/bin/env python3

import os.path
import struct
import math

from . import testbase

from fract4d import fract4dc, gradient, image, messages

from .test_fractalsite import FractalSite

pos_params = [
    0.0, 0.0, 0.0, 0.0,
    4.0,
    0.0, 0.0, 0.0, 0.0,0.0, 0.0
    ]
class Test(testbase.ClassSetup):
    def compileMandel(self):
        f = self.compiler.get_formula("gf4d.frm","Mandelbrot")
        cg = self.compiler.compile(f)
        self.compiler.generate_code(f,cg,Test.pf_name)

    def compileColorMandel(self):
        cf1 = self.compiler.get_formula("gf4d.cfrm","default","cf0")
        self.assertEqual(len(cf1.errors),0)
        self.compiler.compile(cf1)
        
        cf2 = self.compiler.get_formula("gf4d.cfrm","zero","cf1")
        self.assertEqual(len(cf2.errors),0)
        self.compiler.compile(cf2)
        
        f = self.compiler.get_formula("gf4d.frm","Mandelbrot")

        self.color_mandel_params = f.symbols.default_params() + \
                                   cf1.symbols.default_params() + \
                                   cf2.symbols.default_params()

        return self.compiler.compile_all(f,cf1,cf2,[])

    def compileColorDiagonal(self):
        cf1 = self.compiler.get_formula("gf4d.cfrm","default","cf0")
        self.assertEqual(len(cf1.errors),0)

        cf2 = self.compiler.get_formula("gf4d.cfrm","zero","cf1")
        self.assertEqual(len(cf2.errors),0)
        self.compiler.compile(cf2)
        
        f = self.compiler.get_formula("test.frm","test_simpleshape")
        outputfile = self.compiler.compile_all(f,cf1,cf2,[])

        self.color_diagonal_params = f.symbols.default_params() + \
                                     cf1.symbols.default_params() + \
                                     cf2.symbols.default_params()

        return outputfile
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pf_name = os.path.join(cls.tmpdir.name, "test-pf.so")

    def setUp(self):
        self.compiler = Test.g_comp
        self.compiler.load_formula_file("gf4d.frm")
        self.compiler.load_formula_file("gf4d.cfrm")
        self.gradient = gradient.Gradient()
        
    def tearDown(self):
        pass

    def disabled_testGetDefaults(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)

        ret = fract4dc.pf_defaults(
            pfunc,0.001,pos_params, [self.gradient, 0.0, 0.0])
        self.assertTrue(isinstance(ret, list))
        self.assertEqual(3,len(ret))
        self.assertEqual([None,4.0,1.0],ret)

    def testBasic(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)

        fract4dc.pf_init(pfunc,pos_params, [self.gradient, 4.0, 0.5])
        
        # a point which doesn't bail out
        result = fract4dc.pf_calc(pfunc,[0.15, 0.0, 0.0, 0.0],100,0,0,0)
        self.assertEqual(result,(100, 32, 0.0,0))
        
        # one which does
        result = fract4dc.pf_calc(pfunc,[1.0, 1.0, 0.0, 0.0],100,0,0,0)
        self.assertEqual(result,(1,0, 0.0,0)) 

        # one which is already out
        result = fract4dc.pf_calc(pfunc,[17.5, 14.0, 0.0, 0.0],100,0,0,0)
        self.assertEqual(result,(0, 0, 0.0,0)) 

        # without optional args
        result = fract4dc.pf_calc(pfunc,[17.5, 14.0, 0.0, 0.0],100)
        self.assertEqual(result,(0, 0, 0.0,0)) 
        
        pfunc = None
        handle = None

    def makeWorkerAndFunc(self, image, cmap):
        siteobj = FractalSite()
        site = fract4dc.site_create(siteobj)

        file = self.compileColorDiagonal()
        handle = fract4dc.pf_load(file)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params, self.color_diagonal_params)

        fw = fract4dc.fw_create(1,pfunc,cmap,image,site)
        ff = fract4dc.ff_create(
            [0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            2,
            100,
            0,
            1,
            pfunc,
            cmap,
            0,
            1,
            0,
            image,
            site,
            fw,
            False,
            1.0E-9)

        return (fw,ff,site,handle,pfunc)

    def testVectors(self):
        siteobj = FractalSite()
        site = fract4dc.site_create(siteobj)

        file = self.compileColorDiagonal()
        handle = fract4dc.pf_load(file)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params,self.color_diagonal_params)

        (w,h,tw,th) = (40,20,40,20)
        im = image.T(w,h)
        
        cmap = fract4dc.cmap_create([(1.0, 255, 255, 255, 255)])

        fw = fract4dc.fw_create(1,pfunc,cmap,im._img,site)
        
        ff = fract4dc.ff_create(
            [0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            2,
            100,
            0,
            1,
            pfunc,
            cmap,
            0,
            1,
            0,
            im._img,
            site,
            fw,
            False,
            1.0E-9)

        # check dx, dy and topleft
        dx = fract4dc.ff_get_vector(ff, fract4dc.DELTA_X)
        self.assertNearlyEqual(dx, [4.0/tw,0.0,0.0,0.0])

        dy = fract4dc.ff_get_vector(ff, fract4dc.DELTA_Y);
        self.assertNearlyEqual(dy, [0.0,-2.0/th,0.0,0.0])

        topleft = fract4dc.ff_get_vector(ff, fract4dc.TOPLEFT);
        self.assertNearlyEqual(topleft, [-2.0 + 4.0/(tw*2),1.0 - 2.0/(th*2),0.0,0.0])

        # check they are updated if image is bigger
        (w,h,tw,th) = (40,20,400,200)
        im = image.T(w,h,tw,th)
        
        fw = fract4dc.fw_create(1,pfunc,cmap,im._img,site)
        
        ff = fract4dc.ff_create(
            [0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            2,
            100,
            0,
            1,
            pfunc,
            cmap,
            0,
            1,
            0,
            im._img,
            site,
            fw,
            False,
            1.0E-9)

        # check dx, dy and topleft
        dx = fract4dc.ff_get_vector(ff, fract4dc.DELTA_X)
        self.assertNearlyEqual(dx, [4.0/tw,0.0,0.0,0.0])

        dy = fract4dc.ff_get_vector(ff, fract4dc.DELTA_Y);
        self.assertNearlyEqual(dy, [0.0,-2.0/th,0.0,0.0])

        topleft = fract4dc.ff_get_vector(ff, fract4dc.TOPLEFT);
        self.assertNearlyEqual(topleft, [-2.0 + 4.0/(tw*2),1.0 - 2.0/(th*2),0.0,0.0])

        offx = 40
        offy = 10
        im.set_offset(offx, offy)

        fw = fract4dc.fw_create(1,pfunc,cmap,im._img,site)
        
        ff = fract4dc.ff_create(
            [0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            2,
            100,
            0,
            1,
            pfunc,
            cmap,
            0,
            1,
            0,
            im._img,
            site,
            fw,
            False,
            1.0E-9)

        # check dx, dy and topleft
        dx = fract4dc.ff_get_vector(ff, fract4dc.DELTA_X)
        self.assertNearlyEqual(dx, [4.0/tw,0.0,0.0,0.0])

        dy = fract4dc.ff_get_vector(ff, fract4dc.DELTA_Y);
        self.assertNearlyEqual(dy, [0.0,-2.0/th,0.0,0.0])

        topleft = fract4dc.ff_get_vector(ff, fract4dc.TOPLEFT);
        self.assertNearlyEqual(topleft, [
            -2.0 + dx[0] * (offx + 0.5),
             1.0 + dy[1] * (offy + 0.5),
            0.0,0.0])        
                
    def testFractWorker(self):
        xsize = 8
        ysize = 8
        im = image.T(xsize,ysize)
        
        cmap = fract4dc.cmap_create([(1.0, 255, 255, 255, 255)])

        fract4dc.cmap_set_solid(cmap,0,0,0,0,255)
        fract4dc.cmap_set_solid(cmap,1,0,0,0,255)
        
        (fw,ff,site,handle,pfunc) = self.makeWorkerAndFunc(im._img,cmap)

        im.clear()
        fate_buf = im.fate_buffer()
        buf = im.image_buffer() 
        
        # draw 1 pixel, check it's set properly
        fract4dc.fw_pixel(fw,0,0,1,1)
        self.assertPixelIs(im,0,0,[im.OUT]+[im.UNKNOWN]*3)

        fract4dc.fw_pixel(fw,0,4,1,1)
        self.assertPixelIs(im,0,4,[im.IN]+[im.UNKNOWN]*3)
        
        # draw it again, check no change.
        fract4dc.fw_pixel(fw,0,0,1,1)
        self.assertPixelIs(im,0,0,[im.OUT]+[im.UNKNOWN]*3)

        # draw & antialias another pixel
        fract4dc.fw_pixel(fw,2,2,1,1)
        fract4dc.fw_pixel_aa(fw,2,2)
        self.assertPixelIs(im,2,2,[im.OUT, im.OUT, im.IN, im.OUT])

        # change cmap, draw same pixel again, check color changes
        cmap = fract4dc.cmap_create(
            [(1.0, 79, 88, 41, 255)])
        fract4dc.cmap_set_solid(cmap,1,100,101,102,255)
        
        (fw,ff,site,handle,pfunc) = self.makeWorkerAndFunc(im._img,cmap)

        fract4dc.fw_pixel(fw,0,0,1,1)
        self.assertPixelIs(im,0,0,[im.OUT]+[im.UNKNOWN]*3, [79,88,41])

        # redraw antialiased pixel
        fract4dc.fw_pixel_aa(fw,2,2)
        self.assertPixelIs(
            im,2,2, [im.OUT, im.OUT, im.IN, im.OUT],
            [79,88,41], [100,101,102])

        # draw large block overlapping existing pixels
        fract4dc.fw_pixel(fw,0,0,4,4)
        self.assertPixelIs(
            im,0,0, [im.OUT, im.UNKNOWN, im.UNKNOWN, im.UNKNOWN],
            [79,88,41], [100,101,102])

        self.assertPixelIs(
            im,3,1, [im.UNKNOWN]*4,
            [79,88,41], [100,101,102], im.OUT)        

    def testMultiThreadedCalc(self):
        xsize = 64
        ysize = int(xsize * 3.0/4.0)
        im = image.T(xsize,ysize)
        siteobj = FractalSite()
        site = fract4dc.site_create(siteobj)

        file = self.compileColorMandel()
        handle = fract4dc.pf_load(file)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params,self.color_mandel_params)
        cmap = fract4dc.cmap_create(
            [(0.0,0,0,0,255),
             (1/256.0,255,255,255,255),
             (1.0, 255, 255, 255, 255)])
        fract4dc.calc(
            params=[0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=4,
            pfo=pfunc,
            cmap=cmap,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=im._img,
            site=site)

        self.assertEqual(siteobj.progress_list[-1], 0.0)
        self.assertEqual(siteobj.progress_list[-2], 1.0)                        

        self.assertTrue(siteobj.image_list[-1]==(0,0,xsize,ysize))

        self.assertTrue(siteobj.status_list[0]== 1 and \
                         siteobj.status_list[-1]== 0)

        test1_tga = os.path.join(Test.tmpdir.name, "test1.tga")
        self.assertTrue(not os.path.exists(test1_tga))
        im.save(test1_tga)
        self.assertTrue(os.path.exists(test1_tga))

        # fate of all non-aa pixels should be known, aa-pixels unknown
        fate_buf = im.fate_buffer()
        i = 0
        for byte in fate_buf:
            d = im.get_color_index(
                    (i % (im.FATE_SIZE * xsize)) // im.FATE_SIZE,
                    i // (im.FATE_SIZE * xsize),
                    i % im.FATE_SIZE)
            
            if i % 4 == 0:
                # no-aa
                self.assertNotEqual(byte, 255,
                                    "pixel %d is %d" % (i,byte))
                self.assertNotEqual("%g" % d,"inf")
            else:
                self.assertEqual(byte, 255)
            i+= 1

        self.assertPixelCount(xsize,ysize,siteobj)

    def assertPixelCount(self,xsize,ysize,siteobj):
        # total pixels calculated should == w*h        
        self.assertEqual(xsize*ysize,siteobj.stats_list[-1].pixels)
        for stats in siteobj.stats_list:            
            # pixels calced + pixels skipped = pixels
            self.assertEqual(
                stats.pixels,stats.pixels_calculated + stats.pixels_skipped)
            # pixels inside + pixels outside = pixels calculated
            self.assertEqual(
                stats.pixels_calculated, stats.pixels_inside + stats.pixels_outside)

    def testCalc(self):
        xsize = 64
        ysize = int(xsize * 3.0/4.0)
        im = image.T(xsize,ysize)
        siteobj = FractalSite()
        site = fract4dc.site_create(siteobj)

        file = self.compileColorMandel()
        handle = fract4dc.pf_load(file)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params,self.color_mandel_params)
        cmap = fract4dc.cmap_create(
            [(0.0,0,0,0,255),
             (1/256.0,255,255,255,255),
             (1.0, 255, 255, 255, 255)])
        fract4dc.calc(
            params=[0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=1,
            pfo=pfunc,
            cmap=cmap,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=im._img,
            site=site)

        self.assertEqual(siteobj.progress_list[-1], 0.0)
        self.assertEqual(siteobj.progress_list[-2], 1.0)                        

        self.assertTrue(siteobj.image_list[-1]==(0,0,xsize,ysize))

        self.assertTrue(siteobj.status_list[0]== 1 and \
                         siteobj.status_list[-1]== 0)

        test2_tga = os.path.join(Test.tmpdir.name, "test2.tga")
        self.assertTrue(not os.path.exists(test2_tga))
        im.save(test2_tga)
        self.assertTrue(os.path.exists(test2_tga))

        # fate of all non-aa pixels should be known, aa-pixels unknown
        fate_buf = im.fate_buffer()
        i = 0
        for byte in fate_buf:
            d = im.get_color_index(
                    (i % (im.FATE_SIZE * xsize)) // im.FATE_SIZE,
                    i // (im.FATE_SIZE * xsize),
                    i % im.FATE_SIZE)
            
            if i % 4 == 0:
                # no-aa
                self.assertNotEqual(byte, 255,
                                    "pixel %d is %d" % (i,byte))
                self.assertNotEqual("%g" % d,"inf")
            else:
                self.assertEqual(byte, 255)
            i+= 1

        self.assertPixelCount(xsize,ysize,siteobj)

    def testConstants(self):
        self.assertEqual(fract4dc.CALC_DONE, 0)
        self.assertEqual(fract4dc.CALC_DEEPENING, 2)
        self.assertEqual(fract4dc.AA_FAST, 1)

    def testAACalc(self):
        xsize = 64
        ysize = int(xsize * 3.0/4.0)
        im = image.T(xsize,ysize)
        siteobj = FractalSite()
        site = fract4dc.site_create(siteobj)

        file = self.compileColorMandel()
        handle = fract4dc.pf_load(file)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params,self.color_mandel_params)
        cmap = fract4dc.cmap_create(
            [(0.0,0,0,0,255),
             (1/256.0,255,255,255,255),
             (1.0, 255, 255, 255, 255)])
        fract4dc.calc(
            params=[0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            antialias=1,
            maxiter=100,
            yflip=0,
            nthreads=1,
            pfo=pfunc,
            cmap=cmap,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=im._img,
            site=site)

        # fate of all pixels should be known
        fate_buf = im.fate_buffer()
        i = 0
        for byte in fate_buf:
            d = im.get_color_index(
                    (i % (im.FATE_SIZE * xsize)) // im.FATE_SIZE,
                    i // (im.FATE_SIZE * xsize),
                    i % im.FATE_SIZE)

            self.assertNotEqual("%g" % d,"inf", "index %d is %g" % (i,d))
            self.assertNotEqual(byte, 255,
                                "pixel %d is %d" % (i, byte))
            i+= 1

    def testRotMatrix(self):
        params = [0.0, 0.0, 0.0, 0.0,
                 1.0,
                 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        mat = fract4dc.rot_matrix(params)
        self.assertEqual(mat, ((1.0, 0.0, 0.0, 0.0),
                               (0.0, 1.0, 0.0, 0.0),
                               (0.0, 0.0, 1.0, 0.0),
                               (0.0, 0.0, 0.0, 1.0)))

        vec = fract4dc.eye_vector(params,1.0)
        self.assertEqual(vec, (-0.0, -0.0, -1.0, -0.0))
        
        params[6] = math.pi/2.0
        mat = fract4dc.rot_matrix(params)
        self.assertNearlyEqual(mat, ((0.0, 0.0, 1.0, 0.0),
                                     (0.0, 1.0, 0.0, 0.0),
                                     (-1.0, 0.0, 0.0, 0.0),
                                     (0.0, 0.0, 0.0, 1.0)))

        vec = fract4dc.eye_vector(params,10.0)
        self.assertNearlyEqual(vec, (10.0, -0.0, -0.0, -0.0))
                        
    def testFDSite(self):
        xsize = 64
        ysize = int(xsize * 3.0/4.0)
        im = image.T(xsize,ysize)
        (rfd,wfd) = os.pipe()
        site = fract4dc.fdsite_create(wfd)

        file = self.compileColorMandel()

        for x in range(2):
            handle = fract4dc.pf_load(file)
            pfunc = fract4dc.pf_create(handle)
            fract4dc.pf_init(pfunc,pos_params,self.color_mandel_params)
            cmap = fract4dc.cmap_create(
                [(0.0,0,0,0,255),
                 (1/256.0,255,255,255,255),
                 (1.0, 255, 255, 255, 255)])

            fract4dc.calc(
                params=[0.0, 0.0, 0.0, 0.0,
                 4.0,
                 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                antialias=0,
                maxiter=100,
                yflip=0,
                nthreads=1,
                pfo=pfunc,
                cmap=cmap,
                auto_deepen=0,
                periodicity=1,
                render_type=0,
                image=im._img,
                site=site,
                asynchronous=True)

            nrecved = 0
            while True:
                if nrecved == x:
                    #print "hit message count"
                    fract4dc.interrupt(site)
                
                nb = 2*4
                bytes = os.read(rfd,nb)
                if len(bytes) < nb:
                    self.fail("bad message with length %s, value %s" % (len(bytes), bytes))
                    break

                (t,size) = struct.unpack("2i",bytes)
                #print "read %d, len %d" % (t,size)

                # read the rest of the message
                bytes = os.read(rfd,size)
                if len(bytes) < size:
                    self.fail("bad message")
                    break
                
                msg = messages.parse(t, bytes)
                #print "msg: %s" % msg.show()
                if msg.name == "Status" and msg.status == 0:
                    #done
                    #print "done"
                    break
                
                nrecved += 1
            
    def testDirtyFlagFullRender(self):
        '''Render the same image 2x with different colormaps.

        First, with the dirty flag set for a full redraw.  Second,
        with the dirty flag clear. The end result should be the same
        in both cases'''

        # this doesn't work reliably - looks like uninitialized memory
        # used occasionally or something weird.
        buf1 = self.drawTwice(True,64)
        buf2 = self.drawTwice(False,64)

        i=0
        for (a,b) in zip(list(buf1), list(buf2)):
            if a != b:
                print("%s != %s at %d" % (a,b,i))
                self.assertEqual(a,b)
            i += 1

    def testLargeImageDirtyFlagFullRender(self):
        '''Test we can draw and redraw a large image.'''

        buf1 = self.drawTwice(True,1025)
        buf2 = self.drawTwice(False,1025)

        i=0
        for (a,b) in zip(list(buf1), list(buf2)):
            if a != b:
                print("%s != %s at %d" % (a,b,i))
                self.assertEqual(a,b)
            i += 1

        
    def drawTwice(self,is_dirty,xsize):
        ysize = int(xsize * 3.0/4.0)
        im = image.T(xsize,ysize)
        siteobj = FractalSite()
        site = fract4dc.site_create(siteobj)

        file = self.compileColorMandel()
        handle = fract4dc.pf_load(file)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params,self.color_mandel_params)

        cmap = fract4dc.cmap_create(
            [(1.0, 255, 255, 255, 255)])
        
        fract4dc.calc(
            params=[0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=1,
            pfo=pfunc,
            cmap=cmap,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=im._img,
            site=site,
            dirty=is_dirty)

        #print "1st pass %s" % is_dirty
        #fract4dc.image_save(image, "/tmp/pass1%d.tga" % is_dirty)
        #self.print_fates(image,xsize,ysize)
        
        cmap = fract4dc.cmap_create(
            [(1.0, 76, 49, 189, 255)])

        fract4dc.calc(
            params=[0.0, 0.0, 0.0, 0.0,
             4.0,
             0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            antialias=0,
            maxiter=100,
            yflip=0,
            nthreads=1,
            pfo=pfunc,
            cmap=cmap,
            auto_deepen=0,
            periodicity=1,
            render_type=0,
            image=im._img,
            site=site,
            dirty=is_dirty)

        #print "2nd pass %s" % is_dirty
        #self.print_fates(image,xsize,ysize)
        im.save(os.path.join(Test.tmpdir.name, "pass2%d.tga" % is_dirty))
        
        return [] # fract4dc.image_buffer(image)
        
    def testMiniTextRender(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc,pos_params,[0,4.0])
        image = []
        for y in range(-20,20):
            line = []
            for x in range(-20,20):
                (iter,fate,dist,solid) = fract4dc.pf_calc(pfunc,[x/10.0,y/10.0,0,0],100)
                if(fate == 32):
                    line.append("#")
                else:
                    line.append(" ")
            image.append("".join(line))
        printable_image = "\n".join(image)
        self.assertEqual(printable_image[0], " ", printable_image)
        self.assertEqual(printable_image[20*41+20],"#", printable_image) # in the middle
        #print printable_image # shows low-res mbrot in text mode 
        
    def testBadLoad(self):
        # wrong arg type/number
        self.assertRaises(TypeError,fract4dc.pf_load,1)
        self.assertRaises(TypeError,fract4dc.pf_load,"foo","bar")

        # nonexistent
        self.assertRaises(ValueError,fract4dc.pf_load,"garbage.xxx")

        # not a DLL
        self.assertRaises(ValueError,fract4dc.pf_load,"test_pf.py")

    def testBadInit(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)
        self.assertRaises(TypeError,fract4dc.pf_init,pfunc,pos_params,72)
        self.assertRaises(ValueError,fract4dc.pf_init,7,pos_params, [0.4])
        self.assertRaises(ValueError,fract4dc.pf_init,pfunc,pos_params,[0.0]*201)
        self.assertRaises(ValueError,fract4dc.pf_init,pfunc,"fish",72)
        self.assertRaises(ValueError,fract4dc.pf_init,pfunc,[0.0]*12,72)
        pfunc = None
        handle = None

    def testIntInit(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc, pos_params, [1,2,3,4])
        
    def testBadCalc(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)
        fract4dc.pf_init(pfunc, pos_params, [])
        self.assertRaises(ValueError,fract4dc.pf_calc,0,[1.0,2.0,3.0,4.0],100)
        self.assertRaises(TypeError,fract4dc.pf_calc,pfunc,[1.0,2.0,3.0],100)
        pfunc = None

    def testShutdownOrder(self):
        self.compileMandel()
        handle = fract4dc.pf_load(Test.pf_name)
        pfunc = fract4dc.pf_create(handle)
        pfunc2 = fract4dc.pf_create(handle)
        handle = None
        pfunc = None
        pfunc2 = None

    def testCmap(self):
        cmap = fract4dc.cmap_create(
            [(0.0,255,0,100,255), (1.0, 0, 255, 50, 255)])

        self.assertEqual(fract4dc.cmap_lookup(cmap,0.0), (255,0,100,255))
        self.assertEqual(fract4dc.cmap_lookup(cmap,1.0-1e-10), (0,254,50,255))
        self.assertEqual(fract4dc.cmap_lookup(cmap,1.0), (0,255,50,255))
        self.assertEqual(fract4dc.cmap_lookup(cmap,0.5), (127,127,75,255))
        self.assertEqual(fract4dc.cmap_lookup(cmap,0.00000001), (254,0,99,255))
        
        cmap = fract4dc.cmap_create(
            [(0.0,255,0,100,255)])
        expc1 = (255,0,100,255)
        self.assertEqual(fract4dc.cmap_lookup(cmap,0.0),expc1)
        self.assertEqual(fract4dc.cmap_lookup(cmap,1.0),expc1)
        self.assertEqual(fract4dc.cmap_lookup(cmap,0.4),expc1)
        
        colors = []
        for i in range(256):
            colors.append((i/255.0,(i*17)%256,255-i,i//2,i//2+127))

        cmap = fract4dc.cmap_create(colors)
        for i in range(256):
            self.assertEqual(fract4dc.cmap_lookup(cmap,i/255.0),colors[i][1:],i)
            
    def testTransfers(self):
        # test fates
        cmap = fract4dc.cmap_create(
            [(0.0,33,33,33,255)])

        # make inner transfer func none
        fract4dc.cmap_set_transfer(cmap,1,0)
        
        # inside should be all-black by default, outside should never be
        index = 0.0
        while index < 2.0: 
            color = fract4dc.cmap_lookup_flags(cmap,index,0,1)
            self.assertEqual(color,(0,0,0,255))
            color = fract4dc.cmap_lookup_flags(cmap,index,0,0)
            self.assertEqual(color,(33,33,33,255))            
            index += 0.1

        # test setting solid colors and transfers
        fract4dc.cmap_set_solid(cmap,0,166,166,166,255)
        fract4dc.cmap_set_solid(cmap,1,177,177,177,255)
        fract4dc.cmap_set_transfer(cmap,0,0)
        
        index = 0.0
        while index < 2.0: 
            color = fract4dc.cmap_lookup_flags(cmap,index,0,1)
            self.assertEqual(color,(177,177,177,255))
            color = fract4dc.cmap_lookup_flags(cmap,index,0,0)
            self.assertEqual(color,(166,166,166,255))            
            index += 0.1

        # make inner linear
        fract4dc.cmap_set_transfer(cmap,1,1)

        index = 0.0
        while index < 2.0: 
            color = fract4dc.cmap_lookup_flags(cmap,index,0,1)
            self.assertEqual(color,(33,33,33,255))
            color = fract4dc.cmap_lookup_flags(cmap,index,0,0)
            self.assertEqual(color,(166,166,166,255))            
            index += 0.1

        # test that solid overrides
        color = fract4dc.cmap_lookup_flags(cmap,0.1,1,1)
        self.assertEqual(color,(177,177,177,255))
        color = fract4dc.cmap_lookup_flags(cmap,0.1,1,0)
        self.assertEqual(color,(166,166,166,255))

    def assertColorTransformHSV(self,r,g,b,eh,es,ev,a=1.0):
        (h,s,v,a2) = fract4dc.rgb_to_hsv(r,g,b,a)
        self.assertEqual((h,s,v,a),(eh,es,ev,a2))

    def assertColorTransformHSL(self,r,g,b,eh,es,ev,a=1.0):
        (h,s,v,a2) = fract4dc.rgb_to_hsl(r,g,b,a)
        self.assertEqual((h,s,v,a),(eh,es,ev,a2))

        (r2,g2,b2,a3) = fract4dc.hsl_to_rgb(eh,es,ev,a)
        self.assertEqual((r2,g2,b2,a3),(r,g,b,a))
        
    def testColorTransformHSL(self):
        # black
        self.assertColorTransformHSL(
            0.0,0.0,0.0,
            0.0,0.0,0.0)

        # white
        self.assertColorTransformHSL(
            1.0,1.0,1.0,
            0.0,0.0,1.0)

        # mid-grey
        self.assertColorTransformHSL(
            0.5,0.5,0.5,
            0.0,0.0,0.5)

        # red
        self.assertColorTransformHSL(
            1.0,0.0,0.0,
            0.0,1.0,0.5)

        # green
        self.assertColorTransformHSL(
            0.0,1.0,0.0,
            2.0,1.0,0.5)

        # blue
        self.assertColorTransformHSL(
            0.0,0.0,1.0,
            4.0,1.0,0.5)
        
        # cyan
        self.assertColorTransformHSL(
            0.0,1.0,1.0,
            3.0,1.0,0.5)

        # magenta
        self.assertColorTransformHSL(
            1.0,0.0,1.0,
            5.0,1.0,0.5)

        # yellow
        self.assertColorTransformHSL(
            1.0,1.0,0.0,
            1.0,1.0,0.5)

        
    def testColorTransformHSV(self):
        # red
        self.assertColorTransformHSV(
            1.0,0.0,0.0,
            0.0,1.0,1.0)

        # green
        self.assertColorTransformHSV(
            0.0,1.0,0.0,
            2.0,1.0,1.0)

        # blue
        self.assertColorTransformHSV(
            0.0,0.0,1.0,
            4.0,1.0,1.0)
        
        # cyan
        self.assertColorTransformHSV(
            0.0,1.0,1.0,
            3.0,1.0,1.0)

        # magenta
        self.assertColorTransformHSV(
            1.0,0.0,1.0,
            5.0,1.0,1.0)

        # yellow
        self.assertColorTransformHSV(
            1.0,1.0,0.0,
            1.0,1.0,1.0)

        # black
        self.assertColorTransformHSV(
            0.0,0.0,0.0,
            0.0,0.0,0.0)

        # white
        self.assertColorTransformHSV(
            1.0,1.0,1.0,
            0.0,0.0,1.0)

        # mid-grey
        self.assertColorTransformHSV(
            0.5,0.5,0.5,
            0.0,0.0,0.5)

    def testArenaAlloc(self):
        arena = fract4dc.arena_create(100,1)
        alloc = fract4dc.arena_alloc(arena, 1,1,10)
        alloc = fract4dc.arena_alloc(arena, 10,1,1)
        
    def testTooSmallArena(self):
        self.assertRaises(MemoryError, fract4dc.arena_create,0,10)
        self.assertRaises(MemoryError, fract4dc.arena_create,10,0)
        
    def testTooBigAlloc(self):
        arena = fract4dc.arena_create(10,1)
        self.assertRaises(MemoryError, fract4dc.arena_alloc,arena,8,1,10)
        
    def testMultipleAllocs(self):
        arena = fract4dc.arena_create(10,1)
        for i in range(5):
            fract4dc.arena_alloc(arena,8,1,1)

        # should be full now        
        self.assertRaises(MemoryError, fract4dc.arena_alloc,arena,8,1,1)

    def testReadArrayVal(self):
        arena = fract4dc.arena_create(10,1)
        alloc = fract4dc.arena_alloc(arena, 4, 1, 10)

        for i in range(10):
            result = fract4dc.array_get_int(alloc,1,i)
            self.assertEqual(
                (0,1), result,
                "bad result %s for %d"  % (result, i))

        self.assertEqual((-1,0), fract4dc.array_get_int(alloc,1, 10))
        self.assertEqual((-1,0), fract4dc.array_get_int(alloc,1, -1))

    def testReadAndWriteArray(self):
        arena = fract4dc.arena_create(10,1)
        alloc = fract4dc.arena_alloc(arena, 4, 1, 10)

        for i in range(10):
            val = i
            result = fract4dc.array_set_int(alloc,1, i,val)
            self.assertEqual(1,result)
            
        for i in range(10):
            result = fract4dc.array_get_int(alloc,1, i)
            self.assertEqual(
                (i,1), result,
                "bad result %s for %d"  % (result, i))

        self.assertEqual((-1,0), fract4dc.array_get_int(alloc,1,10))
        self.assertEqual((-1,0), fract4dc.array_get_int(alloc,1,-1))

        self.assertEqual(0, fract4dc.array_set_int(alloc,1,10,99))
        self.assertEqual(0, fract4dc.array_set_int(alloc,1,-1,99))

    def testTwoPages(self):
        arena = fract4dc.arena_create(10,2)
        alloc = fract4dc.arena_alloc(arena, 8, 1, 9) # fills first page
        alloc = fract4dc.arena_alloc(arena, 8, 1, 9) # forces second page

        # shouldn't work
        self.assertRaises(MemoryError, fract4dc.arena_alloc,arena, 8, 1, 10)

    def testAllocZeroDimensions(self):
        arena = fract4dc.arena_create(10,2)
        self.assertRaises(MemoryError, fract4dc.arena_alloc,arena, 8, 0, 1)

    def testBadDimensions(self):
        arena = fract4dc.arena_create(10,2)
        self.assertRaises(
            MemoryError, fract4dc.arena_alloc,arena, 8, 0, -1, -1)

    def testTwoDimensions(self):
        arena = fract4dc.arena_create(10,2)
        alloc = fract4dc.arena_alloc(arena, 8, 2, 2, 3)

        i = 0
        for y in range(2):
            for x in range(3):
                result = fract4dc.array_set_int(alloc,2, i, y, x)
                self.assertEqual(
                    1,result,
                    "bad set for %d,%d" % (x,y))
                #print "%d,%d => %d" % (x,y,i)
                i += 1

        i = 0
        for y in range(2):
            for x in range(3):
                val = fract4dc.array_get_int(alloc,2, y, x)
                #print "%d,%d <= %d" % (x,y,i)
                self.assertEqual(
                    (i,1), val,
                    "bad result %s instead of %s for %d,%d" % (val,(i,1),x,y))
                
                i += 1
