/* Wrappers around C++ functions so they can be called from python The
   C code starts one or more non-Python threads which work out which
   points to calculate, and call the dynamically-compiled pointfunc C
   code created by the compiler for each pixel.

   Results are reported back through a site object. There are 2 kinds,
   a synchronous site which calls back into python (used by
   command-line fractal.py script) and an asynchronous site which wraps
   a file descriptor into which we write simple messages. The GTK+ main
   loop then listens to the FD and performs operations in response to
   messages written to the file descriptor.
*/

#include "Python.h"

#include "fract4dc/common.h"
#include "fract4dc/colormaps.h"
#include "fract4dc/loaders.h"
#include "fract4dc/sites.h"
#include "fract4dc/fdsite.h"
#include "fract4dc/images.h"
#include "fract4dc/calcs.h"
#include "fract4dc/workers.h"
#include "fract4dc/functions.h"
#include "fract4dc/arenas.h"


/*
 * loaders
 */

static PyObject *
module_load(PyObject *self, PyObject *args)
{
    return loaders::module_load(self, args);
}

static PyObject *
pf_create(PyObject *self, PyObject *args)
{
    return loaders::pf_create(self, args);
}

static PyObject *
pf_init(PyObject *self, PyObject *args)
{
    return loaders::pf_init(self, args);
}

static PyObject *
pf_defaults(PyObject *self, PyObject *args)
{
    return loaders::pf_defaults(self, args);
}

static PyObject *
pf_calc(PyObject *self, PyObject *args)
{
    return loaders::pf_calc(self, args);
}

/*
 * cmaps
 */

static PyObject *
cmap_create_gradient(PyObject *self, PyObject *args)
{
    return colormaps::cmap_create_gradient(self, args);
}

static PyObject *
cmap_create(PyObject *self, PyObject *args)
{
    return colormaps::cmap_create(self, args);
}

static PyObject *
pycmap_set_solid(PyObject *self, PyObject *args)
{
    return colormaps::pycmap_set_solid(self, args);
}

static PyObject *
pycmap_set_transfer(PyObject *self, PyObject *args)
{
    return colormaps::pycmap_set_transfer(self, args);
}

static PyObject *
cmap_pylookup(PyObject *self, PyObject *args)
{
    return colormaps::cmap_pylookup(self, args);
}

static PyObject *
cmap_pylookup_with_flags(PyObject *self, PyObject *args)
{
    return colormaps::cmap_pylookup_with_flags(self, args);
}


/*
* sites
*/

static PyObject * pysite_create(PyObject *self, PyObject *args)
{
    return sites::pysite_create(self, args);
}

static PyObject * pyfdsite_create(PyObject *self, PyObject *args)
{
    return sites::pyfdsite_create(self, args);
}


/*
* calcs
*/

static PyObject *
pystop_calc(PyObject *self, PyObject *args)
{
    return calcs::pystop_calc(self, args);
}

static PyObject *
pycalc(PyObject *self, PyObject *args, PyObject *kwds)
{
    return calcs::pycalc(self, args, kwds);
}


/*
* images
*/

static PyObject *
pyimage_lookup(PyObject *self, PyObject *args)
{
    return images::pyimage_lookup(self, args);
}

static PyObject *
image_create(PyObject *self, PyObject *args)
{
    return images::image_create(self, args);
}

static PyObject *
image_resize(PyObject *self, PyObject *args)
{
    return images::image_resize(self, args);
}

static PyObject *
image_dims(PyObject *self, PyObject *args)
{
    return images::image_dims(self, args);
}

static PyObject *
image_set_offset(PyObject *self, PyObject *args)
{
    return images::image_set_offset(self, args);
}

static PyObject *
image_clear(PyObject *self, PyObject *args)
{
    return images::image_clear(self, args);
}

static PyObject *
image_writer_create(PyObject *self, PyObject *args)
{
    return images::image_writer_create(self, args);
}

static PyObject *
image_read(PyObject *self, PyObject *args)
{
    return images::image_read(self, args);
}

static PyObject *
image_save_header(PyObject *self, PyObject *args)
{
    return images::image_save_header(self, args);
}

static PyObject *
image_save_tile(PyObject *self, PyObject *args)
{
    return images::image_save_tile(self, args);
}

static PyObject *
image_save_footer(PyObject *self, PyObject *args)
{
    return images::image_save_footer(self, args);
}

static PyObject *
image_buffer(PyObject *self, PyObject *args)
{
    return images::image_buffer(self, args);
}

static PyObject *
image_fate_buffer(PyObject *self, PyObject *args)
{
    return images::image_fate_buffer(self, args);
}

static PyObject *
image_get_color_index(PyObject *self, PyObject *args)
{
    return images::image_get_color_index(self, args);
}

static PyObject *
image_get_fate(PyObject *self, PyObject *args)
{
    return images::image_get_fate(self, args);
}


/*
* workers
*/

static PyObject *
fw_create(PyObject *self, PyObject *args)
{
    return workers::fw_create(self, args);
}

static PyObject *
fw_pixel(PyObject *self, PyObject *args)
{
    return workers::fw_pixel(self, args);
}

static PyObject *
fw_pixel_aa(PyObject *self, PyObject *args)
{
    return workers::fw_pixel_aa(self, args);
}

static PyObject *
fw_find_root(PyObject *self, PyObject *args)
{
    return workers::fw_find_root(self, args);
}


/*
* functions
*/

static PyObject *
ff_create(PyObject *self, PyObject *args)
{
    return functions::ff_create(self, args);
}

static PyObject *
ff_get_vector(PyObject *self, PyObject *args)
{
    return functions::ff_get_vector(self, args);
}

static PyObject *
ff_look_vector(PyObject *self, PyObject *args)
{
    return functions::ff_look_vector(self, args);
}

/*
* arenas
*/

static PyObject *
pyarena_create(PyObject *self, PyObject *args)
{
    return arenas::pyarena_create(self, args);
}

static PyObject *
pyarena_alloc(PyObject *self, PyObject *args)
{
    return arenas::pyarena_alloc(self, args);
}


/*
* utils
*/

static PyObject *
rot_matrix(PyObject *self, PyObject *args)
{
    double params[N_PARAMS];

    if (!PyArg_ParseTuple(
            args,
            "(ddddddddddd)",
            &params[0], &params[1], &params[2], &params[3],
            &params[4], &params[5], &params[6], &params[7],
            &params[8], &params[9], &params[10]))
    {
        return NULL;
    }

    dmat4 rot = rotated_matrix(params);

    return Py_BuildValue(
        "((dddd)(dddd)(dddd)(dddd))",
        rot[0][0], rot[0][1], rot[0][2], rot[0][3],
        rot[1][0], rot[1][1], rot[1][2], rot[1][3],
        rot[2][0], rot[2][1], rot[2][2], rot[2][3],
        rot[3][0], rot[3][1], rot[3][2], rot[3][3]);
}

static PyObject *
eye_vector(PyObject *self, PyObject *args)
{
    double params[N_PARAMS], dist;

    if (!PyArg_ParseTuple(
            args,
            "(ddddddddddd)d",
            &params[0], &params[1], &params[2], &params[3],
            &params[4], &params[5], &params[6], &params[7],
            &params[8], &params[9], &params[10], &dist))
    {
        return NULL;
    }

    dvec4 eyevec = test_eye_vector(params, dist);

    return Py_BuildValue(
        "(dddd)",
        eyevec[0], eyevec[1], eyevec[2], eyevec[3]);
}

static PyObject *
pyrgb_to_hsv(PyObject *self, PyObject *args)
{
    double r, g, b, a = 1.0, h, s, v;
    if (!PyArg_ParseTuple(
            args,
            "ddd|d",
            &r, &g, &b, &a))
    {
        return NULL;
    }

    rgb_to_hsv(r, g, b, &h, &s, &v);

    return Py_BuildValue(
        "(dddd)",
        h, s, v, a);
}

static PyObject *
pyrgb_to_hsl(PyObject *self, PyObject *args)
{
    double r, g, b, a = 1.0, h, l, s;
    if (!PyArg_ParseTuple(
            args,
            "ddd|d",
            &r, &g, &b, &a))
    {
        return NULL;
    }

    rgb_to_hsl(r, g, b, &h, &s, &l);

    return Py_BuildValue(
        "(dddd)",
        h, s, l, a);
}

static PyObject *
pyhsl_to_rgb(PyObject *self, PyObject *args)
{
    double r, g, b, a = 1.0, h, l, s;
    if (!PyArg_ParseTuple(
            args,
            "ddd|d",
            &h, &s, &l, &a))
    {
        return NULL;
    }

    hsl_to_rgb(h, s, l, &r, &g, &b);

    return Py_BuildValue(
        "(dddd)",
        r, g, b, a);
}


/*
* array utils
*/

static PyObject *
pyarray_get(PyObject *self, PyObject *args)
{
    PyObject *pyAllocation;
    int indexes[4];
    int n_indexes;

    if (!PyArg_ParseTuple(
            args,
            "Oii|iii",
            &pyAllocation, &n_indexes,
            &indexes[0], &indexes[1], &indexes[2], &indexes[3]))
    {
        return NULL;
    }

    void *allocation = PyCapsule_GetPointer(pyAllocation, NULL);
    if (allocation == NULL)
    {
        return NULL;
    }

    int retval, inbounds;
    array_get_int(allocation, n_indexes, indexes, &retval, &inbounds);

    PyObject *pyRet = Py_BuildValue(
        "(ii)",
        retval, inbounds);

    return pyRet;
}

static PyObject *
pyarray_set(PyObject *self, PyObject *args)
{
    PyObject *pyAllocation;
    int val;
    int n_indexes;
    int indexes[4];
    if (!PyArg_ParseTuple(
            args,
            "Oiii|iii",
            &pyAllocation,
            &n_indexes,
            &val,
            &indexes[0], &indexes[1], &indexes[2], &indexes[3]))
    {
        return NULL;
    }

    void *allocation = PyCapsule_GetPointer(pyAllocation, NULL);
    if (allocation == NULL)
    {
        return NULL;
    }

    int retval = array_set_int(allocation, n_indexes, indexes, val);

    PyObject *pyRet = Py_BuildValue("i", retval);

    return pyRet;
}

static PyMethodDef PfMethods[] = {
    {"pf_load", module_load, METH_VARARGS,
     "Load a new point function shared library"},
    {"pf_create", pf_create, METH_VARARGS,
     "Create a new point function"},
    {"pf_init", pf_init, METH_VARARGS,
     "Init a point function"},
    {"pf_calc", pf_calc, METH_VARARGS,
     "Calculate one point"},
    {"pf_defaults", pf_defaults, METH_VARARGS,
     "Get defaults for this formula"},

    {"cmap_create", cmap_create, METH_VARARGS,
     "Create a new colormap"},
    {"cmap_create_gradient", cmap_create_gradient, METH_VARARGS,
     "Create a new gradient-based colormap"},
    {"cmap_lookup", cmap_pylookup, METH_VARARGS,
     "Get a color tuple from a distance value"},
    {"cmap_lookup_flags", cmap_pylookup_with_flags, METH_VARARGS,
     "Get a color tuple from a distance value and solid/inside flags"},
    {"cmap_set_solid", pycmap_set_solid, METH_VARARGS,
     "Set the inner or outer solid color"},
    {"cmap_set_transfer", pycmap_set_transfer, METH_VARARGS,
     "Set the inner or outer transfer function"},

    {"rgb_to_hsv", pyrgb_to_hsv, METH_VARARGS,
     "Convert a rgb(a) list into an hsv(a) one"},
    {"rgb_to_hsl", pyrgb_to_hsl, METH_VARARGS,
     "Convert a rgb(a) list into an hls(a) one"},
    {"hsl_to_rgb", pyhsl_to_rgb, METH_VARARGS,
     "Convert an hls(a) list into an rgb(a) one"},

    {"image_create", image_create, METH_VARARGS,
     "Create a new image buffer"},
    {"image_resize", image_resize, METH_VARARGS,
     "Change image dimensions - data is deleted"},
    {"image_set_offset", image_set_offset, METH_VARARGS,
     "set the image tile's offset"},
    {"image_dims", image_dims, METH_VARARGS,
     "get a tuple containing image's dimensions"},
    {"image_clear", image_clear, METH_VARARGS,
     "Clear all iteration and color data from image"},

    {"image_writer_create", image_writer_create, METH_VARARGS,
     "create an object used to write image to disk"},

    {"image_save_header", image_save_header, METH_VARARGS,
     "save an image header - useful for render-to-disk"},
    {"image_save_tile", image_save_tile, METH_VARARGS,
     "save an image fragment ('tile') - useful for render-to-disk"},
    {"image_save_footer", image_save_footer, METH_VARARGS,
     "save the final footer info for an image - useful for render-to-disk"},

    {"image_read", image_read, METH_VARARGS,
     "read an image in from disk"},

    {"image_buffer", image_buffer, METH_VARARGS,
     "get the rgb data from the image"},
    {"image_fate_buffer", image_fate_buffer, METH_VARARGS,
     "get the fate data from the image"},

    {"image_get_color_index", image_get_color_index, METH_VARARGS,
     "Get the color index data from a point on the image"},
    {"image_get_fate", image_get_fate, METH_VARARGS,
     "Get the (solid, fate) info for a point on the image"},

    {"image_lookup", pyimage_lookup, METH_VARARGS,
     "Get the color of a point on an image"},

    {"site_create", pysite_create, METH_VARARGS,
     "Create a new site"},
    {"fdsite_create", pyfdsite_create, METH_VARARGS,
     "Create a new file-descriptor site"},

    {"ff_create", ff_create, METH_VARARGS,
     "Create a fractFunc."},
    {"ff_look_vector", ff_look_vector, METH_VARARGS,
     "Get a vector from the eye to a point on the screen"},
    {"ff_get_vector", ff_get_vector, METH_VARARGS,
     "Get a vector inside the ff"},

    {"fw_create", fw_create, METH_VARARGS,
     "Create a fractWorker."},
    {"fw_pixel", fw_pixel, METH_VARARGS,
     "Draw a single pixel."},
    {"fw_pixel_aa", fw_pixel_aa, METH_VARARGS,
     "Draw a single pixel."},
    {"fw_find_root", fw_find_root, METH_VARARGS,
     "Find closest root considering fractal function along a vector"},

    {"calc", (PyCFunction)pycalc, METH_VARARGS | METH_KEYWORDS,
     "Calculate a fractal image"},

    {"interrupt", pystop_calc, METH_VARARGS,
     "Stop an asynchronous calculation"},

    {"rot_matrix", rot_matrix, METH_VARARGS,
     "Return a rotated and scaled identity matrix based on params"},

    {"eye_vector", eye_vector, METH_VARARGS,
     "Return the line between the user's eye and the center of the screen"},

    {"arena_create", pyarena_create, METH_VARARGS,
     "Create a new arena allocator"},
    {"arena_alloc", pyarena_alloc, METH_VARARGS,
     "Allocate a chunk of memory from the arena"},

    {"array_get_int", pyarray_get, METH_VARARGS,
     "Get an element from an array allocated in an arena"},

    {"array_set_int", pyarray_set, METH_VARARGS,
     "Set an element in an array allocated in an arena"},

    {NULL, NULL, 0, NULL} /* Sentinel */
};


struct module_state
{
    int dummy;
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "fract4dc",
    NULL,
    sizeof(struct module_state),
    PfMethods,
    NULL,
    NULL, // extension_traverse
    NULL, // extension_clear
    NULL};

extern "C" PyMODINIT_FUNC
PyInit_fract4dc(void)
{
    PyObject *pymod = PyModule_Create(&moduledef);

    PyEval_InitThreads();

    /* expose some constants */
    PyModule_AddIntConstant(pymod, "CALC_DONE", GF4D_FRACTAL_DONE);
    PyModule_AddIntConstant(pymod, "CALC_CALCULATING", GF4D_FRACTAL_CALCULATING);
    PyModule_AddIntConstant(pymod, "CALC_DEEPENING", GF4D_FRACTAL_DEEPENING);
    PyModule_AddIntConstant(pymod, "CALC_ANTIALIASING", GF4D_FRACTAL_ANTIALIASING);
    PyModule_AddIntConstant(pymod, "CALC_PAUSED", GF4D_FRACTAL_PAUSED);

    PyModule_AddIntConstant(pymod, "AA_NONE", AA_NONE);
    PyModule_AddIntConstant(pymod, "AA_FAST", AA_FAST);
    PyModule_AddIntConstant(pymod, "AA_BEST", AA_BEST);

    PyModule_AddIntConstant(pymod, "RENDER_TWO_D", RENDER_TWO_D);
    PyModule_AddIntConstant(pymod, "RENDER_LANDSCAPE", RENDER_LANDSCAPE);
    PyModule_AddIntConstant(pymod, "RENDER_THREE_D", RENDER_THREE_D);

    PyModule_AddIntConstant(pymod, "DRAW_GUESSING", DRAW_GUESSING);
    PyModule_AddIntConstant(pymod, "DRAW_TO_DISK", DRAW_TO_DISK);

    PyModule_AddIntConstant(pymod, "DELTA_X", DELTA_X);
    PyModule_AddIntConstant(pymod, "DELTA_Y", DELTA_Y);
    PyModule_AddIntConstant(pymod, "TOPLEFT", TOPLEFT);

    /* cf image_dims */
    PyModule_AddIntConstant(pymod, "IMAGE_WIDTH", 0);
    PyModule_AddIntConstant(pymod, "IMAGE_HEIGHT", 1);
    PyModule_AddIntConstant(pymod, "IMAGE_TOTAL_WIDTH", 2);
    PyModule_AddIntConstant(pymod, "IMAGE_TOTAL_HEIGHT", 3);
    PyModule_AddIntConstant(pymod, "IMAGE_XOFFSET", 4);
    PyModule_AddIntConstant(pymod, "IMAGE_YOFFSET", 5);

    /* image type consts */
    PyModule_AddIntConstant(pymod, "FILE_TYPE_TGA", FILE_TYPE_TGA);
    PyModule_AddIntConstant(pymod, "FILE_TYPE_PNG", FILE_TYPE_PNG);
    PyModule_AddIntConstant(pymod, "FILE_TYPE_JPG", FILE_TYPE_JPG);

    /* message type consts */
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_ITERS", ITERS);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_IMAGE", IMAGE);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_PROGRESS", PROGRESS);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_STATUS", STATUS);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_PIXEL", PIXEL);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_TOLERANCE", TOLERANCE);
    PyModule_AddIntConstant(pymod, "MESSAGE_TYPE_STATS", STATS);

    return pymod;
}
