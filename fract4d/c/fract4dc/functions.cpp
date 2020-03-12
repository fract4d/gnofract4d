#include "Python.h"

#include "functions.h"

#include "common.h"

#include "colormaps.h"
#include "loaders.h"
#include "images.h"
#include "sites.h"
#include "workers.h"

#include "../pf.h"
#include "../fract_public.h"
#include "../fractWorker_public.h"


namespace functions {

    PyObject * ff_create(PyObject *self, PyObject *args)
    {
        PyObject *pypfo, *pycmap, *pyim, *pysite, *pyworker;
        double params[N_PARAMS];
        int eaa = -7, maxiter = -8, nThreads = -9;
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

        if (!PyArg_ParseTuple(
                args,
                "(ddddddddddd)iiiiOOiiiOOOid",
                &params[0], &params[1], &params[2], &params[3],
                &params[4], &params[5], &params[6], &params[7],
                &params[8], &params[9], &params[10],
                &eaa, &maxiter, &yflip, &nThreads,
                &pypfo, &pycmap,
                &auto_deepen,
                &periodicity,
                &render_type,
                &pyim, &pysite,
                &pyworker,
                &auto_tolerance, &tolerance))
        {
            return NULL;
        }

        cmap = colormaps::cmap_fromcapsule(pycmap);
        pfo = (loaders::pf_fromcapsule(pypfo))->pfo;
        im = images::image_fromcapsule(pyim);
        site = sites::site_fromcapsule(pysite);
        worker = workers::fw_fromcapsule(pyworker);

        if (!cmap || !pfo || !im || !site || !worker)
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

        if (!ff)
        {
            return NULL;
        }

        ffHandle *ffh = new struct ffHandle;
        ffh->ff = ff;
        ffh->pyhandle = pyworker;

    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : FF : CTOR\n", ffh);
    #endif

        PyObject *pyret = PyCapsule_New(ffh, OBTYPE_FFH, pyff_delete);

        Py_INCREF(pyworker);

        return pyret;
    }

    PyObject * ff_get_vector(PyObject *self, PyObject *args)
    {
        int vec_type;
        PyObject *pyFF;

        if (!PyArg_ParseTuple(
                args,
                "Oi",
                &pyFF, &vec_type))
        {
            return NULL;
        }

        struct ffHandle *ffh = ff_fromcapsule(pyFF);
        if (ffh == NULL)
        {
            return NULL;
        }

        fractFunc *ff = ffh->ff;
        if (ff == NULL)
        {
            return NULL;
        }

        dvec4 vec;
        switch (vec_type)
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

    PyObject * ff_look_vector(PyObject *self, PyObject *args)
    {
        PyObject *pyFF;
        double x, y;
        if (!PyArg_ParseTuple(
                args,
                "Odd",
                &pyFF, &x, &y))
        {
            return NULL;
        }

        struct ffHandle *ffh = ff_fromcapsule(pyFF);
        if (ffh == NULL)
        {
            return NULL;
        }

        fractFunc *ff = ffh->ff;
        if (ff == NULL)
        {
            return NULL;
        }

        dvec4 lookvec = ff->vec_for_point(x, y);

        return Py_BuildValue(
            "(dddd)",
            lookvec[0], lookvec[1], lookvec[2], lookvec[3]);
    }
}


void pyff_delete(PyObject *pyff)
{
    ffHandle *ff = (ffHandle *)PyCapsule_GetPointer(pyff, OBTYPE_FFH);
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FF : DTOR\n", ffh);
#endif
    delete ff->ff;
    Py_DECREF(ff->pyhandle);
    delete ff;
}


ffHandle * ff_fromcapsule(PyObject *pyff)
{
    ffHandle *ff = (ffHandle *)PyCapsule_GetPointer(pyff, OBTYPE_FFH);
    if (NULL == ff)
    {
        fprintf(stderr, "%p : FF : CTOR\n", ff);
    }
    return ff;
}