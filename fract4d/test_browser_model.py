#!/usr/bin/env python3

import unittest
import string
import subprocess
import re
import os
import time
import pickle

import testbase

import browser_model, fc

g_comp = fc.Compiler()
g_comp.add_func_path("../formulas")
g_comp.add_path("../maps", fc.FormulaTypes.GRADIENT)

g_comp.load_formula_file("gf4d.frm")
g_comp.load_formula_file("test.frm")
g_comp.load_formula_file("gf4d.cfrm")
g_comp.load_formula_file("gf4d.uxf")

class Wrapper(browser_model.T):
    def __init__(self):
        self.type_changelist = []
        self.file_changelist = []
        self.formula_changelist = []
        browser_model.T.__init__(self,g_comp)
        self.type_changed += self._type_changed
        self.file_changed += self._file_changed
        self.formula_changed += self._formula_changed
        
    def _type_changed(self):
        self.type_changelist.append(self.current_type)

    def _file_changed(self):
        self.file_changelist.append(self.current.fname)

    def _formula_changed(self):
        self.formula_changelist.append(self.current.formula)
        
class Test(testbase.TestBase):
    def setUp(self):
        pass
        
    def testCreation(self):
        bm = browser_model.T(g_comp)

    def testFuncMapping(self):
        bm = browser_model.T(g_comp)        
        ti = bm.get_type_info(browser_model.FRACTAL)
        
        self.assertEqual(
            fc.FormulaTypes.FRACTAL, ti.formula_type)

        self.assertEqual( None, ti.fname)
        self.assertEqual( None, ti.formula)
        self.assertEqual( [], ti.formulas)
        
        ti2 = bm.get_type_info(browser_model.GRADIENT)
        
        self.assertEqual(
            fc.FormulaTypes.GRADIENT, ti2.formula_type)

    def testSetType(self):
        bm = Wrapper()
        self.assertEqual([], bm.type_changelist)
        self.assertEqual(browser_model.FRACTAL, bm.current_type)
        self.assertEqual(            
            bm.typeinfo[bm.current_type], bm.current)
        
        bm.set_type(browser_model.INNER)
        self.assertEqual(browser_model.INNER, bm.current_type)
        self.assertEqual(
            [browser_model.INNER],
            bm.type_changelist)

    def testFileList(self):
        bm = browser_model.T(g_comp)
        self.assertNotEqual(bm.current.files, [])
        self.assertListSorted(bm.current.files)
        
    def testSetTypeTwice(self):
        bm = Wrapper()
        bm.set_type(browser_model.INNER)
        bm.set_type(browser_model.INNER)
        self.assertEqual(
            [browser_model.INNER],
            bm.type_changelist)

    def testSetTypeUpdatesFnames(self):
        bm = browser_model.T(g_comp)

        bm.current.fname = "fish"
        bm.current.formula = "haddock"
        
        bm.set_type(browser_model.GRADIENT)

        self.assertEqual( None, bm.current.fname)
        self.assertEqual( None, bm.current.formula)

        bm.set_type(browser_model.FRACTAL)

        self.assertEqual( "fish", bm.current.fname)
        self.assertEqual( "haddock", bm.current.formula)

    def testSetFile(self):
        bm = Wrapper()
        bm.set_file("gf4d.frm")
        self.assertEqual("gf4d.frm",bm.current.fname)
        self.assertEqual(
            ["gf4d.frm"], bm.file_changelist)
        
        self.assertNotEqual(0, bm.current.formulas.count("Mandelbrot"))

    def testSetBadFile(self):
        bm = browser_model.T(g_comp)
        self.assertRaises(IOError,bm.set_file,"nonexistent.frm")

    def assertListSorted(self,l):
        last = ""
        for f in l:
            self.assertTrue(last < f.lower(),"list not sorted: %s" % l)
            last = f.lower()
        
    def testFormulasSorted(self):
        bm = browser_model.T(g_comp)
        bm.set_file("gf4d.frm")
        self.assertListSorted(bm.current.formulas)
        
    def testExcludeList(self):
        bm = browser_model.T(g_comp)
        bm.set_type(browser_model.INNER)
        bm.set_file("gf4d.cfrm")
        self.assertEqual(0, bm.current.formulas.count("default"))

        bm.set_type(browser_model.OUTER)
        bm.set_file("gf4d.cfrm")
        self.assertEqual(1, bm.current.formulas.count("default"))

    def testSetFormula(self):
        bm = Wrapper()
        bm.set_file("gf4d.frm")
        bm.set_formula("Mandelbrot")
        self.assertEqual("Mandelbrot",bm.current.formula)
        self.assertEqual(
            ["Mandelbrot"], bm.formula_changelist)

    def testSetFileResetsFormula(self):
        bm = Wrapper()
        bm.set_file("gf4d.frm")
        bm.set_formula("Mandelbrot")
        bm.set_file("fractint-g4.frm")
        self.assertEqual(None, bm.current.formula)
        self.assertEqual(
            ["Mandelbrot", None], bm.formula_changelist)

    def testUpdate(self):
        bm = Wrapper()
        bm.update("gf4d.frm","Mandelbrot")
        self.assertEqual("gf4d.frm",bm.current.fname)
        self.assertEqual("Mandelbrot", bm.current.formula)

        bm.update("fractint-g4.frm", None)
        self.assertEqual("fractint-g4.frm",bm.current.fname)
        self.assertEqual(None, bm.current.formula)

        bm.update(None, None)
        self.assertEqual(None, bm.current.fname)
        self.assertEqual(None, bm.current.formula)

    def testApplyStatus(self):
        bm = browser_model.T(g_comp)
        self.assertEqual(False, bm.current.can_apply)

        bm.set_file("gf4d.frm")
        self.assertEqual(False, bm.current.can_apply)

        bm.set_formula("Mandelbrot")
        self.assertEqual(True, bm.current.can_apply)

        bm.set_type(browser_model.GRADIENT)
        self.assertEqual(False, bm.current.can_apply)

        bm.set_file("Gallet01.map")
        self.assertEqual(True, bm.current.can_apply)

        bm.set_file("blatte1.ugr")
        self.assertEqual(False, bm.current.can_apply)

        bm.update("test.frm","test_error")
        self.assertEqual(False, bm.current.can_apply)

    def testUgrPresent(self):
        bm = browser_model.T(g_comp)
        bm.set_type(browser_model.GRADIENT)
        files = bm.current.files
        self.assertEqual(1,files.count("blatte1.ugr"))

    def testInstance(self):
        x = browser_model.instance
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

