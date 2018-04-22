/* Wrappers around C++ functions so they can be called from python The
   C code starts one or more non-Python threads which work out which
   points to calculate, and call the dynamically-compiled pointfunc C
   code created by the compiler for each pixel. 

   Results are reported back through a site object. There are 2 kinds,
   a synchronous site which calls back into python (used by
   command-line fractal.py script) and an asynchronous site which wraps
   a file descriptor into which we write simple messages. The GTK+ main
   loop then listens to the FD and performs operations in response to
   messages written to the file descriptor.
*/

#include "Python.h"

#include <dlfcn.h>
#include <pthread.h>

#include "pf.h"
#include "cmap.h"
#include "fractFunc.h"
#include "image.h"
#include "assert.h"

#include <new>

/* not sure why this isn't defined already */
#ifndef PyMODINIT_FUNC 
#define PyMODINIT_FUNC void
#endif

#define CMAP_NAME "/fract4d_stdlib.so"

#ifdef USE_GMP
#define MODULE_NAME "fract4dcgmp"
#include "gmp.h"
#else
#define MODULE_NAME "fract4dc"
#endif

/* 
 * pointfuncs
 */

PyObject *pymod=NULL;
void *cmap_module_handle=NULL;

typedef enum {
    DELTA_X,
    DELTA_Y,
    TOPLEFT
} vec_type_t;


static void
pf_unload(void *p)
{
#ifdef DEBUG_CREATION
    printf("%p : SO : DTOR\n",p);
#endif
    dlclose(p);
}

static int 
ensure_cmap_loaded()
{
    char cwd[PATH_MAX+1];
    // load the cmap module so fract funcs we compile later
    // can call its methods
    if(NULL != cmap_module_handle)
    {
	return 1; // already loaded
    }

    char *filename = PyModule_GetFilename(pymod);
    //printf("base name: %s\n",filename);
    char *path_end = strrchr(filename,'/');
    if(path_end == NULL)
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
    //printf("Filename: %s\n", new_filename);

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
pf_load(PyObject *self, PyObject *args)
{
    if(!ensure_cmap_loaded())
    {
	return NULL;
    }

    char *so_filename;
    if(!PyArg_ParseTuple(args,"s",&so_filename))
    {
	return NULL;
    }

    void *dlHandle = dlopen(so_filename, RTLD_NOW);
#ifdef DEBUG_CREATION
    printf("%p : SO :CTOR\n",dlHandle);
#endif
    if(NULL == dlHandle)
    {
	/* an error */
	PyErr_SetString(PyExc_ValueError,dlerror());
	return NULL;
    }
    return PyCObject_FromVoidPtr(dlHandle,pf_unload);
}

struct pfHandle
{
    PyObject *pyhandle;
    pf_obj *pfo;
} ;

static void
pf_delete(void *p)
{
    struct pfHandle *pfh = (struct pfHandle *)p;
#ifdef DEBUG_CREATION
    printf("%p : PF : DTOR\n",pfh);
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
    PyObject *pyobj;
    pf_obj *(*pfn)(void); 
    if(!PyArg_ParseTuple(args,"O",&pyobj))
    {
	return NULL;
    }
    if(!PyCObject_Check(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    dlHandle = PyCObject_AsVoidPtr(pyobj);
    pfn = (pf_obj *(*)(void))dlsym(dlHandle,"pf_new");
    if(NULL == pfn)
    {
	PyErr_SetString(PyExc_ValueError,dlerror());
	return NULL;
    }
    pf_obj *p = pfn();
    pfh->pfo = p;
    pfh->pyhandle = pyobj;
#ifdef DEBUG_CREATION
    printf("%p : PF : CTOR (%p)\n",pfh,pfh->pfo);
#endif
    // refcount module so it can't be unloaded before all funcs are gone
    Py_INCREF(pyobj); 
    return PyCObject_FromVoidPtr(pfh,pf_delete);
}

void *
get_double_field(PyObject *pyitem, char *name, double *pVal)
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
get_double_array(PyObject *pyitem, char *name, double *pVal, int n)
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
	return NULL;
    }

    if(!(PySequence_Size(pyfield) == n))
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	return NULL;
    }

    for(int i = 0; i < n; ++i)
    {
	PyObject *py_subitem = PySequence_GetItem(pyfield,i);
	if(!py_subitem)
	{
	    PyErr_SetString(PyExc_ValueError, "Bad segment object");
	    return NULL; 
	}
	*(pVal+i)=PyFloat_AsDouble(py_subitem);

	Py_DECREF(py_subitem);
    }

    Py_DECREF(pyfield);

    return pVal;
}

void *
get_int_field(PyObject *pyitem, char *name, int *pVal)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem,name);
    if(pyfield == NULL)
    {
	PyErr_SetString(PyExc_ValueError, "Bad segment object");
	return NULL;
    }
    *pVal = PyInt_AsLong(pyfield);
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
	    return NULL;
	}
	
	cmap->set(i, left, right, mid,
		  left_col,right_col,
		  (e_blendType)bmode, (e_colorType)cmode);

	Py_DECREF(pyitem);
    }
    return cmap;
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

    pyret = PyCObject_FromVoidPtr(cmap,(void (*)(void *))cmap_delete);

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
	if(!PyFloat_Check(pyitem))
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
		return NULL;
	    }
	    if(PyFloat_Check(pyitem))
	    {
		params[i].t = FLOAT;
		params[i].doubleval = PyFloat_AsDouble(pyitem);
		//printf("%d = float(%g)\n",i,params[i].doubleval);
	    }
	    else if(PyInt_Check(pyitem))
	    {
		params[i].t = INT;
		params[i].intval = PyInt_AS_LONG(pyitem);
		//printf("%d = int(%d)\n",i,params[i].intval);
	    }
	    else if(
		PyObject_HasAttrString(pyitem,"cobject") &&
		PyObject_HasAttrString(pyitem,"segments"))
	    {
		PyObject *pycob = PyObject_GetAttrString(pyitem,"cobject");
		if(pycob == Py_None)
		{
		    Py_DECREF(pycob);
		    PyObject *pysegs = PyObject_GetAttrString(
			pyitem,"segments");

		    ColorMap *cmap = cmap_from_pyobject(pysegs);
		    Py_DECREF(pysegs);

		    if(NULL == cmap)
		    {
			return NULL;
		    }

		    pycob = PyCObject_FromVoidPtr(
			cmap, (void (*)(void *))cmap_delete);

		    if(NULL != pycob)
		    {
			PyObject_SetAttrString(pyitem,"cobject",pycob);
			// not quite correct, we are leaking some
			// cmap objects 
			Py_XINCREF(pycob);
		    }
		}
		params[i].t = GRADIENT;
		params[i].gradient = PyCObject_AsVoidPtr(pycob);
		//printf("%d = gradient(%p)\n",i,params[i].gradient);
		Py_DECREF(pycob);
	    }
	    else if(
		PyObject_HasAttrString(pyitem,"_img"))
	    {
		PyObject *pycob = PyObject_GetAttrString(pyitem,"_img");
		params[i].t = PARAM_IMAGE;
		params[i].image = PyCObject_AsVoidPtr(pycob);
		Py_DECREF(pycob);
	    }
	    else
	    {
		Py_XDECREF(pyitem);
		PyErr_SetString(
		    PyExc_ValueError,
		    "All params must be floats, ints, or gradients");
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
    double period_tolerance;
    struct s_param *params;
    struct pfHandle *pfh;
    double pos_params[N_PARAMS];

    if(!PyArg_ParseTuple(
	   args,"OdOO",&pyobj,&period_tolerance,&py_posparams, &pyarray))
    {
	return NULL;
    }
    if(!PyCObject_Check(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    pfh = (struct pfHandle *)PyCObject_AsVoidPtr(pyobj);

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
    pfh->pfo->vtbl->init(pfh->pfo,period_tolerance,pos_params,params,len);
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
	    PyList_SET_ITEM(pyret,i,PyInt_FromLong(params[i].intval));
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
    double period_tolerance;
    struct s_param *params;
    struct pfHandle *pfh;
    double pos_params[N_PARAMS];

    if(!PyArg_ParseTuple(
	   args,"OdOO",&pyobj,&period_tolerance,&py_posparams, &pyarray))
    {
	return NULL;
    }
    if(!PyCObject_Check(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    pfh = (struct pfHandle *)PyCObject_AsVoidPtr(pyobj);

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
	period_tolerance,
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
    int outIters=0, outFate=-777;
    double outDist=0.0;
    int outSolid=0;
    int fDirectColorFlag=0;
    double colors[4] = {0.0, 0.0, 0.0, 0.0};

    if(!PyArg_ParseTuple(args,"O(dddd)i|iii",
			 &pyobj,
			 &params[0],&params[1],&params[2],&params[3],
			 &nIters,&x,&y,&aa))
    {
	return NULL;
    }
    if(!PyCObject_Check(pyobj))
    {
	PyErr_SetString(PyExc_ValueError,"Not a valid handle");
	return NULL;
    }

    pfh = (struct pfHandle *)PyCObject_AsVoidPtr(pyobj);
#ifdef DEBUG_THREADS
    printf("%p : PF : CALC\n",pfh);
#endif
    pfh->pfo->vtbl->calc(pfh->pfo,params,
			 nIters, -1,
			 x,y,aa,
			 &outIters,&outFate,&outDist,&outSolid,
			 &fDirectColorFlag, &colors[0]);
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
	    return NULL; 
	}
	if(!PyArg_ParseTuple(pyitem,"diiii",&d,&r,&g,&b,&a))
	{
	    return NULL;
	}
	cmap->set(i,d,r,g,b,a);
	Py_DECREF(pyitem);
    }
    pyret = PyCObject_FromVoidPtr(cmap,(void (*)(void *))cmap_delete);

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

    cmap = (ColorMap *)PyCObject_AsVoidPtr(pycmap);
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

    cmap = (ColorMap *)PyCObject_AsVoidPtr(pycmap);
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

    cmap = (ColorMap *)PyCObject_AsVoidPtr(pyobj);
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

    cmap = (ColorMap *)PyCObject_AsVoidPtr(pyobj);
    if(!cmap)
    {
	return NULL;
    }

    color = cmap->lookup_with_transfer(d,solid,inside);
    
    pyret = Py_BuildValue("iiii",color.r,color.g,color.b,color.a);

    return pyret;
}

#ifdef THREADS
#define GET_LOCK PyEval_RestoreThread(state)
#define RELEASE_LOCK state = PyEval_SaveThread()
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

	    Py_INCREF(site);
	}

    virtual void iters_changed(int numiters)
	{
	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		"iters_changed",
		"i",
		numiters);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}
    
    // we've drawn a rectangle of image
    virtual void image_changed(int x1, int y1, int x2, int y2)
	{
	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		"image_changed",
		"iiii",x1,y1,x2,y2);
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
		"progress_changed",
		"d",d);
	    Py_XDECREF(ret);
	    RELEASE_LOCK;
	}
    // one of the status values above
    virtual void status_changed(int status_val)
	{
	    assert(this != NULL && site != NULL);
	    //printf("sc: %p %p\n",this,this->status_changed_cb);

	    GET_LOCK;
	    PyObject *ret = PyObject_CallMethod(
		site,
		"status_changed",
		"i", status_val);

	    if(PyErr_Occurred())
	    {
		printf("bad status 2\n");
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
		"is_interrupted",NULL);

	    bool ret = false;
	    if(PyInt_Check(pyret))
	    {
		long i = PyInt_AsLong(pyret);
		//printf("ret: %ld\n",i);
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
		    "pixel_changed",
		    "(dddd)iiiiidiiiiii",
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
	    //printf("dtor %p\n",this);
	    Py_DECREF(site);
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
    PIXEL
} msg_type_t;
    
typedef struct
{
    msg_type_t type;
    int p1,p2,p3,p4;
} msg_t;

struct calc_args
{
    double params[N_PARAMS];
    int eaa, maxiter, nThreads;
    int auto_deepen, yflip, periodicity, dirty;
    int asynchronous, warp_param;
    render_type_t render_type;
    pf_obj *pfo;
    ColorMap *cmap;
    IImage *im;
    IFractalSite *site;

    PyObject *pycmap, *pypfo, *pyim, *pysite;
    calc_args()
	{
#ifdef DEBUG_CREATION
	    printf("%p : CA : CTOR\n",this);
#endif
	    pycmap = NULL;
	    pypfo = NULL;
	    pyim = NULL;
	    pysite = NULL;
	    dirty = 1;
	    periodicity = true;
	    yflip = false;
	    auto_deepen = false;
	    eaa = AA_NONE;
	    maxiter = 1024;
	    nThreads = 1;
	    render_type = RENDER_TWO_D;
	    asynchronous = false;
	    warp_param = -1;
	}

    void set_cmap(PyObject *pycmap_)
	{
	    pycmap = pycmap_;
	    cmap = (ColorMap *)PyCObject_AsVoidPtr(pycmap);
	    Py_XINCREF(pycmap);
	}

    void set_pfo(PyObject *pypfo_)
	{
	    pypfo = pypfo_;

	    pfo = ((pfHandle *)PyCObject_AsVoidPtr(pypfo))->pfo;
	    Py_XINCREF(pypfo);
	}

    void set_im(PyObject *pyim_)
	{
	    pyim = pyim_;
	    im = (IImage *)PyCObject_AsVoidPtr(pyim);
	    Py_XINCREF(pyim);
	}
    void set_site(PyObject *pysite_)
	{
	    pysite = pysite_;
	    site = (IFractalSite *)PyCObject_AsVoidPtr(pysite);
	    Py_XINCREF(pysite);
	}

    ~calc_args()
	{
#ifdef DEBUG_CREATION
	    printf("%p : CA : DTOR\n",this);
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
	    printf("%p : FD : CTOR\n",this);
#endif
	    pthread_mutex_init(&write_lock,NULL);
	}

    inline void send(msg_t *pm)
	{
	    pthread_mutex_lock(&write_lock);
	    write(fd,pm,sizeof(msg_t));
	    pthread_mutex_unlock(&write_lock);
	}
    virtual void iters_changed(int numiters)
	{
	    msg_t m = { ITERS, 0, 0, 0, 0};
	    m.p1 = numiters;

	    send(&m);
	}
    
    // we've drawn a rectangle of image
    virtual void image_changed(int x1, int y1, int x2, int y2)
	{
	    if(!interrupted)
	    {
		msg_t m = { IMAGE };
		m.p1 = x1; m.p2 = y1; m.p3 = x2; m.p4 = y2;

		send(&m);
	    }
	}
    // estimate of how far through current pass we are
    virtual void progress_changed(float progress)
	{
	    if(!interrupted)
	    {
		msg_t m = { PROGRESS };
		m.p1 = (int) (100.0 * progress);
		m.p2 = m.p3 = m.p4 = 0;

		send(&m);
	    }
	}
    // one of the status values above
    virtual void status_changed(int status_val)
	{
	    msg_t m = { STATUS };
	    m.p1 = status_val;
	    m.p2 = m.p3 = m.p4 = 0;

	    send(&m);
	}

    // return true if we've been interrupted and are supposed to stop
    virtual bool is_interrupted()
	{
	    //printf("int: %d\n",interrupted);
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
	    printf("pixel: <%g,%g,%g,%g>(%d,%d,%d) = (%g,%d,%d)\n",
		   params[0],params[1],params[2],params[3],
		   x,y,aa,dist,fate,nIters);
	    */
	    return; // FIXME
	};

    virtual void interrupt() 
	{
#ifdef DEBUG_THREADS
	    printf("%p : CA : INT(%p)\n", this, tid);
#endif
	    interrupted = true;
	}
    
    virtual void start(calc_args *params_) 
	{
#ifdef DEBUG_THREADS
	    printf("clear interruption\n");
#endif
	    interrupted = false;
	    if(params != NULL)
	    {
		delete params;
	    }
	    params = params_;
	}

    virtual void set_tid(pthread_t tid_) 
	{
#ifdef DEBUG_THREADS
	    printf("%p : CA : SET(%p)\n", this,tid_);
#endif
	    tid = tid_;
	}

    virtual void wait()
	{
	    if(tid != 0)
	    {
#ifdef DEBUG_THREADS
		printf("%p : CA : WAIT(%p)\n", this,tid);
#endif
		pthread_join(tid,NULL);
	    }
	}
    ~FDSite()
	{
#ifdef DEBUG_CREATION
	    printf("%p : FD : DTOR\n",this);
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
    printf("%p : FF : DTOR\n",ffh);
#endif
    delete ffh->ff;
    Py_DECREF(ffh->pyhandle);
    delete ffh;
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

    //printf("pysite_create: %p\n",site);
    PyObject *pyret = PyCObject_FromVoidPtr(site,(void (*)(void *))site_delete);

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

    PyObject *pyret = PyCObject_FromVoidPtr(site,(void (*)(void *))site_delete);

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

    IFractalSite *site = (IFractalSite *)PyCObject_AsVoidPtr(pysite);
    if(!site)
    {
	return NULL;
    }

    site->interrupt();

    Py_INCREF(Py_None);
    return Py_None;
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

    cmap = (ColorMap *)PyCObject_AsVoidPtr(pycmap);
    pfo = ((pfHandle *)PyCObject_AsVoidPtr(pypfo))->pfo;
    im = (IImage *)PyCObject_AsVoidPtr(pyim);
    site = (IFractalSite *)PyCObject_AsVoidPtr(pysite);
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

    PyObject *pyret = PyCObject_FromVoidPtr(
	worker,(void (*)(void *))fw_delete);

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
    
    IFractWorker *worker = (IFractWorker *)PyCObject_AsVoidPtr(pyworker);
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
    
    IFractWorker *worker = (IFractWorker *)PyCObject_AsVoidPtr(pyworker);
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
    
    IFractWorker *worker = (IFractWorker *)PyCObject_AsVoidPtr(pyworker);
    dvec4 root;
    int ok = worker->find_root(eye,look,root);

    return Py_BuildValue(
	"i(dddd)",
	ok,root[0], root[1], root[2], root[3]);
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

    if(!PyArg_ParseTuple(
	   args,
	   "(ddddddddddd)iiiiOOiiiOOO",
	   &params[0],&params[1],&params[2],&params[3],
	   &params[4],&params[5],&params[6],&params[7],
	   &params[8],&params[9],&params[10],
	   &eaa,&maxiter,&yflip,&nThreads,
	   &pypfo,&pycmap,
	   &auto_deepen,
	   &periodicity,
	   &render_type,
	   &pyim, &pysite,
	   &pyworker
	   ))
    {
	return NULL;
    }

    cmap = (ColorMap *)PyCObject_AsVoidPtr(pycmap);
    pfo = ((pfHandle *)PyCObject_AsVoidPtr(pypfo))->pfo;
    im = (IImage *)PyCObject_AsVoidPtr(pyim);
    site = (IFractalSite *)PyCObject_AsVoidPtr(pysite);
    worker = (IFractWorker *)PyCObject_AsVoidPtr(pyworker);

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

    PyObject *pyret = PyCObject_FromVoidPtr(
	ffh,(void (*)(void *))ff_delete);

    Py_INCREF(pyworker);

    return pyret;
}


static void *
calculation_thread(void *vdata) 
{
    calc_args *args = (calc_args *)vdata;

#ifdef DEBUG_THREADS
    printf("%p : CA : CALC(%d)\n",args,pthread_self());
#endif

    calc(args->params,args->eaa,args->maxiter,
	 args->nThreads,args->pfo,args->cmap,
	 args->auto_deepen,args->yflip, args->periodicity, args->dirty,
	 0, // debug_flags
	 args->render_type,
	 args->warp_param,
	 args->im,args->site);

#ifdef DEBUG_THREADS 
    printf("%p : CA : ENDCALC(%d)\n",args,pthread_self());
#endif

    return NULL;
}

static calc_args *
parse_calc_args(PyObject *args, PyObject *kwds)
{
    PyObject *pyparams, *pypfo, *pycmap, *pyim, *pysite;
    calc_args *cargs = new calc_args();
    double *p = NULL;

    static char *kwlist[] = {
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
	"asynchronous",
	"warp_param",
	NULL};

    if(!PyArg_ParseTupleAndKeywords(
	   args,
	   kwds,
	   "OOOOO|iiiiiiiiii",
	   kwlist,

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
	   &cargs->asynchronous,
	   &cargs->warp_param
	   ))
    {
	goto error;
    }

    p = cargs->params;
    if(!PyList_Check(pyparams) || PyList_Size(pyparams) != N_PARAMS)
    {
	PyErr_SetString(PyExc_ValueError, "bad parameter list");
	delete cargs;
	return NULL;
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

    if(cargs->asynchronous)
    {
	cargs->site->interrupt();
	cargs->site->wait();

	cargs->site->start(cargs);

	pthread_t tid;

	/* create low-priority attribute block */
	pthread_attr_t lowprio_attr;
	struct sched_param lowprio_param;
	pthread_attr_init(&lowprio_attr);
	lowprio_param.sched_priority = sched_get_priority_min(SCHED_OTHER);
	pthread_attr_setschedparam(&lowprio_attr, &lowprio_param);

	/* start the calculation thread */
	pthread_create(&tid,&lowprio_attr,calculation_thread,(void *)cargs);
	assert(tid != 0);

	cargs->site->set_tid(tid);
    }
    else
    {
	// synchronous
	calc(cargs->params,
	     cargs->eaa,
	     cargs->maxiter,
	     cargs->nThreads,
	     cargs->pfo,
	     cargs->cmap,
	     cargs->auto_deepen,
	     cargs->yflip, 
	     cargs->periodicity, 
	     cargs->dirty,
	     0, // debug_flags
	     cargs->render_type,
	     cargs->warp_param,
	     cargs->im,
	     cargs->site);

	delete cargs;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static void
image_delete(IImage *image)
{
#ifdef DEBUG_CREATION
    printf("%p : IM : DTOR\n",image);
#endif
    delete image;
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
#ifdef DEBUG_CREATION
    printf("%p : IM : CTOR\n",i);
#endif
    i->set_resolution(x,y,totalx, totaly);

    if(! i->ok())
    {
	PyErr_SetString(PyExc_MemoryError, "Image too large");
	delete i;
	return NULL;
    }

    PyObject *pyret = PyCObject_FromVoidPtr(i,(void (*)(void *))image_delete);

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

    IImage *i = (IImage *)PyCObject_AsVoidPtr(pyim);
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

    IImage *i = (IImage *)PyCObject_AsVoidPtr(pyim);
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

    IImage *i = (IImage *)PyCObject_AsVoidPtr(pyim);
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

    IImage *i = (IImage *)PyCObject_AsVoidPtr(pyim);
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

static PyObject *
image_writer_create(PyObject *self,PyObject *args)
{
    PyObject *pyim;
    PyObject *pyFP;
    int file_type;
    if(!PyArg_ParseTuple(args,"OOi",&pyim,&pyFP,&file_type))
    {
	return NULL;
    }

    if(!PyFile_Check(pyFP))
    {
	return NULL;
    }

    image *i = (image *)PyCObject_AsVoidPtr(pyim);

    FILE *fp = PyFile_AsFile(pyFP);

    if(!fp || !i)
    {
	PyErr_SetString(PyExc_ValueError, "Bad arguments");
	return NULL;
    }
    
    ImageWriter *writer = ImageWriter::create((image_file_t)file_type, fp, i);
    if(NULL == writer)
    {
	PyErr_SetString(PyExc_ValueError, "Unsupported file type");
	return NULL;
    }

    return PyCObject_FromVoidPtr(
	writer, (void (*)(void *))image_writer_delete);
}

static PyObject *
image_read(PyObject *self,PyObject *args)
{
    PyObject *pyim;
    PyObject *pyFP;
    int file_type;
    if(!PyArg_ParseTuple(args,"OOi",&pyim,&pyFP,&file_type))
    {
	return NULL;
    }

    if(!PyFile_Check(pyFP))
    {
	return NULL;
    }

    image *i = (image *)PyCObject_AsVoidPtr(pyim);

    FILE *fp = PyFile_AsFile(pyFP);

    if(!fp || !i)
    {
	PyErr_SetString(PyExc_ValueError, "Bad arguments");
	return NULL;
    }
    
    ImageReader *reader = ImageReader::create((image_file_t)file_type, fp, i);
    //if(!reader->ok())
    //{
    //	PyErr_SetString(PyExc_IOError, "Couldn't create image reader");
    //	delete reader;
    //	return NULL;
    //}

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

    ImageWriter *i = (ImageWriter *)PyCObject_AsVoidPtr(pyimwriter);

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

    ImageWriter *i = (ImageWriter *)PyCObject_AsVoidPtr(pyimwriter);

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

    ImageWriter *i = (ImageWriter *)PyCObject_AsVoidPtr(pyimwriter);

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

    image *i = (image *)PyCObject_AsVoidPtr(pyim);

#ifdef DEBUG_CREATION
    printf("%p : IM : BUF\n",i);
#endif

    if(! i->ok())
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
    pybuf = PyBuffer_FromReadWriteMemory(i->getBuffer()+offset,i->bytes()-offset);
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

    image *i = (image *)PyCObject_AsVoidPtr(pyim);

#ifdef DEBUG_CREATION
    printf("%p : IM : BUF\n",i);
#endif

    if(x < 0 || x >= i->Xres() || y < 0 || y >= i->Yres())
    {
	PyErr_SetString(PyExc_ValueError,"request for buffer outside image bounds");
	return NULL;
    }
    int index = i->index_of_subpixel(x,y,0);
    int last_index = i->index_of_sentinel_subpixel();
    assert(index > -1 && index < last_index);

    pybuf = PyBuffer_FromReadWriteMemory(
	i->getFateBuffer()+index,
	(last_index - index)  * sizeof(fate_t));

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

    image *i = (image *)PyCObject_AsVoidPtr(pyim);
    
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

    image *i = (image *)PyCObject_AsVoidPtr(pyim);
    
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

    struct ffHandle *ffh = (struct ffHandle *)PyCObject_AsVoidPtr(pyFF);
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

    struct ffHandle *ffh = (struct ffHandle *)PyCObject_AsVoidPtr(pyFF);
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

    image *i = (image *)PyCObject_AsVoidPtr(pyimage);
    
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

static PyMethodDef PfMethods[] = {
    {"pf_load",  pf_load, METH_VARARGS, 
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
      "Stop an asynchronous calculation" },

    { "rot_matrix", rot_matrix, METH_VARARGS,
      "Return a rotated and scaled identity matrix based on params"},

    { "eye_vector", eye_vector, METH_VARARGS,
      "Return the line between the user's eye and the center of the screen"},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

extern "C" PyMODINIT_FUNC
#ifdef USE_GMP
initfract4dcgmp(void)
#else
initfract4dc(void)
#endif
{
    pymod = Py_InitModule(MODULE_NAME, PfMethods);

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
}
