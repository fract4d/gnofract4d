#!/usr/bin/env python3

# test harness for translate module

import string
import unittest
import types
import pickle

import testbase

import absyn
import translate
import fractparser
import fractlexer
import fracttypes
import ir
import stdlib

class Test(testbase.TestBase):
    def setUp(self):
        self.parser = fractparser.parser

    def tearDown(self):
        pass

    def translate(self,s,prefix="f",dump=None):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        #print(pt.pretty(0,True))
        return translate.T(pt.children[0], prefix, dump)

    def translatecf(self,s,dump=None):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        return translate.ColorFunc(pt.children[0], "cf0", dump)

    def translateGradient(self,s,dump=None):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        return translate.GradientFunc(pt.children[0], dump)

    def translateTransform(self,s,dump=None):
        fractlexer.lexer.lineno = 1
        pt = self.parser.parse(s)
        return translate.Transform(pt.children[0], "t0", dump)
        
    def testEmpty(self):
        pt = absyn.Formula("",[],-1)
        t = translate.T(pt)
        self.assertEqual(t.sections,{})

    def testTransform(self):
        t = self.translateTransform('''t {
        transform:
        #pixel = 2.0 * #pixel
        }
        ''')

        self.assertNoErrors(t)

        xform = t.sections["transform"].children
        self.assertEqual(1, len(xform))        
        
    def testGradientCF(self):
        t = self.translatecf('''c1 {
        #color = gradient(cmag(#z))
        }''')

        self.assertNoErrors(t)

    def testImageCF(self):
        t = self.translatecf('''cf {
        #color = @image(#z)
        #color = @image(1.0,2.0)
        default:
        image param @image
        endparam
        }''')

        self.assertNoErrors(t)

        # check type of default
        self.assertEqual(0,t.symbols.default_params()[-1])
        
    def testBadImageFunc(self):
        t = self.translate('''cf {
        init:
        float wibble
        x = wibble(3)
        }''')

        self.assertError(t, "4: 'wibble' is not a function")
        
    def testGradientFile(self):
        t = self.translateGradient('''
        blatte10 {
gradient:
  title="blatte10" smooth=no index=0 color=3085069 index=25 color=3216141
  index=56 color=10761236 index=83 color=1408165 index=92 color=4050153
  index=110 color=18018 index=134 color=0 index=213 color=5183243 index=284
  color=11494485 index=358 color=0 index=384 color=144
opacity:
  smooth=no index=0 opacity=255
}
''')

        grad_settings = t.sections["gradient"].children

        self.assertEqual(len(grad_settings), 24)

        title = grad_settings[0]
        self.assertEqual(title.children[0].name,"title")
        self.assertEqual(title.children[1].value, "blatte10")

    def testBarney3(self):
        "A function which used to be problematic"
        t = self.translate('''
Barney-3 {
Init:
 if @mode=="Julia"
 z = 1
 else
 z = 0
 endif
 
Bailout:

 |z|<=@bailout

Default:

 title="Barney-3"
 center=(0.0,0.0)
 angle=90
 magn=0.8
 maxiter=250
 method=multipass
 periodicity=0 
 
heading
 caption="Mandelbrot Mode"
 visible=(@mode==0)
endheading
heading
 caption="Julia Mode"
 visible=(@mode==1)
endheading
param mode
 caption="Current Mode"
 enum="Mandelbrot""Julia"
 default=0
 visible=false
endparam
param SwitchMode
 caption="Select Switch"
 enum="Mandelbrot""Julia"
 default=1
 visible=false
endparam
Func fn2
 caption="Function 1"
 default=cabs()
endfunc
}
''')
        self.assertNoErrors(t)

        fn2 = t.symbols["fn2"].first()

        self.assertEqual(
            fracttypes.Float, fn2.ret,
            "fn2 should automatically be a func which returns a float")

    def testPoly3(self):
        "A function which used to be problematic"
        t = self.translate('''
        Poly3_J {
; iteration of f(z) := alpha*z^3 - 3*alpha*z + beta;
; Z-plane (J-set) fractal
; parameters: alpha, beta

global:
   
init:
  z=#pixel
  
loop:
  z = z * @aa * (z^2 - 3) + @bb;
  
bailout:
; -- this isn\'t the bailout but the continuing condition
;    false = bail; true = continue
  |z| < @bailout
  
default:
  title = "Polynomial of degree 3"
  periodicity = 0
  
  complex param aa
    caption="alpha"
    default=exp( (0,2) * #pi / 3 )
  endparam
  complex param bb
    caption="beta"
    default=0
  endparam
  float param bailout
    caption="Bailout"
    default=1e10
    min=1
  endparam
  
switch:
  type = "Poly3_Ma"
  bb = bb
;  aa = aa
  bailout = bailout
}  
''')
        self.assertError(t, "26: only constants can be used in default sections")

    def testUnknownHashVar(self):
        # check that using an unknown var #foo causes the right kind of error

        t = self.translate(''' x {
        init:
        z = #foo
        }''')

        self.assertError(t, "3: symbol '#foo': only predefined symbols can begin with #")
        
    def testBadDefault(self):
        t = self.translate('''t {
        default:
        func foo
           default = bar()
        endfunc
        }
        ''')

        self.assertError(t, "4: unknown default function 'bar'")

    def testParamUsingBuiltin(self):
        t = self.translate(''' t {
        default:
        complex param twirlcenter
        caption = "Ripple Center"
        default = #center
        endparam
        }''')

        self.assertNoErrors(t)

    def testCF(self):
        t1 = self.translatecf('''c1 {
                            final:
                            #index = #numiter / 256.0
                            }''')

        self.assertTrue(isinstance(
            t1.sections["final"].children[-1],ir.Move))
        
        t2 = self.translatecf('c1 {\n#index = #numiter / 256.0\n}')
        
        self.assertNoErrors(t1)
        self.assertNoErrors(t2)
        self.assertEquivalentTranslations(t1,t2)

        t3 = self.translatecf('''
        c2 {
        init:
        float d = |z|
        loop:
        d = d + |z|
        final:
        #index = log(d+1.0)
        }''')
        self.assertNoErrors(t3)

    def disabled_testOrbitTrace(self):
        t1 = self.translatecf('''
OrbitTrace {
loop:
	#count(#z) = #count(#z) + 1
recolor:
        #index = #count/#maxiter
}
''')

        self.assertNoErrors(t1)
        
    def testMultiplyFunc(self):
        "Make sure we get a sensible error for this typo"
        t = self.translatecf('''
        x {
        float x = @redFunc * 50.0
        default:
        float func redFunc
            default = imag
        endfunc
        }''')
        self.assertError(t,"3: '@redFunc' is a function name")

    def testReallyBigInt(self):
        t = self.translate('''
        t {
        int y = 1000000000000000000
        }''')

        self.assertNoErrors(t)
        
    def testHslProblem(self):
        "Make sure this previously-problematic func works"
        t = self.translatecf('''
hsl {
final:
	float h
	float s
	float l
	h = @hueFunc(z) * 6.0
	s = (@satFunc2(@satFunc(z))+1)/2.0
	l = @lumFunc2(@lumFunc(z))

	#color = hsl(h,s,l)
default:
float func hueFunc
	default = real
endfunc
float func satFunc        
	default = real
endfunc
float func satFunc2
        argtype = float
	default = sin
endfunc
float func lumFunc
	default = imag
endfunc
float func lumFunc2
	default = cos
endfunc
}
''')
        #print t.pretty()
        self.assertNoErrors(t)

    def testDoubleDeclare(self):
        "Declare the same param twice: should be an error"

        src = '''t{
        default:
        float param foo
            default = 3
        endparam
        float param foo
            default = 3
        endparam
        }
        '''
        t = self.translate(src)
        self.assertError(t, "6: parameter 'foo' has already been declared")

    def testDoubleFuncDeclare(self):
        "Declare the same func twice: should be an error"

        src = '''t{
        default:
        float func foo
        endfunc
        complex func foo
        endfunc
        }
        '''
        t = self.translate(src)
        self.assertError(t, "5: function 'foo' has already been declared")

    def testDoubleDeclareFuncAndParam(self):
        "Declare the same func twice: should be an error"

        src = '''t{
        default:
        float func foo
        endfunc
        float param foo
        endparam
        }
        '''
        t = self.translate(src)
        self.assertError(t, "5: function 'foo' has already been declared")

    def testGradientCastProblem(self):
        "Test a problem with gradient casting doesn't recur"
        src = '''t {
        init:
        float d = 0.0
        color current = rgb(0,0,0)
        
        current = gradient(d/@threshold)
        default:
        param threshold
            caption = "Threshold"
            default = 0.25
            min = 0
        endparam
        }'''

        t = self.translatecf(src)
        self.assertNoErrors(t)

    def testLightingOddness(self):
        'Test no problems regress with lighting colorfunc from standard.ucl'
        src = '''Lighting {
final:
  float vz = -sqrt(1-|#z|); extract implied portion of normal
  float d2r = #pi/180; degrees to radians conversion factor

  ; create vector for light direction
  float t2 = cos(@elevation*d2r)
  float lx = cos((270-@angle)*d2r) * cos(@elevation*d2r)
default:
  float param @angle
    caption = "Light Rotation"
    default = 90.0
    hint = "Gives the rotation of the light source, in degrees. With 0 \
            degrees, the light comes from above. Positive values give \
            clockwise rotation."
  endparam
  param @elevation
    caption = "Light Elevation"
    default = 30.0
    hint = "Gives the elevation of the light source, in degrees."
  endparam
  param @ambient
    caption = "Ambient Light"
    default = 0.0
    min = -1.0
    max = 1.0
    hint = "Specifies the level of ambient light.  Use -1.0 to \
            color all surfaces."
  endparam
}'''

        t = self.translatecf(src)
        self.assertNoErrors(t)

    def testTriangleInequality(self):
        t = self.translatecf('''
Triangle {
;
; Variation on the Triangle Inequality Average coloring method 
; from Kerry Mitchell. The smoothing used here is based on the
; Smooth formula, which only works for z^n+c and derivates.
;
; Written by Damien M. Jones
;
init:
  float sum = 0.0
  float sum2 = 0.0
  float ac = cabs(#pixel)
  float il = 1/log(@power)
  float lp = log(log(@bailout)/2.0)
  float az2 = 0.0
  float lowbound = 0.0
  float f = 0.0
  BOOL first = true
loop:
  sum2 = sum
  IF (!first)
    az2 = cabs(#z - #pixel)
    lowbound = abs(az2 - ac)
    sum = sum + ((cabs(#z) - lowbound) / (az2+ac - lowbound))
  ELSE
    first = false
  ENDIF
final:
  sum = sum / (#numiter)
  sum2 = sum2 / (#numiter-1)
  f = il*lp - il*log(log(cabs(#z)))
  #index = sum2 + (sum-sum2) * (f+1)  
default:
  title = "Triangle Inequality Average"
  helpfile = "Uf3.chm"
  helptopic = "Html/coloring/standard/triangleinequalityaverage.html"
  float param power
    caption = "Exponent"
    default = 2.0
    hint = "This should be set to match the exponent of the \
            formula you are using. For Mandelbrot, this is 2."
  endparam
  float param bailout
    caption = "Bailout"
    default = 1e20
    min = 1
    hint = "This should be set to match the bail-out value in \
            the Formula tab. Use a very high value for good results."
  endparam
}
        ''')

        self.assertNoErrors(t)

    def testWhile(self):
        t = self.translate('''
        t {
        loop:
        int i = 10
        int j = 0
        while i > 0
           i = i - 1
           j = j + 1
        endwhile
        }''')

        self.assertNoErrors(t)

        self.assertJumpsMatchLabs(t.sections["loop"])
        
        expectedLabs = [
            'L:flabel0',
            'CJ:flabel1,flabel2',
            'L:flabel1',
            'J:flabel0',
            'L:flabel2']

        self.assertJumpsAndLabs(t, expectedLabs)

    def testRandom(self):
        t = self.translate('''
        t {
        init:
        x1 = rand
        x2 = #random
        x3 = #rand        
        }
        ''')

        self.assertNoErrors(t)
        
    def testBadEnum(self):
        t = self.translate('''
        t1 {
        init:
        if @y == "xxx"
           x = 1
        endif          
        default:
        param y
        enum = "foo" "bar"
        endparam
        }
        ''')

        self.assertError(t, "4: Unknown enumeration value 'xxx'")

    def testBadEnum2(self):
        t = self.translate('''
        t1 {
        default:
        param y
        enum = "foo" "bar"
        default = "xxx"
        endparam
        }
        ''')

        self.assertError(t, "6: Unknown enumeration value 'xxx'")

    def testColorParam(self):
        t = self.translate('''
        t {
        default:
        color param x
            default = rgb(0,0,1)
        endparam
        color param x2
            default = rgba(1,1,1,1)
        endparam
        }
        ''')

        self.assertNoErrors(t)
                           
    def testImplicitParamTypes(self):
        # Some UF coloring algorithms cause problems. The
        # type of the param is implicitly set based on the default value
        t = self.translatecf('''
Triangle {
init:
  float sum = 0.0
  float sum2 = 0.0
  float ac = cabs(#pixel)
  float il = 1/log(@power)
  float lp = log(log(@bailout)/2.0)
  float az2 = 0.0
  float lowbound = 0.0
  float f = 0.0
  BOOL first = true
default:
  param power
    caption = "Exponent"
    default = 2.0
    hint = "This should be set to match the exponent of the \
            formula you are using. For Mandelbrot, this is 2."
  endparam
  param bailout
    caption = "Bailout"
    default = 1e20
    min = 1
  endparam
  param implicit_nodefault
  endparam
  param implicit_bool
    default = true
  endparam
  param implicit_int
    default = 7
  endparam
  param complex_of_ints
    default = (2,0)
  endparam
}
        ''')

        self.assertNoErrors(t)

        self.assertEqual(t.symbols["@power"].type, fracttypes.Float)
        self.assertEqual(t.symbols["@bailout"].type, fracttypes.Float)
        self.assertEqual(t.symbols["@implicit_nodefault"].type,
                         fracttypes.Complex)
        self.assertEqual(t.symbols["@implicit_bool"].type, fracttypes.Bool)
        self.assertEqual(t.symbols["@implicit_int"].type, fracttypes.Int)
        self.assertEqual(t.symbols["@complex_of_ints"].type, fracttypes.Complex)

        defval_re = t.symbols["@complex_of_ints"].default.value[0].value
        
        self.assertTrue(isinstance(defval_re,float))
        
    def testFractintSections(self):
        t1 = self.translate("t1 {\na=1,a=2:\nb=2\nc=3}")
        t2 = self.translate('''
             t2 {
                 init: 
                 a=1
                 a=2
                 loop:
                 b=2
                 bailout:
                 c=3
                 }''')
        
        self.assertEquivalentTranslations(t1,t2)
        self.assertNoErrors(t1)
        self.assertNoErrors(t2)

        t3 = self.translate('''
             t3 {
                 a=1:b=2,c=3
                 init:
                 a=1,a=2
                 loop:
                 b=2
                 bailout:
                 c=3
                 }''')
        self.assertEquivalentTranslations(t1,t3)
        self.assertEqual(len(t3.warnings),8,t3.warnings)

        t4 = self.translate('t_c3{\n:init: a = 1 + 3 * 7\n}')
        self.assertNoErrors(t4)

    def testIs4D(self):
        'Check convenience function to report if formula is 4D-enabled'
        t1 = self.translate('''
        no_zw {
        init:
        z = #zwpixel
        loop:
        z = sqr(z) + #pixel
        bailout:
        |z| < 4
        }''')

        self.assertEqual(t1.is4D(), True)

        t2 = self.translate('''
        no_zw {
        init:
        z = 0
        loop:
        z = sqr(z) + #pixel
        bailout:
        |z| < 4
        }''')

        self.assertEqual(t2.is4D(), False)

    def testImplicitConversionToComplex(self):
        t_icc = self.translate('''t11 {
        init: x = exp(1.0,0.0)
        }''')
        t_icc2 = self.translate('''t11 {
        init: x = exp((1.0,0.0))
        }''')
        self.assertNoErrors(t_icc)
        self.assertNoErrors(t_icc2)
        self.assertEquivalentTranslations(t_icc,t_icc2)
        
    def testBailout(self):
        # empty bailout
        t = self.translate('''t_bail_1 {
        bailout:
        }''')

        self.assertWarning(t, "No bailout expression found" )
        self.assertEqual(True, "__bailout" in t.symbols)
        self.assertNoErrors(t)

        # uncastable bailout
        t = self.translate('''t_bail_2 {
        bailout:
        if 1 > 2
        endif
        }''')

        self.assertError(t, "invalid type none")

        # a var
        t = self.translate('''t_bail_3 {        
        bailout:
        x
        }''')

        move = t.sections["bailout"].children[-1]
        self.assertTrue(isinstance(move, ir.Move))
        self.assertEqual(move.children[0].name, "__bailout")

        # a complex expression
        t = self.translate('''t_bail_4 {        
        bailout:
        (x && y) || (y && x)
        }''')

        move = t.sections["bailout"].children[-1]
        self.assertTrue(isinstance(move, ir.Move))
        self.assertEqual(move.children[0].name, "__bailout")

        
    def testGradientFunc(self):
        t = self.translate('''t {
        init:
        #color = gradient(1.0)
        default:
        }''')
        self.assertNoProbs(t)
        
    def testAssign(self):
        # correct declarations
        t9 = self.translate('''t9 {
        init:
        int i
        float f
        complex c
        hyper h
        color col
        loop:
        i = 1
        f = 1.0
        c = (2.1, 2.3)
        h = (1.0,2.0,3.0,4.0)
        col = rgb(0.0,0.0,0.0)
        }''')
        self.assertNoProbs(t9)

        # basic warnings and errors
        t10 = self.translate('''t10 {
        init: int i, float f, complex c
        loop:
        f = 1 ; upcast - warning
        i = 1.0 ; downcast - error
        }''')
        self.assertWarning(t10,"4: Warning: conversion from int to float")
        self.assertError(t10, "5: invalid type float for 1.0, expecting int")

        # basic warnings and errors
        t11 = self.translate('''t11 {
        init: complex c, hyper h
        loop:
        h = c ; upcast - warning
        c = h ; downcast - error
        }''')
        self.assertWarning(t11,"4: Warning: conversion from complex to hyper")
        self.assertError(
            t11,
            "5: invalid type hyper for h, expecting complex")

    def testBadTypeForParam(self):
        t = self.translate('''t_badparam {
        default:
        complex param foo
            default = "fish"
        endparam
        }''')
        self.assertError(t, "4: Unknown enumeration value 'fish'")

    def testParamTypeConversion(self):
        t = self.translate('''t_badparam {
        default:
        complex param foo
            default = (1.0,2.0)
        endparam
        }''')

        self.assertNoErrors(t)
        foo = t.symbols["@foo"]
        self.assertEqual(foo.default.value[0].value,1.0)
        self.assertEqual(foo.default.value[1].value,2.0)

    def testSectionClashWarnings(self):
        t = self.translate('''t_sections {
        x = 1 : x = x + 1, x < 10
        init:
        x= 2
        loop:
        x = x + 2
        bailout:
        x < 8
        default:
        }''')

        self.assertNoErrors(t)
        self.assertWarning(t, "implicit bailout section")
        self.assertWarning(t, "implicit init section")
        self.assertWarning(t, "implicit loop section")

        t2 = self.translate('''t_sections {
        ; this comment shouldnt cause alarm 
        init:
        int x= 2
        loop:
        x = x + 2
        bailout:
        x < 8
        }''')
        self.assertNoProbs(t2)

    def testMixedCaseDefaultBool(self):
        t = self.translate('''t {
        default:
        bool param x
            default = True
        endparam        
        }''')

        self.assertNoErrors(t)
        self.assertEqual(True, t.symbols["@x"].default.value)

    def testLowerCaseDefaultBool(self):
        t = self.translate('''t {
        default:
        bool param x
            default = true
        endparam        
        }''')

        self.assertNoErrors(t)
        self.assertEqual(True, t.symbols["@x"].default.value)
        
    def disable_testMixedImplicitAndNamedParams(self):
        t = self.translate('''t_mix {
        init:
        x = @p1 + @myparam1 + @myparam2
        default:
        param myparam2
        default = (1.0,2.0)
        endparam
        }''')

        print(t.symbols.parameters(True))
        print(t.symbols.default_params())
        
    def testFuncWithCaption(self):
        t = self.translate('''t {
        default:
        func foo
           caption = "fishwich"
        endfunc
        }''')

        self.assertNoErrors(t)
        self.assertEqual("fishwich", t.symbols["@foo"].first().caption.value)
        self.assertEqual(
            "Transfer Function", t.symbols["@_transfer"].first().caption.value)

    def testDefaultSection(self):
        t = self.translate('''t_d1 {
        default:
        maxiter = 100
        xyangle = 4.9
        center = (8.1,-2.0)
        title = "Hello World"
        point_mode = "random"
        complex param foo
            caption = "Angle"
            default = 10.0
        endparam
        complex param with_Turnaround8
            caption = "Turnaround 8?"
            default = true
            hint = ""
        endparam
        float param f1
            default = 1.2
        endparam
        hyper param h1
            default = (4,5,6,7)
        endparam
        }''')
        self.assertNoErrors(t)

        defsection = t.sections["default"]
        # first item should be a move from 10.0 to @foo
        firstchild = defsection.children[0]
        self.assertEqual("@foo", firstchild.children[0].name)
        self.assertEqual(10.0, firstchild.children[1].children[0].value)

        self.assertEqual(t.defaults["maxiter"].value,100)
        self.assertEqual(t.defaults["xyangle"].value,4.9)
        self.assertEqual(t.defaults["center"].value[0].value,8.1)
        self.assertEqual(t.defaults["center"].value[1].value,-2.0)
        self.assertEqual(t.defaults["title"].value,"Hello World")
        self.assertEqual("random", t.defaults["point_mode"].value)
        
        k = list(t.symbols.parameters().keys())
        k.sort()
        exp_k = [
            "t__a__gradient",
            "t__a_f1",
            "t__a_foo",
            "t__a_with_turnaround8",
            "t__a_h1"]
        
        exp_k.sort()
        self.assertEqual(k,exp_k)        

        foo = t.symbols["@foo"]
        self.assertEqual(foo.caption.value, "Angle")
        self.assertEqual(foo.default.value[0].value, 10.0)
        self.assertEqual(foo.default.value[1].value, 0.0)

        t8 = t.symbols["@with_turnaround8"]
        self.assertEqual(t8.hint.value,"")

        f1 = t.symbols["@f1"]
        self.assertEqual(f1.type,fracttypes.Float)

        params = t.symbols.parameters(True)
        op = t.symbols.order_of_params()
        
        self.assertEqual(0, op["t__a__gradient"])
        self.assertEqual(1, op["t__a_foo"])
        self.assertEqual(3, op["t__a_with_turnaround8"])
        self.assertEqual(5, op["t__a_f1"])
        self.assertEqual(6, op["t__a_h1"])
        self.assertEqual(10, op["__SIZE__"])

        defparams = t.symbols.default_params()
        self.assertEqual(defparams,[
            0.0, # gradient
            10.0,0.0, #foo
            1.0,0.0, # turnaround
            1.2, #f1
            4.0,5.0,6.0,7.0, #h1
            ])

        
    def testEnum(self):
        t = self.translate('''t_enum {
        default:
        param calculate
        caption = "Calculate"
        enum    = "Sum" "Abs" "Diff"
        default = 1
        endparam
        init:
        if @calculate == 1
        x = 1
        else
        x = 7
        endif
        }''')

        self.assertNoErrors(t)

        calculate = t.symbols["@calculate"]
        e = calculate.enum
        self.assertEqual(e.value, ["Sum", "Abs", "Diff"])
        self.assertEqual(calculate.type,fracttypes.Int)

    def testEnums(self):
        t = self.translate('''
        t1 {
        init:
        if @y == "fOo"
           x = 1
        elseif @y == "bar"
           x = 2
        endif
        bool b = @y == "bar"
        default:
        param y
        enum = "Foo" "bar"
        default = "bar"
        endparam
        }
        ''')

        self.assertEqual(t.symbols.get("__enum_foo").value,0)
        self.assertEqual(t.symbols.get("__enum_bar").value,1)
        self.assertNoErrors(t)


    def testDefaultWithEnum(self):
        t = self.translate('''t_se {
        init:
        x = 1 + "hello"
        default:
        param @wibble
        enum = "hello"
        endparam
        }''')
        
        self.assertNoErrors(t)
        
    def testParams(self):
        t12 = self.translate('''t_params {
        init: complex x = @p1 + p2 + @my_param
        complex y = @fn1((1,0)) + fn2((2,0)) + @my_func((1,0))
        }''')
        self.assertNoErrors(t12)
        k = list(t12.symbols.parameters().keys())
        k.sort()
        exp_k = ["t__a__gradient",
                 "t__a_p1", "t__a_p2", "t__a_my_param",
                 "t__a_fn1", "t__a_fn2", "t__a_my_func"]
        exp_k.sort()
        self.assertEqual(k,exp_k)

        var_k = ["t__a__gradient",
                 "t__a_p1", "t__a_p2", "t__a_my_param"]
        var_k.sort()
        var_k.append("__SIZE__")

        exp_ord = {
            "t__a__gradient" : 0,
            "t__a_p1": 1,
            "t__a_p2": 3,
            "t__a_my_param": 5,
            "__SIZE__": 7
            }
        
        op = t12.symbols.order_of_params()

        for (key,ord) in list(op.items()):
            self.assertEqual(op[key],exp_ord[key])


    def testCFParams(self):
        t = self.translatecf('''t {
        final:
        #index = |#z|
        }''')

        offset = t.symbols["@_offset"]
        self.assertEqual(0.0, offset.min.value)
        self.assertEqual(1.0, offset.max.value)
        self.assertEqual("Color Offset", offset.caption.value)

        density = t.symbols["@_density"]
        self.assertEqual(1.0, density.default.value)
        self.assertEqual("Color Density", density.caption.value)

        gradient = t.symbols["@_gradient"]

    def testFuncParam(self):
        t =self.translate('''test_func {
        loop:
        z = @myfunc(z) + #pixel
        bailout:
        |z| < @bailout
        default:
        float param bailout
	    default = 4.0
        endparam
        func myfunc
	    default = sqr()
            caption = "hello there"
        endfunc
        func myotherfunc
            default = sqr
            hint = "not used"
        endfunc
        color func mycolorfunc
            default = mergenormal()
        endfunc
        color func mycolorfunc2
        endfunc
        }
        ''')
        self.assertNoErrors(t)

        self.assertEqual(t.symbols["@myfunc"][0].genFunc,stdlib.sqr_c_c)
        self.assertEqual(t.symbols["@myotherfunc"][0].genFunc,stdlib.sqr_c_c)
        self.assertEqual(t.symbols["@mycolorfunc2"][0].genFunc, stdlib.mergenormal_CC_C)
        
    def testBadFunc(self):
        t = self.translate('t_badfunc {\nx= badfunc(0):\n}')
        self.assertError(t,"Unknown function badfunc on line 2")
        
    def testIDs(self):
        t11 = self.translate('''t11 {
        init: int a = 1, int b = 2
        loop: a = b
        }''')
        self.assertNoProbs(t11)

        t12 = self.translate('t12 {\ninit: a = b}')
        self.assertWarning(t12, "Uninitialized variable b referenced on line 2")

    def testBinops(self):
        # simple ops with no coercions
        t13 = self.translate('''t13 {
        loop:
        complex a, complex b, complex c
        int ia, int ib, int ic
        a = b + c
        ia = ib + ic
        }''')
        
        #print t13.sections["loop"].pretty()
        self.assertNoProbs(t13)
        result = t13.sections["loop"]
        self.assertTrue(isinstance(result.children[-1],ir.Move))
        # some coercions
        t = self.translate('''t_binop_2 {
        loop:
        complex a, complex b, complex c
        int ia, int ib, int ic
        float fa, float fb, float fc
        a = fa + ia
        fb = ib / ic
        }''')
        self.assertNoErrors(t)
        (plus,div) = t.sections["loop"].children[-2:]

        self.assertEqual(div.children[1].datatype, fracttypes.Float)
        self.assertEqual(div.children[1].children[0].children[0].datatype,
                         fracttypes.Int)

        self.assertFuncOnList(lambda x,y : x.__class__.__name__ == y,
                              [x for x in plus],
                              ["Move","Var","Cast","Binop","Var","Cast","Var"])


    def testIf(self):
        t = self.translate('''t_if_1 {
        loop:
        if a > b
        a = 2
        else
        a = 3
        endif
        }''')

        self.assertNoErrors(t)
        ifseq = t.sections["loop"].children[0]

        self.assertTrue(ifseq.children[0].op == ">" and \
                        ifseq.children[0].trueDest == "flabel0" and \
                        ifseq.children[0].falseDest == "flabel1")

        self.assertTrue(ifseq.children[1].children[0].name == "flabel0" and \
                        ifseq.children[1].children[-1].dest == "flabel2" and \
                        ifseq.children[2].children[0].name == "flabel1" and \
                        ifseq.children[3].name == "flabel2")

        t = self.translate('''t_if_2 {
        loop:
        if a
        a = 2
        endif
        }''')

        self.assertNoErrors(t)
        ifseq = t.sections["loop"].children[0]
        self.assertTrue(ifseq.children[0].op == "!=")
        
        self.assertTrue(ifseq.children[1].children[0].name == "flabel0" and \
                        ifseq.children[1].children[-1].dest == "flabel2" and \
                        ifseq.children[2].children[0].name == "flabel1" and \
                        ifseq.children[3].name == "flabel2")

        self.assertTrue(len(ifseq.children[2].children)==1)

        expectedLabs = [
            'CJ:flabel0,flabel1',
            'L:flabel0',
            'J:flabel2',
            'L:flabel1',
            'CJ:flabel3,flabel4',
            'L:flabel3',
            'J:flabel5',
            'L:flabel4',
            'L:flabel5',
            'L:flabel2']

        t = self.translate('''t_if_3 {
        loop:
        if a == 1
           a = 2
        elseif a == 2
           a = 3
        else
           a = 4
        endif
        }''')

        self.assertNoErrors(t)
        self.assertJumpsMatchLabs(t.sections["loop"])
        self.assertJumpsAndLabs(t, expectedLabs)

        t = self.translate('''t_if_4 {
        loop:
        if a == 1
        else
           if a == 2
              a = 4
           endif
        endif
        }''')

        self.assertNoErrors(t)
        self.assertJumpsMatchLabs(t.sections["loop"])
        self.assertJumpsAndLabs(t, expectedLabs)

    def testBooleans(self):
        t = self.translate('''t_bool_0 {
        init:
        a == 1 && b == 2
        }''')
        self.assertNoErrors(t)
        self.assertJumpsMatchLabs(t.sections["init"])

        t = self.translate('''t_bool_1 {
        init:
        a == 1 || b == 2
        }''')
        self.assertNoErrors(t)
        self.assertJumpsMatchLabs(t.sections["init"])
        
        t = self.translate('''t_bool_2 {
        init:
        if a == 1 && b == 2
           a = 2
        endif
        }''')
        self.assertNoErrors(t)
        self.assertJumpsMatchLabs(t.sections["init"])

        t = self.translate('''t_bool_3 {
        init:
        if a == 1 || b == 2
           a = 2
        endif
        }''')
        self.assertNoErrors(t)
        self.assertJumpsMatchLabs(t.sections["init"])

        t = self.translate('''t_bool_4 {
        init:
        bool a, bool b
        c = (real(a||b),imag(a&&b))
        float f = |a&&b|
        }''')
        self.assertNoErrors(t)
        
    def testMandel(self):
        t = self.translate('''t_mandel_1 {
        loop:
        z = z * z + c
        bailout:
        |z| < 4.0
        }''')

        self.assertNoErrors(t)

        t = self.translate('''t_mandel_2 {
        : z = z * z + c, |z| < 4.0
        }''')

        self.assertNoErrors(t)

    def testMandelPickle(self):
        t = self.translate('''t_mandel_1 {
        loop:
        z = z * z + c
        bailout:
        |z| < 4.0
        }''')

        self.assertNoErrors(t)
        pickle.dumps(t.canonicalizer.symbols,True)
        
    def testHyperOps(self):
        t = self.translate('''t_c8{
        init:
        hyper x = (1,2,3,4), hyper y = x + 1
        }''')

        self.assertNoErrors(t)
        
    def testDecls(self):
        t1 = self.translate(
            "t4 {\nglobal:int a\ncomplex b\nbool c = true\nhyper h\n}")
        self.assertNoProbs(t1)
        self.assertVar(t1, "a", fracttypes.Int)
        self.assertVar(t1, "b", fracttypes.Complex)
        self.assertVar(t1, "h", fracttypes.Hyper)
        
        t1 = self.translate('''
        t5 {
        init:
        float a = true,complex c = 1.0
        complex x = 2
        }''')
        self.assertNoErrors(t1)
        self.assertVar(t1, "a", fracttypes.Float)
        self.assertVar(t1, "c", fracttypes.Complex)
        self.assertVar(t1, "x", fracttypes.Complex)
        self.assertWarning(t1, "4: Warning: conversion from bool to float")
        self.assertWarning(t1, "4: Warning: conversion from float to complex")
        self.assertWarning(t1, "5: Warning: conversion from int to complex")

    def testMultiDecls(self):
        t1 = self.translate("t6 {\ninit:int a = int b = 2}")
        self.assertVar(t1, "a", fracttypes.Int)
        self.assertVar(t1, "b", fracttypes.Int)
        self.assertNoErrors(t1)

    def testRedeclare(self):
        'For better uf-compat, allow redeclaring vars -ick'
        t1 = self.translate('''
        t {
        init:
        complex z = (3,1)
        int x = 2
        int x = 3
        }
        ''')
        self.assertNoErrors(t1)

    def testBadDecls(self):
        t1 = self.translate("t7 {\nglobal:int z\n}")
        self.assertError(t1,"symbol 'z' is predefined as complex")
        t1 = self.translate("t8 {\nglobal:int a\nfloat A\n}")
        self.assertError(t1,"'A' was already defined as int on line 2")
        t1 = self.translate("t8 {\nglobal:int sin\n}")
        self.assertError(t1,"symbol 'sin' is predefined as a function")

    def testMultiAssign(self):
        t = self.translate("t_ma {\ninit:z = c = 1.0\n}")
        self.assertNoErrors(t)

    def testAssignToFunc(self):
        t = self.translate("t_a2f {\ninit:real(z) = 2.0, imag(z)=1.5\n}")
        self.assertNoErrors(t)

    def testBjax(self):
        t = self.translate('''Bjax {;
  z=c=2/pixel:
   z =(1/((z^(real(p1)))*(c^(real(p2))))*c) + c
  }
''')
        self.assertNoErrors(t)
        self.assertWarning(t,"No bailout condition specified")

    def testComplexBool(self):
        t = self.translate('''t_cb{
            float x=real(z), float y=imag(z)
            bool chrH1 = x<-0.16646 || x>-0.13646; 
            }''')
        
        self.assertNoErrors(t)

    def testVisible(self):
        t = self.translate('''t {
            default:
            param foo
                default = 2.0
                visible = bar == 2.0 && 1.7 == "hello"
            endparam
            func normfunc
                caption=" Function"
                default=ident()
                hint = "Normalization function."
                visible = @norm == "f(z)"
            endfunc
            }''')

        self.assertNoErrors(t)

    def testArray(self):
        t = self.translate('''t {
        init:
        int x[2]
        float f[700]
        complex carray[88]
        }''')

        self.assertNoErrors(t)

        self.checkArrayProperties(t,"x",fracttypes.IntArray, 4, 2, 0)
        self.checkArrayProperties(t,"f",fracttypes.FloatArray, 8, 700, 1)
        self.checkArrayProperties(
            t,"carray",fracttypes.ComplexArray, 8, 88*2, 2)
        
    def checkArrayProperties(self,t,sym,type, esize, size, pos):
        x = t.symbols[sym]
        self.assertEqual(type, x.type)
        self.assertEqual(0,x.value)

        decl = t.sections["init"].children[pos]
        self.assertEqual(ir.Move, decl.__class__)

        element_size = decl.children[1].children[0].children[1]
        self.assertEqual(esize, element_size.value)
        amount_to_alloc = decl.children[1].children[0].children[2]
        if hasattr(amount_to_alloc,"value"):
            self.assertEqual(size,amount_to_alloc.value)            

    def test2DArray(self):
        t = self.translate('''t {
        init:
        int x[2,7]
        }''')

        self.assertNoErrors(t)

        x = t.symbols["x"]
        self.assertEqual(fracttypes.IntArray, x.type)
        self.assertEqual(0,x.value)

        decl = t.sections["init"].children[0]
        self.assertEqual(ir.Move, decl.__class__)

        args = decl.children[1].children[0].children
        self.assertEqual("t__p_stub->arena",args[0].name)        
        self.assertEqual(
            [4, 2,7], # element size, indexes
            [child.value for child in args[1:]])

    def disabled_test3Dand4DArrays(self):
        t = self.translate('''t {
        init:
        float x[2,7,3]
        complex smee[1,2,3,4]
        }''')

        self.assertNoErrors(t)
        
    def testArrayBadIndexType(self):
        t = self.translate('''t {
        init:
        int wibble[2.5]
        }''')

        self.assertError(
            t, "3: invalid type float for 2.5, expecting int")

    def testBadArrayType(self):
        t = self.translate('''t {
        init:
        image wibble[5]
        }''')

        self.assertError(
            t, "3: Arrays of type image are not supported")

    def testTooManyIndexes(self):
        t = self.translate('''t {
        init:
        int wibble[1,2,3]
        }''')

        self.assertError(
            t, "3: Arrays can only have up to 2 indexes")

    def testNotEnoughIndexes(self):
        t = self.translate('''t {
        init:
        int wibble[]
        }''')

        self.assertError(
            t, "3: Syntax error: unexpected rarray ']'")

    def testArrayLookup(self):
        t = self.translate('''t {
        init:
        int x[2]
        x[1] = 4
        int n = x[1]
        }''')

        self.assertNoErrors(t)

        # check array write
        target = t.sections["init"].children[1]
        self.assertEqual(ir.Call, target.__class__)
        self.assertEqual("_write_lookup", target.op)
        
        var= target.children[0]
        self.assertEqual(ir.Var, var.__class__)
        self.assertEqual("x", var.name)
        
        index = target.children[1]
        self.assertEqual(ir.Const, index.__class__)
        self.assertEqual(1, index.value) 

        val = target.children[2]
        self.assertEqual(ir.Const, val.__class__)
        self.assertEqual(4, val.value) 

        # check array read
        dereference = t.sections["init"].children[2].children[1]
        self.assertEqual(ir.Call, dereference.__class__)
        self.assertEqual("_read_lookup", dereference.op)
        
        var= dereference.children[0]
        self.assertEqual(ir.Var, var.__class__)
        self.assertEqual("x", var.name)
        
        index = dereference.children[1]
        self.assertEqual(ir.Const, index.__class__)
        self.assertEqual(1, index.value)

    def disabled_testMoreComplexArrays(self):
        t = self.translate('''t {
        init:
        float x[2,4,8,16]
        x[1,round(2.5),3*1*1-0,4] = 4
        }''')

        self.assertNoErrors(t)
        
    def testArrayTypeMismatch(self):
        t = self.translate('''t {
        init:
        int i[3]
        float f[2]
        f[0] = #z
        i[1] = f[2]
        }''')

        self.assertError(t, "5: invalid type complex for #z, expecting float")

    def testWrongIndexes(self):
        t = self.translate('''t {
        init:
        float f[1,2]
        f[0] = 1
        }''')

        self.assertError(t, "4: wrong number of indexes for f")

    def testLookupOnNonArray(self):
        t = self.translate('''t {
        init:
        int f
        int g
        f[0] = 1
        }''')

        self.assertError(t, "5: f is not an array")

        t = self.translate('''t {
        init:
        int f
        int g
        g = f[0]
        }''')
        
        self.assertError(t, "5: f is not an array")

    def testDeclArrayWithoutType(self):
        t = self.translate('''t {
        init:
        a2[7]
        }''')

        self.assertError(t, "3: a2 not declared as an array")

    def testComplexArray(self):
        t = self.translate('''t {
        init:
        complex a1[3,7]
        complex a2[7]
        a2[0] = (1.8,3.0)
        a1[1,1] = #z
        }''')

        self.assertNoErrors(t)

    def testMinMaxParamProperties(self):
        t = self.translate('''t {
        default:
        float param bailout
          caption="Bailout"
          default=1e10
          min=1
          max=1e20
        endparam
        }''')

        self.assertNoErrors(t)

        bailout = t.symbols["@bailout"]
        self.assertEqual(bailout.min.value, 1.0)
        self.assertEqual(bailout.max.value, 1.0e20)

    def testDubiousProperties(self):
        t = self.translate('''t {
        default:
        float param bailout
          value = 20
          caption="Bailout"
          default=1e10
          min=1
          max=1e20
        endparam
        }''')
        
        self.assertWarning(t, "4: Unrecognized parameter setting 'value' ignored")
        bailout = t.symbols["@bailout"]
        self.assertFalse(hasattr(bailout.value, "value"))

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

