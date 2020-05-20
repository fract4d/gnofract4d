#include "Python.h"
#include <pthread.h>

#include "calcs.h"

#include "model/calcfunc.h"
#include "model/site.h"
#include "model/image.h"

#include "fract4dc/calcargs.h"
#include "fract4dc/loaders.h"
#include "fract4dc/colormaps.h"
#include "fract4dc/images.h"
#include "fract4dc/sites.h"

namespace calcs {

    PyObject * pystop_calc(PyObject *self, PyObject *args)
    {
        PyObject *pysite;
        if (!PyArg_ParseTuple(args, "O", &pysite))
        {
            return NULL;
        }

        IFractalSite *site = sites::site_fromcapsule(pysite);
        if (!site)
        {
            return NULL;
        }

        site->interrupt();

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * pycalc(PyObject *self, PyObject *args, PyObject *kwds)
    {
        calc_args *cargs = parse_calc_args(args, kwds);
        if (NULL == cargs)
        {
            return NULL;
        }

        if (cargs->options.asynchronous)
        {
            cargs->site->interrupt();
            cargs->site->wait();

            // cargs->site->start(cargs);
            cargs->site->start();

            pthread_t tid;

            /* create low-priority attribute block */
            pthread_attr_t lowprio_attr;
            //struct sched_param lowprio_param;
            pthread_attr_init(&lowprio_attr);
            //lowprio_param.sched_priority = sched_get_priority_min(SCHED_OTHER);
            //pthread_attr_setschedparam(&lowprio_attr, &lowprio_param);

            /* start the calculation thread */
            pthread_create(&tid, &lowprio_attr, calculation_thread, (void *)cargs);
            assert(tid != 0);

            cargs->site->set_tid(tid);
        }
        else
        {
            Py_BEGIN_ALLOW_THREADS
                // synchronous
                calc(
                    cargs->options,
                    cargs->params,
                    cargs->pfo,
                    cargs->cmap,
                    cargs->site,
                    cargs->im,
                    0 // debug_flags
                );

            delete cargs;
            Py_END_ALLOW_THREADS
        }

        Py_INCREF(Py_None);

        return Py_None;
    }
}


void * calculation_thread(void *vdata)
{
    calc_args *args = (calc_args *)vdata;

#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : CALC(%d)\n", args, pthread_self());
#endif

    calc(
        args->options,
        args->params,
        args->pfo,
        args->cmap,
        args->site,
        args->im,
        0 // debug_flags
    );

#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : ENDCALC(%d)\n", args, pthread_self());
#endif

    delete args;
    return NULL;
}

calc_args * parse_calc_args(PyObject *args, PyObject *kwds)
{
    PyObject *pyparams, *pypfo, *pycmap, *pyim, *pysite;
    calc_args *cargs = new calc_args();
    double *p = NULL;

    const char *kwlist[] = {
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
        "tolerance",
        "auto_tolerance",
        NULL};

    if (!PyArg_ParseTupleAndKeywords(
            args,
            kwds,
            "OOOOO|iiiiiiiiiidi",
            const_cast<char **>(kwlist),

            &pyim, &pysite,
            &pypfo, &pycmap,
            &pyparams,
            &cargs->options.eaa,
            &cargs->options.maxiter,
            &cargs->options.yflip,
            &cargs->options.nThreads,
            &cargs->options.auto_deepen,
            &cargs->options.periodicity,
            &cargs->options.render_type,
            &cargs->options.dirty,
            &cargs->options.asynchronous,
            &cargs->options.warp_param,
            &cargs->options.period_tolerance,
            &cargs->options.auto_tolerance))
    {
        goto error;
    }

    p = cargs->params;
    if (!PyList_Check(pyparams) || PyList_Size(pyparams) != N_PARAMS)
    {
        PyErr_SetString(PyExc_ValueError, "bad parameter list");
        goto error;
    }

    // todo: code duplicated in loaders.cpp (parse_params function)
    for (int i = 0; i < N_PARAMS; ++i)
    {
        PyObject *elt = PyList_GetItem(pyparams, i);
        if (!PyFloat_Check(elt))
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

    if (!cargs->cmap || !cargs->pfo ||
        !cargs->im || !cargs->site)
    {
        PyErr_SetString(PyExc_ValueError, "bad argument passed to calc");
        goto error;
    }

    if (!cargs->im->ok())
    {
        PyErr_SetString(PyExc_MemoryError, "image not allocated");
        goto error;
    }

    return cargs;

error:
    delete cargs;
    return NULL;
}

