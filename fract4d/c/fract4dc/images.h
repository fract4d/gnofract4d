#ifndef __IMAGES_H_INCLUDED__
#define __IMAGES_H_INCLUDED__


#include "../image_public.h"


void pyimage_delete(PyObject *pyimage);
void pyimage_writer_delete(PyObject *pyim);
ImageWriter * image_writer_fromcapsule(PyObject *p);

namespace images {
    IImage * image_fromcapsule(PyObject *pyimage);
    PyObject * pyimage_lookup(PyObject *self, PyObject *args);
    PyObject * image_create(PyObject *self, PyObject *args);
    PyObject * image_resize(PyObject *self, PyObject *args);
    PyObject * image_dims(PyObject *self, PyObject *args);
    PyObject * image_set_offset(PyObject *self, PyObject *args);
    PyObject * image_clear(PyObject *self, PyObject *args);
    PyObject * image_writer_create(PyObject *self, PyObject *args);
    PyObject * image_read(PyObject *self, PyObject *args);
    PyObject * image_save_header(PyObject *self, PyObject *args);
    PyObject * image_save_tile(PyObject *self, PyObject *args);
    PyObject * image_save_footer(PyObject *self, PyObject *args);
    PyObject * image_buffer(PyObject *self, PyObject *args);
    PyObject * image_fate_buffer(PyObject *self, PyObject *args);
    PyObject * image_get_color_index(PyObject *self, PyObject *args);
    PyObject * image_get_fate(PyObject *self, PyObject *args);
}

#endif
