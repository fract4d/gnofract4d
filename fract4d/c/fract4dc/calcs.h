#ifndef __CALCS_H_INCLUDED__
#define __CALCS_H_INCLUDED__

#include "../pf.h"

struct calc_args
{
    double params[N_PARAMS];
    int eaa, maxiter, nThreads;
    int auto_deepen, yflip, periodicity, dirty;
    int auto_tolerance;
    double tolerance;
    int asynchronous, warp_param;
    render_type_t render_type;
    pf_obj *pfo;
    ColorMap *cmap;
    IImage *im;
    IFractalSite *site;
    PyObject *pycmap, *pypfo, *pyim, *pysite;

    calc_args();

    void set_cmap(PyObject *pycmap_);
    void set_pfo(PyObject *pypfo_);
    void set_im(PyObject *pyim_);
    void set_site(PyObject *pysite_);

    ~calc_args();
};


calc_args * parse_calc_args(PyObject *args, PyObject *kwds);
void * calculation_thread(void *vdata);

namespace calcs {
    PyObject * pystop_calc(PyObject *self, PyObject *args);
    PyObject * pycalc(PyObject *self, PyObject *args, PyObject *kwds);
}


#endif