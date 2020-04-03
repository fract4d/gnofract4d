#ifndef __ARENAS_H_INCLUDED__
#define __ARENAS_H_INCLUDED__

#include "../fract_stdlib.h"

arena_t arena_fromcapsule(PyObject *p);
void pyarena_delete(PyObject *pyarena);

namespace arenas {
    PyObject * pyarena_create(PyObject *self, PyObject *args);
    PyObject * pyarena_alloc(PyObject *self, PyObject *args);
}

#endif