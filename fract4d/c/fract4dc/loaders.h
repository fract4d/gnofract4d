#ifndef __LOADERS_H_INCLUDED__
#define __LOADERS_H_INCLUDED__

typedef struct _object PyObject;

typedef struct s_pf_data pf_obj;
struct s_param;

struct pfHandle
{
    PyObject *pyhandle;
    pf_obj *pfo;
};

bool parse_posparams(PyObject *py_posparams, double *pos_params);
s_param * parse_params(PyObject *pyarray, int *plen);
PyObject * params_to_python(struct s_param *params, int len);

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