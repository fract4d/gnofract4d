#ifndef __FUNCTIONS_H_INCLUDED__
#define __FUNCTIONS_H_INCLUDED__

#include "Python.h"

#include "../fractFunc.h"

struct ffHandle
{
    PyObject *pyhandle;
    fractFunc *ff;
};

typedef enum
{
    DELTA_X,
    DELTA_Y,
    TOPLEFT
} vec_type_t;

namespace functions {
    PyObject * ff_create(PyObject *self, PyObject *args);
    PyObject * ff_get_vector(PyObject *self, PyObject *args);
    PyObject * ff_look_vector(PyObject *self, PyObject *args);
}

#endif