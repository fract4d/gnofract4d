#ifndef __LOADERS_H_INCLUDED__
#define __LOADERS_H_INCLUDED__

#include "Python.h"

#include "../pf.h"

struct pfHandle
{
    PyObject *pyhandle;
    pf_obj *pfo;
};

namespace loaders {
    PyObject *module_load(PyObject *self, PyObject *args);
    PyObject * pf_create(PyObject *self, PyObject *args);
    PyObject * pf_init(PyObject *self, PyObject *args);
    PyObject * pf_defaults(PyObject *self, PyObject *args);
    PyObject * pf_calc(PyObject *self, PyObject *args);
    struct pfHandle * pf_fromcapsule(PyObject *capsule);
    void pf_delete(PyObject *p);
    void * module_fromcapsule(PyObject *p);
    void module_unload(PyObject *p);
}

#endif