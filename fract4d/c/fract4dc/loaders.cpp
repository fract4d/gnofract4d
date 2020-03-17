#include "Python.h"

#include <dlfcn.h>
#include "assert.h"

#include "common.h"
#include "colormaps.h"
#include "loaders.h"


namespace loaders
{

    PyObject *module_load(PyObject *self, PyObject *args)
    {
    #ifdef STATIC_CALC
        Py_INCREF(Py_None);
        return Py_None;
    #else

        char *so_filename;
        if (!PyArg_ParseTuple(args, "s", &so_filename))
        {
            return NULL;
        }

        void *dlHandle = dlopen(so_filename, RTLD_NOW);
    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : SO : REF\n", dlHandle);
    #endif
        if (NULL == dlHandle)
        {
            /* an error */
            PyErr_SetString(PyExc_ValueError, dlerror());
            return NULL;
        }
        return PyCapsule_New(dlHandle, OBTYPE_MODULE, module_unload);
    #endif
    }

    PyObject * pf_create(PyObject *self, PyObject *args)
    {
        struct pfHandle *pfh = (pfHandle *)malloc(sizeof(struct pfHandle));
        void *dlHandle;
        pf_obj *(*pfn)(void);

        PyObject *pyobj;
    #ifdef STATIC_CALC
        pf_obj *p = pf_new();
        pyobj = Py_None;
    #else

        if (!PyArg_ParseTuple(args, "O", &pyobj))
        {
            return NULL;
        }
        if (!PyCapsule_CheckExact(pyobj))
        {
            PyErr_SetString(PyExc_ValueError, "Not a valid handle");
            return NULL;
        }

        dlHandle = module_fromcapsule(pyobj);
        pfn = (pf_obj * (*)(void)) dlsym(dlHandle, "pf_new");
        if (NULL == pfn)
        {
            PyErr_SetString(PyExc_ValueError, dlerror());
            return NULL;
        }
        pf_obj *p = pfn();
    #endif
        pfh->pfo = p;
        pfh->pyhandle = pyobj;
    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : PF : CTOR (%p)\n", pfh, pfh->pfo);
    #endif
        // refcount module so it can't be unloaded before all funcs are gone
        Py_INCREF(pyobj);
        return PyCapsule_New(pfh, OBTYPE_POINTFUNC, pf_delete);
    }


    PyObject * pf_init(PyObject *self, PyObject *args)
    {
        PyObject *pyobj, *pyarray, *py_posparams;
        struct s_param *params;
        struct pfHandle *pfh;
        double pos_params[N_PARAMS];

        if (!PyArg_ParseTuple(
                args, "OOO", &pyobj, &py_posparams, &pyarray))
        {
            return NULL;
        }
        if (!PyCapsule_CheckExact(pyobj))
        {
            PyErr_SetString(PyExc_ValueError, "Not a valid handle");
            return NULL;
        }

        pfh = pf_fromcapsule(pyobj);

        if (!parse_posparams(py_posparams, pos_params))
        {
            return NULL;
        }

        int len = 0;
        params = parse_params(pyarray, &len);
        if (!params)
        {
            return NULL;
        }

        /*finally all args are assembled */
        pfh->pfo->vtbl->init(pfh->pfo, pos_params, params, len);
        free(params);

        Py_INCREF(Py_None);
        return Py_None;
    }


    PyObject * pf_defaults(PyObject *self, PyObject *args)
    {
        PyObject *pyobj, *pyarray, *py_posparams;
        struct s_param *params;
        struct pfHandle *pfh;
        double pos_params[N_PARAMS];

        if (!PyArg_ParseTuple(
                args, "OOO", &pyobj, &py_posparams, &pyarray))
        {
            return NULL;
        }
        if (!PyCapsule_CheckExact(pyobj))
        {
            PyErr_SetString(PyExc_ValueError, "Not a valid handle");
            return NULL;
        }

        pfh = pf_fromcapsule(pyobj);

        if (!parse_posparams(py_posparams, pos_params))
        {
            return NULL;
        }

        int len = 0;
        params = parse_params(pyarray, &len);
        if (!params)
        {
            return NULL;
        }

        /*finally all args are assembled */
        pfh->pfo->vtbl->get_defaults(
            pfh->pfo,
            pos_params,
            params,
            len);

        PyObject *pyret = params_to_python(params, len);
        free(params);

        return pyret;
    }

    PyObject * pf_calc(PyObject *self, PyObject *args)
    {
        PyObject *pyobj, *pyret;
        double params[4];
        struct pfHandle *pfh;
        int nIters, x = 0, y = 0, aa = 0;
        int repeats = 1;
        int outIters = 0, outFate = -777;
        double outDist = 0.0;
        int outSolid = 0;
        int fDirectColorFlag = 0;
        double colors[4] = {0.0, 0.0, 0.0, 0.0};

        if (!PyArg_ParseTuple(args, "O(dddd)i|iiii",
                            &pyobj,
                            &params[0], &params[1], &params[2], &params[3],
                            &nIters, &x, &y, &aa, &repeats))
        {
            return NULL;
        }
        if (!PyCapsule_CheckExact(pyobj))
        {
            PyErr_SetString(PyExc_ValueError, "Not a valid handle");
            return NULL;
        }

        pfh = pf_fromcapsule(pyobj);
    #ifdef DEBUG_THREADS
        fprintf(stderr, "%p : PF : CALC\n", pfh);
    #endif
        for (int i = 0; i < repeats; ++i)
        {
            pfh->pfo->vtbl->calc(
                pfh->pfo, params,
                nIters, -1,
                nIters, 1.0E-9,
                x, y, aa,
                &outIters, &outFate, &outDist, &outSolid,
                &fDirectColorFlag, &colors[0]);
        }
        assert(outFate != -777);
        pyret = Py_BuildValue("iidi", outIters, outFate, outDist, outSolid);
        return pyret; // Python can handle errors if this is NULL
    }


    struct pfHandle * pf_fromcapsule(PyObject *capsule)
    {
        struct pfHandle *pfHandle = (struct pfHandle *)PyCapsule_GetPointer(capsule, OBTYPE_POINTFUNC);
        if (NULL == pfHandle)
        {
            fprintf(stderr, "%p : PF : BAD\n", capsule);
        }
        return pfHandle;
    }

    void pf_delete(PyObject *p)
    {
        struct pfHandle *pfh = pf_fromcapsule(p);
    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : PF : DTOR\n", pfh);
    #endif
        pfh->pfo->vtbl->kill(pfh->pfo);
        Py_DECREF(pfh->pyhandle);
        free(pfh);
    }

    void module_unload(PyObject *p)
    {
        void *vp = module_fromcapsule(p);
    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : SO : CLOSE\n", vp);
    #endif

    #ifndef STATIC_CALC
        dlclose(vp);
    #endif
    }

    void * module_fromcapsule(PyObject *p)
    {
        void *vp = PyCapsule_GetPointer(p, OBTYPE_MODULE);
        if (NULL == vp)
        {
            fprintf(stderr, "%p : SO : BAD\n", p);
        }

        return vp;
    }

} // namespace loaders


/*
* UTILS
*/


bool parse_posparams(PyObject *py_posparams, double *pos_params)
{
    // check and parse pos_params
    if (!PySequence_Check(py_posparams))
    {
        PyErr_SetString(PyExc_TypeError,
                        "Positional params should be an array of floats");
        return false;
    }

    int len = PySequence_Size(py_posparams);
    if (len != N_PARAMS)
    {
        PyErr_SetString(
            PyExc_ValueError,
            "Wrong number of positional params");
        return false;
    }

    for (int i = 0; i < N_PARAMS; ++i)
    {
        PyObject *pyitem = PySequence_GetItem(py_posparams, i);
        if (pyitem == NULL || !PyFloat_Check(pyitem))
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


s_param * parse_params(PyObject *pyarray, int *plen)
{
    struct s_param *params;

    // check and parse fractal params
    if (!PySequence_Check(pyarray))
    {
        PyErr_SetString(PyExc_TypeError,
                        "parameters argument should be an array");
        return NULL;
    }

    int len = PySequence_Size(pyarray);
    if (len == 0)
    {
        params = (struct s_param *)malloc(sizeof(struct s_param));
        params[0].t = FLOAT;
        params[0].doubleval = 0.0;
    }
    else if (len > PF_MAXPARAMS)
    {
        PyErr_SetString(PyExc_ValueError, "Too many parameters");
        return NULL;
    }
    else
    {
        int i = 0;
        params = (struct s_param *)malloc(len * sizeof(struct s_param));
        if (!params)
            return NULL;
        for (i = 0; i < len; ++i)
        {
            PyObject *pyitem = PySequence_GetItem(pyarray, i);
            if (NULL == pyitem)
            {
                free(params);
                return NULL;
            }
            if (PyFloat_Check(pyitem))
            {
                params[i].t = FLOAT;
                params[i].doubleval = PyFloat_AsDouble(pyitem);
                //fprintf(stderr,"%d = float(%g)\n",i,params[i].doubleval);
            }
            else if (PyLong_Check(pyitem))
            {
                params[i].t = INT;
                params[i].intval = PyLong_AS_LONG(pyitem);
                //fprintf(stderr,"%d = int(%d)\n",i,params[i].intval);
            }
            else if (
                PyObject_HasAttrString(pyitem, "cobject") &&
                PyObject_HasAttrString(pyitem, "segments"))
            {
                // looks like a colormap. Either we already have an object, which we can use now,
                // or we need to construct one from a list of segments
                PyObject *pycob = PyObject_GetAttrString(pyitem, "cobject");
                if (pycob == Py_None || pycob == NULL)
                {
                    Py_XDECREF(pycob);
                    PyObject *pysegs = PyObject_GetAttrString(
                        pyitem, "segments");

                    ColorMap *cmap;
                    if (pysegs == Py_None || pysegs == NULL)
                    {
                        cmap = NULL;
                    }
                    else
                    {
                        cmap = colormaps::cmap_from_pyobject(pysegs);
                    }

                    Py_XDECREF(pysegs);

                    if (NULL == cmap)
                    {
                        PyErr_SetString(PyExc_ValueError, "Invalid colormap object");
                        free(params);
                        return NULL;
                    }

                    pycob = PyCapsule_New(cmap, OBTYPE_CMAP, colormaps::pycmap_delete);

                    if (NULL != pycob)
                    {
                        PyObject_SetAttrString(pyitem, "cobject", pycob);
                        // not quite correct, we are leaking some
                        // cmap objects
                        Py_INCREF(pycob);
                    }
                }
                params[i].t = GRADIENT;
                params[i].gradient = colormaps::cmap_fromcapsule(pycob);
                //fprintf(stderr,"%d = gradient(%p)\n",i,params[i].gradient);
                Py_XDECREF(pycob);
            }
            else if (
                PyObject_HasAttrString(pyitem, "_img"))
            {
                PyObject *pycob = PyObject_GetAttrString(pyitem, "_img");
                params[i].t = PARAM_IMAGE;
                params[i].image = PyCapsule_GetPointer(pycob, OBTYPE_IMAGE);
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

/* convert an array of params from the s_param representation to a Python list */
PyObject * params_to_python(struct s_param *params, int len)
{
    PyObject *pyret = PyList_New(len);
    if (!pyret)
    {
        PyErr_SetString(PyExc_MemoryError, "Can't allocate defaults list");
        return NULL;
    }
    for (int i = 0; i < len; ++i)
    {
        switch (params[i].t)
        {
        case FLOAT:
            PyList_SET_ITEM(pyret, i, PyFloat_FromDouble(params[i].doubleval));
            break;
        case INT:
            PyList_SET_ITEM(pyret, i, PyLong_FromLong(params[i].intval));
            break;
        case GRADIENT:
            Py_INCREF(Py_None);
            PyList_SET_ITEM(pyret, i, Py_None);
            break;
        default:
            assert(0 && "Unexpected type for parameter");
            Py_INCREF(Py_None);
            PyList_SET_ITEM(pyret, i, Py_None);
        }
    }
    return pyret;
}