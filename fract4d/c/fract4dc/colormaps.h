#ifndef __COLORMAPS_H_INCLUDED__
#define __COLORMAPS_H_INCLUDED__

#include "Python.h"

#include "../cmap.h"

namespace colormaps {
    PyObject * cmap_create(PyObject *self, PyObject *args);
    PyObject * cmap_create_gradient(PyObject *self, PyObject *args);
    PyObject * pycmap_set_solid(PyObject *self, PyObject *args);
    PyObject * pycmap_set_transfer(PyObject *self, PyObject *args);
    PyObject * cmap_pylookup(PyObject *self, PyObject *args);
    PyObject * cmap_pylookup_with_flags(PyObject *self, PyObject *args);
    ColorMap * cmap_from_pyobject(PyObject *pyarray);
    ColorMap * cmap_fromcapsule(PyObject *capsule);
    void pycmap_delete(PyObject *capsule);
}

#endif