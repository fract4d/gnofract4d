#!/usr/bin/env python3

import os.path
import filecmp
import subprocess

from . import testbase

from fract4d import image


class Test(testbase.ClassSetup):
    def testColossalImage(self):
        # aborts with 'std::bad_array_new_length'
        return

        try:
            im = image.T(400000, 300000)
            self.fail("Should have raised an exception")
        except MemoryError as err:
            pass

        im = image.T(40, 30)
        try:
            im.resize_full(400000, 300000)
            self.fail("Should have raised an exception")
        except MemoryError as err:
            # retains large size even if allocation fails
            self.assertEqual(400000, im.xsize)
            self.assertEqual(300000, im.ysize)
            pass

    def assertImageInvariants(self, im):
        self.assertEqual(im.xsize * im.ysize * im.FATE_SIZE,
                         len(im.fate_buffer()))
        self.assertEqual(im.xsize * im.ysize * im.COL_SIZE,
                         len(im.image_buffer()))

    def testInvalidImages(self):
        self.assertRaises(ValueError, image.T, 0, 100)
        self.assertRaises(ValueError, image.T, 100, 0)
        self.assertRaises(ValueError, image.T, 0, 0)

    def testTiledImage(self):
        # check defaults work OK
        im = image.T(40, 30)
        self.assertEqual(40, im.total_xsize)
        self.assertEqual(30, im.total_ysize)
        self.assertEqual(0, im.xoffset)
        self.assertEqual(0, im.yoffset)

        # check a different total size is honored
        im = image.T(40, 30, 400, 300)
        self.assertEqual(400, im.total_xsize)
        self.assertEqual(300, im.total_ysize)
        self.assertEqual(0, im.xoffset)
        self.assertEqual(0, im.yoffset)

        # check offset has an effect
        im.set_offset(40, 30)
        self.assertEqual(40, im.xoffset)
        self.assertEqual(30, im.yoffset)

        # check offset bounds-checking
        self.assertRaises(ValueError, im.set_offset, 400, 0)
        self.assertRaises(ValueError, im.set_offset, 361, 0)
        self.assertRaises(ValueError, im.set_offset, 0, 300)
        self.assertRaises(ValueError, im.set_offset, 0, 271)
        self.assertRaises(ValueError, im.set_offset, -1, 0)
        self.assertRaises(ValueError, im.set_offset, 0, -1)

        # check offset wasn't changed
        self.assertEqual(40, im.xoffset)
        self.assertEqual(30, im.yoffset)

    def testTileList(self):
        # a single tile
        im = image.T(100, 50)
        self.assertEqual(
            [(0, 0, 100, 50)],
            im.get_tile_list())

        # 2 wide, 1 high
        im = image.T(100, 50, 200, 50)
        self.assertEqual(
            [(0, 0, 100, 50), (100, 0, 100, 50)],
            im.get_tile_list())

        # 2 high, 1 wide
        im = image.T(100, 50, 100, 100)
        self.assertEqual(
            [(0, 0, 100, 50), (0, 50, 100, 50)],
            im.get_tile_list())

        # not evenly divisible, odd-shaped chunks at edges
        im = image.T(100, 50, 101, 51)
        self.assertEqual(
            [(0, 0, 100, 50), (100, 0, 1, 50),
             (0, 50, 100, 1,), (100, 50, 1, 1)],
            im.get_tile_list())

    def testSaveTGA(self):
        self.doTestSave("tga", "TGA")
        self.doTestSave("TGA", "TGA")

    def testSavePNG(self):
        self.doTestSave("png", "PNG")
        self.doTestSave("PNG", "PNG")

    def testSaveJPEG(self):
        self.doTestSave("jpg", "JPEG")
        self.doTestSave("JPG", "JPEG")
        self.doTestSave("jpeg", "JPEG")
        self.doTestSave("JPEG", "JPEG")

    def testFileExtensionLookup(self):
        im = image.T(40, 30)
        self.assertRaises(ValueError, im.file_type, "hello.gif")
        self.assertRaises(ValueError, im.file_type, "hello")

    def testFileMatches(self):
        matches = image.file_matches()
        self.assertTrue("*.tga" in matches)

    def assertImageFileFormat(self, name, format):
        # this doesn't work reliably enough - some people don't
        # have identify installed, etc.
        return

        # run ImageMagick to test file contents
        (status, output) = subprocess.getstatusoutput("identify %s" % name)
        self.assertEqual(status, 0)
        fields = output.split()
        self.assertEqual(fields[0], name)
        self.assertEqual(fields[1], format)
        self.assertEqual(fields[2], "640x400")

    def createTestImage(self):
        # image is [ black, white, green, red]
        im = image.T(2, 2)
        buf = im.image_buffer()
        buf[3] = buf[4] = buf[5] = 255  # white
        buf[7] = 255  # green
        buf[9] = 255  # red
        return im

    def saveTestImage(self, filename):
        im = self.createTestImage()
        im.save(filename)

    def testLoadPNG(self):
        f = os.path.join(Test.tmpdir.name, "test.png")
        self.saveTestImage(f)
        self.doTestLoad(f)
        self.assertRaises(ValueError, self.doTestLoad, "foo.xxx")

    def testLoadMissing(self):
        self.assertRaises(
            IOError, self.doTestLoad, "nonexistent.tga")

    def doTestLoad(self, file):
        im = image.T(1, 1)
        im.load(file)
        cmp_image = self.createTestImage()
        self.assertImagesEqual(im, cmp_image)

    def doTestSave(self, ext, format):
        f1 = os.path.join(Test.tmpdir.name, "save1.%s" % ext)
        f2 = os.path.join(Test.tmpdir.name, "save2.%s" % ext)
        im = image.T(640, 400)
        im.save(f1)
        self.assertTrue(os.path.exists(f1))
        self.assertImageFileFormat(f1, format)

        im = image.T(640, 40, 640, 400)
        im.start_save(f2)
        for (xoff, yoff, w, h) in im.get_tile_list():
            im.resize_tile(w, h)
            im.set_offset(xoff, yoff)
            im.save_tile()
        im.finish_save()
        self.assertTrue(os.path.exists(f2))
        self.assertImageFileFormat(f2, format)

        self.assertEqual(True, filecmp.cmp(f1, f2, False))

    def saveAndCheck(self, name, format):
        im = image.T(640, 400)
        im.save(name)
        self.assertTrue(os.path.exists(name))
        self.assertImageFileFormat(name, format)

    def testBadSaves(self):
        try:
            self.saveAndCheck("test.gif", "GIF")
            self.fail("No exception thrown")
        except ValueError as err:
            self.assertEqual(
                str(err),
                "Unsupported file format '.gif'. Please use one of: .JPEG, .JPG, .PNG, .TGA")

        try:
            self.saveAndCheck("no_extension", "GIF")
            self.fail("No exception thrown")
        except ValueError as err:
            self.assertEqual(
                str(err),
                "No file extension in 'no_extension'. " +
                "Can't determine file format. " +
                "Please use one of: .JPEG, .JPG, .PNG, .TGA")

        try:
            self.saveAndCheck("no_such_dir/test.png", "PNG")
            self.fail("No exception thrown")
        except FileNotFoundError as err:
            self.assertTrue(str(err).startswith("[Errno 2]"))
            self.assertTrue(str(err).endswith("'no_such_dir/test.png'"))

    def testResize(self):
        im = image.T(10, 20)
        self.assertEqual(10, im.xsize)
        self.assertEqual(20, im.ysize)
        self.assertImageInvariants(im)

        im.resize_full(30, 17)
        self.assertEqual(30, im.xsize)
        self.assertEqual(17, im.ysize)
        self.assertImageInvariants(im)

    def testClear(self):
        # check clear() works
        (xsize, ysize) = (61, 33)
        im = image.T(xsize, ysize)
        im.clear()

        fate_buf = im.fate_buffer()
        self.assertEqual(
            list(fate_buf), [im.UNKNOWN] * im.FATE_SIZE * xsize * ysize)

        buf = im.image_buffer()
        self.assertEqual(list(buf), [0] * xsize * ysize * im.COL_SIZE)

    def testBufferBounds(self):
        im = image.T(40, 30)
        im.resize_full(80, 60)
        buf = im.image_buffer()
        fate_buf = im.fate_buffer()

        self.assertRaises(ValueError, im.image_buffer, -1, 0)
        self.assertRaises(ValueError, im.image_buffer, 80, 0)
        self.assertRaises(ValueError, im.image_buffer, 41, 67)

        self.assertRaises(ValueError, im.fate_buffer, -1, 0)
        self.assertRaises(ValueError, im.fate_buffer, 80, 0)
        self.assertRaises(ValueError, im.fate_buffer, 41, 67)

        buf = im.image_buffer(5, 10)
        self.assertEqual(len(buf), 80 * 60 * im.COL_SIZE -
                         (10 * 80 + 5) * im.COL_SIZE)

        buf = im.fate_buffer(5, 10)
        self.assertEqual(len(buf), 80 * 60 * im.FATE_SIZE -
                         (10 * 80 + 5) * im.FATE_SIZE)

    def testLookupOnePixel(self):
        im = image.T(1, 1)
        rgba = im.lookup(0, 0)
        self.assertEqual((0, 0, 0, 1.0), rgba)

        buf = im.image_buffer()
        buf[0] = 20
        buf[1] = 80
        buf[2] = 160

        rgba = im.lookup(0, 0)
        self.assertEqual(
            (20.0 / 255.0, 80.0 / 255.0, 160.0 / 255.0, 1.0), rgba)

        rgba = im.lookup(0.5, 0.5)
        self.assertEqual(
            (20.0 / 255.0, 80.0 / 255.0, 160.0 / 255.0, 1.0), rgba)

        rgba = im.lookup(-0.5, -0.5)
        self.assertEqual(
            (20.0 / 255.0, 80.0 / 255.0, 160.0 / 255.0, 1.0), rgba)

        rgba = im.lookup(10.5, -10.5)
        self.assertEqual(
            (20.0 / 255.0, 80.0 / 255.0, 160.0 / 255.0, 1.0), rgba)

    def grey_pixel(self, amount):
        return (amount, amount, amount, 1.0)

    def testLookupTwoPixels(self):
        im = image.T(2, 1)
        rgba = im.lookup(0, 0)
        self.assertEqual((0, 0, 0, 1.0), rgba)

        buf = im.image_buffer()
        buf[0] = 0
        buf[1] = 0
        buf[2] = 0
        buf[3] = 255
        buf[4] = 255
        buf[5] = 255

        self.assertEqual(self.grey_pixel(0.5), im.lookup(0, 0))
        self.assertEqual(self.grey_pixel(0.0), im.lookup(0.25, 0.25))
        self.assertEqual(self.grey_pixel(1.0), im.lookup(0.75, 0.75))

    def testLookupFourPixels(self):
        im = image.T(2, 2)
        buf = im.image_buffer()
        buf[0] = 0  # top left = black
        buf[1] = 0
        buf[2] = 0
        buf[3] = 255  # top right = red
        buf[4] = 0
        buf[5] = 0
        buf[6] = 0  # bottom left = green
        buf[7] = 255
        buf[8] = 0
        buf[9] = 255  # bottom right = white
        buf[10] = 255
        buf[11] = 255

        # halfway across middle of top pixel = half red
        self.assertEqual((0.5, 0.0, 0.0, 1.0), im.lookup(0.5, 0.25))

        # halfway down left-hand side = half green
        self.assertEqual((0.0, 0.5, 0.0, 1.0), im.lookup(0.25, 0.5))

        # halfway down right-hand side = red/white
        self.assertEqual((1.0, 0.5, 0.5, 1.0), im.lookup(0.75, 0.5))

        # halfway across bottom = green/white
        self.assertEqual((0.5, 1.0, 0.5, 1.0), im.lookup(0.5, 0.75))

        # center = blend of half-red and green/white
        self.assertEqual((0.5, 0.5, 0.25, 1.0), im.lookup(0.5, 0.5))

    def assertImagesEqual(self, im1, im2):
        self.assertEqual(im1.xsize, im2.xsize)
        self.assertEqual(im1.ysize, im2.ysize)

        buf1 = im1.image_buffer()
        buf2 = im2.image_buffer()

        self.assertEqual(buf1, buf2)
