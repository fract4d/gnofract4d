#!/usr/bin/env python3

import io
import os
import sys
import math
import copy
import random
from time import time as now

from . import fract4dc, gradient, image, fctutils, colorizer, formsettings, fc

# the version of the earliest gf4d release which can parse all the files
# this version can output
THIS_FORMAT_VERSION = "3.10"

BLEND_NEAREST = 0
BLEND_FURTHEST = 1
BLEND_CW = 2
BLEND_CCW = 3

class T(fctutils.T):
    XCENTER = 0
    YCENTER = 1
    ZCENTER = 2
    WCENTER = 3
    MAGNITUDE = 4
    XYANGLE = 5
    XZANGLE = 6
    XWANGLE = 7
    YZANGLE = 8
    YWANGLE = 9
    ZWANGLE = 10

    FORMULA = 0
    OUTER = 1
    INNER = 2
    DEFAULT_FORMULA_FILE = "gf4d.frm"
    DEFAULT_FORMULA_FUNC = "Mandelbrot"
    paramnames = ["x","y","z","w","size","xy","xz","xw","yz","yw","zw"]

    def __init__(self,compiler,site=None):
        fctutils.T.__init__(self)
        
        self.format_version = 2.8

        self.bailfunc = 0
        # formula support
        self.forms = [
            formsettings.T(compiler,self),  # formula
            formsettings.T(compiler,self,"cf0"),  # outer
            formsettings.T(compiler,self,"cf1")  # inner
            ]

        self.transforms = []
        self.next_transform_id = 0
        self.compiler_options = {"optimize" : 1}
        self.yflip = False
        self.periodicity = True
        self.period_tolerance = 1.0E-9
        self.auto_epsilon = False  # automatically set @epsilon param, if found
        self.auto_deepen = True  # automatically adjust maxiter
        self.auto_tolerance = True  # automatically adjust periodicity
        self.antialias = 1
        self.compiler = compiler
        self.outputfile = None
        self.render_type = 0
        self.pfunc = None
        self.handle = None

        self.warp_param = None
        # gradient
        
        # default is just white outside
        self.default_gradient = gradient.Gradient()
        self.default_gradient.segments[0].left_color = [1.0,1.0,1.0,1.0]
        self.default_gradient.segments[0].right_color = [1.0,1.0,1.0,1.0]

        # solid colors are black
        self.solids = [(0,0,0,255),(0,0,0,255)]

        # formula defaults
        self.set_formula(T.DEFAULT_FORMULA_FILE,T.DEFAULT_FORMULA_FUNC,0)
        self.set_inner("gf4d.cfrm","zero")
        self.set_outer("gf4d.cfrm","continuous_potential")
        self.dirtyFormula = True  # formula needs recompiling
        self.dirty = True  # parameters have changed
        self.clear_image = True
        
        self.reset()

        # interaction with fract4dc library
        self.site = site or fract4dc.site_create(self)

        # colorfunc lookup
        self.colorfunc_names = [
            "default",
            "continuous_potential",
            "zero",
            "ejection_distance",
            "decomposition",
            "external_angle"]

        self.saved = True  # initial params not worth saving

    def serialize(self,comp=False):
        out = io.StringIO()
        self.save(out,False,compress=comp)
        return out.getvalue()

    def deserialize(self,string):
        self.loadFctFile(io.StringIO(string))
        self.changed()
        
    def apply_params(self,dict):
        for (key,value) in list(dict.items()):
            self.parseVal(key,value,None)

    def save(self,file,update_saved_flag=True,**kwds):
        print("gnofract4d parameter file", file=file)
        print("version=%s" % THIS_FORMAT_VERSION, file=file)

        compress = kwds.get("compress",False)
        if compress is not False:
            # compress this file
            main_file = file
            file = fctutils.Compressor()

        for pair in zip(self.paramnames,self.params):
            print("%s=%.17f" % pair, file=file)

        print("maxiter=%d" % self.maxiter, file=file)
        print("yflip=%s" % self.yflip, file=file)
        print("periodicity=%s" % int(self.periodicity), file=file)
        print("period_tolerance=%.17f" % self.period_tolerance, file=file)
        
        self.forms[0].save_formula_params(file,self.warp_param)
        self.forms[1].save_formula_params(file)
        self.forms[2].save_formula_params(file)

        i = 0
        for transform in self.transforms:
            transform.save_formula_params(file,None,i)
            i += 1
            
        print("[colors]", file=file)
        print("colorizer=1", file=file)
        print("solids=[", file=file)
        for solid in self.solids:
            print("%02x%02x%02x%02x" % solid, file=file)
        print("]", file=file)
        print("[endsection]", file=file)

        if compress:
            file.close()
            print(file.getvalue(), file=main_file)
        
        if update_saved_flag:
            self.saved = True

    def get_gradient(self):
        try:
            g = self.forms[0].get_named_param_value("@_gradient")
            if g == 0:
                g = self.default_gradient
        except Exception as exn:
            g = self.default_gradient
        return g

    def set_gradient(self, g):
        old_g = self.get_gradient()
        if old_g != g:
            self.forms[0].set_gradient(g)
            #needs_redraw = False
            #if self.forms[1].is_direct() or \
            #   self.forms[2].is_direct():
            #    needs_redraw = True
               
            self.changed(True) #needs_redraw)

    def set_gradient_from_file(self, file, name):
        g = self.compiler.get_gradient(file, name)
        self.set_gradient(g)
        
    def parse_periodicity(self,val,f):
        try:
            self.set_periodicity(int(val))
        except ValueError:
            # might be a bool in 'True'/'False' format
            self.set_periodicity(bool(val))

    def parse_period_tolerance(self,val,f):
        self.period_tolerance = float(val)

    def set_period_tolerance(self,val):
        if val != self.period_tolerance:
            self.period_tolerance = val
            self.changed(False)
            
    def normalize_formulafile(self,params,formindex,formtype):
        formula = params.dict.get("formula")
        if formula:
            # we have an in-line formula, use that instead of formulafile/function
            (formulafile, fname) = self.compiler.add_inline_formula(
                formula,formtype)
        else:
            formulafile = params.dict.get(
                "formulafile",self.forms[formtype].funcFile)
            fname = params.dict.get(
                "function", self.forms[formtype].funcName)

        return (formulafile, fname)

    def parse__inner_(self,val,f):
        params = fctutils.ParamBag()
        params.load(f)
        (file,func) = self.normalize_formulafile(
            params,2,fc.FormulaTypes.COLORFUNC)
        self.set_inner(file,func)
        self.forms[2].load_param_bag(params)
        
    def parse__outer_(self,val,f):
        params = fctutils.ParamBag()
        params.load(f)
        (file, func) = self.normalize_formulafile(
            params,1,fc.FormulaTypes.COLORFUNC)
        self.set_outer(file,func)
        self.forms[1].load_param_bag(params)

    def parse__function_(self,val,f):
        params = fctutils.ParamBag()
        params.load(f)
        (file,func) = self.normalize_formulafile(
            params,0,fc.FormulaTypes.FRACTAL)

        self.set_formula(file,func,0)
            
        for (name,val) in list(params.dict.items()):
            if name == "formulafile" or name == "function" or name == "formula" or name == "":
                continue
            elif name == "a" or name == "b" or name == "c":
                # back-compat for older versions
                self.forms[0].set_named_param("@" + name, val)
            else:
                self.forms[0].set_named_item(name,val)

    def parse__transform_(self,val,f):
        which_transform = int(val)
        params = fctutils.ParamBag()
        params.load(f)
        self.set_transform(
            params.dict["formulafile"],
            params.dict["function"],
            which_transform)
        self.transforms[which_transform].load_param_bag(params)
        
    def __del__(self):
        #print "deleting fractal %s" % self
        del self.pfunc
        del self.handle

    def __copy__(self):
        # override shallow-copy to do a deeper copy than normal,
        # but still don't try and copy *everything*

        c = T(self.compiler,self.site)

        c.maxiter = self.maxiter
        c.params = copy.copy(self.params)

        c.bailfunc = self.bailfunc

        for i in range(3):
            c.set_formula(self.forms[i].funcFile,self.forms[i].funcName,i)
            c.forms[i].copy_from(self.forms[i])

        for t in self.transforms:
            c.append_transform(t.funcFile, t.funcName)
            c.transforms[-1].copy_from(t)
            
        c.solids = copy.copy(self.solids)
        c.yflip = self.yflip
        c.periodicity = self.periodicity
        c.period_tolerance = self.period_tolerance
        c.auto_deepen = self.auto_deepen
        c.auto_tolerance = self.auto_tolerance
        c.saved = self.saved
        c.clear_image = self.clear_image
        c.warp_param = self.warp_param
        return c

    def determine_direction(self,a,b,mode):
        isClockwise = False
        
        if mode == BLEND_NEAREST:
            if abs(b-a) <= math.pi and a < b:
                isClockwise = True
            elif abs(b-a) > math.pi and a > b:
                isClockwise = True
        elif mode == BLEND_FURTHEST:
            if abs(b-a) <= math.pi and a > b:
                isClockwise = True
            if abs(b-a) > math.pi and a < b:
                isClockwise = True
        elif mode == BLEND_CW:
            isClockwise = True
        elif mode == BLEND_CCW:
            isClockwise = False
        else:
            raise ValueError("Unknown angle blend mode %s" % mode)

        return isClockwise

    def blend_angle(self,a,b,ratio,mode):
        angle = 0.0
        isClockwise = self.determine_direction(a,b,mode)
        
        if isClockwise and b < a:
            b = b + math.pi * 2.0
        if not isClockwise and b > a:
            a = a + math.pi * 2.0

        angle = a * (1-ratio) + b * ratio
        while angle > math.pi:
            angle -= math.pi * 2.0
            
        return angle
    
    def blend(self,other,ratio,angle_options=()):
        """Create a new fractal which blends the this and other's parameter sets using ratio.
        'angle_options' can be used to override the default method of interpolating angles."""
        new = copy.copy(self)
        for i in range(self.XCENTER,self.MAGNITUDE):
            (a,b) = (self.params[i], other.params[i])
            new.set_param(i, a*(1-ratio) + b*ratio)

        # magnitude is exponential
        (a,b) = (self.params[self.MAGNITUDE], other.params[self.MAGNITUDE])
        if abs(a) > abs(b):
            factor = (a-b)/(math.e-1)
            val = factor * math.exp(1-ratio) + (b - factor)
        else:
            factor = (b-a)/(math.e-1)
            val = factor * math.exp(ratio) + (a - factor)

        new.set_param(self.MAGNITUDE, val)

        for i in range(self.XYANGLE, self.ZWANGLE+1):
            (a,b) = (self.params[i], other.params[i])
            option = angle_options[i-self.XYANGLE:i-self.XYANGLE]
            if len(option):
                mode = option[0]
            else:
                mode = BLEND_NEAREST
            new.set_param(i, self.blend_angle(a,b,ratio,mode))

        for (form1,form2) in zip(new.forms,other.forms):
            form1.blend(form2,ratio)
            
        return new
    
    def reset_angles(self):
        for i in range(self.XYANGLE,self.ZWANGLE+1):
            self.set_param(i,0.0)
        
    def reset(self):
        # set global default values, then override from formula
        # set up defaults
        self.params = [
            0.0, 0.0, 0.0, 0.0,  # center
            4.0,  # size
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0  # angles
            ]

        self.bailout = 0.0
        self.maxiter = 256
        self.rot_by = math.pi/2
        self.title = self.forms[0].funcName
        self.yflip = False
        self.auto_epsilon = False
        self.period_tolerance = 1.0E-9
        
        g = self.get_gradient()
        self.set_formula_defaults(g)

    def reset_zoom(self):
        mag = self.forms[0].formula.defaults.get("magn")
        if mag:
            mag = mag.value
        else:
            mag = self.forms[0].formula.defaults.get("magnitude")
            if mag:
                mag = mag.value
            else:
                mag = 4.0
        self.set_param(self.MAGNITUDE, mag)

    def copy_colors(self, f):
        self.set_gradient(copy.copy(f.get_gradient()))
        self.set_solids(f.solids)
        self.changed(False)

    def set_warp_param(self,param):
        if self.warp_param != param:
            self.warp_param = param
            self.changed(True)
            
    def set_cmap(self,mapfile):
        c = colorizer.T(self)
        with open(mapfile) as file:
            c.parse_map_file(file)
        self.set_gradient(c.gradient)
        self.set_solids(c.solids)
        self.changed(False)

    def get_initparam(self,n,param_type):
        params = self.forms[param_type].params
        return params[n]
    
    def set_initparam(self,n,val, param_type):
        self.forms[param_type].set_param(n,val)

    def set_solid(self,i,newsolid):
        if self.solids[i] == newsolid:
            return
        self.solids[i] = newsolid
        self.changed(False)
        
    def set_solids(self, solids):
        same = True
        for i in range(len(solids)):
            if self.solids[i] != solids[i]:
                same = False
                break
        if same:
            return

        self.solids[0:len(solids)] = solids[:]
        self.changed(False)
        
    def refresh(self):
        for i in range(3):
            if self.compiler.out_of_date(self.forms[i].funcFile):
                self.set_formula(
                    self.forms[i].funcFile,self.forms[i].funcName,i)

    def set_formula_defaults(self, g=None):
        if self.forms[0].formula is None:
            return

        if g is None:
            g = self.get_gradient()

        self.forms[0].set_initparams_from_formula(g)

        for (name,val) in list(self.forms[0].formula.defaults.items()):
            # FIXME helpfile,helptopic,method,precision,
            # render,skew,stretch
            if name == "maxiter":
                self.maxiter = int(val.value)
            elif name == "center" or name == "xycenter":
                self.params[self.XCENTER] = float(val.value[0].value)
                self.params[self.YCENTER] = float(val.value[1].value)
            elif name == "zwcenter":
                self.params[self.ZCENTER] = float(val.value[0].value)
                self.params[self.WCENTER] = float(val.value[1].value)
            elif name == "angle":
                self.params[self.XYANGLE] = float(val.value)
            elif name == "magn":
                self.params[self.MAGNITUDE] = float(val.value)
            elif name == "title":
                self.title = val.value
            elif name == "periodicity":
                self.periodicity = int(val.value)
            else:
                if hasattr(self,name.upper()):
                    self.params[getattr(self,name.upper())] = float(val.value)
                else:
                    print("ignored unknown parameter %s" % name)

        for form in self.forms[1:] + self.transforms:
            form.reset_params()

    def set_formula(self,formulafile,func,index=0):
        self.forms[index].set_formula(formulafile,func,self.get_gradient())

        if index == 0:
            self.set_bailfunc()
            self.warp_param = None
        self.formula_changed()
        self.changed()
        
    def get_saved(self):
        return self.saved
    
    def set_bailfunc(self):
        bailfuncs = [
            "cmag", "manhattanish","manhattanish2",
            "max2","min2",
            "real2","imag2",
            None  # bailout
            ]
        funcname = bailfuncs[self.bailfunc]
        if funcname is None:
            # FIXME deal with diff
            return

        func = self.forms[0].formula.symbols.get("@bailfunc")
        if func is not None:
            self.set_func(func[0],funcname,self.forms[0].formula)

    def changed(self,clear_image=True):
        self.dirty = True
        self.saved = False
        self.clear_image = clear_image
        
    def formula_changed(self):
        self.dirtyFormula = True
        
    def set_func(self,func,fname,formula):
        if func.cname != fname:
            formula.symbols.set_std_func(func,fname)
            self.dirtyFormula = True
            self.changed()
            
    def set_periodicity(self,periodicity):
        if self.periodicity != periodicity:
            self.periodicity = periodicity
            self.changed()
        
    def set_inner(self,funcfile,funcname):
        self.set_formula(funcfile,funcname,2)

    def set_outer(self,funcfile,funcname):
        self.set_formula(funcfile,funcname,1)

    def get_transform_prefix(self):
        i = self.next_transform_id
        prefix = "t%d" % i
        self.next_transform_id += 1
        return prefix
    
    def append_transform(self,funcfile,funcname):
        fs = formsettings.T(self.compiler,self,self.get_transform_prefix())
        fs.set_formula(funcfile, funcname, self.get_gradient())
        self.transforms.append(fs)
        self.formula_changed()
        self.changed()
        
    def set_transform(self,funcfile,funcname,i):
        fs = formsettings.T(self.compiler,self,self.get_transform_prefix())
        fs.set_formula(funcfile, funcname, self.get_gradient())
        if len(self.transforms) <= i:
            self.transforms.extend([None] * (i - len(self.transforms)+1))

        self.transforms[i] = fs
        self.formula_changed()
        self.changed()
        
    def remove_transform(self,i):
        self.transforms.pop(i)
        self.formula_changed()
        self.changed()
        
    def set_compiler_option(self,option,val):
        self.compiler_options[option] = val
        self.dirtyFormula = True

    def apply_options(self,options):
        if options.formula.name and options.formula.func:
            self.set_formula(options.formula.name, options.formula.func)
            self.reset()

        if options.inner.name and options.inner.func:
            self.set_formula(options.inner.name, options.inner.func)
            self.reset()

        if options.outer.name and options.outer.func:
            self.set_formula(options.outer.name, options.outer.func)
            self.reset()

        if options.maxiter != -1:
            self.set_maxiter(options.maxiter)

        for num, val in options.paramchanges.items():
            self.set_param(num, val)

        for t in options.transforms:
            self.append_transform(t.name, t.func)
            
        if options.map:
            self.set_cmap(options.map)

        if options.antialias is not None:
            self.antialias = options.antialias

    def compile(self):
        if self.forms[0].formula is None:
            raise ValueError("no formula")
        if self.dirtyFormula is False:
            return self.outputfile

        outputfile = self.compiler.compile_all(
            self.forms[0].formula,
            self.forms[1].formula,
            self.forms[2].formula,
            [x.formula for x in self.transforms],
            self.compiler_options)
        
        if outputfile is not None:
            self.set_output_file(outputfile)

        self.dirtyFormula = False
        return self.outputfile

    def set_output_file(self, outputfile):
        if self.outputfile != outputfile:
            self.outputfile = outputfile
            self.handle = fract4dc.pf_load(self.outputfile)
            self.pfunc = fract4dc.pf_create(self.handle)

    def make_random_colors(self, n):
        self.get_gradient().randomize(n)
        self.changed(False)
        
    def mul_vs(self,v,s):
        return [x * s for x in v]

    def xy_random(self,weirdness,size):
        return weirdness * 0.5 * size * (random.random() - 0.5)

    def zw_random(self,weirdness,size):
        factor = math.fabs(1.0 - math.log(size)) + 1.0
        return weirdness * (random.random() - 0.5) * 1.0 / factor

    def angle_random(self, weirdness):
        action = random.random()
        if action > weirdness:
            return 0.0  # no change

        action = random.random()
        if action < weirdness/6.0:
            # +/- pi/2
            if random.random() > 0.5:
                return math.pi/2.0
            else:
                return math.pi/2.0
        
        return weirdness * (random.random() - 0.5) * math.pi/2.0

    def is4D(self):
        return self.warp_param is not None or self.forms[0].formula.is4D()

    def mutate(self,weirdness,color_weirdness):
        '''randomly adjust position, colors, angles and parameters.
        weirdness is between 0 and 1 - 0 is no change, 1 is lots'''

        size = self.params[self.MAGNITUDE]
        self.params[self.XCENTER] += self.xy_random(weirdness, size)
        self.params[self.YCENTER] += self.xy_random(weirdness, size)

        self.params[self.XYANGLE] += self.angle_random(weirdness)
        
        if self.is4D():
            self.params[self.ZCENTER] += self.zw_random(weirdness, size)
            self.params[self.WCENTER] += self.zw_random(weirdness, size)

            for a in range(self.XZANGLE,self.ZWANGLE):
                self.params[a] += self.angle_random(weirdness)

        if random.random() < weirdness * 0.75:
            self.params[self.MAGNITUDE] *= 1.0 + (0.5 - random.random())

        for f in self.forms:
            f.mutate(weirdness, size)

        if random.random() < color_weirdness:
            try:
                (file, formula) = self.compiler.get_random_gradient()
                self.set_gradient_from_file(file,formula)
            except IndexError:
                # can occur if no gradients available or occasionally
                # because random.choice is horked
                pass
        
    def nudge(self,x,y,axis=0):
        # move a little way in x or y
        self.relocate(0.025 * x, 0.025 * y, 1.0,axis)

    def get_form(self,param_type):
        if param_type > 2:
            form = self.transforms[param_type-3]
        else:
            form = self.forms[param_type]
        return form
    
    def nudge_param(self, i, param_type, x, y):
        form = self.get_form(param_type)
        form.nudge_param(i,x,y)

    def relocate(self,dx,dy,zoom,axis=0):
        if dx == 0 and dy == 0 and zoom == 1.0:
            return
        
        m = fract4dc.rot_matrix(self.params)

        deltax = self.mul_vs(m[axis],dx)
        if self.yflip:
            deltay = self.mul_vs(m[axis+1],dy)
        else:
            deltay = self.mul_vs(m[axis+1],-dy)

        self.params[self.XCENTER] += deltax[0] + deltay[0]
        self.params[self.YCENTER] += deltax[1] + deltay[1]
        self.params[self.ZCENTER] += deltax[2] + deltay[2]
        self.params[self.WCENTER] += deltax[3] + deltay[3]
        self.params[self.MAGNITUDE] *= zoom
        self.changed()
        
    def flip_to_julia(self):
        self.params[self.XZANGLE] += self.rot_by
        self.params[self.YWANGLE] += self.rot_by
        self.rot_by = - self.rot_by
        self.changed()
        
    # status callbacks
    def status_changed(self,val):
        pass
    
    def progress_changed(self,d):
        pass
    
    def stats_changed(self,s):
        pass

    def is_interrupted(self):
        return False

    def iters_changed(self,iters):
        #print "iters changed to %d" % iters
        self.maxiter = iters

    def tolerance_changed(self,tolerance):
        #print "tolerance changed to %g" % tolerance
        self.period_tolerance = tolerance

    def image_changed(self,x1,y1,x2,y2):
        pass

    def _pixel_changed(self,params,x,y,aa,maxIters,nNoPeriodIters,dist,fate,nIters,r,g,b,a):
        # remove underscore to debug fractal generation
        print("pixel: (%g,%g,%g,%g) %d %d %d %d %d %g %d %d (%d %d %d %d)" %
              (params[0],params[1],params[2],params[3],x,y,aa,maxIters,nNoPeriodIters,dist,fate,nIters,r,g,b,a))

    def epsilon_tolerance(self,w,h):
        #5% of the size of a pixel
        return self.params[self.MAGNITUDE]/(20.0 * max(w,h))

    def all_params(self):
        p = []
        for form in self.forms:
            p += form.params
        for transform in self.transforms:
            p += transform.params
        return p

    def get_colormap(self):
        cmap = fract4dc.cmap_create_gradient(self.get_gradient().segments)

        (r,g,b,a) = self.solids[0]
        fract4dc.cmap_set_solid(cmap,0,r,g,b,a)
        (r,g,b,a) = self.solids[1]
        fract4dc.cmap_set_solid(cmap,1,r,g,b,a)

        return cmap

    def init_pfunc(self):
        initparams = self.all_params()
        fract4dc.pf_init(self.pfunc,self.params,initparams)

    def get_warp(self):
        if self.warp_param:
            warp = self.forms[0].order_of_name(self.warp_param)
        else:
            warp = -1
        return warp

    def set_maxiter(self,new_iter):
        if self.maxiter != new_iter:
            self.maxiter = new_iter
            self.changed(False)

    def set_antialias(self,aa):
        if aa != self.antialias:
            self.antialias = aa
            self.changed(True)

    def set_auto_deepen(self,auto_deepen):
        if auto_deepen != self.auto_deepen:
            self.auto_deepen = auto_deepen
            self.changed(True)

    def set_auto_tolerance(self,auto_tolerance):
        if auto_tolerance != self.auto_tolerance:
            self.auto_tolerance = auto_tolerance
            self.changed(True)
            
    def calc(self,image,colormap,nthreads,site,asynchronous):
        fract4dc.calc(
            params=self.params,
            antialias=self.antialias,
            maxiter=self.maxiter,
            yflip=self.yflip,
            periodicity=self.periodicity,
            nthreads=nthreads,
            pfo=self.pfunc,
            cmap=colormap,
            auto_deepen=self.auto_deepen,
            auto_tolerance=self.auto_tolerance,
            tolerance=self.period_tolerance,
            render_type=self.render_type,
            warp_param=self.get_warp(),
            image=image._img,
            site=site,
            dirty=self.clear_image,
            asynchronous=asynchronous)
        
    def drawpoint(self):
        self.init_pfunc()
        print("x:\t\t%.17f\ny:\t\t%.17f\nz:\t\t%.17f\nw:\t\t%.17f\n" % tuple(self.params[0:4]))
        startTime = now()
        result = fract4dc.pf_calc(
            self.pfunc,self.params[0:4],self.maxiter,0,0,0,100*1000*1000)
        duration = now() - startTime
        print("iterations:\t%s\nfate:\t\t%s\ndistance:\t%s\nsolid:\t\t%s" % result)
        print("duration:\t%.4g" % duration)

    def draw(self,image,nthreads=1):
        self.init_pfunc()

        colormap = self.get_colormap()
        for (xoff,yoff,xres,yres) in image.get_tile_list():
            image.resize_tile(xres,yres)
            image.set_offset(xoff,yoff)

            self.calc(image,colormap,nthreads,self.site,False)

            image.save_tile()
        
    def clean(self):
        self.dirty = False
        
    def set_param(self,n,val):
        val = float(val)
        if self.params[n] != val:
            self.params[n] = val
            self.changed()

    def get_param(self,n):
        return self.params[n]
    
    def parse_gnofract4d_parameter_file(self,val,f):
        pass

    def parse_version_string(self,s):
        try:
            (major,minor) = tuple([int(a) for a in s.split(".")])
            return major * 1000.0 + minor
        except Exception as exn:
            raise ValueError("Invalid version number %s" % s)

    def parse_version(self,val,f):
        global THIS_FORMAT_VERSION
        self.format_version = self.parse_version_string(val)
        this_format_version = self.parse_version_string(THIS_FORMAT_VERSION)
        if self.format_version < 2000.0:
            # old versions displayed everything upside down
            # switch the rotation so they load OK
            self.yflip = True
        if 1700.0 < self.format_version < 2000.0:
            # a version that used auto-tolerance for Nova and Newton
            self.auto_epsilon = True
            
        if self.format_version > this_format_version:
            warning = \
'''This file was created by a newer version of Gnofract 4D.
The image may not display correctly. Please upgrade to version %s or higher.'''

            self.warn(warning % val)

    def warn(self,msg):
        print(msg)

    def parse_bailfunc(self,val,f):
        # can't set function directly because formula hasn't been parsed yet
        self.bailfunc = int(val)

    def apply_colorizer(self, cf):
        if cf.read_gradient:
            self.set_gradient(cf.gradient)
        self.set_solids(cf.solids)
        self.changed(False)
        if cf.direct:
            # loading a legacy rgb colorizer
            self.set_outer("gf4d.cfrm", "rgb")

            val = "(%f,%f,%f,1.0)" % tuple(cf.rgb)
            self.forms[1].set_named_item("@col",val)

    def parse__colors_(self,val,f):
        cf = colorizer.T(self)
        cf.load(f)
        self.apply_colorizer(cf)
        
    def parse__colorizer_(self,val,f):
        which_cf = int(val)
        cf = colorizer.T(self)
        cf.load(f)
        if which_cf == 0:
            self.apply_colorizer(cf)
        # ignore other colorlists for now

    def parse_inner(self,val,f):
        name = self.colorfunc_names[int(val)]
        self.set_inner("gf4d.cfrm",name)

    def parse_outer(self,val,f):
        name = self.colorfunc_names[int(val)]
        self.set_outer("gf4d.cfrm",name)

    def set_yflip(self,yflip):
        if self.yflip != yflip:
            self.yflip = yflip
            self.changed()
        
    def parse_yflip(self,val,f):
        self.yflip = (val == "1" or val == "True")
        
    def parse_x(self,val,f):
        self.set_param(self.XCENTER,val)

    def parse_y(self,val,f):
        self.set_param(self.YCENTER,val)

    def parse_z(self,val,f):
        self.set_param(self.ZCENTER,val)

    def parse_w(self,val,f):
        self.set_param(self.WCENTER,val)

    def parse_size(self,val,f):
        self.set_param(self.MAGNITUDE,val)

    def parse_xy(self,val,f):
        self.set_param(self.XYANGLE,val)

    def parse_xz(self,val,f):
        self.set_param(self.XZANGLE,val)

    def parse_xw(self,val,f):
        self.set_param(self.XWANGLE,val)

    def parse_yz(self,val,f):
        self.set_param(self.YZANGLE,val)

    def parse_yw(self,val,f):
        self.set_param(self.YWANGLE,val)

    def parse_zw(self,val,f):
        self.set_param(self.ZWANGLE,val)

    def parse_bailout(self,val,f):
        self.bailout = float(val)

    def parse_maxiter(self,val,f):
        self.maxiter = int(val)
        
    def parse_antialias(self,val,f):
        # antialias now a user pref, not saved in file
        #self.antialias = int(val)
        pass

    def order_of_name(self,name,symbol_table):
        op = symbol_table.order_of_params()
        rn = symbol_table.mangled_name(name)
        ord = op.get(rn)
        if ord is None:
            #print "can't find %s (%s) in %s" % (name,rn,op)
            pass
        return ord
    
    def fix_bailout(self):
        # because bailout occurs before we know which function this is
        # in older files, we save it in self.bailout then apply to the
        # initparams later
        if self.bailout != 0.0:
            for f in self.forms:
                f.try_set_named_item("@bailout",self.bailout)

    def fix_gradients(self, old_gradient):
        # new gradient is read in after the gradient params have been set,
        # so this is needed to fix any which are using that default
        p = self.forms[0].params
        for i in range(len(p)):
            if p[i] == old_gradient:
                p[i] = self.get_gradient()
        
    def param_display_name(self,name,param):
        if hasattr(param,"title"):
            return param.title.value
        if hasattr(param,"caption"):
            return param.caption.value
        if name[:5] == "t__a_":
            name = name[5:]
        return name.title()

    def param_tip(self,name,param):
        if hasattr(param,"hint"):
            return param.hint.value
        return self.param_display_name(name,param)

    def loadFctFile(self,f):
        #old_gradient = self.get_gradient()
        line = f.readline()
        if line is None or not line.startswith("gnofract4d parameter file"):
            raise Exception("Not a valid parameter file")

        self.load(f)

        self.fix_bailout()
        #self.fix_gradients(old_gradient)
        self.saved = True
