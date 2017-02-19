/* Wrappers around C++ functions so they can be called from python The
   C code starts one or more non-Python threads which work out which
   points to calculate, and call the dynamically-compiled pointfunc C
   code created by the compiler for each pixel. 

   Results are reported back through a site object. There are 2 kinds,
   a synchronous site which calls back into python (used by
   command-line fractal.py script) and an async site which wraps a
   file descriptor into which we write simple messages. The GTK+ main
   loop then listens to the FD and performs operations in response to
   messages written to the file descriptor.
*/

#include "Python.h"

#include <dlfcn.h>
#include <pthread.h>

#include "assert.h"

#include <new>

#include "fract_stdlib.h"
#include "pf.h"
#include "cmap.h"
#include "fractFunc.h"
#include "image.h"


/* not sure why this isn't defined already */
#ifndef PyMODINIT_FUNC 
#define PyMODINIT_FUNC void
#endif

#define CMAP_NAME "/fract4d_stdlib.cpython-35m-x86_64-linux-gnu.so"

#ifdef USE_GMP
#define MODULE_NAME "fract4dcgmp"
#include "gmp.h"
#else
#define MODULE_NAME "fract4dc"
#endif

struct module_state {
    int dummy;
};

// really should be in module_state - one day
void *cmap_module_handle=NULL;

typedef enum {
    DELTA_X,
    DELTA_Y,
    TOPLEFT
} vec_type_t;


#define OBTYPE_MODULE "module"
#define OBTYPE_POINTFUNC "pf"
#define OBTYPE_CMAP "cmap"
#define OBTYPE_IMAGE "image"
#define OBTYPE_SITE "site"
#define OBTYPE_WORKER "worker"
#define OBTYPE_IMAGE_WRITER "image_writer"
#define OBTYPE_FFH "ffh"
#define OBTYPE_ARENA "arena"

static void *
module_fromcapsule(PyObject *p)
{
    void *vp = PyCapsule_GetPointer(p, OBTYPE_MODULE);
    if(NULL == vp)
    {
	fprintf(stderr,"%p : SO : BAD\n",p);
    }
    
    return vp;
}

static ImageWriter *
image_writer_fromcapsule(PyObject *p)
{
    ImageWriter *iw = (ImageWriter *)PyCapsule_GetPointer(p, OBTYPE_IMAGE_WRITER);
    if(NULL == iw)
    {
	fprintf(stderr,"%p : IW : BAD\n",p);
    }
    
    return iw;
}

static arena_t
arena_fromcapsule(PyObject *p)
{
    arena_t arena = (arena_t)PyCapsule_GetPointer(p,OBTYPE_ARENA);
    if(NULL == arena)
    {
	fprintf(stderr,"%p : AR : BAD\n",p);
    }
    
    return arena;
}

static void
module_unload(PyObject *p)
{
    void *vp = module_fromcapsule(p);
#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : SO : CLOSE\n",vp);
#endif

#ifndef STATIC_CALC
    dlclose(vp);
#endif
}

static int 
ensure_cmap_loaded(PyObject *pymod)
{
    char cwd[PATH_MAX+1];
    // load the cmap module so fract funcs we compile later
    // can call its methods
    if(NULL != cmap_module_handle)
    {
	return 1; // already loaded
    }

    // get location of current .so, fract4d_stdlib is in same dir
    const char *filename = NULL; 
    Dl_info dl_info;
    int result = dladdr((void *)ensure_cmap_loaded, &dl_info);
    if(!result)
    {
	fprintf(stderr, "Cannot determine filename of current library\n");
	return 0;
    }
    filename = dl_info.dli_fname;

    if(NULL == filename)
    {
	fprintf(stderr, "NULL filename of current library\n");
	return 0;
    }

    //fprintf(stderr,"base name: %s\n",filename);
    
    const char *path_end = strrchr(filename,'/');

    if (path_end == NULL)
    {
	filename = getcwd(cwd,sizeof(cwd));
	path_end = filename + strlen(filename);
    }
    
    int path_len = strlen(filename) - strlen(path_end);
    int len = path_len + strlen(CMAP_NAME);

    char *new_filename = (char *)malloc(len+1);
    strncpy(new_filename, filename, path_len);
    new_filename[path_len] = '\0';

    strcat(new_filename, CMAP_NAME);
    //fprintf(stderr,"Filename: %s\n", new_filename);

    cmap_module_handle = dlopen(new_filename, RTLD_GLOBAL | RTLD_NOW);
    if(NULL == cmap_module_handle)
    {
	/* an error */
	PyErr_SetString(PyExc_ValueError, dlerror());
	return 0;
    }
    return 1;
}

static PyObject *
module_load(PyObject *self, PyObject *args)
{
    #ifdef STATIC_CALC
    Py_INCREF(Py_None);
    return Py_None;
    #else

    char *so_filename;
    if(!PyArg_ParseTuple(args,"s",&so_filename))
    {
	return NULL;
    }

    void *dlHandle = dlopen(so_filename, RTLD_NOW);
#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : SO : REF\n",dlHandle);
#endif
    if(NULL == dlHandle)
    {
	/* an error */
	PyErr_SetString(PyExc_ValueError,dlerror());
	return NULL;
    }
    return PyCapsule_New(dlHandle, OBTYPE_MODULE, module_unload);
    #endif
}

struct pfHandle
{
    PyObject *pyhandle;
    pf_obj *pfo;
} ;

static struct pfHandle*
pf_fromcapsule(PyObject *capsule)
{
    struct pfHandle *pfHandle = (struct pfHandle *)PyCapsule_GetPointer(capsule, OBTYPE_POINTFUNC);
    if(NULL == pfHandle)
    {
fprintf(stderr, "%p : PF : BAD\n", capsule);
    }
return pfHandle;
}

static void
pf_delete(PyObject *p)
{
struct pfHandle *pfh = pf_fromcapsule(p);
#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : PF : DTOR\n",pfh);
#endif
    pfh->pfo->vtbl->kill(pfh->pfo);
    Py_DECREF(pfh->pyhandle);
    free(pfh);
}

static PyObject *
pf_create(PyObject *self, PyObject *args)
{
    struct pfHandle *pfh = (pfHandle *)malloc(sizeof(struct pfHandle));
    void *dlHandle;
    pf_obj *(*pfn)(void); 

    PyObject *pyobj;
#ifdef STATIC_CALC
    pf_obj *p = pf_new();
    pyobj = Py_None;
#else

    if(!PyArg_ParseTuple(args,"O",&pyobj))
    {
	return NULL;
    }
    if(!PyCapsule_CheckExact(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    dlHandle = module_fromcapsule(pyobj);
    pfn = (pf_obj *(*)(void))dlsym(dlHandle,"pf_new");
    if(NULL == pfn)
    {
	PyErr_SetString(PyExc_ValueError,dlerror());
	return NULL;
    }
    pf_obj *p = pfn();
#endif
    pfh->pfo = p;
    pfh->pyhandle = pyobj;
#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : PF : CTOR (%p)\n",pfh,pfh->pfo);
#endif
    // refcount module so it can't be unloaded before all funcs are gone
    Py_INCREF(pyobj); 
    return PyCapsule_New(pfh, OBTYPE_POINTFUNC,pf_delete);
}

void *
get_double_field(PyObject *pyitem, const char *name, double *pVal)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem,name);
    if(pyfield == NULL)
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	return NULL;
    }
    *pVal = PyFloat_AsDouble(pyfield);
    Py_DECREF(pyfield);

    return pVal;
}

/* member 'name' of pyitem is a N-element list of doubles */
void *
get_double_array(PyObject *pyitem, const char *name, double *pVal, int n)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem,name);
    if(pyfield == NULL)
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	return NULL;
    }

    if(!PySequence_Check(pyfield))
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	Py_DECREF(pyfield);
	return NULL;
    }

    if(!(PySequence_Size(pyfield) == n))
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	Py_DECREF(pyfield);
	return NULL;
    }

    for(int i = 0; i < n; ++i)
    {
	PyObject *py_subitem = PySequence_GetItem(pyfield,i);
	if(!py_subitem)
	{
	    PyErr_SetString(PyExc_ValueError, "Bad segment object");
	    Py_DECREF(pyfield);
	    return NULL; 
	}
	*(pVal+i)=PyFloat_AsDouble(py_subitem);

	Py_DECREF(py_subitem);
    }

    Py_DECREF(pyfield);

    return pVal;
}

void *
get_int_field(PyObject *pyitem, const char *name, int *pVal)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem,name);
    if(pyfield == NULL)
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	return NULL;
    }
    *pVal = PyLong_AsLong(pyfield);
    Py_DECREF(pyfield);

    return pVal;
}

static ColorMap *
cmap_from_pyobject(PyObject *pyarray)
{
    int len, i;
    GradientColorMap *cmap;

    len = PySequence_Size(pyarray);
    if(len == 0)
    {
	PyErr_SetString(PyExc_ValueError,"Empty color array");
	return NULL;
    }

    cmap = new(std::nothrow)GradientColorMap();

    if(!cmap)
    {
	PyErr_SetString(PyExc_MemoryError,"Can't allocate colormap");
	return NULL;
    }
    if(! cmap->init(len))
    {
	PyErr_SetString(PyExc_MemoryError,"Can't allocate colormap array");
	delete cmap;
	return NULL;
    }

    for(i = 0; i < len; ++i)
    {
	double left, right, mid, left_col[4], right_col[4];
	int bmode, cmode;
	PyObject *pyitem = PySequence_GetItem(pyarray,i);
	if(!pyitem)
	{
	    delete cmap;
	    return NULL; 
	}

	if(!get_double_field(pyitem, "left", &left) ||
	   !get_double_field(pyitem, "right", &right) ||
	   !get_double_field(pyitem, "mid", &mid) ||
	   !get_int_field(pyitem, "cmode", &cmode) ||
	   !get_int_field(pyitem, "bmode", &bmode) ||
	   !get_double_array(pyitem, "left_color", left_col, 4) ||
	   !get_double_array(pyitem, "right_color", right_col, 4))
	{
	    Py_DECREF(pyitem);
	    delete cmap;
	    return NULL;
	}
	
	cmap->set(i, left, right, mid,
		  left_col,right_col,
		  (e_blendType)bmode, (e_colorType)cmode);

	Py_DECREF(pyitem);
    }
    return cmap;
}

static ColorMap *
cmap_fromcapsule(PyObject *capsule)
{
    ColorMap *cmap = (ColorMap *)PyCapsule_GetPointer(capsule, OBTYPE_CMAP);
    if (NULL == cmap)
    {
	fprintf(stderr, "%p : CM : BAD", capsule);
    }
    return cmap;
}

static void
pycmap_delete(PyObject *capsule)
{
    ColorMap *cmap = cmap_fromcapsule(capsule);    
    cmap_delete(cmap);
}

static PyObject *
cmap_create_gradient(PyObject *self, PyObject *args)
{
    /* args = a gradient object:
       an array of objects with:
       float: left,right,mid 
       int: bmode, cmode
       [f,f,f,f] : left_color, right_color
    */
    PyObject *pyarray, *pyret;

    if(!PyArg_ParseTuple(args,"O",&pyarray))
    {
	return NULL;
    }

    if(!PySequence_Check(pyarray))
    {
	return NULL;
    }
    
    ColorMap *cmap = cmap_from_pyobject(pyarray);

    if(NULL == cmap)
    {
	return NULL;
    }

    pyret = PyCapsule_New(cmap,OBTYPE_CMAP, pycmap_delete);

    return pyret;
}

static bool
parse_posparams(PyObject *py_posparams, double *pos_params)
{
    // check and parse pos_params
    if(!PySequence_Check(py_posparams))
    {
	PyErr_SetString(PyExc_TypeError,
			"Positional params should be an array of floats");
	return false;
    }

    int len = PySequence_Size(py_posparams);
    if(len != N_PARAMS)
    {
	PyErr_SetString(
	    PyExc_ValueError,
	    "Wrong number of positional params");
	return false;
    }
    
    for(int i = 0; i < N_PARAMS; ++i)
    {
	PyObject *pyitem = PySequence_GetItem(py_posparams,i);
	if(pyitem == NULL || !PyFloat_Check(pyitem))
	{
	    PyErr_SetString(
		PyExc_ValueError,
		"All positional params must be floats");
	    return false;
	}
	pos_params[i] = PyFloat_AsDouble(pyitem);
    }
    return true;
}

static s_param *
parse_params(PyObject *pyarray, int *plen)
{
    struct s_param *params;

    // check and parse fractal params
    if(!PySequence_Check(pyarray))
    {
	PyErr_SetString(PyExc_TypeError,
			"parameters argument should be an array");
	return NULL;
    }


    int len = PySequence_Size(pyarray);
    if(len == 0)
    {
	params = (struct s_param *)malloc(sizeof(struct s_param));
	params[0].t = FLOAT;
	params[0].doubleval = 0.0;
    }
    else if(len > PF_MAXPARAMS)
    {
	PyErr_SetString(PyExc_ValueError,"Too many parameters");
	return NULL;
    }
    else
    {
	int i = 0;
	params = (struct s_param *)malloc(len * sizeof(struct s_param));
	if(!params) return NULL;
	for(i = 0; i < len; ++i)
	{
	    PyObject *pyitem = PySequence_GetItem(pyarray,i);
	    if(NULL == pyitem)
	    {
		free(params);
		return NULL;
	    }
	    if(PyFloat_Check(pyitem))
	    {
		params[i].t = FLOAT;
		params[i].doubleval = PyFloat_AsDouble(pyitem);
		//fprintf(stderr,"%d = float(%g)\n",i,params[i].doubleval);
	    }
	    else if(PyLong_Check(pyitem))
	    {
		params[i].t = INT;
		params[i].intval = PyLong_AS_LONG(pyitem);
		//fprintf(stderr,"%d = int(%d)\n",i,params[i].intval);
	    }
	    else if(
		PyObject_HasAttrString(pyitem,"cobject") &&
		PyObject_HasAttrString(pyitem,"segments"))
	    {
		// looks like a colormap. Either we already have an object, which we can use now,
		// or we need to construct one from a list of segments
		PyObject *pycob = PyObject_GetAttrString(pyitem,"cobject");
		if(pycob == Py_None || pycob == NULL)
		{
		    Py_XDECREF(pycob);
		    PyObject *pysegs = PyObject_GetAttrString(
			pyitem,"segments");

		    ColorMap *cmap;
		    if (pysegs == Py_None || pysegs == NULL)
		    {
			cmap = NULL;
		    }
		    else
		    {
			cmap = cmap_from_pyobject(pysegs);
		    }
		    
		    Py_XDECREF(pysegs);

		    if(NULL == cmap)
		    {
			PyErr_SetString(PyExc_ValueError, "Invalid colormap object");
			free(params);
			return NULL;
		    }

		    pycob = PyCapsule_New(cmap, OBTYPE_CMAP, pycmap_delete);

		    if(NULL != pycob)
		    {
			PyObject_SetAttrString(pyitem,"cobject",pycob);
			// not quite correct, we are leaking some
			// cmap objects 
			Py_INCREF(pycob);
		    }
		}
		params[i].t = GRADIENT;
		params[i].gradient = cmap_fromcapsule(pycob);
		//fprintf(stderr,"%d = gradient(%p)\n",i,params[i].gradient);
		Py_XDECREF(pycob);
	    }
	    else if(
		PyObject_HasAttrString(pyitem,"_img"))
	    {
		PyObject *pycob = PyObject_GetAttrString(pyitem,"_img");
		params[i].t = PARAM_IMAGE;
		params[i].image = PyCapsule_GetPointer(pycob,OBTYPE_IMAGE);
		Py_XDECREF(pycob);
	    }
	    else
	    {
		Py_XDECREF(pyitem);
		PyErr_SetString(
		    PyExc_ValueError,
		    "All params must be floats, ints, images or gradients");
		free(params);
		return NULL;
	    }
	    Py_XDECREF(pyitem);
	} 
    }
    *plen = len;
    return params;
}

static PyObject *
pf_init(PyObject *self, PyObject *args)
{
    PyObject *pyobj, *pyarray, *py_posparams;
    struct s_param *params;
    struct pfHandle *pfh;
    double pos_params[N_PARAMS];

    if(!PyArg_ParseTuple(
	   args,"OOO",&pyobj,&py_posparams, &pyarray))
    {
	return NULL;
    }
    if(!PyCapsule_CheckExact(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    pfh = pf_fromcapsule(pyobj);

    if(!parse_posparams(py_posparams, pos_params))
    {
	return NULL;
    }

    int len=0;
    params = parse_params(pyarray,&len);
    if(!params)
    {
	return NULL;
    }

    /*finally all args are assembled */
    pfh->pfo->vtbl->init(pfh->pfo,pos_params,params,len);
    free(params);

    Py_INCREF(Py_None);
    return Py_None;
}

/* convert an array of params from the s_param representation 
   to a Python list */

static PyObject *
params_to_python(struct s_param *params, int len)
{
    PyObject *pyret = PyList_New(len);
    if(!pyret)
    {
	PyErr_SetString(PyExc_MemoryError, "Can't allocate defaults list");
	return NULL;
    }
    for(int i = 0; i < len; ++i)
    {
	switch(params[i].t)
	{
	case FLOAT:
	    PyList_SET_ITEM(pyret,i,PyFloat_FromDouble(params[i].doubleval));
	    break;
	case INT:
	    PyList_SET_ITEM(pyret,i,PyLong_FromLong(params[i].intval));
	    break;
	case GRADIENT:
	    Py_INCREF(Py_None);
	    PyList_SET_ITEM(pyret,i,Py_None);
	    break;
	default:
	    assert(0 && "Unexpected type for parameter");
	    Py_INCREF(Py_None);
	    PyList_SET_ITEM(pyret,i,Py_None);
	}
    }
    return pyret;
}

static PyObject *
pf_defaults(PyObject *self, PyObject *args)
{
    PyObject *pyobj, *pyarray, *py_posparams;
    struct s_param *params;
    struct pfHandle *pfh;
    double pos_params[N_PARAMS];

    if(!PyArg_ParseTuple(
	   args,"OOO",&pyobj,&py_posparams, &pyarray))
    {
	return NULL;
    }
    if(!PyCapsule_CheckExact(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    pfh = pf_fromcapsule(pyobj);

    if(!parse_posparams(py_posparams, pos_params))
    {
	return NULL;
    }

    int len=0;
    params = parse_params(pyarray,&len);
    if(!params)
    {
	return NULL;
    }

    /*finally all args are assembled */
    pfh->pfo->vtbl->get_defaults(
	pfh->pfo,
	pos_params,
	params,
	len);
    

    PyObject *pyret = params_to_python(params,len);
    free(params);

    return pyret;
}

static PyObject *
pf_calc(PyObject *self, PyObject *args)
{
    PyObject *pyobj, *pyret;
    double params[4];
    struct pfHandle *pfh; 
    int nIters, x=0,y=0,aa=0;
    int repeats = 1;
    int outIters=0, outFate=-777;
    double outDist=0.0;
    int outSolid=0;
    int fDirectColorFlag=0;
    double colors[4] = {0.0, 0.0, 0.0, 0.0};

    if(!PyArg_ParseTuple(args,"O(dddd)i|iiii",
			 &pyobj,
			 &params[0],&params[1],&params[2],&params[3],
			 &nIters,&x,&y,&aa,&repeats))
    {
	return NULL;
    }
    if(!PyCapsule_CheckExact(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    pfh = pf_fromcapsule(pyobj);
#ifdef DEBUG_THREADS
    fprintf(stderr,"%p : PF : CALC\n",pfh);
#endif
    for(int i = 0; i < repeats; ++i)
    {
	pfh->pfo->vtbl->calc(
	    pfh->pfo,params,
	    nIters, -1, 
	    nIters, 1.0E-9,
	    x,y,aa,
	    &outIters,&outFate,&outDist,&outSolid,
	    &fDirectColorFlag, &colors[0]);
    }
    assert(outFate != -777);
    pyret = Py_BuildValue("iidi",outIters,outFate,outDist,outSolid);
    return pyret; // Python can handle errors if this is NULL
}

/* 
 * cmaps
 */
static PyObject *
cmap_create(PyObject *self, PyObject *args)
{
    /* args = an array of (index,r,g,b,a) tuples */
    PyObject *pyarray, *pyret;
    int len, i;
    ListColorMap *cmap;

    if(!PyArg_ParseTuple(args,"O",&pyarray))
    {
	return NULL;
    }

    if(!PySequence_Check(pyarray))
    {
	return NULL;
    }
    
    len = PySequence_Size(pyarray);
    if(len == 0)
    {
	PyErr_SetString(PyExc_ValueError,"Empty color array");
	return NULL;
    }

    cmap = new(std::nothrow)ListColorMap();

    if(!cmap)
    {
	PyErr_SetString(PyExc_MemoryError,"Can't allocate colormap");
	return NULL;
    }
    if(! cmap->init(len))
    {
	PyErr_SetString(PyExc_MemoryError,"Can't allocate colormap array");
	delete cmap;
	return NULL;
    }
    for(i = 0; i < len; ++i)
    {
	double d;
	int r, g, b, a;
	PyObject *pyitem = PySequence_GetItem(pyarray,i);
	if(!pyitem)
	{
	    delete cmap;
	    return NULL; 
	}
	if(!PyArg_ParseTuple(pyitem,"diiii",&d,&r,&g,&b,&a))
	{
	    Py_DECREF(pyitem);
	    delete cmap;
	    return NULL;
	}
	cmap->set(i,d,r,g,b,a);
	Py_DECREF(pyitem);
    }
    pyret = PyCapsule_New(cmap, OBTYPE_CMAP, pycmap_delete);

    return pyret;
}

static PyObject *
pycmap_set_solid(PyObject *self, PyObject *args)
{
    PyObject *pycmap;
    int which,r,g,b,a;
    ColorMap *cmap;

    if(!PyArg_ParseTuple(args,"Oiiiii",&pycmap,&which,&r,&g,&b,&a))
    {
	return NULL;
    }

    cmap = cmap_fromcapsule(pycmap);
    if(!cmap)
    {
	return NULL;
    }

    cmap->set_solid(which,r,g,b,a);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
pycmap_set_transfer(PyObject *self, PyObject *args)
{
    PyObject *pycmap;
    int which;
    e_transferType transfer;
    ColorMap *cmap;

    if(!PyArg_ParseTuple(args,"Oii",&pycmap,&which,&transfer))
    {
	return NULL;
    }

    cmap = cmap_fromcapsule(pycmap);
    if(!cmap)
    {
	return NULL;
    }

    cmap->set_transfer(which,transfer);

    Py_INCREF(Py_None);
    return Py_None;
}
 
static PyObject *
cmap_pylookup(PyObject *self, PyObject *args)
{
    PyObject *pyobj, *pyret;
    double d;
    rgba_t color;
    ColorMap *cmap;

    if(!PyArg_ParseTuple(args,"Od", &pyobj, &d))
    {
	return NULL;
    }

    cmap = cmap_fromcapsule(pyobj);
    if(!cmap)
    {
	return NULL;
    }

    color = cmap->lookup(d);
    
    pyret = Py_BuildValue("iiii",color.r,color.g,color.b,color.a);

    return pyret;
}

static PyObject *
cmap_pylookup_with_flags(PyObject *self, PyObject *args)
{
    PyObject *pyobj, *pyret;
    double d;
    rgba_t color;
    ColorMap *cmap;
    int inside;
    int solid;

    if(!PyArg_ParseTuple(args,"Odii", &pyobj, &d, &solid, &inside))
    {
	return NULL;
    }

    cmap = cmap_fromcapsule(pyobj);
    if(!cmap)
    {
	return NULL;
    }

    color = cmap->lookup_with_transfer(d,solid,inside);
    
    pyret = Py_BuildValue("iiii",color.r,color.g,color.b,color.a);

    return pyret;
}

#ifdef THREADS
#define GET_LOCK PyGILState_STATE gstate; gstate = PyGILState_Ensure()
#define RELEASE_LOCK PyGILState_Release(gstate)
#else
#define GET_LOCK
#define RELEASE_LOCK
#endif

class PySite :public IFractalSite
{
public:
    PySite(PyObject *site_)
	{
	    site = site_;

	    has_pixel_changed_method = 
		PyObject_HasAttrString(site,"pixel_changed");

#ifdef DEBUG_CREATION
	    fprintf(stderr,"%p : SITE : CTOR\n",this);
#endif

	    // Don't incref, that causes a loop with parent fractal
	    //Py_INCREF(site);
	}

    virtual void iters_changed(int numiters)
	{
	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		const_cast<char *>("iters_changed"),
		const_cast<char *>("i"),
		numiters);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}
    
    virtual void tolerance_changed(double tolerance)
	{
	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		const_cast<char *>("tolerance_changed"),
		const_cast<char *>("d"),
		tolerance);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}
    // we've drawn a rectangle of image
    virtual void image_changed(int x1, int y1, int x2, int y2)
	{
	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		const_cast<char *>("image_changed"),
		const_cast<char *>("iiii"),
		x1,y1,x2,y2);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}
    // estimate of how far through current pass we are
    virtual void progress_changed(float progress)
	{
	    double d = (double)progress;

	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		const_cast<char *>("progress_changed"),
		const_cast<char *>("d"),
		d);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}

    virtual void stats_changed(pixel_stat_t& stats)
	{
	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		const_cast<char *>("stats_changed"),
		const_cast<char *>("[kkkkkkkkkk]"),
		stats.s[0], stats.s[1], stats.s[2],stats.s[3],stats.s[4],
		stats.s[5], stats.s[6], stats.s[7],stats.s[8],stats.s[9]);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;			
	}

    // one of the status values above
    virtual void status_changed(int status_val)
	{
	    assert(this != NULL && site != NULL);
	    //fprintf(stderr,"sc: %p %p\n",this,this->status_changed_cb);

	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		const_cast<char *>("status_changed"),
		const_cast<char *>("i"), 
		status_val);

	    if(PyErr_Occurred())
	    {
		fprintf(stderr,"bad status 2\n");
		PyErr_Print();
	    }
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}

    // return true if we've been interrupted and are supposed to stop
    virtual bool is_interrupted()
	{
	    GET_LOCK;
	    PyObject *pyret = PyObject_CallMethod(
		site,
		const_cast<char *>("is_interrupted"),NULL);

	    bool ret = false;
	    if(pyret != NULL && PyLong_Check(pyret))
	    {
		long i = PyLong_AsLong(pyret);
		//fprintf(stderr,"ret: %ld\n",i);
		ret = (i != 0);
	    }

	    Py_XDECREF(pyret);
	    RELEASE_LOCK;
	    return ret;
	}

    // pixel changed
    virtual void pixel_changed(
	const double *params, int maxIters, int nNoPeriodIters,
	int x, int y, int aa,
	double dist, int fate, int nIters,
	int r, int g, int b, int a) 
	{
	    if(has_pixel_changed_method)
	    {
		GET_LOCK;
		PyObject *pyret = PyObject_CallMethod(
		    site,
		    const_cast<char *>("pixel_changed"),
		    const_cast<char *>("(dddd)iiiiidiiiiii"),
		    params[0],params[1],params[2],params[3],
		    x,y,aa,
		    maxIters,nNoPeriodIters,
		    dist,fate,nIters,
		    r,g,b,a);

		Py_XDECREF(pyret);
		RELEASE_LOCK;
	    }
	};
    virtual void interrupt() 
	{
	    // FIXME? interrupted = true;
	}
    
    virtual void start(pthread_t tid_) 
	{
	    tid = tid_;
	}

    virtual void wait()
	{
	    pthread_join(tid,NULL);
	}

    ~PySite()
	{
#ifdef DEBUG_CREATION
	    fprintf(stderr,"%p : SITE : DTOR\n",this);
#endif
	    //Py_DECREF(site);
	}

    //PyThreadState *state;
private:
    PyObject *site;
    bool has_pixel_changed_method;
    pthread_t tid;
};

typedef enum
{
    ITERS,
    IMAGE,
    PROGRESS,
    STATUS,
    PIXEL,
    TOLERANCE,
    STATS,
} msg_type_t;

static IImage *
image_fromcapsule(PyObject *pyimage)
{
    IImage *image = (IImage *)PyCapsule_GetPointer(pyimage, OBTYPE_IMAGE);
    if (NULL == image)
    {
	fprintf(stderr, "%p : IM : BAD\n", pyimage);
    }
    return image;
}

static IFractalSite *
site_fromcapsule(PyObject *pysite)
{
    IFractalSite *site = (IFractalSite *)PyCapsule_GetPointer(pysite, OBTYPE_SITE);
    if (NULL == site)
    {
	fprintf(stderr, "%p : ST : BAD\n", pysite);
    }
    return site;
}


struct calc_args
{
    double params[N_PARAMS];
    int eaa, maxiter, nThreads;
    int auto_deepen, yflip, periodicity, dirty;
    int auto_tolerance;
    double tolerance;
    int async, warp_param;
    render_type_t render_type;
    pf_obj *pfo;
    ColorMap *cmap;
    IImage *im;
    IFractalSite *site;

    PyObject *pycmap, *pypfo, *pyim, *pysite;
    calc_args()
	{
#ifdef DEBUG_CREATION
	    fprintf(stderr,"%p : CA : CTOR\n",this);
#endif
	    pycmap = NULL;
	    pypfo = NULL;
	    pyim = NULL;
	    pysite = NULL;
	    dirty = 1;
	    periodicity = true;
	    yflip = false;
	    auto_deepen = false;
	    auto_tolerance = false;
	    tolerance = 1.0E-9;
	    eaa = AA_NONE;
	    maxiter = 1024;
	    nThreads = 1;
	    render_type = RENDER_TWO_D;
	    async = false;
	    warp_param = -1;
	}

    void set_cmap(PyObject *pycmap_)
	{
	    pycmap = pycmap_;
	    cmap = cmap_fromcapsule(pycmap);
	    Py_XINCREF(pycmap);
	}

    void set_pfo(PyObject *pypfo_)
	{
	    pypfo = pypfo_;

	    pfo = (pf_fromcapsule(pypfo))->pfo;
	    Py_XINCREF(pypfo);
	}

    void set_im(PyObject *pyim_)
	{
	    pyim = pyim_;
	    im = image_fromcapsule(pyim);
	    Py_XINCREF(pyim);
	}
    void set_site(PyObject *pysite_)
	{
	    pysite = pysite_;
	    site = site_fromcapsule(pysite);
	    Py_XINCREF(pysite);
	}

    ~calc_args()
	{
#ifdef DEBUG_CREATION
	    fprintf(stderr,"%p : CA : DTOR\n",this);
#endif
	    Py_XDECREF(pycmap);
	    Py_XDECREF(pypfo);
	    Py_XDECREF(pyim);
	    Py_XDECREF(pysite);
	}
};

// write the callbacks to a file descriptor
class FDSite :public IFractalSite
{
public:
    FDSite(int fd_) : fd(fd_), tid((pthread_t)0), 
		      interrupted(false), params(NULL) 
	{
#ifdef DEBUG_CREATION
	    fprintf(stderr,"%p : FD : CTOR\n",this);
#endif
	    pthread_mutex_init(&write_lock,NULL);
	}

    inline void send(msg_type_t type, int size, void *buf)
	{
	    pthread_mutex_lock(&write_lock);
	    if (write(fd,&type,sizeof(type))) {};
	    if (write(fd,&size,sizeof(size))) {};
	    if (write(fd,buf,size)) {};
	    pthread_mutex_unlock(&write_lock);
	}
    virtual void iters_changed(int numiters)
	{
	    send(ITERS, sizeof(int), &numiters);
	}
    virtual void tolerance_changed(double tolerance)
	{
	    send (TOLERANCE, sizeof(tolerance), &tolerance);
	}

    // we've drawn a rectangle of image
    virtual void image_changed(int x1, int y1, int x2, int y2)
	{
	    if(!interrupted)
	    {
		int buf[4] = { x1, y1, x2, y2 };
		send(IMAGE, sizeof(buf), &buf[0]);
	    }
	}
    // estimate of how far through current pass we are
    virtual void progress_changed(float progress)
	{
	    if(!interrupted)
	    {
		int percentdone = (int) (100.0 * progress); 
		send(PROGRESS, sizeof(percentdone), &percentdone);
	    }
	}

    virtual void stats_changed(pixel_stat_t& stats)
	{
	    if(!interrupted)
	    {
		send(STATS,sizeof(stats),&stats);
	    }
		
	}

    // one of the status values above
    virtual void status_changed(int status_val)
	{
	    send(STATUS,sizeof(status_val),&status_val);
	}

    // return true if we've been interrupted and are supposed to stop
    virtual bool is_interrupted()
	{
	    //fprintf(stderr,"int: %d\n",interrupted);
	    return interrupted;
	}

    // pixel changed
    virtual void pixel_changed(
	const double *params, int maxIters, int nNoPeriodIters,
	int x, int y, int aa,
	double dist, int fate, int nIters,
	int r, int g, int b, int a) 
	{
	    /*
	    fprintf(stderr,"pixel: <%g,%g,%g,%g>(%d,%d,%d) = (%g,%d,%d)\n",
		   params[0],params[1],params[2],params[3],
		   x,y,aa,dist,fate,nIters);
	    */
	    return; // FIXME
	};

    virtual void interrupt() 
	{
#ifdef DEBUG_THREADS
	    fprintf(stderr,"%p : CA : INT(%p)\n", this, tid);
#endif
	    interrupted = true;
	}
    
    virtual void start(calc_args *params_) 
	{
#ifdef DEBUG_THREADS
	    fprintf(stderr,"clear interruption\n");
#endif
	    interrupted = false;
	    params = params_;
	}

    virtual void set_tid(pthread_t tid_) 
	{
#ifdef DEBUG_THREADS
	    fprintf(stderr,"%p : CA : SET(%p)\n", this,tid_);
#endif
	    tid = tid_;
	}

    virtual void wait()
	{
	    if(tid != 0)
	    {
#ifdef DEBUG_THREADS
		fprintf(stderr,"%p : CA : WAIT(%p)\n", this,tid);
#endif
		pthread_join(tid,NULL);
	    }
	}
    ~FDSite()
	{
#ifdef DEBUG_CREATION
	    fprintf(stderr,"%p : FD : DTOR\n",this);
#endif
	    close(fd);
	}
private:
    int fd;
    pthread_t tid;
    volatile bool interrupted;
    calc_args *params;
    pthread_mutex_t write_lock;
};

static void
site_delete(IFractalSite *site)
{
    delete site;
}

    
static void
fw_delete(IFractWorker *worker)
{
    delete worker;
}

struct ffHandle
{
    PyObject *pyhandle;
    fractFunc *ff;
} ;

static void
ff_delete(struct ffHandle *ffh)
{
#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : FF : DTOR\n",ffh);
#endif
    delete ffh->ff;
    Py_DECREF(ffh->pyhandle);
    delete ffh;
}

static void
pysite_delete(PyObject *pysite)
{
    IFractalSite *site = site_fromcapsule(pysite);
    site_delete(site);
}


static PyObject *
pysite_create(PyObject *self, PyObject *args)
{
    PyObject *pysite;
    if(!PyArg_ParseTuple(
	   args,
	   "O",
	   &pysite))
    {
	return NULL;
    }

    IFractalSite *site = new PySite(pysite);

    //fprintf(stderr,"pysite_create: %p\n",site);
    PyObject *pyret = PyCapsule_New(site, OBTYPE_SITE, pysite_delete);

    return pyret;
}

static PyObject *
pyfdsite_create(PyObject *self, PyObject *args)
{
    int fd;
    if(!PyArg_ParseTuple(args,"i", &fd))
    {
	return NULL;
    }

    IFractalSite *site = new FDSite(fd);

    PyObject *pyret = PyCapsule_New(site, OBTYPE_SITE, pysite_delete);

    return pyret;
}

static PyObject *
pystop_calc(PyObject *self, PyObject *args)
{
    PyObject *pysite;
    if(!PyArg_ParseTuple(
	   args,
	   "O",
	   &pysite))
    {
	return NULL;
    }

    IFractalSite *site = site_fromcapsule(pysite);
    if(!site)
    {
	return NULL;
    }

    site->interrupt();

    Py_INCREF(Py_None);
    return Py_None;
}

static IFractWorker *
fw_fromcapsule(PyObject *capsule)
{
    IFractWorker *worker = (IFractWorker *)PyCapsule_GetPointer(capsule, OBTYPE_WORKER);
    return worker;
}

static void
pyfw_delete(PyObject *pyworker)
{
    IFractWorker *worker = fw_fromcapsule(pyworker);
    fw_delete(worker);
}
    
static PyObject *
fw_create(PyObject *self, PyObject *args)
{
    int nThreads;
    pf_obj *pfo;
    ColorMap *cmap;
    IImage *im;
    IFractalSite *site;

    PyObject *pypfo, *pycmap, *pyim, *pysite;

    if(!PyArg_ParseTuple(args,"iOOOO",
			 &nThreads,
			 &pypfo,
			 &pycmap,
			 &pyim,
			 &pysite))
    {
	return NULL;
    }

    cmap = cmap_fromcapsule(pycmap);
    pfo = (pf_fromcapsule(pypfo))->pfo;
    im = image_fromcapsule(pyim);
    site = site_fromcapsule(pysite);
    if(!cmap || !pfo || !im || !im->ok() || !site)
    {
	return NULL;
    }


    IFractWorker *worker = IFractWorker::create(nThreads,pfo,cmap,im,site);

    if(!worker->ok())
    {
	PyErr_SetString(PyExc_ValueError,"Error creating worker");
	delete worker;
	return NULL;
    }

    PyObject *pyret = PyCapsule_New(worker, OBTYPE_WORKER, pyfw_delete);

    return pyret;
}

static PyObject *
fw_pixel(PyObject *self, PyObject *args)
{
    PyObject *pyworker;
    int x,y,w,h;

    if(!PyArg_ParseTuple(args, "Oiiii",
			 &pyworker,
			 &x,&y,&w,&h))
    {
	return NULL;
    }
    
    IFractWorker *worker = fw_fromcapsule(pyworker);
    worker->pixel(x,y,w,h);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
fw_pixel_aa(PyObject *self, PyObject *args)
{
    PyObject *pyworker;
    int x,y;

    if(!PyArg_ParseTuple(args, "Oii",
			 &pyworker,
			 &x,&y))
    {
	return NULL;
    }
    
    IFractWorker *worker = fw_fromcapsule(pyworker);
    worker->pixel_aa(x,y);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
fw_find_root(PyObject *self, PyObject *args)
{
    PyObject *pyworker;
    dvec4 eye, look;

    if(!PyArg_ParseTuple(args, "O(dddd)(dddd)",
			 &pyworker,
			 &eye[VX],&eye[VY], &eye[VZ], &eye[VW],
			 &look[VX],&look[VY], &look[VZ], &look[VW]))
    {
	return NULL;
    }
    
    IFractWorker *worker = fw_fromcapsule(pyworker);
    dvec4 root;
    int ok = worker->find_root(eye,look,root);

    return Py_BuildValue(
	"i(dddd)",
	ok,root[0], root[1], root[2], root[3]);
}

static ffHandle *
ff_fromcapsule(PyObject *pyff)
{
    ffHandle *ff = (ffHandle *)PyCapsule_GetPointer(pyff, OBTYPE_FFH);
    if(NULL == ff)
    {
	fprintf(stderr,"%p : FF : CTOR\n",ff);
    }
    return ff;
}

static void
pyff_delete(PyObject *pyff)
{
    ffHandle *ff = (ffHandle *)PyCapsule_GetPointer(pyff, OBTYPE_FFH);
    ff_delete(ff);
}

static PyObject *
ff_create(PyObject *self, PyObject *args)
{
    PyObject *pypfo, *pycmap, *pyim, *pysite, *pyworker;
    double params[N_PARAMS];
    int eaa=-7, maxiter=-8, nThreads=-9;
    int auto_deepen, periodicity;
    int yflip;
    render_type_t render_type;
    pf_obj *pfo;
    ColorMap *cmap;
    IImage *im;
    IFractalSite *site;
    IFractWorker *worker;
    int auto_tolerance;
    double tolerance;

    if(!PyArg_ParseTuple(
	   args,
	   "(ddddddddddd)iiiiOOiiiOOOid",
	   &params[0],&params[1],&params[2],&params[3],
	   &params[4],&params[5],&params[6],&params[7],
	   &params[8],&params[9],&params[10],
	   &eaa,&maxiter,&yflip,&nThreads,
	   &pypfo,&pycmap,
	   &auto_deepen,
	   &periodicity,
	   &render_type,
	   &pyim, &pysite,
	   &pyworker,
	   &auto_tolerance, &tolerance
	   ))
    {
	return NULL;
    }

    cmap = cmap_fromcapsule(pycmap);
    pfo = (pf_fromcapsule(pypfo))->pfo;
    im = image_fromcapsule(pyim);
    site = site_fromcapsule(pysite);
    worker = fw_fromcapsule(pyworker);

    if(!cmap || !pfo || !im || !site || !worker)
    {
	return NULL;
    }

    fractFunc *ff = new fractFunc(
	params, 
	eaa,
	maxiter,
	nThreads,
	auto_deepen,
	auto_tolerance,
	tolerance,
	yflip,
	periodicity,
	render_type,
	-1, // warp_param
	worker,
	im,
	site);

    if(!ff)
    {
	return NULL;
    }

    ffHandle *ffh = new struct ffHandle;
    ffh->ff = ff;
    ffh->pyhandle = pyworker;

#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : FF : CTOR\n",ffh);
#endif

    PyObject *pyret = PyCapsule_New(ffh, OBTYPE_FFH, pyff_delete);

    Py_INCREF(pyworker);

    return pyret;
}


static void *
calculation_thread(void *vdata) 
{
    calc_args *args = (calc_args *)vdata;

#ifdef DEBUG_THREADS
    fprintf(stderr,"%p : CA : CALC(%d)\n",args,pthread_self());
#endif

    calc(args->params,args->eaa,args->maxiter,
	 args->nThreads,args->pfo,args->cmap,
	 args->auto_deepen,
	 args->auto_tolerance,
	 args->tolerance,
	 args->yflip, args->periodicity, args->dirty,
	 0, // debug_flags
	 args->render_type,
	 args->warp_param,
	 args->im,args->site);

#ifdef DEBUG_THREADS 
    fprintf(stderr,"%p : CA : ENDCALC(%d)\n",args,pthread_self());
#endif

    delete args;
    return NULL;
}

static calc_args *
parse_calc_args(PyObject *args, PyObject *kwds)
{
    PyObject *pyparams, *pypfo, *pycmap, *pyim, *pysite;
    calc_args *cargs = new calc_args();
    double *p = NULL;

    static const char *kwlist[] = {
	"image",
	"site",
	"pfo",
	"cmap",
	"params",
	"antialias",
	"maxiter",
	"yflip",
	"nthreads",
	"auto_deepen",
	"periodicity",
	"render_type",
	"dirty", 
	"async",
	"warp_param",
	"tolerance",
	"auto_tolerance",
	NULL};

    if(!PyArg_ParseTupleAndKeywords(
	   args,
	   kwds,
	   "OOOOO|iiiiiiiiiidi",
	   const_cast<char **>(kwlist),

	   &pyim, &pysite,
	   &pypfo,&pycmap,
	   &pyparams,
	   &cargs->eaa,
	   &cargs->maxiter,
	   &cargs->yflip,
	   &cargs->nThreads,
	   &cargs->auto_deepen,
	   &cargs->periodicity,
	   &cargs->render_type,
	   &cargs->dirty,
	   &cargs->async,
	   &cargs->warp_param,
	   &cargs->tolerance,
	   &cargs->auto_tolerance
	   ))
    {
	goto error;
    }

    p = cargs->params;
    if(!PyList_Check(pyparams) || PyList_Size(pyparams) != N_PARAMS)
    {
	PyErr_SetString(PyExc_ValueError, "bad parameter list");
	goto error;
    }

    for(int i = 0; i < N_PARAMS; ++i)
    {
	PyObject *elt = PyList_GetItem(pyparams, i);
	if(!PyFloat_Check(elt))
	{
	    PyErr_SetString(PyExc_ValueError, "a param is not a float");
	    goto error;
	}

	p[i] = PyFloat_AsDouble(elt);
    }

    cargs->set_cmap(pycmap);
    cargs->set_pfo(pypfo);
    cargs->set_im(pyim);
    cargs->set_site(pysite);
    if(!cargs->cmap || !cargs->pfo || 
       !cargs->im   || !cargs->site)
    {
	PyErr_SetString(PyExc_ValueError, "bad argument passed to calc");
	goto error;
    }

    if(!cargs->im->ok())
    {
	PyErr_SetString(PyExc_MemoryError, "image not allocated"); 
	goto error;
    }

    return cargs;

error:
    delete cargs;
    return NULL;
}

static PyObject *
pycalc(PyObject *self, PyObject *args, PyObject *kwds)
{
    calc_args *cargs = parse_calc_args(args, kwds);
    if(NULL == cargs)
    {
	return NULL;
    }

    if(cargs->async)
    {
	cargs->site->interrupt();
	cargs->site->wait();

	cargs->site->start(cargs);

	pthread_t tid;

	/* create low-priority attribute block */
	pthread_attr_t lowprio_attr;
	//struct sched_param lowprio_param;
	pthread_attr_init(&lowprio_attr);
	//lowprio_param.sched_priority = sched_get_priority_min(SCHED_OTHER);
	//pthread_attr_setschedparam(&lowprio_attr, &lowprio_param);

	/* start the calculation thread */
	pthread_create(&tid,&lowprio_attr,calculation_thread,(void *)cargs);
	assert(tid != 0);

	cargs->site->set_tid(tid);
    }
    else
    {
	Py_BEGIN_ALLOW_THREADS
	// synchronous
	calc(cargs->params,
	     cargs->eaa,
	     cargs->maxiter,
	     cargs->nThreads,
	     cargs->pfo,
	     cargs->cmap,
	     cargs->auto_deepen,
	     cargs->auto_tolerance,
	     cargs->tolerance,
	     cargs->yflip, 
	     cargs->periodicity, 
	     cargs->dirty,
	     0, // debug_flags
	     cargs->render_type,
	     cargs->warp_param,
	     cargs->im,
	     cargs->site);

	delete cargs;
	Py_END_ALLOW_THREADS
    }

    Py_INCREF(Py_None);
    
    return Py_None;
}

static void
image_delete(IImage *image)
{
#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : IM : DTOR\n",image);
#endif
    delete image;
}

static void
pyimage_delete(PyObject *pyimage)
{
    IImage *im = image_fromcapsule(pyimage);
    image_delete(im);
}

static PyObject *
image_create(PyObject *self, PyObject *args)
{
    int x, y;
    int totalx = -1, totaly = -1;
    if(!PyArg_ParseTuple(args,"ii|ii",&x,&y,&totalx, &totaly))
    { 
	return NULL;
    }

    IImage *i = new image();

    i->set_resolution(x,y,totalx, totaly);

    if(! i->ok())
    {
	PyErr_SetString(PyExc_MemoryError, "Image too large");
	delete i;
	return NULL;
    }

#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : IM : CTOR\n",i);
#endif

    PyObject *pyret = PyCapsule_New(i, OBTYPE_IMAGE, pyimage_delete);

    return pyret;
}

static PyObject *
image_resize(PyObject *self, PyObject *args)
{
    int x, y;
    int totalx=-1, totaly=-1;
    PyObject *pyim;

    if(!PyArg_ParseTuple(args,"Oiiii",&pyim,&x,&y,&totalx,&totaly))
    { 
	return NULL;
    }

    IImage *i = image_fromcapsule(pyim);
    if(NULL == i)
    {
	return NULL;
    }

    i->set_resolution(x,y,totalx,totaly);

    if(! i->ok())
    {
	PyErr_SetString(PyExc_MemoryError, "Image too large");
	return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
image_dims(PyObject *self, PyObject *args)
{
    PyObject *pyim;

    if(!PyArg_ParseTuple(args,"O",&pyim))
    { 
	return NULL;
    }

    IImage *i = image_fromcapsule(pyim);
    if(NULL == i)
    {
	return NULL;
    }

    int xsize, ysize, xoffset, yoffset, xtotalsize, ytotalsize;
    xsize = i->Xres();
    ysize = i->Yres();
    xoffset = i->Xoffset();
    yoffset = i->Yoffset();
    xtotalsize = i->totalXres();
    ytotalsize = i->totalYres();

    PyObject *pyret = Py_BuildValue(
	"(iiiiii)", xsize,ysize,xtotalsize, ytotalsize, xoffset, yoffset);

    return pyret;
}

static PyObject *
image_set_offset(PyObject *self, PyObject *args)
{
    int x, y;
    PyObject *pyim;

    if(!PyArg_ParseTuple(args,"Oii",&pyim,&x,&y))
    { 
	return NULL;
    }

    IImage *i = image_fromcapsule(pyim);
    if(NULL == i)
    {
	return NULL;
    }

    bool ok = i->set_offset(x,y);
    if(!ok)
    {
	PyErr_SetString(PyExc_ValueError, "Offset out of bounds");
	return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
image_clear(PyObject *self, PyObject *args)
{
    PyObject *pyim;

    if(!PyArg_ParseTuple(args,"O",&pyim))
    { 
	return NULL;
    }

    IImage *i = image_fromcapsule(pyim);
    if(NULL == i)
    {
	return NULL;
    }

    i->clear();

    Py_INCREF(Py_None);
    return Py_None;
}

static void
image_writer_delete(ImageWriter *im)
{
    delete im;
}


static void
pyimage_writer_delete(PyObject *pyim)
{
    ImageWriter *im = image_writer_fromcapsule(pyim);
    image_writer_delete(im);
}


static PyObject *
image_writer_create(PyObject *self,PyObject *args)
{
    PyObject *pyim;
    char *filename;
    int file_type;
    if(!PyArg_ParseTuple(args,"Osi",&pyim,&filename,&file_type))
    {
	return NULL;
    }

    IImage *i = image_fromcapsule(pyim);
    
    FILE *fp = fopen(filename,"wb");

    if(!fp)
    {
	PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
	return NULL;
    }
    
    ImageWriter *writer = ImageWriter::create((image_file_t)file_type, fp, i);
    if(NULL == writer)
    {
	PyErr_SetString(PyExc_ValueError, "Unsupported file type");
	return NULL;
    }

    return PyCapsule_New(writer, OBTYPE_IMAGE_WRITER, pyimage_writer_delete);
}

static PyObject *
image_read(PyObject *self,PyObject *args)
{
    PyObject *pyim;
    char *filename;
    int file_type;
    if(!PyArg_ParseTuple(args,"Osi",&pyim,&filename,&file_type))
    {
	return NULL;
    }

    IImage *i = image_fromcapsule(pyim);

    FILE *fp = fopen(filename,"rb");

    if(!fp || !i)
    {
	PyErr_SetFromErrnoWithFilename(PyExc_OSError, "filename");
	return NULL;
    }
    
    ImageReader *reader = ImageReader::create((image_file_t)file_type, fp, i);

    if(!reader->read())
    {
	PyErr_SetString(PyExc_IOError, "Couldn't read image contents");
	delete reader;
	return NULL;
    }
    delete reader;

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
image_save_header(PyObject *self,PyObject *args)
{
    PyObject *pyimwriter;
    if(!PyArg_ParseTuple(args,"O",&pyimwriter))
    {
	return NULL;
    }

    ImageWriter *i = image_writer_fromcapsule(pyimwriter);

    if(!i || !i->save_header())
    {
	PyErr_SetString(PyExc_IOError, "Couldn't save file header");
	return NULL;
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}
    
static PyObject *
image_save_tile(PyObject *self,PyObject *args)
{
    PyObject *pyimwriter;
    if(!PyArg_ParseTuple(args,"O",&pyimwriter))
    {
	return NULL;
    }

    ImageWriter *i = image_writer_fromcapsule(pyimwriter);

    if(!i || !i->save_tile())
    {
	PyErr_SetString(PyExc_IOError, "Couldn't save image tile");
	return NULL;
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
image_save_footer(PyObject *self,PyObject *args)
{
    PyObject *pyimwriter;
    if(!PyArg_ParseTuple(args,"O",&pyimwriter))
    {
	return NULL;
    }

    ImageWriter *i = image_writer_fromcapsule(pyimwriter);

    if(!i || !i->save_footer())
    {
	PyErr_SetString(PyExc_IOError, "Couldn't save image footer");
	return NULL;
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
image_buffer(PyObject *self, PyObject *args)
{
    PyObject *pyim;
    PyObject *pybuf;

    int x=0,y=0;
    if(!PyArg_ParseTuple(args,"O|ii",&pyim,&x,&y))
    {
	return NULL;
    }

    image *i = (image *)image_fromcapsule(pyim);

#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : IM : BUF\n",i);
#endif

    if(!i || ! i->ok())
    {
	PyErr_SetString(PyExc_MemoryError, "image not allocated");
	return NULL;
    }

    if(x < 0 || x >= i->Xres() || y < 0 || y >= i->Yres())
    {
	PyErr_SetString(PyExc_ValueError,"request for buffer outside image bounds");
	return NULL;
    }
    int offset = 3 * (y * i->Xres() + x);
    assert(offset > -1 && offset < i->bytes());
    Py_buffer *buffer = new Py_buffer;
    PyBuffer_FillInfo(buffer, NULL, i->getBuffer()+offset,i->bytes()-offset,0, PyBUF_WRITABLE);
    pybuf = PyMemoryView_FromBuffer(buffer);
    Py_XINCREF(pybuf);
    //Py_XINCREF(pyim);

    return pybuf;
}

static PyObject *
image_fate_buffer(PyObject *self, PyObject *args)
{
    PyObject *pyim;
    PyObject *pybuf;

    int x=0,y=0;
    if(!PyArg_ParseTuple(args,"O|ii",&pyim,&x,&y))
    {
	return NULL;
    }

    image *i = (image *)image_fromcapsule(pyim);

#ifdef DEBUG_CREATION
    fprintf(stderr,"%p : IM : BUF\n",i);
#endif

    if(NULL == i)
    {
	PyErr_SetString(PyExc_ValueError,
			"Bad image object");
	return NULL;
    }

    if(x < 0 || x >= i->Xres() || y < 0 || y >= i->Yres())
    {
	PyErr_SetString(PyExc_ValueError,"request for buffer outside image bounds");
	return NULL;
    }
    int index = i->index_of_subpixel(x,y,0);
    int last_index = i->index_of_sentinel_subpixel();
    assert(index > -1 && index < last_index);

    Py_buffer *buffer = new Py_buffer;
    PyBuffer_FillInfo(buffer, NULL, i->getFateBuffer()+index,(last_index - index) * sizeof(fate_t),0, PyBUF_WRITABLE);
    pybuf = PyMemoryView_FromBuffer(buffer);
    
    Py_XINCREF(pybuf);

    return pybuf;
}

static PyObject *
image_get_color_index(PyObject *self, PyObject *args)
{
    PyObject *pyim;

    int x=0,y=0,sub=0;
    if(!PyArg_ParseTuple(args,"Oii|i",&pyim,&x,&y,&sub))
    {
	return NULL;
    }

    image *i = (image *)image_fromcapsule(pyim);
    
    if(NULL == i)
    {
	PyErr_SetString(PyExc_ValueError,
			"Bad image object");
	return NULL;
    }

    if(x < 0 || x >= i->Xres() || 
       y < 0 || y >= i->Yres() || 
       sub < 0 || sub >= image::N_SUBPIXELS)
    {
	PyErr_SetString(PyExc_ValueError,
			"request for data outside image bounds");
	return NULL;
    }

    float dist = i->getIndex(x,y,sub);
    return Py_BuildValue("d", (double)dist);
}

static PyObject *
image_get_fate(PyObject *self, PyObject *args)
{
    PyObject *pyim;

    int x=0,y=0,sub=0;
    if(!PyArg_ParseTuple(args,"Oii|i",&pyim,&x,&y,&sub))
    {
	return NULL;
    }

    image *i = (image *)image_fromcapsule(pyim);
    
    if(NULL == i)
    {
	PyErr_SetString(PyExc_ValueError,
			"Bad image object");
	return NULL;
    }

    if(x < 0 || x >= i->Xres() || 
       y < 0 || y >= i->Yres() || 
       sub < 0 || sub >= image::N_SUBPIXELS)
    {
	PyErr_SetString(PyExc_ValueError,
			"request for data outside image bounds");
	return NULL;
    }

    fate_t fate = i->getFate(x,y,sub);
    if(fate == FATE_UNKNOWN)
    {
	Py_INCREF(Py_None);
	return Py_None;
    }
    int is_solid = fate & FATE_SOLID ? 1 : 0;
    return Py_BuildValue("(ii)", is_solid, fate & ~FATE_SOLID);
}

static PyObject *
rot_matrix(PyObject *self, PyObject *args)
{
    double params[N_PARAMS];

    if(!PyArg_ParseTuple(
	   args,
	   "(ddddddddddd)",
	   &params[0],&params[1],&params[2],&params[3],
	   &params[4],&params[5],&params[6],&params[7],
	   &params[8],&params[9],&params[10]))
    {
	return NULL;
    }

    dmat4 rot = rotated_matrix(params);

    return Py_BuildValue(
	"((dddd)(dddd)(dddd)(dddd))",
	rot[0][0], rot[0][1], rot[0][2], rot[0][3],
	rot[1][0], rot[1][1], rot[1][2], rot[1][3],
	rot[2][0], rot[2][1], rot[2][2], rot[2][3],
	rot[3][0], rot[3][1], rot[3][2], rot[3][3]);
}

static PyObject *
eye_vector(PyObject *self, PyObject *args)
{
    double params[N_PARAMS], dist;

    if(!PyArg_ParseTuple(
	   args,
	   "(ddddddddddd)d",
	   &params[0],&params[1],&params[2],&params[3],
	   &params[4],&params[5],&params[6],&params[7],
	   &params[8],&params[9],&params[10],&dist))
    {
	return NULL;
    }

    dvec4 eyevec = test_eye_vector(params, dist);

    return Py_BuildValue(
	"(dddd)",
	eyevec[0], eyevec[1], eyevec[2], eyevec[3]);
}

static PyObject *
ff_get_vector(PyObject *self, PyObject *args)
{
    int vec_type;
    PyObject *pyFF;

    if(!PyArg_ParseTuple(
	   args,
	   "Oi",
	   &pyFF, &vec_type))
    {
	return NULL;
    }

    struct ffHandle *ffh = ff_fromcapsule(pyFF);
    if(ffh == NULL)
    {
	return NULL;
    }

    fractFunc *ff = ffh->ff;
    if(ff == NULL)
    {
	return NULL;
    }

    dvec4 vec;
    switch(vec_type)
    {
    case DELTA_X:
	vec = ff->deltax;
	break;
    case DELTA_Y:
	vec = ff->deltay;
	break;
    case TOPLEFT:
	vec = ff->topleft;
	break;
    default:
	PyErr_SetString(PyExc_ValueError, "Unknown vector requested");
	return NULL;
    }

    return Py_BuildValue(
	"(dddd)",
	vec[0], vec[1], vec[2], vec[3]);
    
    return NULL;
}

static PyObject *
ff_look_vector(PyObject *self, PyObject *args)
{
    PyObject *pyFF;
    double x, y;
    if(!PyArg_ParseTuple(
	   args,
	   "Odd",
	   &pyFF, &x, &y))
    {
	return NULL;
    }

    struct ffHandle *ffh = ff_fromcapsule(pyFF);
    if(ffh == NULL)
    {
	return NULL;
    }

    fractFunc *ff = ffh->ff;
    if(ff == NULL)
    {
	return NULL;
    }

    dvec4 lookvec = ff->vec_for_point(x,y);

    return Py_BuildValue(
	"(dddd)",
	lookvec[0], lookvec[1], lookvec[2], lookvec[3]);

}

static PyObject *
pyimage_lookup(PyObject *self, PyObject *args)
{
    PyObject *pyimage=NULL;
    double x,y;
    double r,g,b;

    if(!PyArg_ParseTuple(
	   args,
	   "Odd",
	   &pyimage, &x, &y))
    {
	return NULL;
    }    

    image *i = (image *)image_fromcapsule(pyimage);
    
    image_lookup(i,x,y,&r,&g,&b);

    return Py_BuildValue(
	"(dddd)",
	r,g,b,1.0);
}

static PyObject *
pyrgb_to_hsv(PyObject *self, PyObject *args)
{
    double r,g,b,a=1.0,h,s,v;
    if(!PyArg_ParseTuple(
	   args,
	   "ddd|d",
	   &r,&g,&b,&a))
    {
	return NULL;
    }

    rgb_to_hsv(r,g,b,&h,&s,&v);

    return Py_BuildValue(
	"(dddd)",
	h,s,v,a);
}

static PyObject *
pyrgb_to_hsl(PyObject *self, PyObject *args)
{
    double r,g,b,a=1.0,h,l,s;
    if(!PyArg_ParseTuple(
	   args,
	   "ddd|d",
	   &r,&g,&b,&a))
    {
	return NULL;
    }

    rgb_to_hsl(r,g,b,&h,&s,&l);

    return Py_BuildValue(
	"(dddd)",
	h,s,l,a);
}

static PyObject *
pyhsl_to_rgb(PyObject *self, PyObject *args)
{
    double r,g,b,a=1.0,h,l,s;
    if(!PyArg_ParseTuple(
	   args,
	   "ddd|d",
	   &h,&s,&l,&a))
    {
	return NULL;
    }

    hsl_to_rgb(h,s,l,&r,&g,&b);

    return Py_BuildValue(
	"(dddd)",
	r,g,b,a);
}

static void
pyarena_delete(PyObject *pyarena)
{
    arena_t arena = arena_fromcapsule(pyarena);
    arena_delete(arena);
}

static PyObject *
pyarena_create(PyObject *self, PyObject *args)
{
    int page_size, max_pages;
    if(!PyArg_ParseTuple(
	   args,
	   "ii",
	   &page_size,&max_pages))
    {
	return NULL;
    }
    
    arena_t arena = arena_create(page_size,max_pages);

    if(NULL == arena)
    {
	PyErr_SetString(PyExc_MemoryError,"Cannot allocate arena");
	return NULL;
    }

    PyObject *pyarena = PyCapsule_New(arena, OBTYPE_ARENA, pyarena_delete);

    return pyarena;
}

static PyObject *
pyarena_alloc(PyObject *self, PyObject *args)
{
    PyObject *pyArena;
    int element_size;
    int n_dimensions;
    int n_elements[4];

    if(!PyArg_ParseTuple(
	   args,
	   "Oiii|iii",
	   &pyArena, &element_size, 
	   &n_dimensions,
	   &n_elements[0],
	   &n_elements[1],
	   &n_elements[2],
	   &n_elements[3]
	   ))
    {
	return NULL;
    }

    arena_t arena = arena_fromcapsule(pyArena);
    if(arena == NULL)
    {
	return NULL;
    }

    void *allocation = arena_alloc(
	arena, element_size, 
	n_dimensions,
	n_elements);
    if(allocation == NULL)
    {
	PyErr_SetString(PyExc_MemoryError, "Can't allocate array");
	return NULL;
    }

    PyObject *pyAlloc = PyCapsule_New(allocation, NULL, NULL);

    return pyAlloc;
}

static PyObject *
pyarray_get(PyObject *self, PyObject *args)
{
    PyObject *pyAllocation;
    int indexes[4];
    int n_indexes;

    if(!PyArg_ParseTuple(
	   args,
	   "Oii|iii",
	   &pyAllocation, &n_indexes, 
	   &indexes[0], &indexes[1], &indexes[2], &indexes[3]))
    {
	return NULL;
    }

    void *allocation = PyCapsule_GetPointer(pyAllocation, NULL);
    if(allocation == NULL)
    {
	return NULL;
    }
 
    int retval, inbounds;
    array_get_int(allocation, n_indexes, indexes, &retval, &inbounds);
    
    PyObject *pyRet = Py_BuildValue(
	"(ii)",
	retval,inbounds);

    return pyRet;
}

static PyObject *
pyarray_set(PyObject *self, PyObject *args)
{
    PyObject *pyAllocation;
    int val;
    int n_indexes;
    int indexes[4];
    if(!PyArg_ParseTuple(
	   args,
	   "Oiii|iii",
	   &pyAllocation, 
	   &n_indexes,
	   &val, 
	   &indexes[0], &indexes[1], &indexes[2], &indexes[3]))
    {
	return NULL;
    }

    void *allocation = PyCapsule_GetPointer(pyAllocation, NULL);
    if(allocation == NULL)
    {
	return NULL;
    }
 
    int retval = array_set_int(allocation, n_indexes, indexes, val);
    
    PyObject *pyRet = Py_BuildValue("i",retval);

    return pyRet;
}

static PyMethodDef PfMethods[] = {
    {"pf_load",  module_load, METH_VARARGS, 
     "Load a new point function shared library"},
    {"pf_create", pf_create, METH_VARARGS,
     "Create a new point function"},
    {"pf_init", pf_init, METH_VARARGS,
     "Init a point function"},
    {"pf_calc", pf_calc, METH_VARARGS,
     "Calculate one point"},
    {"pf_defaults", pf_defaults, METH_VARARGS,
     "Get defaults for this formula"},

    { "cmap_create", cmap_create, METH_VARARGS,
      "Create a new colormap"},
    { "cmap_create_gradient", cmap_create_gradient, METH_VARARGS,
      "Create a new gradient-based colormap"},
    { "cmap_lookup", cmap_pylookup, METH_VARARGS,
      "Get a color tuple from a distance value"},
    { "cmap_lookup_flags", cmap_pylookup_with_flags, METH_VARARGS,
      "Get a color tuple from a distance value and solid/inside flags"},
    { "cmap_set_solid", pycmap_set_solid, METH_VARARGS,
      "Set the inner or outer solid color"},
    { "cmap_set_transfer", pycmap_set_transfer, METH_VARARGS,
      "Set the inner or outer transfer function"},
    
    { "rgb_to_hsv", pyrgb_to_hsv, METH_VARARGS,
      "Convert a rgb(a) list into an hsv(a) one"},
    { "rgb_to_hsl", pyrgb_to_hsl, METH_VARARGS,
      "Convert a rgb(a) list into an hls(a) one"},
    { "hsl_to_rgb", pyhsl_to_rgb, METH_VARARGS,
      "Convert an hls(a) list into an rgb(a) one"},

    { "image_create", image_create, METH_VARARGS,
      "Create a new image buffer"},
    { "image_resize", image_resize, METH_VARARGS,
      "Change image dimensions - data is deleted" },
    { "image_set_offset", image_set_offset, METH_VARARGS,
      "set the image tile's offset" },
    { "image_dims", image_dims, METH_VARARGS,
      "get a tuple containing image's dimensions"},
    { "image_clear", image_clear, METH_VARARGS,
      "Clear all iteration and color data from image" },

    { "image_writer_create", image_writer_create, METH_VARARGS,
      "create an object used to write image to disk" },

    { "image_save_header", image_save_header, METH_VARARGS,
      "save an image header - useful for render-to-disk"},
    { "image_save_tile", image_save_tile, METH_VARARGS,
      "save an image fragment ('tile') - useful for render-to-disk"},
    { "image_save_footer", image_save_footer, METH_VARARGS,
      "save the final footer info for an image - useful for render-to-disk"},

    { "image_read", image_read, METH_VARARGS,
      "read an image in from disk"},

    { "image_buffer", image_buffer, METH_VARARGS,
      "get the rgb data from the image"},
    { "image_fate_buffer", image_fate_buffer, METH_VARARGS,
      "get the fate data from the image"},

    { "image_get_color_index", image_get_color_index, METH_VARARGS,
      "Get the color index data from a point on the image"},
    { "image_get_fate", image_get_fate, METH_VARARGS,
      "Get the (solid, fate) info for a point on the image"},

    { "image_lookup", pyimage_lookup, METH_VARARGS,
      "Get the color of a point on an image"},

    { "site_create", pysite_create, METH_VARARGS,
      "Create a new site"},
    { "fdsite_create", pyfdsite_create, METH_VARARGS,
      "Create a new file-descriptor site"},

    { "ff_create", ff_create, METH_VARARGS,
      "Create a fractFunc." },
    { "ff_look_vector", ff_look_vector, METH_VARARGS,
      "Get a vector from the eye to a point on the screen" },
    { "ff_get_vector", ff_get_vector, METH_VARARGS,
      "Get a vector inside the ff" },

    { "fw_create", fw_create, METH_VARARGS,
      "Create a fractWorker." },
    { "fw_pixel", fw_pixel, METH_VARARGS,
      "Draw a single pixel." },
    { "fw_pixel_aa", fw_pixel_aa, METH_VARARGS,
      "Draw a single pixel." },
    { "fw_find_root", fw_find_root, METH_VARARGS,
      "Find closest root considering fractal function along a vector"},
    
    { "calc", (PyCFunction) pycalc, METH_VARARGS | METH_KEYWORDS,
      "Calculate a fractal image"},

    { "interrupt", pystop_calc, METH_VARARGS,
      "Stop an async calculation" },

    { "rot_matrix", rot_matrix, METH_VARARGS,
      "Return a rotated and scaled identity matrix based on params"},

    { "eye_vector", eye_vector, METH_VARARGS,
      "Return the line between the user's eye and the center of the screen"},

    { "arena_create", pyarena_create, METH_VARARGS,
      "Create a new arena allocator" },
    { "arena_alloc", pyarena_alloc, METH_VARARGS,
      "Allocate a chunk of memory from the arena" },

    { "array_get_int", pyarray_get, METH_VARARGS,
      "Get an element from an array allocated in an arena" },

    { "array_set_int", pyarray_set, METH_VARARGS,
      "Set an element in an array allocated in an arena" },
    
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "fract4dc",
    NULL,
    sizeof(struct module_state),
    PfMethods,
    NULL,
    NULL, // extension_traverse
    NULL, // extension_clear
    NULL
};

extern "C" PyMODINIT_FUNC
PyInit_fract4dc(void)
{
    PyObject *pymod = PyModule_Create(&moduledef);

    PyEval_InitThreads();

#ifdef USE_GMP
    mpf_t x;
    mpf_init(x);
#endif
    /* expose some constants */
    PyModule_AddIntConstant(pymod, "CALC_DONE", GF4D_FRACTAL_DONE);
    PyModule_AddIntConstant(pymod, "CALC_CALCULATING", GF4D_FRACTAL_CALCULATING);
    PyModule_AddIntConstant(pymod, "CALC_DEEPENING", GF4D_FRACTAL_DEEPENING);
    PyModule_AddIntConstant(pymod, "CALC_ANTIALIASING", GF4D_FRACTAL_ANTIALIASING);
    PyModule_AddIntConstant(pymod, "CALC_PAUSED", GF4D_FRACTAL_PAUSED);

    PyModule_AddIntConstant(pymod, "AA_NONE", AA_NONE);
    PyModule_AddIntConstant(pymod, "AA_FAST", AA_FAST);
    PyModule_AddIntConstant(pymod, "AA_BEST", AA_BEST);

    PyModule_AddIntConstant(pymod, "RENDER_TWO_D", RENDER_TWO_D);
    PyModule_AddIntConstant(pymod, "RENDER_LANDSCAPE", RENDER_LANDSCAPE);
    PyModule_AddIntConstant(pymod, "RENDER_THREE_D", RENDER_THREE_D);

    PyModule_AddIntConstant(pymod, "DRAW_GUESSING", DRAW_GUESSING);
    PyModule_AddIntConstant(pymod, "DRAW_TO_DISK", DRAW_TO_DISK);

    PyModule_AddIntConstant(pymod, "DELTA_X", DELTA_X);
    PyModule_AddIntConstant(pymod, "DELTA_Y", DELTA_Y);
    PyModule_AddIntConstant(pymod, "TOPLEFT", TOPLEFT);

    /* cf image_dims */
    PyModule_AddIntConstant(pymod, "IMAGE_WIDTH", 0);
    PyModule_AddIntConstant(pymod, "IMAGE_HEIGHT", 1);
    PyModule_AddIntConstant(pymod, "IMAGE_TOTAL_WIDTH", 2);
    PyModule_AddIntConstant(pymod, "IMAGE_TOTAL_HEIGHT", 3);
    PyModule_AddIntConstant(pymod, "IMAGE_XOFFSET", 4);
    PyModule_AddIntConstant(pymod, "IMAGE_YOFFSET", 5);

    /* image type consts */
    PyModule_AddIntConstant(pymod, "FILE_TYPE_TGA", FILE_TYPE_TGA);
    PyModule_AddIntConstant(pymod, "FILE_TYPE_PNG", FILE_TYPE_PNG);
    PyModule_AddIntConstant(pymod, "FILE_TYPE_JPG", FILE_TYPE_JPG);

    /* message type consts */
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_ITERS", ITERS);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_IMAGE", IMAGE);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_PROGRESS", PROGRESS);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_STATUS", STATUS);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_PIXEL", PIXEL);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_TOLERANCE", TOLERANCE);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_STATS", STATS);

    if(!ensure_cmap_loaded(pymod))
    {
	return NULL;
    }
    
    return pymod;
}
