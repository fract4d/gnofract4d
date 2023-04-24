import copy
import math
import os.path

from . import testgui

from gi.repository import Gdk, GLib, Gtk

from fract4dgui import gtkfractal


class FakeGesture:
    def __init__(self, button=1, modifier_state=0):
        self.button = button
        self.modifier_state = modifier_state

    def get_current_button(self):
        return self.button

    def get_current_event_state(self):
        return self.modifier_state

    def set_state(self, state):
        pass


class CallCounter:
    def __init__(self):
        self.count = 0

    def cb(self, *args):
        self.count += 1


class Recurser:
    def __init__(self):
        self.count = 0

    def cb(self, f, *args):
        self.count += 1
        nv = f.params[f.MAGNITUDE]
        f.set_param(f.MAGNITUDE, nv * 2.0)


class TestHidden(testgui.TestCase):
    def wait(self):
        self.loop = GLib.MainLoop()
        self.loop.run()

    def quitloop(self, f, status):
        if status == 0:
            self.loop.quit()

    def testCreate(self):
        # draw a default fractal
        f = gtkfractal.Hidden(TestHidden.g_comp, 64, 40)
        f.connect('status-changed', self.quitloop)
        f.draw_image(0, 1)
        self.wait()

    def testCopy(self):
        f = gtkfractal.Hidden(TestHidden.g_comp, 64, 40)
        copy = f.copy_f()
        mag = f.get_param(f.MAGNITUDE)
        copy.set_param(copy.MAGNITUDE, 176.3)
        self.assertEqual(mag, f.get_param(f.MAGNITUDE))
        self.assertNotEqual(mag, copy.get_param(copy.MAGNITUDE))

    def testSignals(self):
        f = gtkfractal.Hidden(TestHidden.g_comp, 64, 40)
        cc = CallCounter()
        f.connect('parameters-changed', cc.cb)
        self.assertEqual(cc.count, 0)

        f.set_param(f.MAGNITUDE, 0.7)
        self.assertEqual(cc.count, 1)

        # set to the same value, no callback
        f.set_param(f.MAGNITUDE, 0.7)
        self.assertEqual(cc.count, 1)

        # maxiter
        f.set_maxiter(778)
        f.set_maxiter(778)
        self.assertEqual(cc.count, 2)

        # size
        f.set_size(57, 211)
        f.set_size(57, 211)

    def testLoad(self):
        f = gtkfractal.Hidden(TestHidden.g_comp, 64, 40)
        with open("testdata/test_bail.fct") as fh:
            f.loadFctFile(fh)
        self.assertEqual(f.saved, True)
        f.connect('status-changed', self.quitloop)
        f.draw_image(0, 1)
        self.wait()

    def testBigImage(self):
        f = gtkfractal.HighResolution(TestHidden.g_comp, 640, 400)
        f.connect('status-changed', self.quitloop)
        hires_image = os.path.join(TestHidden.tmpdir.name, "hires.png")
        f.draw_image(hires_image)
        self.wait()
        self.assertEqual(True, os.path.exists(hires_image))


class Test(testgui.TestCase):
    def setUp(self):
        self.window = Gtk.Window()
        self.f = gtkfractal.T(Test.g_comp)
        self.window.set_child(self.f.widget)
        self.window.present()

    def tearDown(self):
        self.window.destroy()
        self.f = None

    def wait(self):
        self.loop = GLib.MainLoop()
        self.loop.run()

    def quitloop(self, f, status):
        if status == 0:
            self.loop.quit()

    def testCreate(self):
        # draw a default fractal
        self.f.connect('status-changed', self.quitloop)
        self.f.draw_image(0, 1)
        self.wait()

    def disabled_testSignalsDontRecurse(self):
        # test no recurse, but doesn't work. Maybe I've misunderstood
        # signal recursion semantics?
        r = Recurser()
        self.f.connect('parameters-changed', r.cb)

        self.f.set_param(self.f.MAGNITUDE, 0.7)
        self.assertEqual(r.count, 1)

    def testButton1(self):
        f = self.f

        # check click updates member vars
        f.onButtonPress(gesture=FakeGesture(), start_x=17, start_y=88)
        self.assertEqual((f.x, f.y, f.newx, f.newy), (17, 88, 17, 88))

        # click+release in middle of screen zooms but doesn't change params
        (xp, yp) = (f.width / 2, f.height / 2)
        f.onButtonPress(gesture=FakeGesture(), start_x=xp, start_y=yp)
        self.assertEqual((f.x, f.y, f.newx, f.newy), (xp, yp, xp, yp))
        tparams = copy.copy(f.params())
        tparams[f.MAGNITUDE] /= 2.0

        f.onButtonRelease(FakeGesture(), offset_x=0, offset_y=0)
        self.assertEqual(f.params(), tparams)

        # select entire screen & release should be a no-op
        f.onButtonPress(FakeGesture(), start_x=0, start_y=0)
        self.assertEqual((f.x, f.y, f.newx, f.newy), (0, 0, 0, 0))

        f.onMotionNotify(FakeGesture(), offset_x=f.width - 1, offset_y=f.height - 1)
        self.assertEqual((f.x, f.y, f.newx, f.newy),
                         (0, 0, f.width - 1, f.height - 1))

        f.onButtonRelease(FakeGesture(), f.width - 1, f.height - 1)
        self.assertEqual(f.params(), tparams)

        # same if you do the corners the other way and get newx automatically
        (wm1, hm1) = (f.width - 1, f.height - 1)
        f.onButtonPress(FakeGesture(), start_x=wm1, start_y=hm1)
        self.assertEqual((f.x, f.y, f.newx, f.newy), (wm1, hm1, wm1, hm1))

        f.onMotionNotify(FakeGesture(), offset_x=-wm1, offset_y=-hm1)
        self.assertEqual((f.x, f.y, f.newx, f.newy), (wm1, hm1, 0, 0))

        f.onButtonRelease(FakeGesture(), -wm1, -hm1)
        self.assertEqual(f.params(), tparams)

    def testShiftButton1(self):
        f = self.f

        # shift + click on center should have no effect
        (xp, yp) = (f.width / 2, f.height / 2)
        f.onButtonPress(FakeGesture(), start_x=xp, start_y=yp)
        self.assertEqual((f.x, f.y, f.newx, f.newy), (xp, yp, xp, yp))
        tparams = copy.copy(f.params())

        f.onButtonRelease(
            FakeGesture(modifier_state=Gdk.ModifierType.SHIFT_MASK), 0, 0)
        self.assertEqual(f.params(), tparams)

    def testZooms(self):
        self.doTestZooms(1)

    def testFlipYZooms(self):
        self.f.f.yflip = True
        self.doTestZooms(-1)

    def doTestZooms(self, dir):
        # select each quarter of the screen to zoom into - check
        # that resulting params look correct
        f = self.f
        tparams = copy.copy(f.params())

        # select the top LH quadrant zooms and recenters
        f.onButtonPress(FakeGesture(), start_x=0, start_y=0)
        offset_x = f.width / 2 - 1
        offset_y = f.height / 2 - 1
        f.onMotionNotify(gesture=FakeGesture(), offset_x=offset_x, offset_y=offset_y)
        f.onButtonRelease(FakeGesture(), offset_x, offset_y)

        tparams[f.XCENTER] -= tparams[f.MAGNITUDE] / 4.0
        tparams[f.YCENTER] += dir * tparams[f.MAGNITUDE] / \
            4.0 * (float(f.height) / f.width)
        tparams[f.MAGNITUDE] /= 2.0

        self.assertEqual(f.params(), tparams)

        # top RH quadrant
        f.onButtonPress(FakeGesture(), start_x=f.width / 2, start_y=0)
        offset_x = (f.width - 1) - (f.width / 2)
        offset_y = f.height / 2 - 1
        f.onMotionNotify(gesture=FakeGesture(), offset_x=offset_x, offset_y=offset_y)
        f.onButtonRelease(FakeGesture(), offset_x, offset_y)

        tparams[f.XCENTER] += tparams[f.MAGNITUDE] / 4.0
        tparams[f.YCENTER] += dir * tparams[f.MAGNITUDE] / \
            4.0 * (float(f.height) / f.width)
        tparams[f.MAGNITUDE] /= 2.0

        self.assertEqual(f.params(), tparams)

        # bottom LH quadrant
        f.onButtonPress(FakeGesture(), start_x=0, start_y=f.height / 2)
        offset_x = f.width / 2 - 1
        offset_y = (f.height - 1) - (f.height / 2)
        f.onMotionNotify(gesture=FakeGesture(), offset_x=offset_x, offset_y=offset_y)
        f.onButtonRelease(FakeGesture(), offset_x, offset_y)

        tparams[f.XCENTER] -= tparams[f.MAGNITUDE] / 4.0
        tparams[f.YCENTER] -= dir * tparams[f.MAGNITUDE] / \
            4.0 * (float(f.height) / f.width)
        tparams[f.MAGNITUDE] /= 2.0

        self.assertEqual(f.params(), tparams)

        # bottom RH quadrant
        f.onButtonPress(FakeGesture(), start_x=f.width / 2, start_y=f.height / 2)
        offset_x = (f.width - 1) - (f.width / 2)
        offset_y = (f.height - 1) - (f.height / 2)
        f.onMotionNotify(gesture=FakeGesture(), offset_x=offset_x, offset_y=offset_y)
        f.onButtonRelease(FakeGesture(), offset_x, offset_y)

        tparams[f.XCENTER] += tparams[f.MAGNITUDE] / 4.0
        tparams[f.YCENTER] -= dir * tparams[f.MAGNITUDE] / \
            4.0 * (float(f.height) / f.width)
        tparams[f.MAGNITUDE] /= 2.0

        self.assertEqual(f.params(), tparams)

    def testButton3(self):
        f = self.f
        f.newx = 0
        f.newy = 0
        tparams = copy.copy(f.params())

        # right click in center just zooms out
        f.onButtonRelease(FakeGesture(button=3), f.width / 2, f.height / 2)
        tparams[f.MAGNITUDE] *= 2.0

        self.assertEqual(f.params(), tparams)

        # right click in top corner zooms + recenters
        f.onButtonRelease(FakeGesture(button=3), 0, 0)
        tparams[f.XCENTER] -= tparams[f.MAGNITUDE] / 2.0
        tparams[f.YCENTER] += tparams[f.MAGNITUDE] / \
            2.0 * (float(f.height) / f.width)
        tparams[f.MAGNITUDE] *= 2.0

        self.assertEqual(f.params(), tparams)

    def testButton2(self):
        f = self.f
        f.newx = 0
        f.newy = 0
        tparams = copy.copy(f.params())

        # middle click in center goes to Julia
        f.onButtonRelease(FakeGesture(button=2), f.width / 2, f.height / 2)
        tparams[f.XZANGLE] = math.pi / 2
        tparams[f.YWANGLE] = math.pi / 2

        self.assertEqual(f.params(), tparams)

        # middle click again goes back to Mandelbrot
        f.onButtonRelease(FakeGesture(button=2), f.width / 2, f.height / 2)
        tparams[f.XZANGLE] = 0.0
        tparams[f.YWANGLE] = 0.0

        self.assertEqual(f.params(), tparams)

        # click off to one side changes center
        f.onButtonRelease(FakeGesture(button=2), f.width, 0)
        tparams[f.XZANGLE] = math.pi / 2
        tparams[f.YWANGLE] = math.pi / 2
        tparams[f.XCENTER] += tparams[f.MAGNITUDE] / 2.0
        tparams[f.YCENTER] += tparams[f.MAGNITUDE] / \
            2.0 * (float(f.height) / f.width)

        self.assertNearlyEqual(f.params(), tparams)

        # click off to the other side changes xycenter
        f.onButtonRelease(FakeGesture(button=2), 0, f.height)
        tparams[f.XZANGLE] = 0.0
        tparams[f.YWANGLE] = 0.0
        tparams[f.ZCENTER] -= tparams[f.MAGNITUDE] / 2.0
        tparams[f.WCENTER] -= tparams[f.MAGNITUDE] / \
            2.0 * (float(f.height) / f.width)

        self.assertNearlyEqual(f.params(), tparams)

    def disabled_testTumorCrash(self):
        '''Provokes an issue which used to cause a crash.
        Disabled because if we don\'t crash wait() hangs'''
        self.f.loadFctFile(open("testdata/tumor.fct"))
        self.f.compile()
        print("d1")
        self.f.draw_image(0, 1)
        print("d1 done")
        self.f.set_formula("gf4d.frm", "Buffalo")
        print("d2")
        self.f.draw_image(0, 1)
        print("d2 done")
        self.wait()

    def assertNearlyEqual(self, a, b):
        # check that each element is within epsilon of expected value
        epsilon = 1.0e-12
        for (ra, rb) in zip(a, b):
            d = abs(ra - rb)
            self.assertTrue(d < epsilon, f"{ra:f} != {rb:f} (by {d:f})")
