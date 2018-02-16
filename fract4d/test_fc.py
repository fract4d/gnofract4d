#!/usr/bin/env python3

import unittest
import string
import subprocess
import re
import os
import time

import testbase

from fract4d import fc, fractconfig
from fract4d import translate

# centralized to speed up tests
g_comp = fc.Compiler()
g_comp.add_func_path("../formulas")
g_comp.add_path("../maps", fc.FormulaTypes.GRADIENT)

g_comp.load_formula_file("gf4d.frm")
g_comp.load_formula_file("test.frm")
g_comp.load_formula_file("gf4d.cfrm")
g_comp.load_formula_file("gf4d.uxf")

class Test(testbase.TestBase):
    def setUp(self):
        global g_comp
        self.compiler = g_comp
        
    def tearDown(self):
        pass

    def testGetFileType(self):
        self.assertEqual(
            translate.T,
            self.compiler.guess_type_from_filename("x.frm"))
        self.assertEqual(
            translate.ColorFunc,
            self.compiler.guess_type_from_filename("x.ucl"))
        self.assertEqual(
            translate.Transform,
            self.compiler.guess_type_from_filename("x.uxf"))

    def testTypes(self):
        self.assertEqual(0, fc.FormulaTypes.FRACTAL)

    def assertListContains(self,list,element):
        try:
            return list.index(element)
        except ValueError as err:
            raise AssertionError("couldn't find %s in %s" % (element, list))

    def assertListDoesntContain(self,list,element):
        self.assertEqual(0, list.count(element))
                         
    def testFindFilesOfType(self):
        expected_files = {
            fc.FormulaTypes.FRACTAL : "gf4d.frm",
            fc.FormulaTypes.COLORFUNC : "gf4d.cfrm",
            fc.FormulaTypes.TRANSFORM : "gf4d.uxf",
            fc.FormulaTypes.COLORFUNC : "standard.ucl",
            fc.FormulaTypes.GRADIENT : "blatte1.ugr",
            fc.FormulaTypes.GRADIENT : "4zebbowx.map"
            }

        for type in range(fc.FormulaTypes.FRACTAL, fc.FormulaTypes.GRADIENT + 1):
            files = self.compiler.find_files_of_type(type)

            for (exp_t, exp_val) in list(expected_files.items()):
                if exp_t == type:
                    self.assertListContains(files, exp_val)
                else:
                    self.assertListDoesntContain(files, exp_val)

    def testLists(self):
        file = self.compiler.files["gf4d.cfrm"]
        names = file.get_formula_names()
        self.assertEqual(names,list(file.formulas.keys()))

        inside_names = file.get_formula_names("OUTSIDE")
        for f in inside_names:
            self.assertNotEqual(file.formulas[f].symmetry, "OUTSIDE")

        outside_names = file.get_formula_names("INSIDE")
        for f in outside_names:            
            self.assertNotEqual(file.formulas[f].symmetry, "INSIDE")

    def testFileTimeChecking(self):
        'Check we notice when a file changes'
        try:
            f2 = fc.Compiler()
            
            formulas = '''
test_circle {
loop:
z = pixel
bailout:
|z| < @bailout
default:
float param bailout
	default = 4.0
endparam
}
test_square {
loop:
z = pixel
bailout: abs(real(z)) > 2.0 || abs(imag(z)) > 2.0
}
'''
            f = open("fttest.frm","w")
            f.write(formulas)
            f.close()
            
            f2.load_formula_file("fttest.frm")
            frm = f2.get_formula("fttest.frm","test_circle")
            self.assertEqual(frm.symbols.default_params(),[0, 4.0])

            formulas = formulas.replace('4.0','6.0')
            time.sleep(1.0) # ensure filesystem will have a different time
            f = open("fttest.frm","w")
            f.write(formulas)
            f.close()

            frm2 = f2.get_formula("fttest.frm","test_circle")
            self.assertEqual(frm2.symbols.default_params(),[0, 6.0])
            
        finally:
            os.remove("fttest.frm")
            
    def testCompile(self):
        'Check we can compile a fractal and the resulting .so looks ok'
        ff = self.compiler.files["gf4d.frm"]
        self.assertNotEqual(ff.contents.index("Modified for Gf4D"),-1)
        self.assertNotEqual(ff.get_formula("T03-01-G4"),None)
        self.assertEqual(len(ff.formulas) > 0,1)
        f = self.compiler.get_formula("gf4d.frm","T03-01-G4")
        self.assertEqual(f.errors, [])
        subprocess.getoutput("rm -f test-out.so")
        cg = self.compiler.compile(f)
        self.compiler.generate_code(f,cg,"test-out.so",None)
        # check the output contains the right functions
        (status,output) = subprocess.getstatusoutput('nm test-out.so')
        self.assertEqual(status,0)
        self.assertEqual(output.count("pf_new"),1)
        self.assertEqual(output.count("pf_calc"),1)
        self.assertEqual(output.count("pf_init"),1)
        self.assertEqual(output.count("pf_kill"),1)

    def testErrors(self):
        'Check we raise appropriate exns when formulas are busted'
        self.assertRaises(
            IOError, self.compiler.load_formula_file, "nonexistent.frm")

        self.assertRaises(
            ValueError, self.compiler.get_formula, "test.xxx","nonexistent") 

        f = self.compiler.get_formula("test.frm","nonexistent")
        self.assertEqual(f,None)
        f = self.compiler.get_formula("test.frm","parse_error")
        self.assertEqual(len(f.errors),1)

    def disabled_testEvil(self):
        # this was too slow so turned it off
        f = self.compiler.get_formula("test.frm","ny2004-4")
        self.assertEqual(len(f.errors),0)
        cg = self.compiler.compile(f)
        self.compiler.generate_code(f,cg,"test-evil.so",None)
        
        f = self.compiler.get_formula("test.frm","Fractint-9-21")
        self.assertNoErrors(f)
        cg = self.compiler.compile(f)
        self.compiler.generate_code(f,cg,"test-evil.so",None)

    def testPreprocessor(self):
        f = self.compiler.get_formula("test.frm","test_preprocessor")
        self.assertNoErrors(f)
        cg = self.compiler.compile(f)
        of = self.compiler.generate_code(f,cg)

    def testPreprocessorError(self):
        ff = self.compiler.load_formula_file("test_bad_pp.frm")
        f = self.compiler.get_formula("test_bad_pp.frm","error")
        self.assertEqual(len(f.errors),1)        
        self.compiler.files["test_bad_pp.frm"] = None

    def testBehr(self):
        ff = self.compiler.get_file("Bujumbura.cs")
        ff = self.compiler.get_file("BehrQuiltedRed.cs")
        
    def testColorFunc(self):
        'Compile inner + outer colorfuncs and merge'
        cf1 = self.compiler.get_formula("gf4d.cfrm","default","cf0")
        self.assertEqual(len(cf1.errors),0)
        self.compiler.compile(cf1)
        
        cf2 = self.compiler.get_formula("gf4d.cfrm","zero","cf1")
        self.assertEqual(len(cf2.errors),0)
        self.compiler.compile(cf2)
        
        f = self.compiler.get_formula("gf4d.frm","Mandelbrot")
        cg = self.compiler.compile(f)

        f.merge(cf1,"cf0_")
        f.merge(cf2,"cf1_")

        ofile = self.compiler.generate_code(f,cg)
        self.assertTrue(os.path.exists(ofile))

    def testDoubleCompile(self):
        'Compile the same thing twice, check results same'
        f = self.compiler.get_formula("gf4d.frm","Mandelbrot")
        cg = self.compiler.compile(f)
        of1 = self.compiler.generate_code(f,cg)

        f2 = self.compiler.get_formula("gf4d.frm","Mandelbrot")
        cg2 = self.compiler.compile(f2)
        of2 = self.compiler.generate_code(f,cg2)

        self.assertEqual(of1,of2)

    def testFormulasNotConnected(self):
        'fetch the same thing twice, check symbols tables differ'
        f = self.compiler.get_formula("fractint-builtin.frm","julfn+exp")
        f2 = self.compiler.get_formula("fractint-builtin.frm","julfn+exp")
        self.assertNotEqual(f,f2)
        self.assertNotEqual(f.symbols, f2.symbols)
        ol = f.symbols["@fn1"]
        ol2 = f2.symbols["@fn1"]
        self.assertNotEqual(ol, ol2)
        func = ol[0]
        func2 = ol2[0]
        self.assertNotEqual(func,func2)

    def testPrefs(self):
        compiler = fc.Compiler()
        prefs = fractconfig.T("testprefs")
        prefs.set("compiler","name","x")
        prefs.set("compiler","options","foo")
        prefs.set_list("formula_path",["fish"])
        prefs.set_list("map_path", ["wibble"])
        
        compiler.update_from_prefs(prefs)

        self.assertEqual("x", compiler.compiler_name)
        self.assertEqual("foo", compiler.flags)
        self.assertEqual(["fish"], compiler.path_lists[0])
        self.assertEqual(["wibble"], compiler.path_lists[3])
        
    def testInstance(self):
        compiler = fc.Compiler()
        compiler.update_from_prefs(fractconfig.instance)
        self.assertNotEqual(None, compiler)
        self.assertEqual(
            compiler.flags, fractconfig.instance.get("compiler", "options"))
            
    def testAllFormulasCompile(self):
        'Go through every formula and check for errors'
        for filename in self.compiler.find_formula_files():
            ff = self.compiler.get_file(filename)
            for fname in ff.get_formula_names():
                # skip formulas expected to produce an error
                if fname.count("error") == 0:
                    f = self.compiler.get_formula(ff.filename, fname)
                    self.assertNoErrors(f, "%s:%s" % (filename, fname))

    def testGetFormulaText(self):
        t = self.compiler.get_formula_text("gf4d.frm","Mandelbrot")
        self.assertTrue(t.startswith("Mandelbrot {"))

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

