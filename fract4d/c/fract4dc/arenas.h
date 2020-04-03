#ifndef __ARENAS_H_INCLUDED__
#define __ARENAS_H_INCLUDED__

typedef struct _object PyObject;
typedef struct s_arena *arena_t;

arena_t arena_fromcapsule(PyObject *p);
void pyarena_delete(PyObject *pyarena);

namespace arenas {
    PyObject * pyarena_create(PyObject *self, PyObject *args);
    PyObject * pyarena_alloc(PyObject *self, PyObject *args);
}

#endif