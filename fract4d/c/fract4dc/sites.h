#ifndef __SITES_H_INCLUDED__
#define __SITES_H_INCLUDED__

#include "../fract_public.h"

namespace sites {
    void pysite_delete(PyObject *pysite);
    PyObject * pysite_create(PyObject *self, PyObject *args);
    PyObject * pyfdsite_create(PyObject *self, PyObject *args);
    IFractalSite * site_fromcapsule(PyObject *pysite);
}

#endif