#ifndef __FUNCTIONS_H_INCLUDED__
#define __FUNCTIONS_H_INCLUDED__

typedef struct _object PyObject;

class fractFunc;

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


void pyff_delete(PyObject *pyff);
ffHandle * ff_fromcapsule(PyObject *pyff);


namespace functions {
    PyObject * ff_create(PyObject *self, PyObject *args);
    PyObject * ff_get_vector(PyObject *self, PyObject *args);
    PyObject * ff_look_vector(PyObject *self, PyObject *args);
}

#endif