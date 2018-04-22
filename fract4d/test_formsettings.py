#!/usr/bin/env python3

import io
import unittest
import copy

import testbase

from fract4d import formsettings, gradient, fracttypes, fctutils

g_grad = gradient.Gradient()

class Parent:
    def __init__(self):
        self.dirty = False
        self.changes = 0
    def changed(self):
        self.dirty = True
        self.changes += 1
    
class Test(testbase.ClassSetup):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.g_comp.load_formula_file("gf4d.frm")
        cls.g_comp.load_formula_file("test.cfrm")
        cls.g_comp.load_formula_file("gf4d.cfrm")

    def testCreate(self):
        fs = formsettings.T(Test.g_comp)

        self.assertEqual(None,fs.formula)
        self.assertEqual(None,fs.funcName)
        self.assertEqual(None,fs.funcFile)
        self.assertEqual([], fs.params)
        self.assertEqual(False,fs.dirty)

        p = Parent()
        fs2 = formsettings.T(Test.g_comp,p)

        fs2.changed()
        self.assertEqual(1,p.changes)
        self.assertEqual(True, fs2.dirty)
        self.assertEqual(True, p.dirty)
        
    def testSetFormula(self):
        fs = formsettings.T(Test.g_comp)
        fs.set_formula("gf4d.frm","Mandelbrot",g_grad)
        
        self.assertEqual("gf4d.frm",fs.funcFile)
        self.assertEqual("Mandelbrot", fs.funcName)
        self.assertNotEqual(None,fs.formula, "Formula should have been set")
        self.assertNotEqual([], fs.params)
        
    def testNames(self):
        fs = formsettings.T(Test.g_comp)
        fs.set_formula("gf4d.frm","Mandelbrot",g_grad)

        names = fs.func_names()
        names.sort()
        self.assertEqual(["@bailfunc"],names)

        names = fs.param_names()
        names.sort()
        self.assertEqual(["@_gradient", "@bailout"],names)

    def testParamsOfType(self):
        fs = formsettings.T(Test.g_comp)
        fs.set_formula("test.frm","test_all_types",g_grad)

        params = fs.params_of_type(fracttypes.Complex)
        self.assertEqual(params, ['t__a_c'])

        params = fs.params_of_type(fracttypes.Image)
        self.assertEqual(params, ['t__a_im'])
        
    def testFuncValue(self):
        fs = formsettings.T(Test.g_comp)
        fs.set_formula("gf4d.frm","Mandelbrot",g_grad)

        self.assertEqual("cmag",fs.get_func_value("@bailfunc"))
        
    def testNoSuchFormula(self):
        fs = formsettings.T(Test.g_comp)
        self.assertRaises(ValueError, fs.set_formula,"gf4d.frm","no_such_formula", g_grad)

    def testNoSuchFile(self):
        fs = formsettings.T(Test.g_comp)
        self.assertRaises(IOError, fs.set_formula,"no_such_file.frm","Mandelbrot", g_grad)

    def testErroneousFormula(self):
        fs = formsettings.T(Test.g_comp)
        self.assertRaises(ValueError, fs.set_formula,"test.frm","test_error", g_grad)

    def testCopy(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("gf4d.frm","Mandelbrot",g_grad)

        fs2 = copy.copy(fs1)
        fs1.set_formula("test.frm", "test_defaults", g_grad)

        # check fs2 wasn't updated
        self.assertEqual(fs2.funcFile, "gf4d.frm")
        self.assertEqual(fs2.funcName, "Mandelbrot")
        self.assertEqual(fs2.params, [g_grad, 4.0])
        self.assertEqual(fs2.paramtypes, [fracttypes.Gradient, fracttypes.Float])

    def testSetFuncs(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("gf4d.frm","Mandelbrot",g_grad)

        # should return true if it actually changed
        self.assertEqual(True,fs1.set_named_func("@bailfunc", "manhattanish"))
        self.assertEqual(False,fs1.set_named_func("@bailfunc", "manhattanish"))

    def testSetParams(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("gf4d.frm","Mandelbrot",g_grad)

        self.assertEqual(True, fs1.set_param(1,"5.0"))
        self.assertEqual(False, fs1.set_param(1,"5.0"))

        # fixme, should be more extensive testing

    def testGetNamedParamValue(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("gf4d.frm","Mandelbrot",g_grad)

        self.assertEqual(4.0,fs1.get_named_param_value("@bailout"))

    def testMutate(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("gf4d.frm","Mandelbrot",g_grad)

        fs1.mutate(0.0,1.0)

    def testNudge(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("test.frm","test_defaults",g_grad)

        (a,b) = (fs1.params[1],fs1.params[2])
        self.assertEqual(False,fs1.nudge_param(1,0,0))
        self.assertEqual(a, fs1.params[1])
        self.assertEqual(b, fs1.params[2])        
        
        self.assertEqual(True,fs1.nudge_param(1,4,2))

        self.assertEqual(a + 4 * 0.025, fs1.params[1])
        self.assertEqual(b + 2 * 0.025, fs1.params[2])

    def testAllTypesBasic(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("test.frm","test_all_types",g_grad)
        
    def testInitValue(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("test.frm","test_all_types",g_grad)

        self.assertEqual("1",fs1.initvalue("@b"))
        self.assertEqual("7",fs1.initvalue("@i"))
        self.assertEqual("99.00000000000000000",fs1.initvalue("@f"))
        self.assertEqual("(3.00000000000000000,4.00000000000000000)",fs1.initvalue("@c"))
        self.assertEqual("(1.00000000000000000,2.00000000000000000,3.00000000000000000,4.00000000000000000)",
                         fs1.initvalue("@h"))

        self.assertEqual("warp",fs1.initvalue("@c","@c"))
        self.assertEqual("[\n]", fs1.initvalue("@im"))

        
    def testSetNamedParam(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("test.frm","test_all_types",g_grad)

        fs1.set_named_param("@b","True")
        self.assertEqual(True, fs1.get_named_param_value("@b"))

        fs1.set_named_param("@b","0")
        self.assertEqual(False, fs1.get_named_param_value("@b"))

        fs1.set_named_param("@i","-122985354")
        self.assertEqual(-122985354, fs1.get_named_param_value("@i"))

        # FIXME this is weird behavior
        fs1.set_named_param("@c","(77.1,-90.3)")
        self.assertEqual(77.1, fs1.get_named_param_value("@c")) 

        fs1.set_named_param("@h","(79.1,-90.3,99.0,17.777)")
        self.assertEqual(79.1, fs1.get_named_param_value("@h")) 

        fs1.set_named_param("@_gradient","""GIMP Gradient
Name: burning_coals
3
0.000000 0.000000 0.000000 0.000000 0.000000 0.000000 0.000000 0.871094 0.429688 0.156250 1.000000 0 0
0.000000 0.002500 0.005000 0.871094 0.429688 0.156250 1.000000 0.894531 0.484375 0.035156 1.000000 0 0
0.005000 0.006250 0.007500 0.894531 0.484375 0.035156 1.000000 0.750000 0.546875 0.015625 1.000000 0 0
""")
        
    def testSetNamedItem(self):
        fs1 = formsettings.T(Test.g_comp)
        fs1.set_formula("gf4d.frm","Mandelbrot",g_grad)

        fs1.set_named_item("@bailfunc","manhattan")
        fs1.set_named_item("@bailout","7.0")

    def testSetParamBag(self):
        fs1 = formsettings.T(Test.g_comp,None,"cf0")
        fs1.set_formula("standard.ucl","DirectOrbitTraps",g_grad)
        
        bag = fctutils.ParamBag()
        bag.load(io.StringIO("""formulafile=stdexp.cfrm
function=DirectOrbitTraps
@_transfer=ident
@trapmergemode=mergenormal
@_density=1.00000000000000000
@_offset=0.00000000000000000
@angle=0.00000000000000000
@aspect=1.00000000000000000
@diameter=1.00000000000000000
@solidcolor=0
@startcolor=(1.00000000000000000,1.00000000000000000,1.00000000000000000,0.00000000000000000)
@threshold=0.25000000000000000
@trapcenter=(0.00000000000000000,0.00000000000000000)
@trapcolor=8
@trapfreq=1.00000000000000000
@trapmergemodifier=0
@trapmergeopacity=0.20000000000000001
@trapmergeorder=0
@traporder=4.00000000000000000
@trapshape=23
[endsection]
"""))
        fs1.load_param_bag(bag)

        self.assertEqual(fs1.get_func_value("@trapmergemode"),"mergenormal")
        self.assertEqual(fs1.get_named_param_value("@trapshape"),23)
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
