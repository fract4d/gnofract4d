#ifndef __CALCARGS_H_INCLUDED__
#define __CALCARGS_H_INCLUDED__

#include "model/enums.h"

// @TODO: create a subclass for python interfaces and remove this
typedef struct _object PyObject;
// forward references
typedef struct s_pf_data pf_obj;
class ColorMap;
class IImage;
class IFractalSite;

struct calc_args
{
    // double params[N_PARAMS]; // @TODO: moved to cpp dynamic initialization to avoid including pf header here
    double *params;
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

    // @TODO: remove PyObject from this interface for the model classes to be portable
    // possible solution: create a subclass in the python module interface that get's the real object inside this capsules
    void set_cmap(PyObject *pycmap_);
    void set_pfo(PyObject *pypfo_);
    void set_im(PyObject *pyim_);
    void set_site(PyObject *pysite_);

    ~calc_args();
};

#endif