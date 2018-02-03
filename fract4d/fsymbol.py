#!/usr/bin/env python3

# Trivial symbol table implementation

import copy
from collections import UserDict
from collections import UserList
import string
import types
import re
import math
import copy
import inspect

from .fracttypes import *
from . import ir
from . import stdlib

class OverloadList(UserList):
    def __init__(self,list,**kwds):
        UserList.__init__(self,list)
        self.pos = -1
        self._is_operator = kwds.get("operator")
        self.__doc__ = kwds.get("doc")
        self.declared = False
        
    def __copy__(self):
        copied_data = [ copy.copy(x) for x in self.data]
        c = OverloadList(copied_data)
        c.pos = self.pos
        c._is_operator = self._is_operator
        c.__doc__ = self.__doc__
        return c
    
    def first(self):
        return self[0]

    def is_operator(self):
        return self._is_operator

def efl(fname, template, tlist,**kwds):
    'short-hand for expandFuncList - just reduces the amount of finger-typing'
    list = []
    for t in tlist:            
        f = "Func(%s,\"%s\")" % (re.sub("_", str(t), template), fname)
        realf = eval(f)
        list.append(eval(f))
    return OverloadList(list,**kwds)

def cfl(template, tlist):
    list = []
    for t in tlist:            
        f = re.sub("_", str(t), template)
        realf = eval(f)
        list.append(eval(f))
    return list

def mkf(args, ret, fname):
    # create a function
    return Func(args,ret,fname)

def mkfl(dict, name, lst, **kwds):
    "make a list of functions"
    fname = kwds.get("fname",name) # fname overrides name if present
    # avoid having to provide list of one element
    if not isinstance(lst[0][0],list):
        lst = [lst]
    funclist = [mkf(x[0],x[1],fname) for x in lst]

    implicit = kwds.get("implicit",None)
    if implicit:
        for f in funclist:
            f.set_implicit_arg(implicit)
            
    dict[name] = OverloadList(funclist,**kwds)
        
class Alias:
    def __init__(self,realName):
        self.realName = realName
        self.pos = -1
        self.cname = None

    
def createDefaultDict():
    d = {
        "^": OverloadList([Func([Float, Float], Float, "pow"),
                           Func([Complex, Float], Complex, "pow"),
                           Func([Complex, Complex], Complex, "pow")],
                          operator=True,
                          doc='''Exponentiation operator. Computes x to the power y.'''),
        
        "t__neg": efl("neg", "[_], _", [Int, Float, Complex, Hyper]),

        # logical ops
        "&&": OverloadList(
            [ Func([Bool, Bool], Bool, None) ],
            doc="Logical AND.", operator=True),
        "||": OverloadList(
            [ Func([Bool, Bool], Bool, None) ],
            doc="Logical OR.", operator=True),
        "t__not" : OverloadList(
            [ Func([Bool],Bool, "not") ],
            doc="Logical NOT.", operator=True),

        # predefined magic variables
        "t__h_pi" : Alias("pi"),
        "t__h_rand" : Alias("rand"),
        "t__h_random" : Alias("rand"),
        "t__h_magn" : Var(Float,doc="The magnification factor of the image. This is the number of times the image size has doubled, or ln(4.0/size)"),
        "t__h_center" : Var(Complex,doc="Where the center of the image is located on the complex plane"),
        "rand" : OverloadList(
          [ Func([], Complex, "rand") ],
          doc="Each time this is accessed, it returns a new pseudo-random complex number. This is primarily for backwards compatibility with Fractint formulas - use the random() function in new formulas."),
        
        "t__h_pixel": Alias("pixel"),
        "t__h_xypixel": Alias("pixel"),
        "pixel" : Var(Complex,doc="The (X,Y) coordinates of the current point. When viewing the Mandelbrot set, this has a different value for each pixel. When viewing the Julia set, it remains constant for each pixel."),
        "pi": Var(Float),
        "t__h_z" : Alias("z"),
        "z"  : Var(Complex),
        "t__h_index": Var(Float,doc="The point in the gradient to use for the color of this point."),
        "t__h_numiter": Var(Int,doc="The number of iterations performed."),
        "t__h_maxiter": Alias("maxiter"),
        "t__h_maxit" : Alias("maxiter"),
        "maxit" : Alias("maxiter"),
        "maxiter" : Var(Int, "The maximum number of iterations set by the user."),
        "pi" : Var(Float,math.pi, doc="The constant pi, 3.14159..."),
        "t__h_tolerance" : Var(Float, doc="10% of the distance between adjacent pixels."),
        "t__h_zwpixel" : Var(Complex,doc="The (Z,W) coordinates of the current point. (See #pixel for the other two coordinates.) When viewing the Mandelbrot set, this remains constant for each pixel on the screen; when viewing the Julia set, it's different for each pixel. Initialize z to some function of this to take advantage of 4D drawing."),
        "t__h_solid" : Var(Bool,doc="Set this to true in a coloring function to use the solid color rather than the color map."),
        "t__h_color" : Var(Color,doc="Set this from a coloring function to directly set the color instead of using a gradient"),
        "t__h_fate" : Var(Int,doc="The fate of a point can be used to distinguish between different basins of attraction or whatever you like. Set this to a number from 2 to 128 to indicate that a different 'fate' has befallen this point. 0 indicates the point has diverged, 1 that it has been trapped, >1 whatever you like. Can only be usefully updated in the #final section."),
        "t__h_inside" : Var(Bool,doc="Set this in the final section of a formula to override whether a point is colored with the inside or outside coloring algorithm. This is mainly useful in conjuction with #fate.")
        }

    # extra shorthand to make things as short as possible
    def f(name, list, **kwds):
        mkfl(d,name,list,**kwds)

    # standard functions
    f("bool",
      [[Bool], Bool],
      doc="""Construct a boolean. It's not really required (bool x = bool(true) is just the same as bool x = true) but is included for consistency.""")

    f("int",
      [[Int], Int],
      doc="""Construct an integer. To convert a float to an int, use floor, ceil, round or trunc instead.""")

    f("float",
      [[Float], Float],
      doc="""Construct a floating-point number.""")

    f("color",
     [[Float, Float, Float, Float], Color],
     doc="""Constructs a new color from floating point red, green, blue and alpha
     components. Equivalent to rgba.""")
    
    f("complex",
      [[Float, Float], Complex],
      doc='''Construct a complex number from two real parts.
      complex(a,b) is equivalent to (a,b).''')

    f("hyper",
      [[[Float, Float, Float, Float], Hyper], [[Complex, Complex], Hyper]],
      doc='''Construct a hypercomplex number with a real and 3 imaginary parts.
      Can be passed either 2 complex numbers or 4 floating-point numbers.
      hyper(a,b,c,d) is equivalent to the shorthand (a,b,c,d).''')

    f("sqr",
      cfl("[_] , _",  [Int, Float, Complex, Hyper]),
      doc="Square the argument. sqr(x) is equivalent to x*x or x^2.")

    #f("cube",
    #  cfl("[_] , _", [Int, Float, Complex]),
    #  doc="Cube the argument. cube(x) is equivalent to x*x*x or x^3.")
    
    f("ident",
      cfl("[_] , _",  [Int, Float, Complex, Bool, Hyper]),
      doc='''Do nothing. ident(x) is equivalent to x.
      This function is useless in normal formulas but
      comes in useful as a value for a function parameter
      to a formula. For example, a general formula like z = @fn1(z*z)+c
      can be set back to a plain Mandelbrot by setting fn1 to ident.
      Note: ident() is compiled out so there\'s no speed penalty involved.''')
    
    f("conj",
      cfl("[_] , _",  [Complex, Hyper]),
      doc="The complex conjugate. conj(a,b) is equivalent to (a,-b).")

    f("flip",
      cfl("[_] , _",  [Complex, Hyper]),
      doc='''Swap the real and imaginary parts of a complex number.
      flip(a,b) = (b,a).''')

    f("real",
      [[[Complex], Float], [[Hyper], Float]],
      doc='''Extract the real part of a complex or hypercomplex number.
      real(a,b) = a.
      real() is unusual in that it can be assigned to: real(z) = 7 changes
      the real part of z.''')

    f("real2",
      [[Complex], Float],
      doc='''The square of the real part of a complex number.
      real2(a,b) = a*a.
      While not a generally useful function, this is provided to ease porting
      of files from older Gnofract 4D versions.''')

    f("imag",
      [[[Complex], Float], [[Hyper], Float]],
      doc='''Extract the imaginary part of a complex or hypercomplex number.
      imag(a,b) = b.
      imag() is unusual in that it can be assigned to: imag(z) = 7 changes
      the imag part of z.''')

    f("imag2",
      [[Complex], Float],
      doc='''The square of the imaginary part of a complex number.
      real2(a,b) = b*b.
      While not a generally useful function, this is provided to ease porting
      of files from older Gnofract 4D versions.''')

    f("hyper_ri",
      [[Hyper], Complex],
      doc='''The real and imaginary parts of a hypercomplex number.
      Can be assigned to. hyper_ri(a,b,c,d) = (a,b).''')

    f("hyper_jk",
      [[Hyper], Complex],
      doc='''The 3rd and 4th parts of a hypercomplex number.
      Can be assigned to. hyper_jk(a,b,c,d) = (c,d).''')
    
    f("hyper_j",
      [[Hyper], Float],
      doc='''The 3rd component of a hypercomplex number. Can be assigned to.
      hyper_j(a,b,c,d) = c.''')

    f("hyper_k",
      [[Hyper], Float],
      doc='''The 4th component of a hypercomplex number. Can be assigned to.
      hyper_k(a,b,c,d) = d.''')

    f("red",
      [[Color], Float],
      doc='''The red component of a color. Can be assigned to.''')

    f("green",
      [[Color], Float],
      doc='''The green component of a color. Can be assigned to.''')

    f("blue",
      [[Color], Float],
      doc='''The blue component of a color. Can be assigned to.''')

    f("alpha",
      [[Color], Float],
      doc='''The alpha component of a color. Can be assigned to.''')

    f("hue",
      [[Color], Float],
      doc='''The hue of a color.''')

    f("sat",
      [[Color], Float],
      doc='''The saturation of a color.''')

    f("lum",
      [[Color], Float],
      doc='''The luminance (or brightness) of a color.''')

    f("gradient",
      [[Float], Color],
      doc='''Look up a color from the default gradient.''')
    
    f("recip",
      cfl("[_] , _", [Float, Complex, Hyper]),
      doc='''The reciprocal of a number. recip(x) is equivalent to 1/x.
      Note that not all hypercomplex numbers have a proper reciprocal.''')

    f("trunc",
      [[[Float], Int], [[Complex], Complex]],
      doc='''Round towards zero.''')

    f("round",
      [[[Float], Int], [[Complex], Complex]],
      doc='''Round to the nearest number (0.5 rounds up).''')

    f("floor",
      [[[Float], Int], [[Complex], Complex]],
      doc='''Round down to the next lowest number.''')

    f("ceil",
      [[[Float], Int], [[Complex], Complex]],
      doc='''Round up to the next highest number.''')

    f("zero",
      cfl("[_], _ ", [Int, Float, Complex]),
      doc='''Returns zero.''')
    
    f("abs",
      cfl("[_], _", [Int,Float, Complex]),
      doc='''The absolute value of a number. abs(3) = abs(-3) = 3.
      abs() of a complex number is a complex number consisting of
      the absolute values of the real and imaginary parts, i.e.
      abs(a,b) = (abs(a),abs(b)).''')

    f("cabs",
      [[Complex], Float],
      doc='''The complex modulus of a complex number z.
      cabs(a,b) is equivalent to sqrt(a*a+b*b).
      This is also the same as sqrt(|z|)''')

    f("cmag",
      [[[Complex], Float], [[Hyper], Float]],
      doc='''The squared modulus of a complex or hypercomplex number z.
      cmag(a,b) is equivalent to a*a+b*b. This is the same as |z|.''')

    f("log",
      cfl("[_], _", [Float, Complex, Hyper]),
      doc='The natural log.')

    f("sqrt",
      cfl("[_], _", [Float, Complex, Hyper]),
      doc='''The square root.
      The square root of a negative float number is NaN
      (ie it is NOT converted to complex). Thus sqrt((-3,0)) != sqrt(-3).''' )

    f("exp",
      cfl("[_], _", [Float, Complex, Hyper]),
      doc='exp(x) is equivalent to e^x')

    f("manhattan",
      [[Complex], Float],
      doc='''The Manhattan distance between the origin and complex number z.
      manhattan(a,b) is equivalent to abs(a) + abs(b).''')
    
    f("manhattanish",
      [[Complex], Float],
      doc='''A variant on Manhattan distance provided for backwards
      compatibility. manhattanish(a,b) is equivalent to a+b.''')
      
    f("manhattanish2",
      [[Complex], Float],
      doc='''A variant on Manhattan distance provided for backwards
      compatibility. manhattanish2(a,b) is equivalent to (a*a + b*b)^2.''')

    f("min",
      [[Float, Float], Float],
      doc='''Returns the smaller of its two arguments.''')
      
    f("max",
      [[Float, Float], Float],
      doc='''Returns the larger of its two arguments.''')

    f("max2",
      [[Complex], Float],
      doc='''max2(a,b) returns the larger of a*a or b*b. Provided for
      backwards compatibility.''')

    f("min2",
      [[Complex], Float],
      doc='''min2(a,b) returns the smaller of a*a or b*b. Provided for
      backwards compatibility.''')

    f("sin",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='trigonometric sine function.')
    
    f("cos",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='trigonometric sine function.')

    f("cosxx",
      cfl( "[_], _", [Complex, Hyper]),
      doc='''Incorrect version of cosine function. Provided for backwards
      compatibility with equivalent wrong function in Fractint.''')
    
    f("tan",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='trigonometric sine function.')

    f("cotan",
      cfl("[_], _", [Float, Complex, Hyper]),
      doc="Trigonometric cotangent function.")
      
    f("sinh",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Hyperbolic sine function.')
    
    f("cosh",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Hyperbolic cosine function.')
    
    f("tanh",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Hyperbolic tangent function.')

    f("cotanh",
      cfl("[_], _", [Float, Complex, Hyper]),
      doc='Hyperbolic cotangent function.')
        
    f("asin",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Inverse sine function.')
    
    f("acos",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Inverse cosine function.')
    
    f("atan",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Inverse tangent function.')

    f("atan2",
      [[Complex], Float],
      doc='''The angle between this complex number and the real line,
      aka the complex argument.''')
    
    f("asinh",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Inverse hyperbolic sine function.')
    
    f("acosh",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Inverse hyperbolic cosine function.')
    
    f("atanh",
      cfl( "[_], _", [Float, Complex, Hyper]),
      doc='Inverse hyperbolic tangent function.')

    # color functions
    f("blend",
      [ [Color, Color, Float], Color],
      doc='Blend two colors together in the ratio given by the 3rd parameter.')

    f("compose",
      [ [Color, Color, Float], Color],
      doc='''Composite the second color on top of the first, with opacity given
by the 3rd parameter.''')

    f("mergenormal",
      [ [Color, Color], Color],
      doc='''Returns second color, ignoring first.''')

    f("mergemultiply",
      [ [Color, Color], Color],
      doc='''Multiplies colors together. Result is always darker than either input.''')

    f("rgb",
      [ [Float, Float, Float], Color],
      doc='''Create a color from three color components. The alpha channel is set to to 1.0 (=100%).''')

    f("rgba",
      [ [Float, Float, Float, Float], Color],
      doc='Create a color from three color components and an alpha channel.')

    f("hsl",
      [ [Float, Float, Float], Color],
      doc='''Create a color from hue, saturation and lightness components. The alpha channel is set to to 1.0 (=100%).''')

    f("hsla",
      [ [Float, Float, Float,Float], Color],
      doc='''Create a color from hue, saturation and lightness components and an alpha channel.''')

    f("hsv",
      [ [Float, Float, Float], Color],
      doc='''Create a color from hue, saturation and value components. HSV is a similar color model to HSL but has a different valid range for brightness.''')

    f("_image",
      [ [Image, Complex], Color],
      doc='''Look up a color from a 2D array of colors.''')

    f("_alloc",
      [ [ [VoidArray, Int, Int], VoidArray],
        [ [VoidArray, Int, Int, Int], VoidArray],
        [ [VoidArray, Int, Int, Int, Int], VoidArray],
        [ [VoidArray, Int, Int, Int, Int, Int], VoidArray]],
      doc='''Allocate an array. First argument is element size in bytes, subsequent args are array sizes''')

    f("_write_lookup",
      # args are array, indexes, value. returns false if index is out of bounds
      [ [ [IntArray, Int, Int], Bool],
        [ [IntArray, Int, Int, Int], Bool],
        [ [IntArray, Int, Int, Int, Int], Bool],
        [ [IntArray, Int, Int, Int, Int, Int], Bool],
        
        [ [FloatArray, Int, Float], Bool],
        [ [FloatArray, Int, Int, Float], Bool],
        [ [FloatArray, Int, Int, Int, Float], Bool],
        [ [FloatArray, Int, Int, Int, Int, Float], Bool],

        [ [ComplexArray, Int, Complex], Bool],
        [ [ComplexArray, Int, Int, Complex], Bool],
        [ [ComplexArray, Int, Int, Int, Complex], Bool],
        [ [ComplexArray, Int, Int, Int, Int, Complex], Bool],

        ],
      doc='''Write a value into an array''')

    f("_read_lookup",
      # args are array, indexes, value
      [ [ [IntArray, Int], Int],
        [ [IntArray, Int, Int], Int],
        [ [IntArray, Int, Int, Int], Int],
        [ [IntArray, Int, Int, Int, Int], Int],

        [ [FloatArray, Int], Float],
        [ [FloatArray, Int, Int], Float],
        [ [FloatArray, Int, Int, Int], Float],
        [ [FloatArray, Int, Int, Int, Int], Float],
        
        [ [ComplexArray, Int], Complex],
        [ [ComplexArray, Int, Int], Complex],
        [ [ComplexArray, Int, Int, Int], Complex],
        [ [ComplexArray, Int, Int, Int, Int], Complex],
        
        ],
      doc='''Read a value out of an array''')
    
    # operators
    
    f("+", 
      cfl("[_,_] , _", [Int, Float, Complex, Hyper, Color]),
      fname="add",
      operator=True,
      doc='Adds two numbers together.')

    f("-",
      cfl("[_,_] , _", [Int, Float, Complex, Hyper, Color]),
      fname="sub",
      operator=True,
      doc='Subtracts two numbers')

    f("*",
      cfl("[_,_] , _", [Int, Float, Complex, Hyper]) +
      cfl("[_, Float], _", [Hyper, Color]),
      fname="mul",
      operator=True,
      doc='''Multiplication operator.''')

    f("/",
      [
        [[Float, Float], Float],
        [[Complex, Float], Complex],
        [[Complex, Complex], Complex],
        [[Hyper, Float], Hyper],
        [[Color, Float], Color]
      ],
      fname="div",
      operator=True,
      doc='''Division operator''')

    f("!=",
      cfl("[_,_] , Bool", [Int, Float, Complex, Bool]),
      fname="noteq",
      operator=True,
      precedence=3,
      doc='''Inequality operator. Compare two values and return true if
      they are different.''')

    f("==",
      cfl("[_,_] , Bool", [Int, Float, Complex, Bool]),
      fname="eq",
      operator=True,
      precedence=3,
      doc='''Equality operator. Compare two values and return true if they are
      the same.''')

    # fixme - issue a warning for complex compares
    f(">",
      cfl("[_,_], Bool", [Int, Float, Complex]),
      fname="gt",
      operator=True,
      precedence=3,
      doc='''Greater-than operator. Compare two values and return true if the first is greater than the second.''')

    f(">=",
      cfl("[_,_], Bool", [Int, Float, Complex]),
      fname="gte",
      operator=True,
      precedence=3,
      doc='''Greater-than-or-equal operator. Compare two values and return true if the first is greater than or equal to the second.''')

    f("<",
      cfl("[_,_], Bool", [Int, Float, Complex]),
      fname="lt",
      operator=True,
      precedence=3,
      doc='''Less-than operator. Compare two values and return true if the first is less than the second.''')

    f("<=",
      cfl("[_,_], Bool", [Int, Float, Complex]),
      fname="lte",
      operator=True,
      precedence=3,
      doc='''Less-than-or-equal operator. Compare two values and return true if the first is less than or equal to the second.''')

    f("%",
      cfl("[_,_] , _", [Int, Float]),
      fname="mod",
      operator=True,
      doc='''Modulus operator. Computes the remainder when x is divided by y. Not to be confused with the complex modulus.'''),
    
    # predefined parameters
    for p in range(1,7):
        name = "p%d" % p
        d[name] = Alias("t__a_" + name)
        d["t__a_" + name]  = Var(Complex,doc="Predefined parameter used by Fractint formulas")
        
    # predefined functions
    for p in range(1,5):
        name = "fn%d" % p
        d[name] = Alias("t__a_" + name)
        d["t__a_" + name ] = OverloadList(
            [Func([Complex],Complex, "ident") ],
            doc="Predefined function parameter used by Fractint formulas")

    # predefined gradient-related vars and functions
    tfunc = Func([Float],Float, "ident")
    tfunc.caption = ir.Const("Transfer Function", None, String)
    transfer = OverloadList([tfunc])
    d["t__a__transfer"] = transfer

    d["t__a__gradient"] = Var(Gradient)
    
    for (k,v) in list(d.items()):
        if hasattr(v,"cname") and v.cname == None:
            v.cname = k
            
    return d


def mangle(k,prefix=""):
    l = k.lower()
    if l[0] == '#':
        l = "t__h_" + prefix + l[1:]
    elif l[0] == '@':
        l = "t__a_" + prefix + l[1:]
    return l
               
class T(UserDict):
    default_dict = createDefaultDict()
    def __init__(self,prefix=""):
        UserDict.__init__(self)
        self.reset()
        self.nextlabel = 0
        self.nextTemp = 0
        self.nextEnum = 0
        self.nextParamSlot = 0
        self.var_params = []
        self.prefix = prefix
        self.temp_prefix = "t__%s" % prefix
        
    def __copy__(self):
        c = T(self.prefix)
        c.nextlabel = self.nextlabel
        c.nextTemp = self.nextTemp
        for k in list(self.data.keys()):
            c.data[k] = copy.copy(self.data[k])

        return c

    def merge(self,other):
        # self = union(self,other)
        # any clashes are won by self
        for k in list(other.data.keys()):
            #print "key",k
            if self.data.get(k) == None:
                #print "don't already have", k
                if self.is_param(k):
                    #print "update param", k
                    new_key = self.insert_prefix(other.prefix,k)
                    new_val = copy.copy(other.data[k])
                    self.data[new_key] = new_val
                    if isinstance(new_val,Var):
                        new_val.param_slot += self.nextParamSlot
                else:
                    self.data[k] = copy.copy(other.data[k])
            elif hasattr(self.data[k],"cname") and \
                 hasattr(other.data[k],"cname") and \
                 self.data[k].cname != other.data[k].cname:
                #print "have", k
                new_key = self.insert_prefix(other.prefix,k)
                new_val = copy.copy(other.data[k])
                self.data[new_key] = new_val
                if self.is_param(k) and isinstance(new_val,Var):
                    new_val.param_slot += self.nextParamSlot

        self.nextParamSlot += other.nextParamSlot
        
    def has_user_key(self,key):
        return mangle(key) in self.data
    
    def has_key(self,key):
        if mangle(key) in self.data:
            return True        
        return mangle(key) in self.default_dict

    def is_user(self,key):
        val = self.data.get(mangle(key),None)
        if val == None:
            val = self.default_dict.get(mangle(key))
        return val.pos != -1

    def insert_prefix(self, prefix, key):
        if key[0:5] == "t__a_":
            return "t__a_" + prefix + key[5:]
        if key[0:3] == "t__":
            return "t__" + prefix + key[3:]
        return prefix + key
    
    def is_param(self,key):
        return key[0:5] == 't__a_'

    def is_private(self,key):
        return key[0:3] == "t__"

    def mangled_name(self,key):
        k = mangle(key)
        return k
    
    def realName(self,key):
        ' returns mangled key even if var not present for test purposes'
        k = mangle(key)
        return self._realName(k)

    def _realName(self,k):
        val = self.data.get(k,None)
        if val == None:
            val = self.default_dict.get(k)
        if isinstance(val,Alias):
            val = self.default_dict.get(val.realName)
        if val != None:
            if val.cname == None:
                #print k
                raise Exception("argh" + k)
            return val.cname
        return k
    
    def get(self,key):
        try:
            return self[key]
        except KeyError:
            return None

    def __contains__(self, key):
        k = mangle(key)
        val = self.data.get(k,None)
        if val == None:
            val = self.default_dict.get(k,None)

        return val

    
    def __getitem__(self,key):
        k = mangle(key)
        val = self.data.get(k,None)
        if val == None:
            val = self.default_dict[k]
            if isinstance(val,Alias):
                key = val.realName
                return self.__getitem__(key)

            val = copy.copy(val)
            self.data[k] = val
            if self.is_param(k) and isinstance(val,Var) and \
                   val.param_slot == -1:
                self.record_param(val)
        return val

    def is_builtin(self,key):
        return key[0] == '#'

    def clashes_with_private(self,mangled_key,old_key):
        if mangled_key.find("t__",0,3)!=0:
            return False
        if old_key[0]=='@':
            return False
        return True

    def record_param(self,value):
        if value.cname == "z":
            print(value)
            assert False
        value.param_slot = self.nextParamSlot
        self.nextParamSlot += slotsForType(value.type)
        self.var_params.append(value)
        
    def __setitem__(self,key,value):
        k = mangle(key)
        if k in self.data:
            pre_type = self.data[k].type
            if  pre_type != value.type:                
                l = self.data[k].pos
                msg = ("was already defined as %s on line %d" % \
                       (strOfType(pre_type), l))
                raise KeyError("symbol '%s' %s" % (key,msg))
            return
        elif k in T.default_dict:
            pre_var = T.default_dict[k]
            #print("in default: %s" % k)
            if isinstance(pre_var,OverloadList):
                msg = "is predefined as a function"
                raise KeyError("symbol '%s' %s" % (key,msg))
            else:
                if pre_var.type != value.type:
                    msg = "is predefined as %s" % \
                          strOfType(T.default_dict[k].type)
                    raise KeyError("symbol '%s' %s" % (key,msg))

                if self.is_param(k):
                    self.record_param(pre_var)
            return
        elif self.is_builtin(key):
            msg = "symbol '%s': only predefined symbols can begin with #" % key
            raise KeyError(msg)                  
        elif self.clashes_with_private(k,key):
            raise KeyError("symbol '%s': no symbol starting with t__ is allowed" % key)
        self.data[k] = value
        if self.is_param(k) and isinstance(value,Var):
            #print "recording",k
            self.record_param(value)
        else:
            pass #print "not recording",k
            
        if hasattr(value,"cname") and value.cname == None:
            value.cname=self.insert_prefix(self.prefix,k)

    def ensure(self, name, var):
        # make sure an item is referred to in main dict
        self.__setitem__(name, var)
        self.__getitem__(name)
        
    def parameters(self,varOnly=False):
        params = {}
        for (name,sym) in list(self.data.items()):
            if self.is_param(name):
                if not varOnly or isinstance(sym,Var):
                    try:
                        params[name] = sym.first()
                    except AttributeError:
                        print(sym, name)
                        raise
                        
        return params

    def demangle(self,name):
        # remove most obvious mangling.
        # because of case-folding, demangle(mangle(s)) != s
        if name[:3] == "t__":
            name = name[3:]

        if name[:2] == "a_":
            name = "@" + name[2:]
        elif name[:2] == "h_":
            name = "#" + name[2:]
            
        return name

    def is_direct(self):
        return self.has_user_key("#color")
    
    def param_names(self):
        params = self.parameters()

        names = []
        for (name,param) in list(params.items()):
            if isinstance(param,Var):
                names.append(self.demangle(name))

        return names

    def func_names(self):
        params = self.parameters()

        func_names = []
        for (name,param) in list(params.items()):
            if isinstance(param,Func):
                func_names.append(self.demangle(name))
        return func_names

    def available_param_functions(self,ret,args):
        # a list of all function names which take args of type 'args'
        # and return 'ret' (for GUI to select a function)
        flist = []
        for (name,func) in list(self.default_dict.items()):
            try:
                for f in func:
                    if f.ret == ret and f.args == args and \
                           not self.is_private(name) and \
                           not func.is_operator():
                        flist.append(name)
            except TypeError:
                # wasn't a list
                pass
            
        return flist

    def order_of_params(self):
        # a hash which maps param name -> order in input list
        p = self.parameters(True)

        op = {}; 
        for k in list(p.keys()):
            op[k] = self[k].param_slot

        op["__SIZE__"]=self.nextParamSlot

        return op

    def type_of_params(self):
        # an array from param order -> type
        p = self.parameters(True)

        tp = [ None] * self.nextParamSlot; 
        for k in list(p.keys()):
            i = self[k].param_slot
            t = p[k].type
            if t == Complex:
                tp[i:i+2] = [Float, Float]
            elif t == Hyper or t == Color:
                tp[i:i+4] = [Float, Float, Float, Float]
            elif t == Float:
                tp[i] = Float
            elif t == Int:
                tp[i] = Int
            elif t == Bool:
                tp[i] = Bool
            elif t == Gradient:
                tp[i] = Gradient
            elif t == Image:
                tp[i] = Image
            else:
                raise ValueError("Unknown param type %s for %s" % (t, k))
        #assert not None in tp
        return tp

    def default_params(self):
        op = self.order_of_params()
        defaults = [0.0] * op["__SIZE__"]

        for (k,i) in list(op.items()):
            param = self.get(k)
            if not param: continue
            defval = getattr(param,"default",None)
            if param.type == Complex:
                if not defval:
                    dv = default_value(param.type)
                    defaults[i:i+2] = dv
                else:
                    defaults[i] = defval.value[0].value
                    defaults[i+1] = defval.value[1].value
            elif param.type == Hyper or param.type == Color:
                for j in range(len(defval.value)):
                    defaults[i+j] = defval.value[j].value
            elif param.type == Image:
                defaults[i] = 0
            else:
                if not defval:                    
                    defaults[i] = default_value(param.type)
                else:
                    defaults[i] = defval.value
        return defaults

    def set_std_func(self,func,fname):
        # repoint parameter @func to use fname next time we compile
        func.set_func(fname)
        
    def __delitem__(self,key):
        del self.data[mangle(key)]
        
    def reset(self):
        self.data = {} 

    def newLabel(self):
        label = "%slabel%d" % (self.prefix, self.nextlabel)
        self.nextlabel += 1
        return label

    def newTemp(self,type):
        name = self.temp_prefix + str(self.nextTemp) #"%s%d" % (self.temp_prefix, self.nextTemp)
        self.nextTemp += 1

        # bypass normal setitem because that checks for t__
        self.data[name] = Temp(type,name)
                
        return name

    def newEnum(self,name,val,pos):
        var = Var(Int, val, pos)
        # set cname because the enum value may not be a valid C identifier
        var.cname = "enum%s%d" % (self.prefix,self.nextEnum) 
        self.nextEnum += 1
        self["__enum_" + name] = var
        return var
