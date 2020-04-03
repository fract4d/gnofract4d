#include "Python.h"

#include "workers.h"
#include "common.h"

#include "colormaps.h"
#include "loaders.h"
#include "images.h"
#include "sites.h"


namespace workers {

    IFractWorker * fw_fromcapsule(PyObject *capsule)
    {
        IFractWorker *worker = (IFractWorker *)PyCapsule_GetPointer(capsule, OBTYPE_WORKER);
        return worker;
    }

    PyObject * fw_create(PyObject *self, PyObject *args)
    {
        int nThreads;
        pf_obj *pfo;
        ColorMap *cmap;
        IImage *im;
        IFractalSite *site;

        PyObject *pypfo, *pycmap, *pyim, *pysite;

        if (!PyArg_ParseTuple(args, "iOOOO",
                            &nThreads,
                            &pypfo,
                            &pycmap,
                            &pyim,
                            &pysite))
        {
            return NULL;
        }

        cmap = colormaps::cmap_fromcapsule(pycmap);
        pfo = (loaders::pf_fromcapsule(pypfo))->pfo;
        im = images::image_fromcapsule(pyim);
        site = sites::site_fromcapsule(pysite);
        if (!cmap || !pfo || !im || !im->ok() || !site)
        {
            return NULL;
        }

        IFractWorker *worker = IFractWorker::create(nThreads, pfo, cmap, im, site);

        if (!worker->ok())
        {
            PyErr_SetString(PyExc_ValueError, "Error creating worker");
            delete worker;
            return NULL;
        }

        PyObject *pyret = PyCapsule_New(worker, OBTYPE_WORKER, pyfw_delete);

        return pyret;
    }

    PyObject * fw_pixel(PyObject *self, PyObject *args)
    {
        PyObject *pyworker;
        int x, y, w, h;

        if (!PyArg_ParseTuple(args, "Oiiii",
                            &pyworker,
                            &x, &y, &w, &h))
        {
            return NULL;
        }

        IFractWorker *worker = fw_fromcapsule(pyworker);
        worker->pixel(x, y, w, h);

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * fw_pixel_aa(PyObject *self, PyObject *args)
    {
        PyObject *pyworker;
        int x, y;

        if (!PyArg_ParseTuple(args, "Oii",
                            &pyworker,
                            &x, &y))
        {
            return NULL;
        }

        IFractWorker *worker = fw_fromcapsule(pyworker);
        worker->pixel_aa(x, y);

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * fw_find_root(PyObject *self, PyObject *args)
    {
        PyObject *pyworker;
        dvec4 eye, look;

        if (!PyArg_ParseTuple(args, "O(dddd)(dddd)",
                            &pyworker,
                            &eye[VX], &eye[VY], &eye[VZ], &eye[VW],
                            &look[VX], &look[VY], &look[VZ], &look[VW]))
        {
            return NULL;
        }

        IFractWorker *worker = fw_fromcapsule(pyworker);
        dvec4 root;
        int ok = worker->find_root(eye, look, root);

        return Py_BuildValue(
            "i(dddd)",
            ok, root[0], root[1], root[2], root[3]);
    }

}


void pyfw_delete(PyObject *pyworker)
{
    IFractWorker *worker = workers::fw_fromcapsule(pyworker);
    delete worker;
}

