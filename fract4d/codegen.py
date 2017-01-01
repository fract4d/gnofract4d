#!/usr/bin/env python3

# Generate C code from a linearized IR trace

import string
import tempfile
import copy
import os

import absyn
import ir
import re
import types

import optimize
import fracttypes

from fracttypes import Bool, Int, Float, Complex, Hyper, Color, IntArray, FloatArray, ComplexArray, VoidArray
from instructions import *
    
class Formatter:
    ' fed to print to fill the output template'
    def __init__(self, codegen, tree, lookup):
        self.codegen = codegen
        self.lookup = lookup
        self.tree = tree
    def __getitem__(self,key):
        try:
            out = self.tree.output_sections[key]
            str_output = "\n".join([x.format() for x in out])
            return str_output

        except KeyError as err:
            #print "missed %s" % key
            return self.lookup.get(key,"")

class T:
    'code generator'
    def __init__(self,symbols,options={}):
        self.symbols = symbols
        self.out = []
        self.optimize_flags = options.get("optimize",optimize.Nothing)
        # a list of templates and associated actions
        # this must be ordered with largest, most efficient templates first
        # thus performing a crude 'maximal munch' instruction generation
        self.templates = self.expand_templates([
            [ "Binop" , T.binop],
            [ "Unop", T.unop],
            [ "Call", T.call],
            [ "Var" , T.var],
            [ "Const", T.const],
            [ "Label", T.label],
            [ "Move", T.move],
            [ "Jump", T.jump],
            [ "CJump", T.cjump],
            [ "Cast", T.cast],
            ])
        
        self.generate_trace = False

        self.generate_trace = options.get("trace",False)
        self.log_z = options.get("tracez", False)
        
        self.output_template = '''
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

%(fract_stdlib)s
%(pf)s

typedef struct {
    pf_obj parent;
    struct s_param p[PF_MAXPARAMS];
    double pos_params[N_PARAMS];
    %(struct_members)s
} pf_real ;

#ifdef WIN32
#pragma comment(linker, "/EXPORT:_pf_new")
#endif

static void pf_init(
    struct s_pf_data *p_stub,
    double *pos_params,
    struct s_param *params,
    int nparams)
{
    pf_real *pfo = (pf_real *)p_stub;
    int i;
    
    if(nparams > PF_MAXPARAMS)
    {
        nparams = PF_MAXPARAMS;
    }
    for(i = 0; i < nparams; ++i)
    {
        pfo->p[i] = params[i];
        /* printf("param %%d = %%.17g\\n",i,params[i]); */
    }
    for(i = 0; i < N_PARAMS; ++i)
    {
        pfo->pos_params[i] = pos_params[i];
    }    
}

static void pf_get_defaults(
      // "object" pointer
      struct s_pf_data *t__p_stub,
      // in params
      double *pos_params,
      // out params
      struct s_param *params,
      // in param
      int nparams
    )
{
    pf_real *t__pfo = (pf_real *)t__p_stub;
    /*
    %(default)s
    %(return_syms)s
    */
}

static void pf_calc(
    // "object" pointer
    struct s_pf_data *t__p_stub,
    // in params
    const double *t__params, int maxiter, int t__warp_param, 
    // periodicity params
    int min_period_iter, double period_tolerance,
    // only used for debugging
    int t__p_x, int t__p_y, int t__p_aa,
    // out params
    int *t__p_pnIters, int *t__p_pFate, double *t__p_pDist, int *t__p_pSolid,
    int *t__p_pDirectColorFlag, double *t__p_pColors
    )
{
    pf_real *t__pfo = (pf_real *)t__p_stub;

    double pixel_re = t__params[0];
    double pixel_im = t__params[1];
    double t__h_zwpixel_re = t__params[2];
    double t__h_zwpixel_im = t__params[3];
    
    double t__h_index = 0.0;
    int t__h_solid = 0;
    int t__h_fate = 0;
    int t__h_inside = 0;
    double t__h_color_re = 0.0;
    double t__h_color_i = 0.0;
    double t__h_color_j = 0.0;
    double t__h_color_k = 0.0;
    
    *t__p_pDirectColorFlag = %(dca_init)s;
    
    if(t__warp_param != -1)
    {
        t__pfo->p[t__warp_param].doubleval = t__h_zwpixel_re;
        t__pfo->p[t__warp_param+1].doubleval = t__h_zwpixel_im;
        t__h_zwpixel_re = t__h_zwpixel_im = 0.0;
    }
    
    /* variable declarations */
    %(var_inits)s
    %(decl_period)s
    int t__h_numiter = 0;
    
    %(t_transform)s
    
    %(init)s
    
    %(init_inserts)s
    
    %(cf0_init)s
    %(cf1_init)s
    
    %(init_period)s
    do
    {
        %(loop)s
    
        %(loop_inserts)s
        %(bailout)s
    
        %(bailout_inserts)s
        if(!%(bailout_var)s) break;
        %(check_period)s
        %(cf0_loop)s
        %(cf1_loop)s
    
        t__h_numiter++;
    }while(t__h_numiter < maxiter);
    
    /* fate of 0 = escaped, 1 = trapped */
    t__h_inside = (t__h_numiter >= maxiter);
    *t__p_pFate = (t__h_numiter >= maxiter);

    loop_done:
    %(pre_final_inserts)s
    %(final)s
    %(done_inserts)s
    
    *t__p_pnIters = t__h_numiter;
    if(t__h_inside == 0)
    {
        %(cf0_final)s
            ;
    }
    else
    {
        %(cf1_final)s
            ;
    }
    *t__p_pFate = t__h_fate | (t__h_inside ? FATE_INSIDE : 0);
    *t__p_pDist = t__h_index;
    *t__p_pSolid = t__h_solid;
    %(save_colors)s
    %(return_inserts)s
    arena_clear((arena_t)(t__p_stub->arena));
    return;
}

static void pf_kill(
    struct s_pf_data *p_stub)
{
    arena_delete((arena_t)(p_stub->arena));
    free(p_stub);
}

static struct s_pf_vtable vtbl = 
{
    pf_get_defaults,
    pf_init,
    pf_calc,
    pf_kill
};

pf_obj *pf_new()
{
    pf_real *p = (pf_real *)malloc(sizeof(pf_real));
    if(!p) return NULL;
    p->parent.vtbl = &vtbl;
    p->parent.arena = arena_create(100000,1);
    return (pf_obj*)p;
}

%(main_inserts)s
'''

        # we insert pf.h so C compiler doesn't have to find it
        # this needs to be updated each time pf.h changes
        self.pf_header= '''
#ifndef PF_H_
#define PF_H_

/* C signature of point-funcs generated by compiler 
   
   This is essentially an opaque object with methods implemented in C. 
   Typical usage:

   //#pixel.re, #pixel.im, #z.re, #z.im 
   double pparams[] = { 1.5, 0.0, 0.0, 0.0};
   double initparams[] = {5.0, 2.0};
   int nItersDone=0;
   int nFate=0;
   double dist=0.0;
   int solid=0;
   pf_obj *pf = pf_new();
   pf->vtbl->init(pf,0.001,initparams,2);
   
   pf->vtbl->calc(
        pf,
        pparams,
        100,
        0,0,0,
        &nItersDone, &nFate, &dist, &solid);
   
   pf->vtbl->kill(pf);
*/

// maximum number of params which can be passed to init
#define PF_MAXPARAMS 200

// number of positional params used
#define N_PARAMS 11

/* the 'fate' of a point. This can be either
   Unknown (255) - not yet calculated
   N - reached an attractor numbered N (up to 30)
   N | FATE_INSIDE - did not escape
   N | FATE_SOLID - color with solid color 
   N | FATE_DIRECT - color with DCA
*/

typedef unsigned char fate_t;

#define FATE_UNKNOWN 255
#define FATE_SOLID 0x80
#define FATE_DIRECT 0x40
#define FATE_INSIDE 0x20

typedef enum
{
    INT = 0,
    FLOAT = 1,
    GRADIENT = 2,
    PARAM_IMAGE = 3
} e_paramtype;

struct s_param
{
    e_paramtype t;
    int intval;
    double doubleval;
    void *gradient;
    void *image;
};

struct s_pf_data;

struct s_pf_vtable {
    /* fill in params with the default values for this formula */
    void (*get_defaults)(
	struct s_pf_data *p,
	double *pos_params,
        struct s_param *params,
	int nparams
	);

    /* fill in fields in pf_data with appropriate stuff */
    void (*init)(
	struct s_pf_data *p,
	double *pos_params,
        struct s_param *params,
	int nparams
	);

    /* calculate one point.
       perform up to nIters iterations,
       return:
       number of iters performed in pnIters
       outcome in pFate: 0 = escaped, 1 = trapped. 
       More fates may be generated in future
       dist : index into color table from 0.0 to 1.0
    */
    void (*calc)(
	struct s_pf_data *p,
        // in params
        const double *params, int nIters, int warp_param, 
	// tolerance params
	int min_period_iter, double period_tolerance,
	// only used for debugging
	int x, int y, int aa,
        // out params
        int *pnIters, int *pFate, double *pDist, int *pSolid,
	int *pDirectColorFlag, double *pColors
	);
    /* deallocate data in p */
    void (*kill)(
	struct s_pf_data *p
	);
} ;

struct s_pf_data {
    struct s_pf_vtable *vtbl;
    void *arena;
} ;

typedef struct s_pf_vtable pf_vtable;
typedef struct s_pf_data pf_obj;



#ifdef __cplusplus
extern "C" {
#endif

/* create a new pf_obj.*/
extern pf_obj *pf_new(void);

#ifdef __cplusplus
}
#endif

#endif /* PF_H_ */
'''

        self.fract_stdlib_header = '''
#ifndef FRACT_STDLIB_H_
#define FRACT_STDLIB_H_

#ifdef __cplusplus
extern "C" {
#endif

    void fract_rand(double *re, double *im);

    typedef struct s_arena *arena_t;
    arena_t arena_create(int page_size, int max_pages);

    void arena_clear(arena_t arena);
    void arena_delete(arena_t arena);

    void *arena_alloc(
	arena_t arena, 
	int element_size, 
	int n_dimensions,
	int *n_elements);

    void array_get_int(
	void *allocation, int n_dimensions, int *indexes, 
	int *pRetVal, int *pInBounds);

    void array_get_double(
	void *allocation, int n_dimensions, int *indexes, 
	double *pRetVal, int *pInBounds);

    int array_set_int(
	void *allocation, int n_dimensions, int *indexes, int val);

    int array_set_double(
	void *allocation, int n_dimensions, int *indexes, double val);
    
    void *alloc_array1D(arena_t arena, int element_size, int size);
    void *alloc_array2D(arena_t arena, int element_size, int xsize, int ysize);
    void *alloc_array3D(arena_t arena, int element_size, int xsize, int ysize, int zsize);
    void *alloc_array4D(arena_t arena, int element_size, int xsize, int ysize, int zsize, int wsize);

    int read_int_array_1D(void *array, int x);
    int write_int_array_1D(void *array, int x, int val);

    int read_int_array_2D(void *array, int x, int y);
    int write_int_array_2D(void *array, int x, int y, int val);

    double read_float_array_1D(void *array, int x);
    int write_float_array_1D(void *array, int x, double val);

    double read_float_array_2D(void *array, int x, int y);
    int write_float_array_2D(void *array, int x, int y, double val);

#ifdef __cplusplus
}
#endif

#endif
'''
        

    def emit_binop(self,op,srcs,type):
        dst = self.newTemp(type)

        self.out.append(Binop(op, srcs ,[ dst ], self.generate_trace))
        return dst

    def emit_func(self,op,srcs,type):
        # emit a call to C stdlib function 'op'
        dst = self.newTemp(type)
        assem = "%(d0)s = " + op + "(%(s0)s);"
        self.out.append(Oper(assem, srcs, [dst]))
        return dst

    def emit_func2(self,op,srcs,type):
        # emit a call to C stdlib function 'op'
        dst = self.newTemp(type)
        assem = "%(d0)s = " + op + "(%(s0)s,%(s1)s);"
        self.out.append(Oper(assem, srcs, [dst]))
        return dst

    def emit_func3(self,op,srcs,type):
        # emit a call to a C func which takes 3 args and returns 1
        dst = self.newTemp(type)
        assem = "%(d0)s = " + op + "(%(s0)s,%(s1)s,%(s2)s);"
        self.out.append(Oper(assem,srcs, [dst]))
        return dst

    def emit_func_n(self,n,op,srcs,type):
        dst = self.newTemp(type)
        srcstrings = []
        for i in range(n):
            srcstrings.append("%%(s%d)s" % i)
            
        assem = "%(d0)s = " + op + "(" + ",".join(srcstrings) + ");"
        self.out.append(Oper(assem,srcs, [dst]))
        return dst
        
    def emit_func3_3(self,op,srcs,type):
        # emit a call to a C func which takes 3 args and returns 3 out params
        # This rather specialized feature is to call hls2rgb or image lookup
        dst = [
            self.newTemp(type),
            self.newTemp(type),
            self.newTemp(type)]
        assem = op + "(%(s0)s,%(s1)s,%(s2)s, &%(d0)s, &%(d1)s, &%(d2)s);"
        self.out.append(Oper(assem,srcs, dst))
        return dst

    def emit_func2_3(self,op,srcs,type):
        # take 2 objects and return 3, as in gradient func
        dst = [
            self.newTemp(type),
            self.newTemp(type),
            self.newTemp(type)]
        assem = op + "(%(s0)s,%(s1)s, &%(d0)s, &%(d1)s, &%(d2)s);"
        self.out.append(Oper(assem,srcs, dst))
        return dst

    def emit_func0_2(self,op,srcs,type):
        # take 0 objects and return 2, as in random()
        dst = [
            self.newTemp(type),
            self.newTemp(type)]
        assem = op + "(&%(d0)s, &%(d1)s);"
        self.out.append(Oper(assem,srcs, dst))
        return dst
        
    def emit_move(self, src, dst):
        self.out.append(Move([src],[dst], self.generate_trace))

    def emit_cjump(self, test,dst):
        assem = "if(%(s0)s) goto " + dst + ";"
        self.out.append(Oper(assem, [test], []))

    def emit_jump(self, dst):
        assem = "goto %s;" % dst
        self.out.append(Oper(assem,[],[],[dst]))

    def emit_label(self,name):
        self.out.append(Label(name))

    def get_gradient_var(self):
        temp_ir = ir.Var("@_gradient", absyn.Empty(0), fracttypes.Gradient)
        var = self.var(temp_ir)
        return var

    def is_direct(self):
        return self.symbols.has_user_key("#color")

    def decl_with_init_from_sym(self,sym):
        "Declare a variable for sym and initialize it"
        parts = sym.part_names
        vals = sym.init_val()
        decls = [None] * len(parts)
        for i in range(len(parts)):
            decls[i] = Decl(
                "%s %s%s = %s;"% (sym.ctype,sym.cname,parts[i],vals[i]))

        return decls

    def decl_from_sym(self,sym):
        """Declare a variable for sym"""
        parts = sym.part_names
        decls = [
            Decl("%s %s%s;" % (sym.ctype,sym.cname,part)) \
            for part in parts]
        return decls

    def return_sym(self,sym):
        "Code to return computed value of sym to C caller"
        initvals = sym.init_val()
        parts = sym.part_names
        returns = [None] * len(parts)
        for i in range(len(parts)):
            returns[i] = Move(
                [ Literal( sym.cname + parts[i])], [Literal(initvals[i]) ],
                self.generate_trace)

        return returns
            
            
    def output_symbol(self,key,sym,out,overrides):
        if not isinstance(sym,fracttypes.Var):
            return

        override = overrides.get(key)
        
        if override == None:
            out += self.decl_with_init_from_sym(sym)
        else:
            #print "override %s for %s" % (override, key)
            out.append(Decl(override))
        
    def output_decl(self,key,sym,out,overrides):
        if not isinstance(sym,fracttypes.Var):
            return
        
        override = overrides.get(key)
        if override == None:
            out += self.decl_from_sym(sym)
        else:
            #print "override %s for %s" % (override, key)
            out.append(Decl(override))

    def output_struct_members(self,ir,user_overrides):            
        overrides = {
            "t__h_zwpixel" : "",
            "pixel" : "",
            "t__h_numiter" : "",
            "t__h_index" : "",
            "maxiter" : "",
            "t__h_tolerance" : "",
            "t__h_solid" : "",
            "t__h_color" : "",
            "t__h_fate" : "",
            "t__h_inside" : ""            
            }
        
        for (k,v) in list(user_overrides.items()):
            overrides[k] = v
            
        out = []

        for (key,sym) in list(ir.symbols.items()):
            self.output_decl(key,sym,out,overrides)

        if hasattr(ir,"output_sections"):
            ir.output_sections["struct_members"] = out
        return out

    def output_local_vars(self,ir,user_overrides):
        overrides = {
            "t__h_zwpixel" : "",
            "pixel" : "",
            "t__h_numiter" : "",
            "t__h_index" : "",
            "maxiter" : "",
            "t__h_tolerance" :
            "double t__h_tolerance = period_tolerance;",
            "t__h_solid" : "",
            "t__h_color" : "",
            "t__h_fate" : "",
            "t__h_inside" : "",
            "t__h_magn" : \
                "double t__h_magn = log(4.0/t__pfo->pos_params[4])/log(2.0) + 1.0;",
            "t__h_center" : \
                """double t__h_center_re = t__pfo->pos_params[0];
                double t__h_center_im = t__pfo->pos_params[1];"""
            }
        
        for (k,v) in list(user_overrides.items()):
            #print "%s = %s" % (k,v)
            overrides[k] = v
            
        out = []
        for (key,sym) in list(ir.symbols.items()):
            self.output_symbol(key,sym,out,overrides)

        if hasattr(ir,"output_sections"):
            ir.output_sections["var_inits"] = out
                
        return out

    def output_return_syms(self,ir):
        out = []
        for key in sorted(ir.symbols):
            sym = ir.symbols[key]
            if self.symbols.is_param(key) and isinstance(sym,fracttypes.Var):
                out += self.return_sym(sym)

        if hasattr(ir,"output_sections"):
            ir.output_sections["return_syms"] = out

        return out
    
    def output_section(self,t,section):
        self.out = []
        #print "output: %s => %s" % ( \
        #    section,[x.pretty() for x in t.canon_sections[section]])
        self.generate_all_code(t.canon_sections[section])
        self.emit_label("t__end_%s%s" % (t.symbols.prefix, section))
        t.output_sections[section] = self.out
    
    def output_all(self,t):
        for k in list(t.canon_sections.keys()):
            self.output_section(t,k)

    def output_decls(self,t,overrides={}):
        # must be done after other sections or temps are missing
        self.output_local_vars(t,overrides)
        self.output_struct_members(t,overrides)
        self.output_return_syms(t)
        
    def get_bailout_var(self,t):
        return t.symbols["__bailout"].cname
    
    def output_c(self,t,inserts={},output_template=None):
        inserts["bailout_var"] = self.get_bailout_var(t)
        inserts["pf"] = self.pf_header
        inserts["fract_stdlib"] = self.fract_stdlib_header
        inserts["dca_init"] = "%d" % self.is_direct()

        if self.is_direct():
            inserts["save_colors"] = '''
            t__p_pColors[0] = t__h_color_re;
            t__p_pColors[1] = t__h_color_i;
            t__p_pColors[2] = t__h_color_j;
            t__p_pColors[3] = t__h_color_k;
            '''

        if self.log_z:
            inserts["init_inserts"] = 'printf("%d,%d,%.17g,%.17g : ", t__p_x, t__p_y, pixel_re, pixel_im);'
            inserts["loop_inserts"] = 'printf("%.17g,%.17g ",z_re, z_im);'
            inserts["done_inserts"] = 'printf("\\n");'
            
        # can only do periodicity if formula uses z
        if "z" in self.symbols.data:
            inserts["decl_period"] = '''
                double old_z_re;
                double old_z_im;
                int period_iters = 0;
                int save_mask = 9;
                int save_incr = 1;
                int next_save_incr = 4;
                '''
            inserts["init_period"] = '''
                old_z_re = z_re;
                old_z_im = z_im;'''

            inserts["check_period"] = '''
                if ( t__h_numiter >= min_period_iter)
                {
                    if( (t__h_numiter & save_mask) == 0)
                    {
                        /* save a value */
                        old_z_re = z_re;
                        old_z_im = z_im;

                        if(--save_incr == 0)
                        {
                            /* lengthen period check */
                            save_mask = (save_mask << 1) + 1;
                            save_incr = next_save_incr;
                        }
                    }
                    else
                    {
                        /* compare to an older value */
                        if ( (fabs(z_re - old_z_re) < period_tolerance)
                           &&(fabs(z_im - old_z_im) < period_tolerance))
                        {
                            period_iters = t__h_numiter;
                            //t__h_numiter = maxiter; 
                            t__h_inside = 1;
                            *t__p_pFate = 1;

                            goto loop_done;
                        }
                    }
                }
                '''
        else:
            inserts["decl_period"]=""
            inserts["init_period"]=""
            inserts["check_period"]=""
            
        f = Formatter(self,t,inserts)
        if output_template == None:
            output_template = self.output_template
        return output_template % f

    def writeToTempFile(self,data=None,suffix=""):
        (fileno,cFileName) = tempfile.mkstemp(suffix,"gf4d")
        cFile = os.fdopen(fileno,"w")

        if data != None:
            cFile.write(data)
        cFile.close()
        return cFileName

    def findOp(self,t):
        ' find the most appropriate overload for this op'
        overloadList = self.symbols[t.op]
        typelist = [n.datatype for n in t.children]
        try:
            for ol in overloadList:
                if ol.matchesArgs(typelist):
                    return ol
        except TypeError as err:
            print(overloadList)
            print(err)
            
        raise fracttypes.TranslationError(
            "Internal Compiler Error: Invalid argument types %s for %s" % \
            (typelist, t.op))

    def newTemp(self,type):
        return TempArg(self.symbols.newTemp(type),type)

    def temp(self,name,type):
        return TempArg(name,type)
    
    # action routines
    def cast(self,t):
        'Generate code to cast child of type child.datatype to t.datatype' 
        child = t.children[0]
        src = self.generate_code(child)

        dst = None
        if t.datatype == Complex:
            dst = ComplexArg(self.newTemp(Float),
                             self.newTemp(Float))
            if child.datatype == Int or child.datatype == Bool:
                assem = "%(d0)s = ((double)%(s0)s);"
                self.out.append(Oper(assem,[src], [dst.re]))
                assem = "%(d0)s = 0.0;"
                self.out.append(Oper(assem,[src], [dst.im]))
            elif child.datatype == Float:
                assem = "%(d0)s = %(s0)s;"
                self.out.append(Oper(assem,[src], [dst.re]))
                assem = "%(d0)s = 0.0;"
                self.out.append(Oper(assem,[src], [dst.im]))
        elif t.datatype == Float:
            if child.datatype == Int or child.datatype == Bool:
                dst = self.newTemp(Float)
                assem = "%(d0)s = ((double)%(s0)s);" 
                self.out.append(Oper(assem,[src], [dst]))
        elif t.datatype == Int:
            if child.datatype == Bool:
                # needn't do anything
                dst = src
        elif t.datatype == Bool:
            dst = self.newTemp(Bool)
            if child.datatype == Int or child.datatype == Bool:
                assem = "%(d0)s = (%(s0)s != 0);"
                self.out.append(Oper(assem,[src], [dst]))
            elif child.datatype == Float:
                assem = "%(d0)s = (%(s0)s != 0.0);"
                self.out.append(Oper(assem,[src], [dst]))
            elif child.datatype == Complex:
                assem = "%(d0)s = ((%(s0)s != 0.0) || (%(s1)s != 0.0));"
                self.out.append(Oper(assem,[src.re, src.im], [dst]))
            else:
                dst = None
        elif t.datatype == Hyper or t.datatype == Color:
            dst = HyperArg(self.newTemp(Float),
                           self.newTemp(Float),
                           self.newTemp(Float),
                           self.newTemp(Float))
            if child.datatype == Int or \
                   child.datatype == Bool or child.datatype == Float:
                assem = "%(d0)s = ((double)%(s0)s);"
                self.out.append(Oper(assem,[src], [dst.parts[0]]))
                assem = "%(d0)s = 0.0;"
                for i in range(1,4):
                    self.out.append(Oper(assem,[src], [dst.parts[i]]))
            elif child.datatype == Complex:
                assem = "%(d0)s = ((double)%(s0)s);"
                self.out.append(Oper(assem,[src.re], [dst.parts[0]]))
                self.out.append(Oper(assem,[src.im], [dst.parts[1]]))
                assem = "%(d0)s = 0.0;"
                self.out.append(Oper(assem,[src], [dst.parts[2]]))
                self.out.append(Oper(assem,[src], [dst.parts[3]]))
            else:
                dst = None
        elif t.datatype == IntArray or t.datatype == FloatArray or t.datatype == ComplexArray:
            if child.datatype == VoidArray:
                if t.datatype == IntArray:
                    cast = "(int *)"
                else:
                    cast = "(double *)"
                assem = "%%(d0)s = (%s%%(s0)s);" % cast
                dst = self.newTemp(t.datatype)
                self.out.append(Oper(assem, [src], [dst]))
                
        if dst == None:
            msg = "%d: Invalid Cast from %s to %s" % \
                  (t.node.pos,fracttypes.strOfType(child.datatype),
                   fracttypes.strOfType(t.datatype))
            raise fracttypes.TranslationError(msg)
        
        return dst
                
    def move(self,t):
        dst = self.generate_code(t.children[0])
        src = self.generate_code(t.children[1])
        if t.datatype == Complex:
            self.emit_move(src.re,dst.re)
            self.emit_move(src.im,dst.im)
        elif t.datatype == Hyper or t.datatype == Color:
            for i in range(4):
                self.emit_move(src.parts[i],dst.parts[i])
        else:
            self.emit_move(src,dst)
        return dst
    
    def label(self,t):
        assert(t.children == [])
        self.emit_label(t.name)

    def cjump(self,t):
        # canonicalize has ensured we fall through to false branch,
        # so we can just deal with true case
        binop = ir.Binop(t.op,t.children,t.node,Bool)
        result = self.binop(binop)
        self.emit_cjump(result,t.trueDest)
        
    def jump(self,t):
        self.emit_jump(t.dest)

    def unop(self,t):
        s0 = t.children[0]
        src = self.generate_code(s0)
        op = self.findOp(t)
        dst = op.genFunc(self, t, [src])
        return dst

    def call(self,t):
        srcs = [self.generate_code(x) for x in t.children]
        op = self.findOp(t)
        try:
            dst = op.genFunc(self, t, srcs)
        except TypeError as err:
            msg = "Internal Compiler Error: missing stdlib function %s" % \
                  op.genFunc
            raise fracttypes.TranslationError(msg)
        
        return dst
        
    def binop(self,t):
        s0 = t.children[0]
        s1 = t.children[1]
        srcs = [self.generate_code(s0), self.generate_code(s1)]
        op = self.findOp(t)
        try:
            dst = op.genFunc(self,t,srcs)
        except TypeError as err:
            msg = "Internal Compiler Error: missing stdlib function %s" % \
                  op.genFunc
            print(msg)
            raise fracttypes.TranslationError(msg)
        return dst
    
    def const(self,t):
        return create_arg(t)
    
    def var(self,t):
        name = self.symbols.realName(t.name)
        if t.datatype == fracttypes.Complex:
            return ComplexArg(
                self.temp(name + "_re", fracttypes.Float),
                self.temp(name + "_im", fracttypes.Float))
        elif t.datatype == fracttypes.Hyper or t.datatype == fracttypes.Color:
            return HyperArg(
                self.temp(name + "_re", fracttypes.Float),
                self.temp(name + "_i", fracttypes.Float),
                self.temp(name + "_j", fracttypes.Float),
                self.temp(name + "_k", fracttypes.Float))
        else:
            return self.temp(name,t.datatype)
    
    # matching machinery
    def generate_all_code(self,treelist):
        for tree in treelist:
            self.generate_code(tree)
        self.optimize(self.optimize_flags)
        
    def generate_code(self,tree):
        action = self.match(tree)
        return action(*(self,tree))

    def expand_templates(self,list):
        return [[self.expand(x[0]), x[1]] for x in list]

    def expand(self, template):
        return eval(re.sub(r'(\w+)',r'ir.\1',template))

    # implement naive tree matching. We match an ir tree against a
    # nested list of classes
    def match_template(self, tree, template):
        if isinstance(template,list):
            object = template[0]
            children = template[1:]

            if not isinstance(tree, object):
                return 0
        
            for (child, matchChild) in zip(tree.children,children):
                if not self.match_template(child,matchChild):
                    return 0
                
            return 1
        else:
            return isinstance(tree, template)
        
    def optimize(self, flags):
        optimizer = optimize.T()
        self.out = optimizer.optimize(flags, self.out)
    
    def match(self,tree):
        for (template,action) in self.templates:
            if self.match_template(tree,template):
                return action
        
        # every possible tree ought to be matched by *something* 
        msg = "Internal Compiler Error:%d:unmatched tree %s" % (tree.node.pos,tree)
        raise fracttypes.TranslationError(msg)

        
