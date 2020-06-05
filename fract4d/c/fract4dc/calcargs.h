#ifndef __CALCARGS_H_INCLUDED__
#define __CALCARGS_H_INCLUDED__

#include "model/calcoptions.h"

typedef struct _object PyObject;
// forward references
typedef struct s_pf_data pf_obj;
class ColorMap;
class IImage;
class IFractalSite;

struct calc_args
{
    int asynchronous = false;
    calc_options options;

    double *params;
    pf_obj *pfo;
    ColorMap *cmap;
    IImage *im;
    IFractalSite *site;
    PyObject *pycmap, *pypfo, *pyim, *pysite;

    calc_args();

    // possible solution: create a subclass in the python module interface that get's the real object inside this capsules
    void set_cmap(PyObject *pycmap_);
    void set_pfo(PyObject *pypfo_);
    void set_im(PyObject *pyim_);
    void set_site(PyObject *pysite_);

    ~calc_args();
};

#endif