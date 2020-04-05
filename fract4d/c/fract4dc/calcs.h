#ifndef __CALCS_H_INCLUDED__
#define __CALCS_H_INCLUDED__

typedef struct _object PyObject;

struct calc_args;

calc_args * parse_calc_args(PyObject *args, PyObject *kwds);
void * calculation_thread(void *vdata);

namespace calcs {
    PyObject * pystop_calc(PyObject *self, PyObject *args);
    PyObject * pycalc(PyObject *self, PyObject *args, PyObject *kwds);
}

#endif