#include "Python.h"

#include <pthread.h>

#include "../fract_public.h"
#include "../fractFunc.h"

#include "calcs.h"
#include "loaders.h"
#include "colormaps.h"
#include "images.h"
#include "sites.h"


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

        if (cargs->asynchronous)
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
            pthread_create(&tid, &lowprio_attr, calculation_thread, (void *)cargs);
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
}


void * calculation_thread(void *vdata)
{
    calc_args *args = (calc_args *)vdata;

#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : CALC(%d)\n", args, pthread_self());
#endif

    calc(args->params, args->eaa, args->maxiter,
         args->nThreads, args->pfo, args->cmap,
         args->auto_deepen,
         args->auto_tolerance,
         args->tolerance,
         args->yflip, args->periodicity, args->dirty,
         0, // debug_flags
         args->render_type,
         args->warp_param,
         args->im, args->site);

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
            &cargs->eaa,
            &cargs->maxiter,
            &cargs->yflip,
            &cargs->nThreads,
            &cargs->auto_deepen,
            &cargs->periodicity,
            &cargs->render_type,
            &cargs->dirty,
            &cargs->asynchronous,
            &cargs->warp_param,
            &cargs->tolerance,
            &cargs->auto_tolerance))
    {
        goto error;
    }

    p = cargs->params;
    if (!PyList_Check(pyparams) || PyList_Size(pyparams) != N_PARAMS)
    {
        PyErr_SetString(PyExc_ValueError, "bad parameter list");
        goto error;
    }

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


calc_args::calc_args()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : CA : CTOR\n", this);
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
    asynchronous = false;
    warp_param = -1;
}

void calc_args::set_cmap(PyObject *pycmap_)
{
    pycmap = pycmap_;
    cmap = colormaps::cmap_fromcapsule(pycmap);
    Py_XINCREF(pycmap);
}

void calc_args::set_pfo(PyObject *pypfo_)
{
    pypfo = pypfo_;

    pfo = (loaders::pf_fromcapsule(pypfo))->pfo;
    Py_XINCREF(pypfo);
}

void calc_args::set_im(PyObject *pyim_)
{
    pyim = pyim_;
    im = images::image_fromcapsule(pyim);
    Py_XINCREF(pyim);
}
void calc_args::set_site(PyObject *pysite_)
{
    pysite = pysite_;
    site = sites::site_fromcapsule(pysite);
    Py_XINCREF(pysite);
}

calc_args::~calc_args()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : CA : DTOR\n", this);
#endif
    Py_XDECREF(pycmap);
    Py_XDECREF(pypfo);
    Py_XDECREF(pyim);
    Py_XDECREF(pysite);
}
