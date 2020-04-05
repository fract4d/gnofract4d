#ifndef __UTILS_H_INCLUDED__
#define __UTILS_H_INCLUDED__

typedef struct _object PyObject;

namespace utils {
    PyObject * rot_matrix(PyObject *self, PyObject *args);
    PyObject * eye_vector(PyObject *self, PyObject *args);

    PyObject * pyrgb_to_hsv(PyObject *self, PyObject *args);
    PyObject * pyrgb_to_hsl(PyObject *self, PyObject *args);
    PyObject * pyhsl_to_rgb(PyObject *self, PyObject *args);

    PyObject * pyarray_get(PyObject *self, PyObject *args);
    PyObject * pyarray_set(PyObject *self, PyObject *args);
}

#endif