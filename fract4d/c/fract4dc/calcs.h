#ifndef __CALCS_H_INCLUDED__
#define __CALCS_H_INCLUDED__

typedef struct _object PyObject;

struct calc_args;

calc_args * parse_calc_args(PyObject *args, PyObject *kwds);
void * calculation_thread(calc_args *args);
void * calculation_thread_xaos(calc_args *args);

namespace calcs {
    PyObject * pystop_calc(PyObject *self, PyObject *args);
    PyObject * pycalc(PyObject *self, PyObject *args, PyObject *kwds);
    PyObject * pycalc_xaos(PyObject *self, PyObject *args, PyObject *kwds);
    PyObject * pyupdate_xaos(PyObject *self, PyObject *args);
    PyObject * pystop_xaos(PyObject *self, PyObject *args);
}

#endif