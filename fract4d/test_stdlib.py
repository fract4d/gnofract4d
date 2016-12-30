#!/usr/bin/env python3

# tests the standard library of math functions
import unittest
import math
import cmath
import string
import subprocess
import types

import testbase

import absyn
import codegen
import fractparser
import fractlexer
import fsymbol
import translate


class Test(testbase.TestBase):
    def setUp(self):
        self.fakeNode = absyn.Empty(0)
        self.codegen = codegen.T(fsymbol.T())
        self.parser = fractparser.parser

    def compileAndRun(self,c_code):
        cFileName = self.codegen.writeToTempFile(c_code,".cpp")
        oFileName = self.codegen.writeToTempFile("")
        #print c_code
        cmd = "g++ -Wall %s -o %s -Ic -lm" % (cFileName, oFileName)
        #print cmd
        (status,output) = subprocess.getstatusoutput(cmd)
        self.assertEqual(status,0,"C error:\n%s\nProgram:\n%s\n" % \
                         ( output,c_code))
        #print "status: %s\noutput:\n%s" % (status, output)
        cmd = oFileName
        (status,output) = subprocess.getstatusoutput(cmd)
        self.assertEqual(status,0, "Runtime error:\n" + output)
        print("status: %s\noutput:\n%s" % (status, output))
        return output

    def makeC(self,user_preamble="", user_postamble=""):
        # construct a C stub for testing
        preamble = '''
        #include <stdio.h>
        #include <math.h>

        #include "cmap.cpp"
        
        typedef enum
	{
	    INT = 0,
	    FLOAT = 1,
            GRADIENT = 2
	} e_paramtype;
	
	struct s_param
	{
	    e_paramtype t;
	    int intval;
	    double doubleval;
            void *gradient;
	};

        typedef struct {
            struct s_param *p;
            void *arena;
        } pf_fake;
        
        int main(){
        struct s_param params[20];
        int i = 0;

        ListColorMap *pMap = new ListColorMap();
        pMap->init(2);
        pMap->set(0,0.0,255,0,0,0);
        pMap->set(1,1.0,0,255,0,0);

        for(i = 0; i < 20; ++i) {
            params[i].t = FLOAT;
            params[i].intval = 773;
            params[i].doubleval = 0.0;
            params[i].gradient = pMap;
        };
        pf_fake t__f;
        t__f.p = params;
        pf_fake *t__pfo = &t__f;
        double pixel_re = 0.0, pixel_im = 0.0;
        double t__h_zwpixel_re = 0.0, t__h_zwpixel_im = 0.0;
        double t__h_color_re = 0.0;
        double t__h_color_i = 0.0;
        double t__h_color_j = 0.0;
        double t__h_color_k = 0.0;
        double inputs[] = {
            0, 0,
            0, 1,
            1, 0,
            1, 1,
            3, 2,
            1,-0.0,
            0,-1,
            -3,2,
            -2,-2,
            -1,0
        };
        for(int i__ = 0; i < sizeof(inputs)/sizeof(double); i__ += 2)
        {
            

        '''

        codegen_symbols = self.codegen.output_symbols(self.codegen,{})
        decls = string.join([x.format() for x in codegen_symbols],"\n")
        str_output = string.join([x.format() for x in self.codegen.out],"\n")
        postamble = "}\nreturn 0;}\n"

        return string.join([preamble,decls,"\n",
                            user_preamble,str_output,"\n",
                            user_postamble,postamble],"")


    def inspect_bool(self,name):
        return "printf(\"%s = %%d\\n\", f%s);" % (name,name)

    def inspect_float(self,name):
        return "printf(\"%s = %%g\\n\", f%s);" % (name,name)

    def inspect_int(self,name):
        return "printf(\"%s = %%d\\n\", f%s);" % (name,name)

    def inspect_complex(self,name,prefix="f"):
        return "printf(\"%s = (%%g,%%g)\\n\", %s%s_re, %s%s_im);" % \
               (name,prefix,name,prefix,name)

    def inspect_hyper(self,name,prefix="f"):
        return ("printf(\"%s = (%%g,%%g,%%g,%%g)\\n\"," +
               "%s%s_re, %s%s_i, %s%s_j, %s%s_k);") % \
               (name,prefix,name,prefix,name,prefix,name,prefix,name)

    def inspect_color(self,name,prefix="f"):
        return self.inspect_hyper(name, prefix)

    def inspect_colors(self,namelist):
        return "".join([self.inspect_color(x) for x in namelist])
    
    def predict(self,f,arg1=0,arg2=1):
        # compare our compiler results to Python stdlib
        try:
            x = "%.6g" % f(arg1)
        except ZeroDivisionError:
            x = "inf"
        try:
            y = "%.6g" % f(arg2)
        except ZeroDivisionError:
            y = "inf"
        
        return "(%s,%s)" % (x,y)

    def cpredict(self,f,arg=(1+0j)):
        try:
            z = f(arg)
            return "(%.6g,%.6g)" % (z.real,z.imag) 
        except OverflowError:
            return "(inf,inf)"
        except ZeroDivisionError:
            return "(nan,nan)"
    
    def make_test(self,myfunc,pyfunc,val,n):
        codefrag = "ct_%s%d = %s((%d,%d))" % (myfunc, n, myfunc, val.real, val.imag)
        lookat = "ct_%s%d" % (myfunc, n)
        result = self.cpredict(pyfunc,val)
        return [ codefrag, lookat, result]
        
    def manufacture_tests(self,myfunc,pyfunc):
        vals = [ 0+0j, 0+1j, 1+0j, 1+1j, 3+2j, 1-0j, 0-1j, -3+2j, -2-2j, -1+0j ]
        return [self.make_test(myfunc,pyfunc,x_y[0],x_y[1]) for x_y in zip(vals,list(range(1,len(vals))))]

    def cotantests(self):
        def mycotan(z):
            return cmath.cos(z)/cmath.sin(z)

        tests = self.manufacture_tests("cotan",mycotan)
        
        # CONSIDER: comes out as -0,1.31304 in python, but +0 in C++ and gf4d
        # think Python's probably in error, but not 100% sure
        tests[6][2] = "(0,1.31304)"
        
        return tests

    def logtests(self):
        tests = self.manufacture_tests("log",cmath.log)
                    
        tests[0][2] = "(-inf,0)" # log(0+0j) is overflow in python
        return tests

    def asintests(self):
        tests = self.manufacture_tests("asin",cmath.asin)
        # asin(x+0j) = (?,-0) in python, which is wrong
        tests[0][2] = "(0,0)" 
        tests[2][2] = tests[5][2] = "(1.5708,0)"

        return tests

    def acostests(self):
        # work around buggy python acos 
        tests = self.manufacture_tests("acos",cmath.acos)
        tests[0][2] = "(1.5708,0)"
        tests[2][2] = tests[5][2] = "(0,0)"
        return tests

    def atantests(self):
        tests = self.manufacture_tests("atan",cmath.atan)
        tests[1][2] = "(nan,nan)"
        tests[6][2] = "(nan,-inf)" # not really sure who's right on this
        return tests

    def atanhtests(self):
        tests = self.manufacture_tests("atanh",cmath.atanh)
        tests[2][2] = tests[5][2] = "(inf,0)" # Python overflows the whole number
        return tests

    def test_stdlib(self):
        '''This is the slowest test, due to how much compilation it does.
        Calls standard functions with a variety
        of values, checking that they produce the right answers'''
        
        # additions to python math stdlib
        def myfcotan(x):
            return math.cos(x)/math.sin(x)
        
        def myfcotanh(x):
            return math.cosh(x)/math.sinh(x)

        def mycotanh(z):
            return cmath.cosh(z)/cmath.sinh(z)

        def myasinh(z):
            return cmath.log(z + cmath.sqrt(z*z+1))

        def myacosh(z):
            return cmath.log(z + cmath.sqrt(z-1) * cmath.sqrt(z+1))

        def myctrunc(z):
            return complex(int(z.real),int(z.imag))

        def mycfloor(z):
            return complex(math.floor(z.real),math.floor(z.imag))

        def mycround(z):
            return complex(int(z.real+0.5),int(z.imag+0.5))

        def mycceil(z):
            x = complex(math.ceil(z.real),math.ceil(z.imag))
            return x
        
        def mycosxx(z):
            cosz = cmath.cos(z)
            return complex(cosz.real, -cosz.imag)
        
        def myczero(z):
            return complex(0,0)
        
        tests = []
        #    # code to run, var to inspect, result
        #    [ "fm = (3.0 % 2.0, 3.1 % 1.5)","fm","(1,0.1)"], 
        #    [ "cj = conj(y)", "cj", "(1,-2)"],
        #    [ "fl = flip(y)", "fl", "(2,1)"],
        #    [ "ri = (imag(y),real(y))","ri", "(2,1)"],
        #    [ "m = |y|","m","(5,0)"],
        #    [ "t = (4,2) * (2,-1)", "t", "(10,0)"],
        #    [ "d1 = y/(1,0)","d1","(1,2)"],
        #    [ "d2 = y/y","d2","(1,0)"],
        #    [ "d3 = (4,2)/y","d3","(1.6,-1.2)"],
        #    [ "d4 = (2,1)/2","d4","(1,0.5)"],
        #    [ "recip1 = recip((4,0))/recip(4)", "recip1", "(1,0)"],
        #    [ "i = ident(y)","i","(1,2)"],
        #    [ "a = (abs(4),abs(-4))","a","(4,4)"],
        #    [ "a2 = abs((4,-4))","a2","(4,4)"],
        #    [ "cab = (cabs((0,0)), cabs((3,4)))", "cab", "(0,5)"],
        #    [ "sq = (sqrt(4),sqrt(2))", "sq", self.predict(math.sqrt,4,2)],
        #    [ "l = (log(1),log(3))", "l", self.predict(math.log,1,3)],
        #    [ "ex = (exp(1),exp(2))","ex", self.predict(math.exp,1,2)],
        #    [ "p = (2^2,9^0.5)","p", "(4,3)"],
        #    [ "pow1 = (1,0)^2","pow1", "(1,0)"],
        #    [ "pow2 = (-2,-3)^7.5","pow2","(-13320.5,6986.17)"],
        #    [ "pow3 = (-2,-3)^(1.5,-3.1)","pow3","(0.00507248,-0.00681128)"],
        #    [ "pow4 = (0,0)^(1.5,-3.1)","pow4","(0,0)"],
        #    [ "manh1 = (manhattanish(2.0,-1.0),manhattanish(0.1,-0.1))",
        #      "manh1", "(1,0)"],
        #    [ "manh2 = (manhattan(2.0,-1.5),manhattan(-2,1.7))",
        #      "manh2", "(3.5,3.7)"],
        #    [ "manh3 = (manhattanish2(2.0,-1.0),manhattanish2(0.1,-0.1))",
        #      "manh3", "(25,0.0004)"],
        #    [ "mx2 = (max2(2,-3),max2(-3,0))", "mx2", "(9,9)"],
        #    [ "mn2 = (min2(-1,-2),min2(7,4))", "mn2", "(1,16)"],
        #    [ "r2 = (real2(3,1),real2(-2.5,2))","r2","(9,6.25)"],
        #    [ "i2 = (imag2(3,2),imag2(2,-0))", "i2", "(4,0)"],
        #    [ "ftrunc1 = (trunc(0.5), trunc(0.4))", "ftrunc1", "(0,0)"],
        #    [ "ftrunc2 = (trunc(-0.5), trunc(-0.4))", "ftrunc2", "(0,0)"],
        #    [ "frnd1 = (round(0.5), round(0.4))", "frnd1", "(1,0)"],
        #    [ "frnd2 = (round(-0.5), round(-0.4))", "frnd2", "(0,0)"],
        #    [ "fceil1 = (ceil(0.5), ceil(0.4))", "fceil1", "(1,1)"],
        #    [ "fceil2 = (ceil(-0.5), ceil(-0.4))", "fceil2", "(0,0)"],
        #    [ "ffloor1 = (floor(0.5), floor(0.4))", "ffloor1", "(0,0)"],
        #    [ "ffloor2 = (floor(-0.5), floor(-0.4))", "ffloor2", "(-1,-1)"],
        #    [ "fzero = (zero(77),zero(-41.2))", "fzero", "(0,0)"],
        #    
        #    # trig functions
        #    [ "t_sin = (sin(0),sin(1))","t_sin", self.predict(math.sin)],
        #    [ "t_cos = (cos(0),cos(1))","t_cos", self.predict(math.cos)],
        #    [ "t_tan = (tan(0),tan(1))","t_tan", self.predict(math.tan)],
        #    [ "t_cotan = (cotan(0),cotan(1))","t_cotan", self.predict(myfcotan)],
        #    [ "t_sinh = (sinh(0),sinh(1))","t_sinh", self.predict(math.sinh)],
        #    [ "t_cosh = (cosh(0),cosh(1))","t_cosh", self.predict(math.cosh)],
        #    [ "t_tanh = (tanh(0),tanh(1))","t_tanh", self.predict(math.tanh)],
        #    [ "t_cotanh = (cotanh(0),cotanh(1))","t_cotanh",
        #      self.predict(myfcotanh)],
        #      
        #    # inverse trig functions
        #    [ "t_asin = (asin(0),asin(1))","t_asin", self.predict(math.asin)],
        #    [ "t_acos = (acos(0),acos(1))","t_acos", self.predict(math.acos)],
        #    [ "t_atan = (atan(0),atan(1))","t_atan", self.predict(math.atan)],
        #    [ "t_atan2 = (atan2((1,1)),atan2((-1,-1)))",
        #      "t_atan2", "(0.785398,-2.35619)"],
        #    # these aren't in python stdlib, need to hard-code results
        #    [ "t_asinh = (asinh(0),asinh(1))","t_asinh", "(0,0.881374)" ],
        #    [ "t_acosh = (acosh(10),acosh(1))","t_acosh", "(2.99322,0)" ],
        #    [ "t_atanh = (atanh(0),atanh(0.5))","t_atanh", "(0,0.549306)" ],
        #]
        #tests += self.manufacture_tests("sin",cmath.sin)
        #tests += self.manufacture_tests("cos",cmath.cos)
        #tests += self.manufacture_tests("cosxx", mycosxx)
        #tests += self.manufacture_tests("tan",cmath.tan)
        #tests += self.manufacture_tests("sinh",cmath.sinh)
        #tests += self.manufacture_tests("cosh",cmath.cosh)
        #tests += self.manufacture_tests("tanh",cmath.tanh)
        #tests += self.manufacture_tests("exp",cmath.exp)
        #tests += self.manufacture_tests("sqrt",cmath.sqrt)
        #tests += self.manufacture_tests("round",mycround)
        #tests += self.manufacture_tests("ceil",mycceil)
        #tests += self.manufacture_tests("floor",mycfloor)
        #tests += self.manufacture_tests("trunc",myctrunc)
        #tests += self.manufacture_tests("zero",myczero)
        #tests += self.cotantests()
        #tests += self.manufacture_tests("cotanh",mycotanh)
        #tests += self.logtests()
        #
        #tests += self.asintests()
        #tests += self.acostests()
        #tests += self.atantests()
        #tests += self.manufacture_tests("asinh",myasinh)
        tests += self.manufacture_tests("acosh",myacosh)
        #tests += self.atanhtests()

        # construct a formula calculating all of the above,
        # run it and compare results with expected values
        src = 't_c6{\ninit: y = (1,2)\n' + \
              string.join([x[0] for x in tests],"\n") + "\n}"

        check = string.join([self.inspect_complex(x[1]) for x in tests],"\n")
        exp = ["%s = %s" % (x[1],x[2]) for x in tests]
        self.assertCSays(src,"init",check,exp)

    def assertCSays(self,source,section,check,result,dump=None):
        asm = self.sourceToAsm(source,section,dump)
        postamble = "t__end_f%s:\n%s\n" % (section,check)
        c_code = self.makeC("", postamble)        
        output = self.compileAndRun(c_code)
        if isinstance(result,list):
            outputs = string.split(output,"\n")
            for (exp,res) in zip(result,outputs):
                self.assertEqual(exp,res)
        else:
            self.assertEqual(output,result)

    def translate(self,s,options={}):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        #print pt.pretty()
        t = translate.T(pt.children[0],options)
        #print t.pretty()
        self.assertNoErrors(t)
        self.codegen = codegen.T(t.symbols,options)
        return t

    def translatecf(self,s,name,options={}):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        #print pt.pretty()
        t = translate.ColorFunc(pt.children[0],name,options)
        #print t.pretty()
        self.assertNoErrors(t)
        return t
        
    def sourceToAsm(self,s,section,options={}):
        t = self.translate(s,options)
        self.codegen.generate_all_code(t.canon_sections[section])
        if options.get("dumpAsm") == 1:
            self.printAsm()
        return self.codegen.out



def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
