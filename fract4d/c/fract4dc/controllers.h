#ifndef __CONTROLLERS_H_INCLUDED__
#define __CONTROLLERS_H_INCLUDED__

#include "Python.h"

#include "model/enums.h"

typedef struct s_pf_data pf_obj;
class IFractalSite;
class ColorMap;
class IImage;

struct calc_options
{
    int
        eaa = AA_NONE,
        maxiter =  1024,
        nThreads = 1,
        auto_deepen = false,
        yflip = false,
        periodicity = true,
        dirty = 1,
        auto_tolerance = false,
        asynchronous = false,
        warp_param = -1;
    double tolerance = 1.0E-9;
    render_type_t render_type = RENDER_TWO_D;
};

typedef struct fractal_controller {
    PyObject_HEAD
    void *lib_handle;
    pf_obj *pf_handle;
    calc_options c_options;
    double *c_pos_params;
    IFractalSite *site;
    ColorMap *cmap;
    PyObject *py_cmap;
    IImage *image;
    PyObject *py_image;
    void set_message_handler(PyObject *message_handler);
    void start_calculating(PyObject *pyimage, PyObject *pycmap, PyObject *pyparams, calc_options coptions);
    ~fractal_controller();
} FractalController;

namespace controllers {
    void create_controller(PyObject *self, PyObject *args, FractalController *fc);
}

#endif