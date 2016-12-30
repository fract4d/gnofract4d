# a class to hold a formula and all the parameter settings which go with it

import copy
import math
import random
import re
import io
import weakref

import fracttypes
import gradient
import image

# matches a complex number
cmplx_re = re.compile(r'\((.*?),(.*?)\)')
# matches a hypercomplex number
hyper_re = re.compile(r'\((.*?),(.*?),(.*?),(.*?)\)')

class T:
    def __init__(self,compiler,parent=None,prefix=None):
        self.compiler = compiler
        self.formula = None
        self.funcName = None
        self.funcFile = None
        self.params = []
        self.paramtypes = []
        self.dirty = False
        self.set_prefix(prefix)
        if parent:
            self.parent = weakref.ref(parent)
        else:
            self.parent = None
            
    def set_prefix(self,prefix):
        self.prefix = prefix
        if prefix == None:
            self.sectname = "function"
        elif prefix == "cf0":
            self.sectname = "outer"
        elif prefix == "cf1":
            self.sectname = "inner"
        elif prefix[0] == 't':
            self.sectname = "transform" 
        else:
            raise ValueError("Unexpected prefix '%s' " % prefix)
        
    def set_initparams_from_formula(self,g):
        self.params = self.formula.symbols.default_params()
        self.paramtypes = self.formula.symbols.type_of_params()
        for i in range(len(self.paramtypes)):
            if self.paramtypes[i] == fracttypes.Gradient:
                self.params[i] = copy.copy(g)
            elif self.paramtypes[i] == fracttypes.Image:
                im = image.T(1,1)
                #b = im.image_buffer()
                #b[0] = chr(216)
                #b[3] = chr(88)
                #b[4] = chr(192)
                #b[11] = chr(255)
                self.params[i] = im 
                
    def reset_params(self):
        self.params = self.formula.symbols.default_params()
        self.paramtypes = self.formula.symbols.type_of_params()

    def copy_from(self,other):
        # copy the function overrides
        for name in self.func_names():
            self.set_named_func(name,
                                other.get_func_value(name))

        # copy the params
        self.params = [copy.copy(x) for x in other.params]

    def initvalue(self,name,warp_param=None):
        ord = self.order_of_name(name)
        type = self.formula.symbols[name].type
        
        if type == fracttypes.Complex:
            if warp_param == name:
                return "warp"
            else:
                return "(%.17f,%.17f)"%(self.params[ord],self.params[ord+1])
        elif type == fracttypes.Hyper or type == fracttypes.Color:
            return "(%.17f,%.17f,%.17f,%.17f)"% \
                   (self.params[ord],self.params[ord+1],
                    self.params[ord+2],self.params[ord+3])
        elif type == fracttypes.Float:
            return "%.17f" % self.params[ord]
        elif type == fracttypes.Int:
            return "%d" % self.params[ord]
        elif type == fracttypes.Bool:
            return "%s" % int(self.params[ord])
        elif type == fracttypes.Gradient:
            return "[\n" + self.params[ord].serialize() + "]"
        elif type == fracttypes.Image:
            return "[\n" + self.params[ord].serialize() + "]"
        else:
            raise ValueError("Unknown type %s for param %s" % (type,name))

    def save_formula_params(self,file,warp_param=None,sectnum=None):
        if sectnum == None:
            print("[%s]" % self.sectname, file=file)
        else:
            print("[%s]=%d" % (self.sectname, sectnum), file=file)
            
        print("formulafile=%s" % self.funcFile, file=file)
        print("function=%s" % self.funcName, file=file)

        if(self.compiler.is_inline(self.funcFile, self.funcName)):
            contents = self.compiler.get_formula_text(
                self.funcFile, self.funcName)
            print("formula=[\n%s\n]" % contents, file=file)

        names = self.func_names()
        names.sort()
        for name in names:
            print("%s=%s" % (name, self.get_func_value(name)), file=file)
        names = self.param_names()
        names.sort()
        for name in names:
            print("%s=%s" % (name, self.initvalue(name,warp_param)), file=file)

        print("[endsection]", file=file)
        
    def func_names(self):
        return self.formula.symbols.func_names()

    def param_names(self):
        return self.formula.symbols.param_names()

    def params_of_type(self,type,readable=False):
        params = []
        op = self.formula.symbols.order_of_params()
        for name in list(op.keys()):
            if name != '__SIZE__':
                if self.formula.symbols[name].type == type:
                    if readable:
                        params.append(self.formula.symbols.demangle(name))
                    else:
                        params.append(name)
        return params

    def get_func_value(self,func_to_get):
        fname = self.formula.symbols.demangle(func_to_get)
        func = self.formula.symbols[fname]
        return func[0].cname

    def get_named_param_value(self,name):
        op = self.formula.symbols.order_of_params()
        ord = op.get(self.formula.symbols.mangled_name(name))
        return self.params[ord]

    def order_of_name(self,name):
        symbol_table = self.formula.symbols
        op = symbol_table.order_of_params()
        rn = symbol_table.mangled_name(name)
        ord = op.get(rn)
        if ord == None:
            #print "can't find %s (%s) in %s" % (name,rn,op)
            pass
        return ord

    def set_gradient(self,g):
        ord = self.order_of_name("@_gradient")
        self.params[ord] = g

    def try_set_named_item(self,name,val):
        # set the item if it exists, don't worry if it doesn't
        try:
            self.set_named_item(name,val)
        except KeyError:
            pass

    def text(self):
        "Return the text of this formula"
        return self.compiler.get_formula_text(
            self.funcFile, self.funcName)

    def set_named_item(self,name,val):
        sym = self.formula.symbols[name].first()
        if isinstance(sym, fracttypes.Func):
            self.set_named_func(name,val)
        else:
            self.set_named_param(name,val)

    def set_named_param(self,name,val):
        ord = self.order_of_name(name)
        if ord == None:
            #print "Ignoring unknown param %s" % name
            return

        t = self.formula.symbols[name].type 
        if t == fracttypes.Complex:
            m = cmplx_re.match(val)
            if m != None:
                re = float(m.group(1)); im = float(m.group(2))
                if self.params[ord] != re:
                    self.params[ord] = re
                    self.changed()
                if self.params[ord+1] != im:                
                    self.params[ord+1] = im
                    self.changed()
            elif val == "warp":
                self.parent().set_warp_param(name)
        elif t == fracttypes.Hyper or t == fracttypes.Color:
            m = hyper_re.match(val)
            if m!= None:
                for i in range(4):
                    val = float(m.group(i+1))
                    if self.params[ord+i] != val:
                        self.params[ord+i] = val
                        self.changed()
        elif t == fracttypes.Float:
            newval = float(val)
            if self.params[ord] != newval:
                self.params[ord] = newval
                self.changed()
        elif t == fracttypes.Int:
            newval = int(val)
            if self.params[ord] != newval:
                self.params[ord] = newval
                self.changed()
        elif t == fracttypes.Bool:
            # don't use bool(val) - that makes "0" = True
	    try:
               i = int(val)
	       i = (i != 0)
	    except ValueError:
	       # an old release included a 'True' or 'False' string
	       if val == "True": i = 1
               else: i = 0
            if self.params[ord] != i:                
                self.params[ord] = i
                self.changed()
        elif t == fracttypes.Gradient:
            grad = gradient.Gradient()
            grad.load(io.StringIO(val))
            self.params[ord] = grad
            self.changed()
        elif t == fracttypes.Image:
            im = image.T(2,2)
            self.params[ord] = im
            self.changed()
        else:
            raise ValueError("Unknown param type %s for %s" % (t,name))

    def set_named_func(self,func_to_set,val):
        fname = self.formula.symbols.demangle(func_to_set)
        func = self.formula.symbols.get(fname)
        return self.set_func(func[0],val)            

    def zw_random(self,weirdness,size):
        factor = math.fabs(1.0 - math.log(size)) + 1.0
        return weirdness * (random.random() - 0.5 ) * 1.0 / factor

    def mutate(self, weirdness, size):
        for i in range(len(self.params)):
            if self.paramtypes[i] == fracttypes.Float:
                self.params[i] += self.zw_random(weirdness, size)
            elif self.paramtypes[i] == fracttypes.Int:
                # FIXME: need to be able to look up enum to find min/max
                pass
            elif self.paramtypes[i] == fracttypes.Bool:
                if random.random() < weirdness * 0.2:
                    self.params[i] = not self.params[i]

    def nudge_param(self,n,x,y):
        if x == 0 and y == 0:
            return False
        
        self.params[n] += (0.025 * x)
        self.params[n+1] += (0.025 * y)
        self.changed()
        return True
    
    def set_param(self,n,val):
        # set the N'th param to val, after converting from a string
        t = self.paramtypes[n]

        if t == fracttypes.Float:
            val = float(val)
        elif t == fracttypes.Int:
            val = int(val)
        elif t == fracttypes.Bool:
            val = bool(val)
        else:
            raise ValueError("Unknown parameter type %s" % t)
        
        if self.params[n] != val:
            self.params[n] = val
            self.changed()
            return True
        return False

    def set_func(self,func,fname):
        if func.cname != fname:
            self.formula.symbols.set_std_func(func,fname)
            self.dirty = True
            self.changed()
            return True
        else:
            return False

    def changed(self):
        self.dirty = True
        if self.parent:
            self.parent().changed()

    def is_direct(self):
        return self.formula.is_direct()
    
    def set_formula(self,file,func,gradient):
        formula = self.compiler.get_formula(file,func,self.prefix)

        if formula == None:
            raise ValueError("no such formula: %s:%s" % (file, func))

        if formula.errors != []:
            raise ValueError("invalid formula '%s':\n%s" % \
                             (func, "\n".join(formula.errors)))

        self.formula = formula
        self.funcName = func
        self.funcFile = file

        self.set_initparams_from_formula(gradient)

    def load_param_bag(self,bag):
        for (name,val) in list(bag.dict.items()):
            if name == "formulafile" or name=="function":
                pass
            else:
                self.try_set_named_item(name,val)

    def blend(self, other, ratio):
        # update in-place our settings so that they are a mixture with the other
        if self.funcName != other.funcName or self.funcFile != other.funcFile:
            raise ValueError("Cannot blend parameters between different formulas")
        
        for i in range(len(self.params)):
            (a,b) = (self.params[i],other.params[i])
            if self.paramtypes[i] == fracttypes.Float:
                self.params[i] = a*(1.0-ratio) + b*ratio
            elif self.paramtypes[i] == fracttypes.Int:
                self.params[i] = int(a*(1.0-ratio) + b*ratio)
            elif self.paramtypes[i] == fracttypes.Bool:
                if ratio >= 0.5:
                    self.params[i] = b
            else:
                # don't interpolate
                pass

        
            
