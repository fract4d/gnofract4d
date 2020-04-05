#ifndef __WORKERS_H_INCLUDED__
#define __WORKERS_H_INCLUDED__

typedef struct _object PyObject;

class IFractWorker;

void pyfw_delete(PyObject *pyworker);

namespace workers {
    IFractWorker * fw_fromcapsule(PyObject *capsule);
    PyObject * fw_create(PyObject *self, PyObject *args);
    PyObject * fw_pixel(PyObject *self, PyObject *args);
    PyObject * fw_pixel_aa(PyObject *self, PyObject *args);
    PyObject * fw_find_root(PyObject *self, PyObject *args);
}

#endif