#include "Python.h"

#include "arenas.h"
#include "common.h"


namespace arenas {

    PyObject * pyarena_create(PyObject *self, PyObject *args)
    {
        int page_size, max_pages;
        if (!PyArg_ParseTuple(
                args,
                "ii",
                &page_size, &max_pages))
        {
            return NULL;
        }

        arena_t arena = arena_create(page_size, max_pages);

        if (NULL == arena)
        {
            PyErr_SetString(PyExc_MemoryError, "Cannot allocate arena");
            return NULL;
        }

        PyObject *pyarena = PyCapsule_New(arena, OBTYPE_ARENA, pyarena_delete);

        return pyarena;
    }

    PyObject * pyarena_alloc(PyObject *self, PyObject *args)
    {
        PyObject *pyArena;
        int element_size;
        int n_dimensions;
        int n_elements[4];

        if (!PyArg_ParseTuple(
                args,
                "Oiii|iii",
                &pyArena, &element_size,
                &n_dimensions,
                &n_elements[0],
                &n_elements[1],
                &n_elements[2],
                &n_elements[3]))
        {
            return NULL;
        }

        arena_t arena = arena_fromcapsule(pyArena);
        if (arena == NULL)
        {
            return NULL;
        }

        void *allocation = arena_alloc(
            arena, element_size,
            n_dimensions,
            n_elements);
        if (allocation == NULL)
        {
            PyErr_SetString(PyExc_MemoryError, "Can't allocate array");
            return NULL;
        }

        PyObject *pyAlloc = PyCapsule_New(allocation, NULL, NULL);

        return pyAlloc;
    }
}


arena_t arena_fromcapsule(PyObject *p)
{
    arena_t arena = (arena_t)PyCapsule_GetPointer(p, OBTYPE_ARENA);
    if (NULL == arena)
    {
        fprintf(stderr, "%p : AR : BAD\n", p);
    }

    return arena;
}

void pyarena_delete(PyObject *pyarena)
{
    arena_t arena = arena_fromcapsule(pyarena);
    arena_delete(arena);
}