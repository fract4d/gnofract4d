#ifndef __CONTROLLERS_H_INCLUDED__
#define __CONTROLLERS_H_INCLUDED__

#include "Python.h"

#include "model/calcoptions.h"

typedef struct s_pf_data pf_obj;
class IFractalSite;
class ColorMap;
class IImage;

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
    void set_fd(int fd);
    void start_calculating(PyObject *pyimage, PyObject *pycmap, PyObject *pyparams, calc_options coptions, bool asynchronous);
    void stop_calculating();
    void free_resources();
    ~fractal_controller();
} FractalController;

namespace controllers {
    bool create_controller(PyObject *self, PyObject *args, FractalController *fc);
}

#endif