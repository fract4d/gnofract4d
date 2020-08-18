#include "Python.h"
#include <thread>
#include <iostream>

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

    PyObject * pystop_calc([[maybe_unused]] PyObject *self, PyObject *args)
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

    PyObject * pycalc_xaos([[maybe_unused]] PyObject *self, PyObject *args, PyObject *kwds)
    {
        calc_args *cargs = parse_calc_args(args, kwds);
        if (NULL == cargs)
        {
            return NULL;
        }

        std::thread t([cargs](){
            auto &site = *cargs->site;
            site.interrupt();
            site.wait();
            site.start();
            site.set_thread(std::thread(calculation_thread, cargs));
        });
        t.detach();

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * pycalc([[maybe_unused]] PyObject *self, PyObject *args, PyObject *kwds)
    {
        calc_args *cargs = parse_calc_args(args, kwds);
        if (NULL == cargs)
        {
            return NULL;
        }

        if (cargs->asynchronous)
        {
            std::thread t([cargs](){
                auto &site = *cargs->site;
                site.interrupt();
                site.wait();
                site.start();
                site.set_thread(std::thread(calculation_thread, cargs));
            });
            t.detach();
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

struct GIL_guard {
    PyGILState_STATE state;
    bool active;
    GIL_guard():
        state(PyGILState_Ensure()), active(true) {}
    void restore()
    {
        PyGILState_Release(state);
        active = false;
    }
    ~GIL_guard()
    {
        if (active) restore();
    }
};
void * calculation_thread_xaos(calc_args *args)
{
    calc_xaos(
        args->options,
        args->params,
        args->params_previous,
        args->pfo,
        args->cmap,
        args->site,
        args->im,
        0 // debug_flags
    );
    delete args;
    return NULL;
}

void * calculation_thread(calc_args *args)
{
#ifdef DEBUG_THREADS
    std::cerr << args << " : CA : CALC(" << std::this_thread::get_id() << ")\n";
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
    std::cerr << args << " : CA : ENDCALC(" << std::this_thread::get_id() << ")\n";
#endif
    GIL_guard e;
    delete args;
    return NULL;
}

calc_args * parse_calc_args(PyObject *args, PyObject *kwds)
{
    PyObject *pyparams, *pypfo, *pycmap, *pyim, *pysite;
    PyObject *pyparams_previous = NULL;
    calc_args *cargs = new calc_args();

    const char *kwlist[] = {
        "image",
        "site",
        "pfo",
        "cmap",
        "params",
        "params_previous",
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
            "OOOOO|Oiiiiiiiiiidi",
            const_cast<char **>(kwlist),

            &pyim, &pysite,
            &pypfo, &pycmap,
            &pyparams,
            &pyparams_previous,
            &cargs->options.eaa,
            &cargs->options.maxiter,
            &cargs->options.yflip,
            &cargs->options.nThreads,
            &cargs->options.auto_deepen,
            &cargs->options.periodicity,
            &cargs->options.render_type,
            &cargs->options.dirty,
            &cargs->asynchronous,
            &cargs->options.warp_param,
            &cargs->options.period_tolerance,
            &cargs->options.auto_tolerance))
    {
        goto error;
    }

    if (!parse_posparams(pyparams, cargs->params))
    {
        goto error;
    }

    if (pyparams_previous != NULL)
    {
        if (!parse_posparams(pyparams_previous, cargs->params_previous))
        {
            goto error;
        }
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

