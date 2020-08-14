#include "Python.h"

#include "calcargs.h"

#include "fract4dc/colormaps.h"
#include "fract4dc/sites.h"
#include "fract4dc/loaders.h"
#include "fract4dc/images.h"

#include "pf.h"

calc_args::calc_args()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : CA : CTOR\n", this);
#endif
    params = new double[N_PARAMS];
    params_previous = new double[N_PARAMS]{}; // initialize to 0's because it's actually optional
}

void calc_args::set_cmap(PyObject *pycmap_)
{
    pycmap = pycmap_;
    cmap = colormaps::cmap_fromcapsule(pycmap);
    Py_XINCREF(pycmap);
}

void calc_args::set_pfo(PyObject *pypfo_)
{
    pypfo = pypfo_;
    pfo = (loaders::pf_fromcapsule(pypfo))->pfo;
    Py_XINCREF(pypfo);
}

void calc_args::set_im(PyObject *pyim_)
{
    pyim = pyim_;
    im = images::image_fromcapsule(pyim);
    Py_XINCREF(pyim);
}
void calc_args::set_site(PyObject *pysite_)
{
    pysite = pysite_;
    site = sites::site_fromcapsule(pysite);
    Py_XINCREF(pysite);
}

calc_args::~calc_args()
{
    delete [] params;
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : CA : DTOR\n", this);
#endif
    Py_XDECREF(pycmap);
    Py_XDECREF(pypfo);
    Py_XDECREF(pyim);
    Py_XDECREF(pysite);
}
