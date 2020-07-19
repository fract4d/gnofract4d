#include "Python.h"
#include "functions.h"

#include "fract4dc/common.h"
#include "fract4dc/colormaps.h"
#include "fract4dc/loaders.h"
#include "fract4dc/images.h"
#include "fract4dc/sites.h"
#include "fract4dc/workers.h"
#include "model/enums.h"
#include "model/worker.h"
#include "model/fractfunc.h"
#include "model/calcoptions.h"

#include "pf.h"

namespace functions {

    PyObject * ff_create([[maybe_unused]] PyObject *self, PyObject *args)
    {
        PyObject *pypfo, *pycmap, *pyim, *pysite, *pyworker;
        double params[N_PARAMS];
        pf_obj *pfo;
        ColorMap *cmap;
        IImage *im;
        IFractalSite *site;
        IFractWorker *worker;
        calc_options options;

        if (!PyArg_ParseTuple(
                args,
                "(ddddddddddd)iiiiOOiiiOOOid",
                &params[0], &params[1], &params[2], &params[3],
                &params[4], &params[5], &params[6], &params[7],
                &params[8], &params[9], &params[10],
                &options.eaa, &options.maxiter, &options.yflip, &options.nThreads,
                &pypfo, &pycmap,
                &options.auto_deepen,
                &options.periodicity,
                &options.render_type,
                &pyim, &pysite,
                &pyworker,
                &options.auto_tolerance, &options.period_tolerance))
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
            options,
            params,
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

        // refcount worker so it can't be unloaded before funct is gone
        Py_INCREF(pyworker);

        return pyret;
    }

    PyObject * ff_get_vector([[maybe_unused]] PyObject *self, PyObject *args)
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
            vec = ff->get_geometry().deltax;
            break;
        case DELTA_Y:
            vec = ff->get_geometry().deltay;
            break;
        case TOPLEFT:
            vec = ff->get_geometry().topleft;
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

    PyObject * ff_look_vector([[maybe_unused]] PyObject *self, PyObject *args)
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

        dvec4 lookvec = ff->get_geometry().vec_for_point_3d(x, y);

        return Py_BuildValue(
            "(dddd)",
            lookvec[0], lookvec[1], lookvec[2], lookvec[3]);
    }
}


void pyff_delete(PyObject *pyff)
{
    ffHandle *ff = (ffHandle *)PyCapsule_GetPointer(pyff, OBTYPE_FFH);
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FF : DTOR\n", ff);
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
        fprintf(stderr, "%p : FF : BAD\n", static_cast<void *>(ff));
    }
    return ff;
}