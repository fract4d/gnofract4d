#!/usr/bin/env python3

import cmath
import math
from pathlib import Path
import re
import subprocess
import tempfile

from fract4d.tests import testbase

from fract4d_compiler import (absyn, ir, fsymbol, codegen, translate,
                              fractparser, fractlexer, optimize, instructions)
from fract4d_compiler.fracttypes import *

g_exp = None
g_x = None


class Test(testbase.ClassSetup):
    def setUp(self):
        self.fakeNode = absyn.Empty(0)
        self.codegen = codegen.T(fsymbol.T())
        self.parser = fractparser.parser
        self.main_stub = '''

#include "fract_stdlib.cpp"
int main()
{
    double pparams[] = { 1.5, 0.0, 0.0, 0.0};
    double pos_params[] = {
        0.0, 0.0, 0.0, 0.0,
        4.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0} ;

    struct s_param initparams[] = {
        { GRADIENT, 0, 0},
        { FLOAT, 0, 0.0},
        { FLOAT, 0, 1.0},
        { FLOAT, 0, 0.0},
        { FLOAT, 0, 1.0},
        { FLOAT, 0, 5.0},
        { FLOAT, 0, 2.0},
        { FLOAT, 888, 1.0e20} /* sentinel to see if we read too far */
        };
    int nItersDone=0;
    int nFate=0;
    double dist=0.0;
    int solid=0;
    int fDirectUsed=0;
    double colors[4] = {0.0};

    pf_obj *pf = pf_new();
    pf->vtbl->init(pf,pos_params,initparams,7);

    pf->vtbl->calc(
         pf,
         pparams,
         100, -1,
         ((100)), ((1.0E-9)),
         0,0,0,
         &nItersDone, &nFate, &dist,&solid,&fDirectUsed, &colors[0]);

    printf("(%d,%d,%g)\\n",nItersDone,nFate,dist);
    if(fDirectUsed)
    {
        printf("[%g,%g,%g,%g]\\n", colors[0], colors[1], colors[2], colors[3]);
    }

    pparams[0] = 0.1; pparams[1] = 0.2;
    pparams[2] = 0.1; pparams[3] = 0.3;
    initparams[5].doubleval = 3.0; initparams[6].doubleval = 3.5;

    pf->vtbl->calc(
        pf,
        pparams,
        20, -1,
        ((100)), ((1.0E-9)),
        0,0,0,
        &nItersDone, &nFate, &dist,&solid,&fDirectUsed, &colors[0]);

    printf("(%d,%d,%g)\\n",nItersDone,nFate,dist);
    if(fDirectUsed)
    {
        printf("[%g,%g,%g,%g]\\n", colors[0], colors[1], colors[2], colors[3]);
    }

    pf->vtbl->kill(pf);
    return 0;
}
'''

    def tearDown(self):
        pass

    # convenience methods to make quick trees for testing
    def eseq(self, stms, exp):
        return ir.ESeq(stms, exp, self.fakeNode, Int)

    def seq(self, stms):
        return ir.Seq(stms, self.fakeNode)

    def var(self, name="a", type=Int):
        self.codegen.symbols[name] = Var(type)
        return ir.Var(name, self.fakeNode, type)

    def const(self, value=None, type=Int):
        return ir.Const(value, self.fakeNode, type)

    def binop(self, stms, op="+", type=Int):
        return ir.Binop(op, stms, self.fakeNode, type)

    def move(self, dest, exp):
        return ir.Move(dest, exp, self.fakeNode, Int)

    def cjump(self, e1, e2, trueDest="trueDest", falseDest="falseDest"):
        return ir.CJump(">", e1, e2, trueDest, falseDest, self.fakeNode)

    def jump(self, dest):
        return ir.Jump(dest, self.fakeNode)

    def cast(self, e, type):
        return ir.Cast(e, self.fakeNode, type)

    def label(self, name):
        return ir.Label(name, self.fakeNode)

    def generate_code(self, t):
        self.codegen = codegen.T(fsymbol.T())
        self.codegen.generate_code(t)

    def translate(self, s, options={}):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        # print pt.pretty()
        t = translate.T(pt.children[0], options)
        # print t.pretty()
        self.assertNoErrors(t)
        self.codegen = codegen.T(t.symbols, options)
        return t

    def translatecf(self, s, name, options={}):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        # print pt.pretty()
        t = translate.ColorFunc(pt.children[0], name, options)
        # print t.pretty()
        self.assertNoErrors(t)
        return t

    def sourceToAsm(self, s, section, options={}):
        t = self.translate(s, options)
        if options.get("trace") == 1:
            self.codegen.generate_trace = True
        self.codegen.generate_all_code(t.canon_sections[section])
        if options.get("dumpAsm") == 1:
            self.printAsm()
        return self.codegen.out

    def printAsm(self):
        for i in self.codegen.out:
            try:
                print(i)
                print(i.format())
            except Exception as e:
                print("Can't format %s:%s" % (i, e))
                raise

    def makeC(self, user_preamble="", user_postamble=""):
        # construct a C stub for testing
        preamble = '''
        #include <stdio.h>
        #include <math.h>

        #include "colorutils.cpp"
        #include "model/image.cpp"
        #include "model/colormap.cpp"
        #include "fract_stdlib.cpp"
        #include "pf.h"

        typedef struct {
            struct s_param *p;
            double pos_params[N_PARAMS];
            arena_t arena;
        } pf_fake;

        int main(){
        struct s_param params[20];
        int i = 0;

        ListColorMap *pMap = new ListColorMap();
        pMap->init(2);
        pMap->set(0,0.0,255,0,0,0);
        pMap->set(1,1.0,0,255,0,0);

        image *im = new image();
        im->set_resolution(1,1,-1,-1);
        rgba_t blue;
        blue.r = 0; blue.g = 0; blue.b = 255;
        im->put(0,0,blue);

        for(i = 0; i < 20; ++i) {
            params[i].t = FLOAT;
            params[i].intval = 773;
            params[i].doubleval = 0.0;
            params[i].gradient = pMap;
            params[i].image = im;
        };

        pf_fake t__f;
        pf_fake *t__p_stub = &t__f;

        for(i = 0; i < N_PARAMS; ++i) {
           t__f.pos_params[i] = 0.0;
        }
        t__f.pos_params[4]=4.0;

        t__f.p = params;
        t__f.arena = arena_create(10000,1);
        pf_fake *t__pfo = &t__f;
        double pixel_re = 0.0, pixel_im = 0.0;
        double t__h_zwpixel_re = 0.0, t__h_zwpixel_im = 0.0;
        double t__h_color_re = 0.0;
        double t__h_color_i = 0.0;
        double t__h_color_j = 0.0;
        double t__h_color_k = 0.0;
        '''

        codegen_symbols = self.codegen.output_local_vars(self.codegen, {})
        decls = "\n".join([x.format() for x in codegen_symbols])
        str_output = "\n".join([x.format() for x in self.codegen.out])
        postamble = "\nreturn 0;}\n"

        return "".join([preamble, decls, "\n",
                        user_preamble, str_output, "\n",
                        user_postamble, postamble])

    def compileSharedLib(self, c_code):
        cFile = tempfile.NamedTemporaryFile(mode="w",
                                            prefix="gf4d", suffix=".c", dir=Test.tmpdir.name)
        cFile.write(c_code)
        cFile.flush()

        oFileName = str(Path(cFile.name).with_suffix(".so"))
        import sys
        if sys.platform[:6] == "darwin":
            cmd = "gcc -Wall -fPIC -DPIC -shared %s -o %s -lm -flat_namespace -undefined suppress" % (
                cFile.name, oFileName)
        else:
            cmd = "gcc -Wall -fPIC -DPIC -shared %s -o %s -lm" % (
                cFile.name, oFileName)
        status, output = subprocess.getstatusoutput(cmd)
        self.assertEqual(status, 0, "C error:\n%s\nProgram:\n%s\n" %
                         (output, c_code))
        cFile.close()

    def compileAndRun(self, c_code):
        cFile = tempfile.NamedTemporaryFile(mode="w",
                                            prefix="gf4d", suffix=".cpp", dir=Test.tmpdir.name)
        cFile.write(c_code)
        cFile.flush()
        oFileName = str(Path(cFile.name).with_suffix(""))

        cmd = "g++ -g -Wall %s -o %s -Ifract4d/c -lm" % (cFile.name, oFileName)
        status, output = subprocess.getstatusoutput(cmd)
        self.assertEqual(status, 0, "C error:\n%s\nProgram:\n%s\n" %
                         (output, c_code))

        cmd = oFileName
        status, output = subprocess.getstatusoutput(cmd)
        self.assertEqual(status, 0, "Runtime error:\n" + output)

        cFile.close()
        return output

    # test methods
    def testInitMethods(self):
        v = Var(
            Complex, [-1.0, 3.7])
        v.cname = "wibble"

        (d_re, d_im) = self.codegen.decl_from_sym(v)
        self.assertEqual("double wibble_re;", d_re.assem)
        self.assertEqual("double wibble_im;", d_im.assem)

        v.param_slot = 4
        (a_re, a_im) = self.codegen.return_sym(v)

        self.assertEqual("t__pfo->p[4].doubleval = wibble_re;", a_re.format())
        self.assertEqual("t__pfo->p[5].doubleval = wibble_im;", a_im.format())

    def testMove(self):
        x = Var(Float, 2.0)
        self.codegen.symbols["@x"] = x
        self.assertNotEqual(-1, x.param_slot)
        t = self.move(self.var("@x", Float), self.const(2.0, Float))
        self.codegen.generate_code(t)

        self.assertEqual(1, len(self.codegen.out))
        move = self.codegen.out[0]
        # print move.format()

    def testPFHeader(self):
        'Check inline copy of pf.h is up-to-date'
        pfh = open('fract4d/c/pf.h')
        header_contents = pfh.read()
        pfh.close()
        self.assertEqual(header_contents, self.codegen.pf_header)

    def testStdlibHeader(self):
        'Check inline copy of fract_stdlib.h is up-to-date'
        header = open('fract4d/c/fract_stdlib.h')
        header_contents = header.read()
        header.close()
        self.assertEqual(header_contents, self.codegen.fract_stdlib_header)

    def testMatching(self):
        'test tree matching works'
        template = "[Binop, Const, Const]"

        tree = self.binop([self.const(), self.const()])
        self.assertMatchResult(tree, template, 1)

        tree = self.const()
        self.assertMatchResult(tree, template, 0)

        tree = self.binop([self.const(), self.var()])
        self.assertMatchResult(tree, template, 0)

        template = "[Binop, Exp, Exp]"
        self.assertMatchResult(tree, template, 1)

    def testOutput(self):
        tree = self.binop([self.const([1, 3], Complex),
                           self.var("a", Complex)], "*", Complex)
        self.codegen.generate_code(tree)
        out = "\n".join([str(x) for x in self.codegen.out])
        self.assertEqual(
            out,
            """BINOP(*,[Float(1.00000000000000000),Temp(a_re)],[Temp(t__0)])
BINOP(*,[Float(3.00000000000000000),Temp(a_im)],[Temp(t__1)])
BINOP(*,[Float(3.00000000000000000),Temp(a_re)],[Temp(t__2)])
BINOP(*,[Float(1.00000000000000000),Temp(a_im)],[Temp(t__3)])
BINOP(-,[Temp(t__0),Temp(t__1)],[Temp(t__4)])
BINOP(+,[Temp(t__2),Temp(t__3)],[Temp(t__5)])""")

    def testWhichMatch(self):
        'check we get the right tree match'
        tree = self.binop([self.const(), self.const()])
        self.assertEqual(self.codegen.match(tree).__name__, "binop")

    def testGen(self):
        'test simple code generation from ir trees'
        tree = self.const()
        x = self.codegen.generate_code(tree)
        self.assertEqual(isinstance(x, codegen.ConstIntArg), 1)
        self.assertEqual(x.value, 0)
        self.assertEqual(x.format(), "0")

        tree = self.var()
        x = self.codegen.generate_code(tree)
        self.assertEqual(isinstance(x, codegen.TempArg), 1)
        self.assertEqual(x.value, "a")
        self.assertEqual(x.format(), "a")

        tree = self.var("b", Complex)
        x = self.codegen.generate_code(tree)
        self.assertEqual(isinstance(x, codegen.ComplexArg), 1)
        self.assertEqual(x.re.value, "b_re")
        self.assertEqual(x.im.format(), "b_im")

        tree = self.binop([self.const(), self.var()])
        x = self.codegen.generate_code(tree)
        self.assertEqual(isinstance(x, codegen.TempArg), 1, x)
        self.assertEqual(x.value, "t__0")
        self.assertEqual(x.format(), "t__0")

        self.assertEqual(len(self.codegen.out), 1)
        op = self.codegen.out[0]
        self.assertTrue(isinstance(self.codegen.out[0], codegen.Oper))
        self.assertEqual(op.format(), "t__0 = 0 + a;", op.format())

    def testHyperGen(self):
        'generate hypercomplex code'
        tree = self.var("h", Hyper)
        x = self.codegen.generate_code(tree)
        self.assertEqual(isinstance(x, codegen.HyperArg), 1)
        self.assertEqual(x.parts[0].value, "h_re")
        self.assertEqual(x.parts[1].value, "h_i")
        self.assertEqual(x.parts[2].value, "h_j")
        self.assertEqual(x.parts[3].value, "h_k")

    def testComplexAdd(self):
        'simple complex arithmetic'
        # (1,3) + a
        tree = self.binop([self.const([1, 3], Complex),
                           self.var("a", Complex)], "+", Complex)
        x = self.codegen.generate_code(tree)
        self.assertEqual(isinstance(x, codegen.ComplexArg), 1, x)

        self.assertEqual(len(self.codegen.out), 2)

        expAdd = "t__0 = 1.00000000000000000 + a_re;\n" + \
                 "t__1 = 3.00000000000000000 + a_im;"
        self.assertOutputMatch(expAdd)

    def testComplexAdd2(self):
        # a + (1,3)
        tree = self.binop(
            [self.var("a", Complex), self.const([1, 3], Complex)], "+", Complex)
        self.codegen.generate_code(tree)
        self.assertEqual(len(self.codegen.out), 2)
        self.assertTrue(isinstance(self.codegen.out[0], codegen.Oper))

        expAdd = "t__0 = a_re + 1.00000000000000000;\n" + \
                 "t__1 = a_im + 3.00000000000000000;"

        self.assertOutputMatch(expAdd)

    def testComplexAdd3(self):
        # a + b + c
        tree = self.binop([
            self.binop([
                self.var("a", Complex),
                self.var("b", Complex)], "+", Complex),
            self.var("c", Complex)], "+", Complex)
        self.codegen.generate_code(tree)
        self.assertEqual(len(self.codegen.out), 4)
        self.assertTrue(isinstance(self.codegen.out[0], codegen.Oper))

        expAdd = "t__0 = a_re + b_re;\n" + \
                 "t__1 = a_im + b_im;\n" + \
                 "t__2 = t__0 + c_re;\n" +\
                 "t__3 = t__1 + c_im;"

        self.assertOutputMatch(expAdd)

    def testComplexMul(self):
        tree = self.binop([self.const([1, 3], Complex),
                           self.var("a", Complex)], "*", Complex)
        self.codegen.generate_code(tree)
        self.assertEqual(len(self.codegen.out), 6)
        exp = '''t__0 = 1.00000000000000000 * a_re;
t__1 = 3.00000000000000000 * a_im;
t__2 = 3.00000000000000000 * a_re;
t__3 = 1.00000000000000000 * a_im;
t__4 = t__0 - t__1;
t__5 = t__2 + t__3;'''

        self.assertOutputMatch(exp)

    def testComplexMul2(self):
        # a * b * c
        tree = self.binop([
            self.binop([
                self.var("a", Complex),
                self.var("b", Complex)], "*", Complex),
            self.var("c", Complex)], "*", Complex)
        self.codegen.generate_code(tree)

        expAdd = '''t__0 = a_re * b_re;
t__1 = a_im * b_im;
t__2 = a_im * b_re;
t__3 = a_re * b_im;
t__4 = t__0 - t__1;
t__5 = t__2 + t__3;
t__6 = t__4 * c_re;
t__7 = t__5 * c_im;
t__8 = t__5 * c_re;
t__9 = t__4 * c_im;
t__10 = t__6 - t__7;
t__11 = t__8 + t__9;'''
        self.assertOutputMatch(expAdd)

    def testCompareInt(self):
        'test comparisons produce correct code'
        tree = self.binop([self.const(3, Int), self.var("a", Int)], ">", Bool)
        self.codegen.generate_code(tree)
        self.assertOutputMatch("t__0 = 3 > a;")

    def testCompareComplexGreaterThan(self):
        tree = self.binop([self.const([1, 3], Complex),
                           self.var("a", Complex)], ">", Complex)
        self.codegen.generate_code(tree)
        self.assertOutputMatch("t__0 = 1.00000000000000000 > a_re;")

    def testCompareComplexEquality(self):
        tree = self.binop(
            [self.const([1, 3], Complex), self.var("a", Complex)], "==", Complex)

        self.codegen.generate_code(tree)
        self.assertOutputMatch('''t__0 = 1.00000000000000000 == a_re;
t__1 = 3.00000000000000000 == a_im;
t__2 = t__0 && t__1;''')

    def testCompareComplexInequality(self):
        tree = self.binop(
            [self.const([1, 3], Complex), self.var("a", Complex)], "!=", Complex)

        self.codegen.generate_code(tree)
        self.assertOutputMatch('''t__0 = 1.00000000000000000 != a_re;
t__1 = 3.00000000000000000 != a_im;
t__2 = t__0 || t__1;''')

    def testS2A(self):
        'test C code produced by simple code snippets'
        asm = self.sourceToAsm('''t_s2a {
init:
int a = 1
loop:
z = z + a
}''', "loop")
        self.assertOutputMatch('''t__start_floop: ;

t__f0 = ((double)fa);
t__f1 = 0.0;
t__f2 = z_re + t__f0;
t__f3 = z_im + t__f1;
z_re = t__f2;
z_im = t__f3;
goto t__end_floop;''')

        asm = self.sourceToAsm('t_s2a_2{\ninit: a = -1.5\n}', "init")
        self.assertOutputMatch('''t__start_finit: ;

t__f0 = -(1.50000000000000000);
t__f1 = t__f0;
t__f2 = 0.0;
fa_re = t__f1;
fa_im = t__f2;
goto t__end_finit;''')

    def testNewSymbol(self):
        'test symbols used are declared correctly'
        self.codegen.symbols["q"] = Var(Complex)
        z = self.codegen.symbols["q"]  # ping z to get it in output list
        out = self.codegen.output_local_vars(self.codegen, {})
        l = [x for x in out if x.assem == "double q_re = 0.00000000000000000;"]
        self.assertTrue(len(l) == 1, l)

    def testOverrideSymbol(self):
        z = self.codegen.symbols["z"]  # ping z to get it in output list
        out = self.codegen.output_local_vars(self.codegen, {"z": "foo"})
        l = [x for x in out if x.assem == "foo"]
        self.assertTrue(len(l) == 1)

    def testTempSymbol(self):
        x = self.codegen.newTemp(Float)
        dummy = self.codegen.symbols[x.value]
        out = self.codegen.output_local_vars(self.codegen, {})
        l = [x for x in out if x.assem == "double t__0 = 0.00000000000000000;"]
        self.assertTrue(len(l) == 1)

    def testBailoutVars(self):
        t = self.translate('''t{
        init:
        bool x
        bool y
        bailout:
        x
        }''')

        self.codegen.output_all(t)

        # print t.sections["bailout"].pretty()
        # print [x.pretty() for x in t.canon_sections["bailout"]]
        # print [x.format() for x in t.output_sections["bailout"]]

        self.assertEqual('f__bailout', self.codegen.get_bailout_var(t))

    def testBailoutVars2(self):
        t = self.translate('''t{
        init:
        bool x
        bool y
        bailout:
        (x && y) || (y && x)
        }''')

        self.codegen.output_all(t)
        # print t.sections["bailout"].pretty()
        # print [x.pretty() for x in t.canon_sections["bailout"]]
        # print [x.format() for x in t.output_sections["bailout"]]

        self.assertEqual('f__bailout', self.codegen.get_bailout_var(t))

    def testBailoutVars3(self):
        t = self.translate('''t{
        init:
        bool x
        bool y
        bailout:
        x < 2
        }''')

        self.codegen.output_all(t)
        # print t.sections["bailout"].pretty()
        # print [x.pretty() for x in t.canon_sections["bailout"]]
        # print [x.format() for x in t.output_sections["bailout"]]
        self.assertEqual('f__bailout', self.codegen.get_bailout_var(t))

    def testNoZ(self):
        'test a formula which doesn\'t use Z'
        src = '''t_mandel{
init:
x = #zwpixel
loop:
x = x*x + pixel
bailout:
|x| < 4.0
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)

        inserts = {
            "loop_inserts": "printf(\"(%g,%g)\\n\",fx_re,fx_im);",
            "main_inserts": self.main_stub
        }
        c_code = self.codegen.output_c(t, inserts)
        # print c_code
        output = self.compileAndRun(c_code)
        lines = output.split("\n")
        # 1st point we try should bail out
        self.assertEqual(
            lines[0:3], ["(1.5,0)", "(3.75,0)", "(1,0,0)"], output)

        # 2nd point doesn't
        self.assertEqual(lines[3], "(0.02,0.26)", output)
        self.assertEqual(lines[-1], "(20,32,0)", output)
        self.assertEqual(lines[-2], lines[-3], output)

    def testBirch(self):
        'Test whether a UF formula which used to be problematic works'

        # from jgr.ufm
        src = '''Birch {
init:
  z=fn1(fn2((#pixel^@power)))
loop:

bailout:
  @inside
default:
  title = "Birch (Pixel)"
  maxiter = 1
  param inside
    caption = "Inside"
    default = true
  endparam
  param power
    caption = "Power"
    default = (2,0)
  endparam
}
'''
        t = self.translate(src)
        cg = codegen.T(t.symbols)
        cg.output_all(t)
        c = cg.output_c(t)

    def testLattice(self):
        'Test whether a UF formula which used to be problematic works'

        # from daz.ufm
        src = '''Lattice(BOTH) {
init:
loop:
  complex dist=@spacing
  if(real(dist)==0.0)
    dist=dist+(1.0,0.0)
  endif
  if(imag(dist)==0.0)
    dist=dist+(0.0,1.0)
  endif
  complex zp=trunc(#z/dist)
  complex zc=#z-(zp*dist)
  if(@mode==1)
    if(floor(imag(zp))%2==1)
      zc=(zc+real(dist)/2)
      if(zc>dist)
        zc=zc-dist
      endif
    endif
  endif
final:
  #index=|zc|/|dist|
default:
  title="daz.ucl:Lattice"
  param mode
    enum="Square" "Hexagonal"
    default=1
    caption="Style"
    hint="Arrangement of points in the lattice"
  endparam
  param spacing
    default=(1.0,1.0)
    caption="Spacing"
    hint="Spacing of points in the lattice"
  endparam
}
'''
        self.assertCSays(src, "loop", "", "")

    def testFnPartsWorks(self):
        src = '''FnParts {
; A generalization of Burning Ship - apply separate functions to the
; X and Y parts of Z, then another to Z itself
init:
	z = #zwpixel
loop:
	z = @fnComplex(@fnReal(real(z)), @fnImag(imag(z))) + #pixel
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 4.0
endparam
float func bailfunc
	default =cmag
endfunc
float func fnReal
        argtype = float
	default = ident
endfunc
float func fnImag
        argtype = float
	default = ident
endfunc
func fnComplex
	default = sqr
endfunc
}
'''
        t = self.translate(src)
        cg = codegen.T(t.symbols)
        cg.output_all(t)
        c = cg.output_c(t)

    def testDeclareP1andFN1(self):
        'Test that having a param which clashes with built-in names is OK'

        # from jos.ufm
        src = '''
        Ball {
init:
  z = @ps
  c = fn1(#pixel)*@jp
loop:
  z = @p1*c^@exp*z+@p3*z
  c = c*@p2

bailout:
  |z| <= @bailout
default:
  title = "Ball"
  maxiter=30
  param ps
     caption = "Start Parameter"
     default = (20.0,0.0)
  endparam
param jp
     caption = "Julia Parameter"
     default = (1.0,0.0)
  endparam

  param p1
     caption = "Param1"
     default = (0.1,0.0)
  endparam

  param p2
     caption = "Param2"
     default = (0.95,0.0)
  endparam
param p3
     caption = "Param3"
     default = (0.0,0.0)
  endparam
  param exp
     caption = "Exponent"
     default = (1.0,0.0)
  endparam

param bailout
    caption = "Bailout value"
    default = 4000000.0
  endparam
func fn1
  caption = "Function 1"
     default = ident()
  endfunc
}'''
        t = self.translate(src)
        cg = codegen.T(t.symbols)
        cg.output_all(t)
        c = cg.output_c(t)

    def testCF(self):
        'generate code for a coloring function'
        tcf0 = self.translatecf('''
        biomorph {
        init:
        float d = |z|
        loop:
        d = d + |z|
        final:
        #index = log(d+1.0) + 3.0
        }''', "cf0")

        self.assertEqual(-1, tcf0.symbols["z"].param_slot)

        cg_cf0 = codegen.T(tcf0.symbols)
        cg_cf0.output_all(tcf0)

        tcf1 = self.translatecf(
            'x {\n float d = 1.0\n#index = 789.1\n}', "cf1")
        self.assertEqual(-1, tcf0.symbols["z"].param_slot)

        cg_cf1 = codegen.T(tcf1.symbols)
        cg_cf1.output_all(tcf1)

        self.assertEqual(-1, tcf1.symbols["d"].param_slot)
        self.assertEqual(-1, tcf1.symbols["z"].param_slot)

        t = self.translate('''
        mandel {
        loop:
        z = z
        bailout:
        real(pixel) != 1.5 && imag(pixel) != 0.0
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)

        t.merge(tcf0, "cf0_")
        t.merge(tcf1, "cf1_")

        self.assertEqual(-1, t.symbols["cf1d"].param_slot)

        cg.output_decls(t)

        inserts = {
            "main_inserts": self.main_stub
        }

        c_code = self.codegen.output_c(t, inserts)

        # print c_code
        output = self.compileAndRun(c_code)
        self.assertEqual(
            ["(0,0,3)", "(20,32,789.1)"], output.split("\n"))

    def testSolidCF(self):
        'test that #solid works correctly'
        tcf0 = self.translatecf('''
        biomorph {
        init:
        float d = |z|
        loop:
        d = d + |z|
        final:
        #index = log(d+1.0) + 3.0
        }''', "cf0")
        cg_cf0 = codegen.T(tcf0.symbols)
        cg_cf0.output_all(tcf0)

        tcf1 = self.translatecf('x {\n #solid = true\n}', "cf1")
        cg_cf1 = codegen.T(tcf1.symbols)
        cg_cf1.output_all(tcf1)

        t = self.translate('''
        mandel {
        loop:
        z = sqr(z)+#pixel
        bailout:
        |z| < 4.0
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)

        t.merge(tcf0, "cf0_")
        t.merge(tcf1, "cf1_")

        cg.output_decls(t)

        inserts = {
            "main_inserts": self.main_stub,
            "return_inserts": "printf(\"%d\\n\",t__h_solid);"
        }

        c_code = self.codegen.output_c(t, inserts)
        output = self.compileAndRun(c_code)
        outlines = output.split("\n")
        self.assertEqual(outlines[0], "0")
        self.assertEqual(outlines[2], "1")

    def testParamDefaults(self):
        'Test that parameter defaults are computed correctly'
        t = self.translate('''
        p {
        default:
        complex param x
            default = #center
        endparam
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)
        cg.output_decls(t)

        defaults = t.output_sections["default"]
        self.assertEqual("t__a_fx_re = t__h_center_re;",
                         defaults[1].format())

        return_syms = t.output_sections["return_syms"]
        self.assertEqual("t__pfo->p[1].doubleval = t__a_fx_re;",
                         return_syms[1].format())

    def testStructMembers(self):
        'Test that parameter defaults are computed correctly'
        t = self.translate('''
        p {
        init:
        int x = 4 + 3
        complex xx = (1.0,2.0)
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)
        cg.output_decls(t)

        structs = t.output_sections["struct_members"]

        struct_string = "".join([x.format() for x in structs])
        self.assertEqual(True, "int fx;" in struct_string)
        self.assertEqual(True, "int t__f0;" in struct_string)
        self.assertEqual(True, "double fxx_re;" in struct_string)
        self.assertEqual(True, "double fxx_im;" in struct_string)

    def testInside(self):
        'test that #inside works correctly'
        t = self.translate('''
        mandel {
        loop:
        z = sqr(z)+#pixel
        bailout:
        |z| < 4.0
        final:
        #inside = ! #inside
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)
        cg.output_decls(t)

        inserts = {
            "main_inserts": self.main_stub,
            "return_inserts": "printf(\"%d\\n\",t__h_inside);"
        }

        c_code = self.codegen.output_c(t, inserts)
        output = self.compileAndRun(c_code)
        outlines = output.split("\n")
        self.assertEqual(outlines[0], "1")
        self.assertEqual(outlines[2], "0")

    def testFateCF(self):
        'test that #fate works correctly'
        tcf0 = self.translatecf('''
        biomorph {
        init:
        float d = |z|
        loop:
        d = d + |z|
        final:
        #index = log(d+1.0) + 3.0
        }''', "cf0")
        cg_cf0 = codegen.T(tcf0.symbols)
        cg_cf0.output_all(tcf0)

        tcf1 = self.translatecf('x {\n #solid = true\n}', "cf1")
        cg_cf1 = codegen.T(tcf1.symbols)
        cg_cf1.output_all(tcf1)

        t = self.translate('''
        mandel {
        loop:
        z = sqr(z)+#pixel
        bailout:
        |z| < 4.0
        final:
        if #fate == 0
          #fate = 2
        endif
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)

        t.merge(tcf0, "cf0_")
        t.merge(tcf1, "cf1_")

        cg.output_decls(t)

        inserts = {
            "main_inserts": self.main_stub,
            "return_inserts": "printf(\"%d\\n\",t__h_fate);"
        }

        c_code = self.codegen.output_c(t, inserts)
        output = self.compileAndRun(c_code)
        outlines = output.split("\n")
        self.assertEqual(outlines[0], "2")
        self.assertEqual(outlines[2], "2")

    def testDirectCF(self):
        'test that direct coloring algorithms work'
        tcf0 = self.translatecf('''
        dca {
        init:
        float d = |z|
        loop:
        d = d + |z|
        final:
        #color = rgb(|z|, atan2(z), d)
        }''', "cf0")
        cg_cf0 = codegen.T(tcf0.symbols)
        self.assertEqual(cg_cf0.is_direct(), True)

        cg_cf0.output_all(tcf0)

        tcf1 = self.translatecf('x {\n #solid = true\n}', "cf1")
        cg_cf1 = codegen.T(tcf1.symbols)
        cg_cf1.output_all(tcf1)

        t = self.translate('''
        mandel {
        loop:
        z = sqr(z)+#pixel
        bailout:
        |z| < 4.0
        }''')

        cg = codegen.T(t.symbols)
        cg.output_all(t)

        t.merge(tcf0, "cf0_")
        t.merge(tcf1, "cf1_")

        self.assertEqual(cg.is_direct(), True)

        cg.output_decls(t)

        inserts = {
            "main_inserts": self.main_stub,
            "return_inserts": "printf(\"%d\\n\",t__h_solid);"
        }

        c_code = self.codegen.output_c(t, inserts)
        output = self.compileAndRun(c_code)
        outlines = output.split("\n")
        self.assertEqual(len(outlines), 6)
        self.assertEqual(outlines[2], '[14.0625,0,2.25,1]')
        self.assertEqual(outlines[5], '[0,0,0,0]')

    def testCColor(self):
        'test color arithmetic'
        src = '''t_color{
        init:
        color r = rgba(1,0,0,1)
        color g = rgba(0,1,0,1)
        color b = rgba(0,0,1,1)
        color a = rgba(0,0,0,1)
        color yellow = (r + g) / 2
        color cyan = (b + g) / 2
        color white = (r + b + g)
        color black = white - r - b - g
        color yellow2 = yellow * 0.5
        color yellow3 = yellow2 / 0.5
        }'''

        exp = "\n".join([
            "yellow = (0.5,0.5,0,1)",
            "cyan = (0,0.5,0.5,1)",
            "white = (1,1,1,3)",
            "black = (0,0,0,0)",
            "yellow2 = (0.25,0.25,0,0.5)",
            "yellow3 = (0.5,0.5,0,1)"])
        self.assertCSays(src, "init",
                         self.inspect_color("yellow") +
                         self.inspect_color("cyan") +
                         self.inspect_color("white") +
                         self.inspect_color("black") +
                         self.inspect_color("yellow2") +
                         self.inspect_color("yellow3"),
                         exp)

    def testMandelbrotMix(self):
        src = '''MandelbrotMix4a {; Jim Muth
init:
  float a=-1 ;real(p1)
  float b=1.5 ;imag(p1)
  float d=1 ;real(p2)
  float f=-1.5 ;imag(p2)
  float g=1/f
  float h=1/d
  complex j=1/(f-b),
  float abgh = -a*b*g*h
  complex z2= (-a*b*g*h)^j,
  float k=real(p3)+1
  float l=imag(p3)+100
  c=fn1(pixel)
  complex z3=k*((a*(z2^b))+(d*(z2^f)))+c
loop:
  z=k*((a*(z^b))+(d*(z^f)))+c
bailout:
  |z| < l
default:
complex param p1
endparam
complex param p2
endparam
complex param p3
endparam
}
'''
        exp = "g = -0.666667\nh = 1\nj = (-0.333333,0)\nabgh = -1\nz2 = (0.5,-0.866025)\nz3 = (0,2)"

        self.assertCSays(
            src, "init",
            self.inspect_float("g") +
            self.inspect_float("h") +
            self.inspect_complex("j") +
            self.inspect_float("abgh") +
            self.inspect_complex("z2") +
            self.inspect_complex("z3"),
            exp)

    def testTrace(self):
        src = '''t {
        init:
        x = (1,3)
        y = x
        int i = 4
        }'''

        self.assertCSays(
            src, "init",
            "",
            "fx_re = 1\n" +
            "fx_im = 3\n" +
            "fy_re = 1\n" +
            "fy_im = 3\n" +
            "fi = 4",
            {"trace": 1})

    def testRandom(self):
        src = '''t {
        init:
        x = rand
        y = #rand
        }'''

        asm = self.sourceToAsm(src, "init")
        check = self.inspect_complex("x") + self.inspect_complex("y")

        postamble = "t__end_f%s:\n%s\n" % ("init", check)
        c_code = self.makeC("", postamble)
        find_re = re.compile(r'\((.*?),(.*?)\)')

        # run once, gather output
        output = self.compileAndRun(c_code)
        found = find_re.findall(output)
        self.assertEqual(len(found), 2)

        numbers = {}
        for f in found:
            for part in list(f):
                if numbers.get(part):
                    # we generated the same number twice. Highly suspicious
                    self.fail("All numbers should differ in %s" % output)
                numbers[part] = 1

    def testColorParts(self):
        # access to parts
        src = '''t_color3 {
        init:
        color x = rgba(1.0,2.0,3.0,4.0)
        float a=red(x),float b=green(x),float c=blue(x),float d=alpha(x)
        red(x) = 4
        green(x) = 3
        blue(x) = 2
        alpha(x) = 1
        }'''
        self.assertCSays(src, "init",
                         self.inspect_float("a") +
                         self.inspect_float("b") +
                         self.inspect_float("c") +
                         self.inspect_float("d") +
                         self.inspect_color("x"),
                         "a = 1\nb = 2\nc = 3\nd = 4\n" +
                         "x = (4,3,2,1)")

    def testColorStdlib(self):
        # functions on colors
        src = '''t_color4 {
        init:
        color x = rgba(1.0,2.0,3.0,4.0)
        color y = rgba(0.1,0.2,0.3,0.4)

        color b1 = blend(x,y,0.0)
        color b2 = blend(x,y,1.0)
        color b3 = blend(x,y,0.25)

        color r = rgb(1.0,0.0,0.0)
        color gp5 = rgba(0.0,1.0,0.0,0.5)

        color c1 = compose(r, gp5,0)
        color c2 = compose(r, gp5,0.5)
        color c3 = compose(r, gp5,1)
        }'''
        self.assertCSays(src, "init",
                         self.inspect_colors(
                             ["b1", "b2", "b3", "c1", "c2", "c3"]),
                         "b1 = (1,2,3,4)\n" +
                         "b2 = (0.1,0.2,0.3,0.4)\n" +
                         "b3 = (0.775,1.55,2.325,3.1)\n" +
                         "c1 = (1,0,0,1)\n" +
                         "c2 = (0.75,0.25,0,1)\n" +
                         "c3 = (0.5,0.5,0,1)"
                         )

    def testColorHSL(self):
        src = '''t_color_hsl {
        init:
        color r = hsl(0.0,1.0,0.5)
        color g = hsl(2.0,1.0,0.5)
        color b = hsl(4.0,1.0,0.5)
        color white = hsl(0.0,0.0,1.0)
        color black = hsl(0.0,0.0,0.0)
        color transyellow = hsla(1.0,1.0,0.3,0.5)

        float h = hue(b)
        float s = sat(b)
        float l = lum(b)
        }'''
        self.assertCSays(src, "init",
                         self.inspect_colors(["r", "g", "b", "white", "black", "transyellow"]) +
                         self.inspect_float("h") +
                         self.inspect_float("s") +
                         self.inspect_float("l"),
                         "r = (1,0,0,1)\n" +
                         "g = (0,1,0,1)\n" +
                         "b = (0,0,1,1)\n" +
                         "white = (1,1,1,1)\n" +
                         "black = (0,0,0,1)\n" +
                         "transyellow = (0.6,0.6,0,0.5)\n" +
                         "h = 4\ns = 1\nl = 0.5"
                         )

    def testMergeFunctions(self):
        # color merging functions
        funcs = [
            ("mergenormal", "(0,1,0,0.5)"),
            ("mergemultiply", "(0,0,0,0.5)")
        ]

        srcs = []
        inspects = []
        results = []
        for (f, res) in funcs:
            srcs.append("color c_%s = %s(r,gp5)" % (f, f))
            inspects.append(self.inspect_color("c_%s" % f))
            results.append("c_%s = %s" % (f, res))

        src = '''t_merge {
        init:
        color r = rgb(1.0,0.0,0.0)
        color gp5 = rgba(0.0,1.0,0.0,0.5)

        %s
        }''' % "\n".join(srcs)

        self.assertCSays(src, "init", "".join(inspects), "\n".join(results))

    def testGradientFunc(self):
        # gradient() functionality
        src = '''t_grad {
        init:
        color r = gradient(0.0)
        color y = gradient(0.5)
        color g = gradient(1.0)
        }'''

        # y should really be 0.5, but has rounding errors
        self.assertCSays(
            src,
            "init",
            self.inspect_color("r") +
            self.inspect_color("y") +
            self.inspect_color("g"),
            "r = (1,0,0,1)\n" +
            "y = (0.498039,0.498039,0,1)\n" +
            "g = (0,1,0,1)")

    def testImageFunc(self):
        # image() functionality
        src = '''t_image {
        init:
        complex zz
        color imcolor = @foo(zz)
        default:
        image param foo
        endparam
        }'''

        self.assertCSays(
            src,
            "init",
            self.inspect_color("imcolor"),
            "imcolor = (0,0,1,1)")

    def testCHyper(self):
        'test arithmetic in hypercomplex numbers'

        # basic invariants
        src = '''t_hyper1{
        init:
        hyper i = (0,1,0,0)
        hyper j = (0,0,1,0)
        hyper k = (0,0,0,1)
        hyper i2 = i * i
        hyper j2 = j * j
        hyper k2 = k * k
        }'''
        self.assertCSays(src, "init",
                         self.inspect_hyper("i2") +
                         self.inspect_hyper("j2") +
                         self.inspect_hyper("k2"),
                         "i2 = (-1,0,0,0)\nj2 = (-1,0,0,0)\nk2 = (1,0,0,0)")
        # other values
        src = '''t_hyper2{
        init:
        hyper x = (1,2,-3,4)
        hyper y = x + (4,1,-1,0)
        hyper hm = x - (1,1,1,-1)
        hyper h2 = x * y
        hyper h3 = y * x ; check commutativity
        hyper hr = recip(x)
        hyper xnew = x * recip(x)
        hyper zero_ = x + -x
        float m = |x|
        hyper negx = x * -1
        hyper negx2 = x / -1
        }'''
        self.assertCSays(src, "init",
                         self.inspect_hyper("x") +
                         self.inspect_hyper("y") +
                         self.inspect_hyper("h2") +
                         self.inspect_hyper("h3") +
                         self.inspect_hyper("hm") +
                         self.inspect_hyper("hr") +
                         self.inspect_hyper("xnew") +
                         self.inspect_hyper("zero_") +
                         self.inspect_float("m") +
                         self.inspect_hyper("negx") +
                         self.inspect_hyper("negx2"),
                         "x = (1,2,-3,4)\n" +
                         "y = (5,3,-4,4)\n" +
                         "h2 = (3,41,-39,7)\n" +
                         "h3 = (3,41,-39,7)\n" +
                         "hm = (0,1,-4,5)\n" +
                         "hr = (-0.1,0,0.1,0.2)\n" +
                         "xnew = (1,0,0,0)\n" +
                         "zero_ = (0,0,0,0)\n" +
                         "m = 30\n" +
                         "negx = (-1,-2,3,-4)\n" +
                         "negx2 = (-1,-2,3,-4)"
                         )

        # access to parts
        src = '''t_hyper3 {
        init:
        hyper x = (1,2,3,4)
        hyper y
        float a=real(x),float b=imag(x),float c=hyper_j(x),float d=hyper_k(x)
        complex c1 = hyper_ri(x), c2 = hyper_jk(x)
        real(x) = 4
        imag(x) = 3
        hyper_j(x) = 2
        hyper_k(x) = 1
        hyper_ri(y) = (3,4)
        hyper_jk(y) = (1,2)
        }'''
        self.assertCSays(src, "init",
                         self.inspect_float("a") +
                         self.inspect_float("b") +
                         self.inspect_float("c") +
                         self.inspect_float("d") +
                         self.inspect_complex("c1") +
                         self.inspect_complex("c2") +
                         self.inspect_hyper("x") +
                         self.inspect_hyper("y"),
                         "a = 1\nb = 2\nc = 3\nd = 4\n" +
                         "c1 = (1,2)\nc2 = (3,4)\n" +
                         "x = (4,3,2,1)\n" +
                         "y = (3,4,1,2)")

    def testHyperFuncs(self):
        'test calling an example hypercomplex function'
        src = '''t_hyperfunc {
        init:
        hyper s = sin((1,2,3,4))
        }'''
        self.assertCSays(src, "init",
                         self.inspect_hyper("s"),
                         "s = (-5.9761,-36.897,-36.5636,4.49641)")

    def testCtors(self):
        src = '''t_ctors {
        init:
        bool a = bool(true)
        int i = int(2)
        float f = float(2.5)
        complex c = complex(1.0, 2.0)
        hyper h = hyper(1.0,2.0,3.0,4.0)
        hyper h2 = hyper((1.0,2.0),(3.0,4.0))
        color c2 = color(0.0,1.0,1.0,0.0)
        }'''
        self.assertCSays(src, "init",
                         self.inspect_bool("a") +
                         self.inspect_int("i") +
                         self.inspect_float("f") +
                         self.inspect_complex("c") +
                         self.inspect_hyper("h") +
                         self.inspect_hyper("h2") +
                         self.inspect_color("c2"),
                         "a = 1\n" +
                         "i = 2\n" +
                         "f = 2.5\n" +
                         "c = (1,2)\n" +
                         "h = (1,2,3,4)\n" +
                         "h2 = (1,2,3,4)\n" +
                         "c2 = (0,1,1,0)")

    def testMultipleDeclare(self):
        'Declare a var in both branches of an if. Check for correct answer'

        src = '''t_ifdecl {
        init:
        int a = 1
        if a == 1
            int b = 2
        else
            int b = 3
        endif

        if a == 77
            int c = 3
        else
            int c = 2
        endif
        }'''
        self.assertCSays(src, "init",
                         self.inspect_int("b") +
                         self.inspect_int("c"),
                         "b = 2\nc = 2")

    def testC(self):
        '''basic end-to-end testing. Compile a code fragment + instrumentation,
        run it and check output'''

        src = 't_c1 {\nloop: int a = 1\nz = z + a\n}'
        self.assertCSays(src, "loop", "printf(\"%g,%g\\n\",z_re,z_im);", "1,0")

        src = '''t_c2{\ninit:int a = 1 + 3 * 7 + 4 % 2\n}'''
        self.assertCSays(src, "init", "printf(\"%d\\n\",fa);", "22")

        src = 't_c3{\ninit: b = 1 + 3 * 7 - 2\n}'
        self.assertCSays(src, "init", "printf(\"%g\\n\",fb_re);", "20")

        src = 't_c4{\ninit: bool x = |z| < 4.0\n}'
        self.assertCSays(src, "init", "printf(\"%d\\n\",fx);", "1")

        src = 't_c5{\ninit: complex x = (1,3), complex y = (2.5,1.5)\n' + \
              'z = x - y\n}'
        self.assertCSays(src, "init", "printf(\"(%g,%g)\\n\", z_re, z_im);",
                         "(-1.5,1.5)")

        src = 't_c5{\ninit: complex x = #Pixel\nz = z - x\n}'
        self.assertCSays(src, "init", "printf(\"(%g,%g)\\n\", z_re, z_im);",
                         "(0,0)")

        src = 't_c6{\ninit: complex x = y = (2,1), real(y)=3\n}'
        self.assertCSays(src, "init",
                         self.inspect_complex("x") +
                         self.inspect_complex("y"),
                         "x = (2,1)\ny = (3,1)")

        src = 't_c7{\ninit: complex x = (2,1), y = -x\n}'
        self.assertCSays(src, "init",
                         self.inspect_complex("x") +
                         self.inspect_complex("y"),
                         "x = (2,1)\ny = (-2,-1)")

        src = '''t_c_if{
        init:
        int x = 1
        int y = 0
        if x == 1
            y = 2
        else
            y = 3
        endif
        }'''
        self.assertCSays(src, "init", "printf(\"%d\\n\",fy);", "2")

        # casts to & from bool
        src = '''t_c7{
        init:
        bool t = 1
        bool f = 0
        bool temp
        int i7 = 7
        int i0 = 0
        float f0 = 0.0
        float f7 = 7.0
        complex c0 = (0.0,0.0)
        complex c1 = (1.0,0.0)
        complex ci1 = (0.0,1.0)
        complex c7 = (7,7)

        ; now check for casts by round-tripping
        temp = c7
        complex c_from_bt = temp
        temp = c0
        complex c_from_bf = temp
        temp = ci1
        complex c_from_bt2 = temp
        temp = i7
        int i_from_bt = temp
        temp = i0
        int i_from_bf = temp
        temp = f7
        float f_from_bt = temp
        temp = f0
        float f_from_bf = temp

        }'''

        tests = "".join([
            self.inspect_bool("t"),
            self.inspect_bool("f"),
            self.inspect_complex("c_from_bt"),
            self.inspect_complex("c_from_bt2"),
            self.inspect_complex("c_from_bf"),
            self.inspect_int("i_from_bt"),
            self.inspect_int("i_from_bf"),
            self.inspect_float("f_from_bt"),
            self.inspect_float("f_from_bf"),
        ])

        results = "\n".join([
            "t = 1",
            "f = 0",
            "c_from_bt = (1,0)",
            "c_from_bt2 = (1,0)",
            "c_from_bf = (0,0)",
            "i_from_bt = 1",
            "i_from_bf = 0",
            "f_from_bt = 1",
            "f_from_bf = 0",
        ])
        self.assertCSays(src, "init", tests, results)

    def testOptimizeFlagsWork(self):
        self.assertEqual(optimize.Nothing, self.codegen.optimize_flags)
        src = '''t_opt{
        init:
        float x = 2.0 * 0.0
        }
        '''

        asm = self.sourceToAsm(src, "init", {"optimize": optimize.Peephole})
        self.assertEqual(optimize.Peephole, self.codegen.optimize_flags)

        # check we just assign 0 to x instead of doing any math
        move_insn = asm[1]
        self.assertTrue(isinstance(move_insn, instructions.Move))
        self.assertEqual(0.0, move_insn.source()[0][0].value)

    def testEnum(self):
        'Test we can correctly generate code for enumerated params'
        src = '''t_c7{
        init:
        bool b = @y != "bar"
        bool b2 = @zp == "bar"
        int zval = @zp
        default:
        param y
        enum = "foo" "bar"
        endparam
        param zp
        enum = "bar" "foo" "baz"
        default = "foo"
        endparam
        }'''

        tests = "".join([
            self.inspect_bool("b"),
            self.inspect_bool("b2"),
            self.inspect_int("zval"),
        ])

        results = "\n".join([
            "b = 1",
            "b2 = 0",
            "zval = 773",
        ])
        self.assertCSays(src, "init", tests, results)

    def testParams(self):
        'test formulas with parameters work correctly'
        src = 't_cp0{\ninit: complex @p = (2,1)\n}'
        self.assertCSays(src, "init", self.inspect_complex("t__a_fp", ""),
                         "t__a_fp = (2,1)")

        src = '''t_params {
        init: complex x = @p1 + p2 + @my_param
        complex y = @fn1((1,-1)) + fn2((2,0)) + @my_func((2,0))
        }'''

        # first without overrides
        t = self.translate(src)
        self.codegen.generate_all_code(t.canon_sections["init"])

        check = self.inspect_complex("x") + self.inspect_complex("y")
        postamble = "t__end_f%s:\n%s\n" % ("init", check)
        c_code = self.makeC("", postamble)
        output = self.compileAndRun(c_code)
        self.assertEqual(output, "x = (0,0)\ny = (5,-1)")

        # then again with overridden funcs
        t = self.translate(src)
        t.symbols["@my_func"][0].set_func("sqr")
        t.symbols["@fn1"][0].set_func("conj")
        t.symbols["@fn2"][0].set_func("ident")
        self.codegen.generate_all_code(t.canon_sections["init"])

        check = self.inspect_complex("x") + self.inspect_complex("y")
        postamble = "t__end_f%s:\n%s\n" % ("init", check)
        c_code = self.makeC("", postamble)
        output = self.compileAndRun(c_code)
        self.assertEqual(output, "x = (0,0)\ny = (7,1)")

    def testFormulas(self):
        '''these formulas caused an error at one point in development
        so have been added to regression suite'''

        t = self.translate('''andy03 {
        z = c = pixel/4:
        z = p1*z + c
        z = p2*z^3 + c
        z = c + c/2 + z
        ;SOURCE: andy_1.frm
        }''')

        self.assertNoErrors(t)

        # compiler error

        t = self.translate('''
TileMandel {; Terren Suydam (terren@io.com), 1996
            ; modified by Sylvie Gallet [101324,3444]
            ; Modified for if..else logic 3/19/97 by Sylvie Gallet
            ; p1 = center = coordinates for a good Mandel
   ; 0 <= real(p2) = magnification. Default for magnification is 1/3
   ; 0 <= imag(p2) = numtiles. Default for numtiles is 3
  center = p1
  IF (p2 > 0)
     mag = real(p2)
  ELSE
     mag = 1/3
  ENDIF
  IF (imag(p2) > 0)
     numtiles = imag(p2)
  ELSE
     numtiles = 3
  ENDIF
  omega = numtiles*2*pi/3
  x = asin(sin(omega*real(pixel))), y = asin(sin(omega*imag(pixel)))
  z = c = (x+flip(y)) / mag + center:
  z = z*z + c
  |z| <= 4
  ;SOURCE: fract196.frm
}
''')
        self.assertNoErrors(t)

    def testUseBeforeAssign(self):
        src = 't_uba0{\ninit: z = z - x\n}'
        self.assertCSays(src, "init", self.inspect_complex("z", ""),
                         "z = (0,0)")

    def inspect_bool(self, name):
        return "printf(\"%s = %%d\\n\", f%s);" % (name, name)

    def inspect_float(self, name):
        return "printf(\"%s = %%g\\n\", f%s);" % (name, name)

    def inspect_int(self, name):
        return "printf(\"%s = %%d\\n\", f%s);" % (name, name)

    def inspect_complex(self, name, prefix="f"):
        return "printf(\"%s = (%%g,%%g)\\n\", isnan(%s%s_re) ? NAN : %s%s_re, isnan(%s%s_im) ? NAN : %s%s_im);" % \
               (name, prefix, name, prefix, name, prefix, name, prefix, name)

    def inspect_hyper(self, name, prefix="f"):
        return ("printf(\"%s = (%%g,%%g,%%g,%%g)\\n\"," +
                "%s%s_re, %s%s_i, %s%s_j, %s%s_k);") % \
               (name, prefix, name, prefix, name, prefix, name, prefix, name)

    def inspect_color(self, name, prefix="f"):
        return self.inspect_hyper(name, prefix)

    def inspect_colors(self, namelist):
        return "".join([self.inspect_color(x) for x in namelist])

    def predict(self, f, arg1=0, arg2=1):
        # compare our compiler results to Python stdlib
        try:
            x = "%.6g" % f(arg1)
        except ZeroDivisionError:
            x = "inf"
        try:
            y = "%.6g" % f(arg2)
        except ZeroDivisionError:
            y = "inf"

        return "(%s,%s)" % (x, y)

    def cpredict(self, f, arg=(1 + 0j)):
        try:
            z = f(arg)
            return "(%.6g,%.6g)" % (z.real, z.imag)
        except OverflowError:
            return "(inf,inf)"
        except ZeroDivisionError:
            return "(nan,nan)"
        except ValueError:
            return "(inf,inf)"

    def make_test(self, myfunc, pyfunc, val, n):
        codefrag = "ct_%s%d = %s((%d,%d))" % (
            myfunc, n, myfunc, val.real, val.imag)
        lookat = "ct_%s%d" % (myfunc, n)
        result = self.cpredict(pyfunc, val)
        return [codefrag, lookat, result]

    def manufacture_tests(self, myfunc, pyfunc):
        vals = [0 + 0j, 0 + 1j, 1 + 0j, 1 + 1j, 3 + 2j,
                1 - 0j, 0 - 1j, -3 + 2j, -2 - 2j, -1 + 0j]
        return [self.make_test(myfunc, pyfunc, x_y[0], x_y[1])
                for x_y in zip(vals, list(range(1, len(vals))))]

    def cotantests(self):
        def mycotan(z):
            return cmath.cos(z) / cmath.sin(z)

        tests = self.manufacture_tests("cotan", mycotan)

        # CONSIDER: Python 2.7 thinks this cotan(0) is -nan,-nan, older
        # versions think (nan,nan)
        tests[0][2] = "(nan,nan)"

        # CONSIDER: comes out as -0,1.31304 in python, but +0 in C++ and gf4d
        # think Python's probably in error, but not 100% sure
        tests[6][2] = "(0,1.31304)"

        return tests

    def cotanhtests(self):
        def mycotanh(z):
            return cmath.cosh(z) / cmath.sinh(z)

        tests = self.manufacture_tests("cotanh", mycotanh)

        # print tests

        # CONSIDER: Python 2.7 thinks this cotanh(0) is -nan,-nan, older
        # versions think (nan,nan)
        tests[0][2] = "(nan,nan)"

        return tests

    def logtests(self):
        tests = self.manufacture_tests("log", cmath.log)

        tests[0][2] = "(-inf,0)"  # log(0+0j) is overflow in python
        return tests

    def asintests(self):
        tests = self.manufacture_tests("asin", cmath.asin)
        # asin(x+0j) = (?,-0) in python, which is wrong
        tests[0][2] = "(0,0)"
        tests[2][2] = tests[5][2] = "(1.5708,0)"

        return tests

    def acostests(self):
        # work around buggy python acos
        tests = self.manufacture_tests("acos", cmath.acos)
        tests[0][2] = "(1.5708,0)"
        tests[2][2] = tests[5][2] = "(0,0)"
        return tests

    def atantests(self):
        tests = self.manufacture_tests("atan", cmath.atan)

        #print("before", tests)
        tests[1][2] = "(nan,nan)"
        tests[6][2] = "(nan,-inf)"  # not really sure who's right on this
        #print("after", tests)
        return tests

    def atanhtests(self):
        tests = self.manufacture_tests("atanh", cmath.atanh)
        # Python overflows the whole number
        tests[2][2] = tests[5][2] = "(inf,0)"
        return tests

    def test_stdlib_quick(self):
        # TODO compile a function which prints out fn(z) for each function
        # then a main body which passes in a set of different values
        # and construct a set of expected outputs to go with it.
        pass

    def test_colors(self):
        '''Do a bunch of color-related bits and bobs'''

        src = '''t {
        init:
        color black = rgb(0,0,0)
        color something = rgba(0.4, 0.7, 0.3,0.9)
        #color = something
        }'''

        check = "\n".join([self.inspect_color("black"),
                           self.inspect_color("something")])
        exp = "\n".join([
            "black = (0,0,0,1)",
            "something = (0.4,0.7,0.3,0.9)"])
        self.assertCSays(src, "init", check, exp)

    def test_stdlib(self):
        '''This is the slowest test, due to how much compilation it does.
        Calls standard functions with a variety
        of values, checking that they produce the right answers'''

        # additions to python math stdlib
        def myfcotan(x):
            return math.cos(x) / math.sin(x)

        def myfcotanh(x):
            return math.cosh(x) / math.sinh(x)

        def mycotanh(z):
            return cmath.cosh(z) / cmath.sinh(z)

        def myasinh(z):
            return cmath.log(z + cmath.sqrt(z * z + 1))

        def myacosh(z):
            return cmath.log(z + cmath.sqrt(z - 1) * cmath.sqrt(z + 1))

        def myctrunc(z):
            return complex(int(z.real), int(z.imag))

        def mycfloor(z):
            return complex(math.floor(z.real), math.floor(z.imag))

        def mycround(z):
            return complex(int(z.real + 0.5), int(z.imag + 0.5))

        def mycceil(z):
            x = complex(math.ceil(z.real), math.ceil(z.imag))
            return x

        def mycosxx(z):
            # python 2.6's cmath cos produces opposite sign from 2.5 &
            # my implementation. odd but hopefully harmless
            if z == (0 - 1j):
                return cmath.cos(z)

            cosz = cmath.cos(z)
            i = -cosz.imag

            return complex(cosz.real, i)

        def myczero(z):
            return complex(0, 0)

        tests = [
            # code to run, var to inspect, result
            ["fm = (3.0 % 2.0, 3.1 % 1.5)", "fm", "(1,0.1)"],
            ["cj = conj(y)", "cj", "(1,-2)"],
            ["fl = flip(y)", "fl", "(2,1)"],
            ["ri = (imag(y),real(y))", "ri", "(2,1)"],
            ["m = |y|", "m", "(5,0)"],
            ["t = (4,2) * (2,-1)", "t", "(10,0)"],
            ["d1 = y/(1,0)", "d1", "(1,2)"],
            ["d2 = y/y", "d2", "(1,0)"],
            ["d3 = (4,2)/y", "d3", "(1.6,-1.2)"],
            ["d4 = (2,1)/2", "d4", "(1,0.5)"],
            ["recip1 = recip((4,0))/recip(4)", "recip1", "(1,0)"],
            ["i = ident(y)", "i", "(1,2)"],
            ["a = (abs(4),abs(-4))", "a", "(4,4)"],
            ["a2 = abs((4,-4))", "a2", "(4,4)"],
            ["cab = (cabs((0,0)), cabs((3,4)))", "cab", "(0,5)"],
            ["sq = (sqrt(4),sqrt(2))", "sq", self.predict(math.sqrt, 4, 2)],
            ["l = (log(1),log(3))", "l", self.predict(math.log, 1, 3)],
            ["ex = (exp(1),exp(2))", "ex", self.predict(math.exp, 1, 2)],
            ["pow0a = (2^2, 9^0.5)", "pow0a", "(4,3)"],
            ["pow0b = ((-1)^0.5,(-1)^2)", "pow0b", "(nan,1)"],
            ["pow1 = (1,0)^2", "pow1", "(1,0)"],
            ["pow2 = (-2,-3)^7.5", "pow2", "(-13320.5,6986.17)"],
            ["pow3 = (-2,-3)^(1.5,-3.1)", "pow3", "(0.00507248,-0.00681128)"],
            ["pow4 = (0,0)^(1.5,-3.1)", "pow4", "(0,0)"],
            ["manh1 = (manhattanish(2.0,-1.0),manhattanish(0.1,-0.1))",
             "manh1", "(1,0)"],
            ["manh2 = (manhattan(2.0,-1.5),manhattan(-2,1.7))",
             "manh2", "(3.5,3.7)"],
            ["manh3 = (manhattanish2(2.0,-1.0),manhattanish2(0.1,-0.1))",
             "manh3", "(25,0.0004)"],
            ["mx2 = (max2(2,-3),max2(-3,0))", "mx2", "(9,9)"],
            ["mn2 = (min2(-1,-2),min2(7,4))", "mn2", "(1,16)"],
            ["r2 = (real2(3,1),real2(-2.5,2))", "r2", "(9,6.25)"],
            ["i2 = (imag2(3,2),imag2(2,-0))", "i2", "(4,0)"],
            ["ftrunc1 = (trunc(0.5), trunc(0.4))", "ftrunc1", "(0,0)"],
            ["ftrunc2 = (trunc(-0.5), trunc(-0.4))", "ftrunc2", "(0,0)"],
            ["frnd1 = (round(0.5), round(0.4))", "frnd1", "(1,0)"],
            ["frnd2 = (round(-0.5), round(-0.4))", "frnd2", "(0,0)"],
            ["fceil1 = (ceil(0.5), ceil(0.4))", "fceil1", "(1,1)"],
            ["fceil2 = (ceil(-0.5), ceil(-0.4))", "fceil2", "(0,0)"],
            ["ffloor1 = (floor(0.5), floor(0.4))", "ffloor1", "(0,0)"],
            ["ffloor2 = (floor(-0.5), floor(-0.4))", "ffloor2", "(-1,-1)"],
            ["fzero = (zero(77),zero(-41.2))", "fzero", "(0,0)"],
            ["fmin = (min(-2,-3), min(2,3))", "fmin", "(-3,2)"],
            ["fmax = (max(-2,-3), max(2,3))", "fmax", "(-2,3)"],

            # trig functions
            ["t_sin = (sin(0),sin(1))", "t_sin", self.predict(math.sin)],
            ["t_cos = (cos(0),cos(1))", "t_cos", self.predict(math.cos)],
            ["t_tan = (tan(0),tan(1))", "t_tan", self.predict(math.tan)],
            ["t_cotan = (cotan(0),cotan(1))", "t_cotan",
             self.predict(myfcotan)],
            ["t_sinh = (sinh(0),sinh(1))", "t_sinh", self.predict(math.sinh)],
            ["t_cosh = (cosh(0),cosh(1))", "t_cosh", self.predict(math.cosh)],
            ["t_tanh = (tanh(0),tanh(1))", "t_tanh", self.predict(math.tanh)],
            ["t_cotanh = (cotanh(0),cotanh(1))", "t_cotanh",
             self.predict(myfcotanh)],

            # inverse trig functions
            ["t_asin = (asin(0),asin(1))", "t_asin", self.predict(math.asin)],
            ["t_acos = (acos(0),acos(1))", "t_acos", self.predict(math.acos)],
            ["t_atan = (atan(0),atan(1))", "t_atan", self.predict(math.atan)],
            ["t_atan2 = (atan2((1,1)),atan2((-1,-1)))",
             "t_atan2", "(0.785398,-2.35619)"],
            # these aren't in python stdlib, need to hard-code results
            ["t_asinh = (asinh(0),asinh(1))", "t_asinh", "(0,0.881374)"],
            ["t_acosh = (acosh(10),acosh(1))", "t_acosh", "(2.99322,0)"],
            ["t_atanh = (atanh(0),atanh(0.5))", "t_atanh", "(0,0.549306)"],
        ]
        tests += self.manufacture_tests("sin", cmath.sin)
        tests += self.manufacture_tests("cos", cmath.cos)
        tests += self.manufacture_tests("cosxx", mycosxx)
        tests += self.manufacture_tests("tan", cmath.tan)
        tests += self.manufacture_tests("sinh", cmath.sinh)
        tests += self.manufacture_tests("cosh", cmath.cosh)
        tests += self.manufacture_tests("tanh", cmath.tanh)
        tests += self.manufacture_tests("exp", cmath.exp)
        tests += self.manufacture_tests("sqrt", cmath.sqrt)
        tests += self.manufacture_tests("round", mycround)
        tests += self.manufacture_tests("ceil", mycceil)
        tests += self.manufacture_tests("floor", mycfloor)
        tests += self.manufacture_tests("trunc", myctrunc)
        tests += self.manufacture_tests("zero", myczero)
        tests += self.cotantests()
        tests += self.cotanhtests()
        tests += self.logtests()

        tests += self.asintests()
        tests += self.acostests()
        tests += self.atantests()
        tests += self.manufacture_tests("asinh", myasinh)
        tests += self.manufacture_tests("acosh", myacosh)
        tests += self.atanhtests()

        # construct a formula calculating all of the above,
        # run it and compare results with expected values
        src = 't_c6{\ninit: y = (1,2)\n' + \
              "\n".join([x[0] for x in tests]) + "\n}"

        check = "\n".join([self.inspect_complex(x[1]) for x in tests])
        exp = ["%s = %s" % (x[1], x[2]) for x in tests]
        self.assertCSays(src, "init", check, exp)

    def testExpression(self):
        '''this is for quick manual experiments - skip if input var not set'''
        global g_exp, g_x
        if g_exp is None:
            return
        x = g_x or "(1,0)"
        src = 't_test {\ninit:\nx = %s\nresult = %s\n}' % (x, g_exp)
        asm = self.sourceToAsm(src, "init", {})
        postamble = "t__end_finit:\nprintf(\"(%g,%g)\\n\",fresult_re,fresult_im);"
        c_code = self.makeC("", postamble)
        output = self.compileAndRun(c_code)
        print(output)

    def testPeriodicity(self):
        'test that periodicity actually short-circuits calculations'
        src = '''t_mandel{
init:
z = 0
float k = 0
loop:
z = z + 1.0/2^(k+1)
k = k+1
bailout:
|z| < 1e100
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)

        inserts = {
            "done_inserts": 'printf(\"%g\\n\",fk);',
            "main_inserts": self.main_stub.replace("((100))", "0")
        }
        c_code = self.codegen.output_c(t, inserts)
        output = self.compileAndRun(c_code)
        lines = output.split("\n")

        self.assertEqual('34', lines[0])
        self.assertEqual('(33,32,0)', lines[1])

    def testTolerance(self):
        'test that period_tolerance var changes periodicity behavior'

        src = '''t_mandel{
init:
z = 0
float k = 0
loop:
z = z + 1.0/2^(k+1)
k = k+1
bailout:
|z| < 1e100
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)

        inserts = {
            "done_inserts": 'printf(\"%g\\n\",fk);',
            "main_inserts": self.main_stub.replace("((100))", "0").replace("((1.0E-9))", "0.001")
        }
        c_code = self.codegen.output_c(t, inserts)
        output = self.compileAndRun(c_code)
        lines = output.split("\n")

        self.assertEqual(lines[0], '10')
        self.assertEqual(lines[1], '(9,32,0)')

    def complexFromLine(self, str):
        cmplx_re = re.compile(r'\((.*?),(.*?)\)')
        m = cmplx_re.match(str)
        self.assertTrue(m is not None)
        real = float(m.group(1))
        imag = float(m.group(2))
        return real + imag * 1j

    def testMandel(self):
        '''test that formula for the mandelbrot set does the right thing
        for a couple of selected values'''
        src = '''t_mandel{
init:
z = #zwpixel
loop:
z = z*z + pixel
bailout:
|z| < 4.0
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)

        inserts = {
            "loop_inserts": "printf(\"(%g,%g)\\n\",z_re,z_im);",
            "main_inserts": self.main_stub
        }
        c_code = self.codegen.output_c(t, inserts)
        # print c_code
        output = self.compileAndRun(c_code)
        lines = output.split("\n")
        # 1st point we try should bail out
        self.assertEqual(
            lines[0:3], ["(1.5,0)", "(3.75,0)", "(1,0,0)"], output)

        # 2nd point doesn't
        self.assertEqual(lines[3], "(0.02,0.26)", output)
        self.assertEqual(lines[-1], "(20,32,0)", output)

        # last 2 points should be within #tolerance of each other
        p1 = self.complexFromLine(lines[-2])
        p2 = self.complexFromLine(lines[-3])

        diff = max(math.fabs(p1.real - p2.real), math.fabs(p1.imag - p2.imag))
        self.assertTrue(diff < 0.001)

        # try again with sqr function and check results match
        src = '''t_mandel{
init:
z = #zwpixel
loop:
z = sqr(z) + pixel
bailout:
|z| < 4.0
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)
        c_code = self.codegen.output_c(t, inserts)
        output2 = self.compileAndRun(c_code)
        lines2 = output2.split("\n")
        # 1st point we try should bail out
        self.assertEqual(lines, lines2, output2)

        # and again with ^2
        src = '''t_mandel{
init:
z = #zwpixel
loop:
z = z^2 + pixel
bailout:
|z| < 4.0
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)
        c_code = self.codegen.output_c(t, inserts)
        output3 = self.compileAndRun(c_code)
        lines3 = output2.split("\n")
        # 1st point we try should bail out
        self.assertEqual(lines, lines3, output3)

    def testFinal(self):
        # test that final section works
        src = '''t_mandel{
init:
loop:
z = z*z + pixel
bailout:
|z| < 4.0
final:
z = (-77.0,9.0)
float t = #tolerance
}'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)

        inserts = {
            "main_inserts": self.main_stub,
            "done_inserts": "printf(\"(%g,%g,%g)\\n\",z_re,z_im,ft);",
            "pre_final_inserts": "printf(\"(%g,%g)\\n\",z_re,z_im);"
        }
        c_code = self.codegen.output_c(t, inserts)
        # print c_code
        output = self.compileAndRun(c_code)
        lines = output.split("\n")
        self.assertEqual(lines[1], "(-77,9,1e-09)")
        self.assertEqual(lines[4], "(-77,9,1e-09)")

    def testDumpParams(self):
        cg = codegen.T(fsymbol.T(), {"trace": True})
        self.assertEqual(cg.generate_trace, True)

    def testLibrary(self):
        # create a library containing the compiled code
        src = '''
Newton4(XYAXIS) {; Mark Peterson
  ; Note that floating-point is required to make this compute accurately
  z = pixel, Root = 1:
   z3 = z*z*z
   z4 = z3 * z
   z = (3 * z4 + Root) / (4 * z3)
    .004 <= |z4 - Root|
  }
'''
        t = self.translate(src)
        self.codegen.output_all(t)
        self.codegen.output_decls(t)
        c_code = self.codegen.output_c(t)
        self.compileSharedLib(c_code)

    def testReservedWords(self):
        '''Check that user vars don\'t clash with C reserved words'''
        src = '''t_foo {
        init:
        int for
        float double
        bool main
        }'''
        self.assertCSays(src, "init", "", "")

    def testMagn(self):
        '''Use the #magn variable and check it has the right value'''
        src = '''t_magn {
        init:
        float x = #magn
        }'''
        self.assertCSays(src, "init", self.inspect_float("x"), "x = 1")

    def testCenter(self):
        '''Use the #center variable and check it has the right value'''
        src = '''t_center {
        init:
        complex c = #center
        }'''
        self.assertCSays(src, "init", self.inspect_complex("c"), "c = (0,0)")

    def testArray(self):
        src = '''t_array1 {
        init:
        int array[100]
        int a2[10,10]
        array[0] = -77
        int x = array[0]
        array[1] = 22
        int y = array[1]
        a2[4,7] = 109
        int moop = a2[4,7]
        }'''

        self.assertCSays(
            src, "init",
            self.inspect_int("x") + self.inspect_int("y") +
            self.inspect_int("moop"),
            "x = -77\ny = 22\nmoop = 109")

    def testFloatArray(self):
        src = '''t_array1 {
        init:
        float array[100]
        float a2[10,10]
        array[0] = -77.1
        float x = array[0]
        array[1] = 22.9
        float y = array[1]
        a2[4,7] = 109.3
        float moop = a2[4,7]
        }'''

        self.assertCSays(
            src, "init",
            self.inspect_float("x") + self.inspect_float("y") +
            self.inspect_float("moop"),
            "x = -77.1\ny = 22.9\nmoop = 109.3")

    def testComplexArray(self):
        src = '''t_array1 {
        init:
        complex array[100]
        complex a2[10,10]
        array[0] = (-77.1, 22.0)
        complex x = array[0]
        array[1] = (22.9,0.5)
        complex y = array[1]
        a2[4,7] = (77,10.0)
        complex moop = a2[4,7]
        }'''

        self.assertCSays(
            src, "init",
            "".join([
                self.inspect_complex("x"),
                self.inspect_complex("y"),
                self.inspect_complex("moop")
            ]),
            "x = (-77.1,22)\ny = (22.9,0.5)\nmoop = (77,10)")

    def disabled_testDivisionByZero(self):
        src = '''zero {
        init:
        int x = -1 % 0
        }'''

        self.assertCSays(
            src, "init",
            self.inspect_int("x"),
            "x = -inf")

    # assertions
    def assertCSays(self, source, section, check, result, options={}):
        asm = self.sourceToAsm(source, section, options)
        postamble = "t__end_f%s:\n%s\n" % (section, check)
        c_code = self.makeC("", postamble)
        output = self.compileAndRun(c_code)

        # print c_code
        if isinstance(result, list):
            outputs = output.split("\n")
            for (exp, res) in zip(result, outputs):
                self.assertEqual(exp, res)
        else:
            self.assertEqual(output, result)

    def assertOutputMatch(self, exp):
        str_output = "\n".join([x.format() for x in self.codegen.out])
        self.assertEqual(str_output, exp)

    def assertMatchResult(self, tree, template, result):
        template = self.codegen.expand(template)
        self.assertEqual(self.codegen.match_template(tree, template), result,
                         "%s mismatches %s" % (tree.pretty(), template))
