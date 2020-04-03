#include "Python.h"
#include <cassert>
#include <new>

#include "images.h"

#include "fract4dc/common.h"

#include "model/imagereader.h"
#include "model/imagewriter.h"
#include "model/image.h"

namespace images {

    PyObject * image_create(PyObject *self, PyObject *args)
    {
        int x, y;
        int totalx = -1, totaly = -1;
        if (!PyArg_ParseTuple(args, "ii|ii", &x, &y, &totalx, &totaly))
        {
            return NULL;
        }

        IImage *i = new image();

        i->set_resolution(x, y, totalx, totaly);

        if (!i->ok())
        {
            PyErr_SetString(PyExc_MemoryError, "Image too large");
            delete i;
            return NULL;
        }

    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : IM : CTOR\n", i);
    #endif

        PyObject *pyret = PyCapsule_New(i, OBTYPE_IMAGE, pyimage_delete);

        return pyret;
    }

    IImage * image_fromcapsule(PyObject *pyimage)
    {
        IImage *image = (IImage *)PyCapsule_GetPointer(pyimage, OBTYPE_IMAGE);
        if (NULL == image)
        {
            fprintf(stderr, "%p : IM : BAD\n", pyimage);
        }
        return image;
    }


    PyObject * pyimage_lookup(PyObject *self, PyObject *args)
    {
        PyObject *pyimage = NULL;
        double x, y;
        double r, g, b;

        if (!PyArg_ParseTuple(
                args,
                "Odd",
                &pyimage, &x, &y))
        {
            return NULL;
        }

        image *i = (image *)image_fromcapsule(pyimage);

        image_lookup(i, x, y, &r, &g, &b);

        return Py_BuildValue(
            "(dddd)",
            r, g, b, 1.0);
    }


    PyObject * image_resize(PyObject *self, PyObject *args)
    {
        int x, y;
        int totalx = -1, totaly = -1;
        PyObject *pyim;

        if (!PyArg_ParseTuple(args, "Oiiii", &pyim, &x, &y, &totalx, &totaly))
        {
            return NULL;
        }

        IImage *i = image_fromcapsule(pyim);
        if (NULL == i)
        {
            return NULL;
        }

        i->set_resolution(x, y, totalx, totaly);

        if (!i->ok())
        {
            PyErr_SetString(PyExc_MemoryError, "Image too large");
            return NULL;
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_dims(PyObject *self, PyObject *args)
    {
        PyObject *pyim;

        if (!PyArg_ParseTuple(args, "O", &pyim))
        {
            return NULL;
        }

        IImage *i = image_fromcapsule(pyim);
        if (NULL == i)
        {
            return NULL;
        }

        int xsize, ysize, xoffset, yoffset, xtotalsize, ytotalsize;
        xsize = i->Xres();
        ysize = i->Yres();
        xoffset = i->Xoffset();
        yoffset = i->Yoffset();
        xtotalsize = i->totalXres();
        ytotalsize = i->totalYres();

        PyObject *pyret = Py_BuildValue(
            "(iiiiii)", xsize, ysize, xtotalsize, ytotalsize, xoffset, yoffset);

        return pyret;
    }

    PyObject * image_set_offset(PyObject *self, PyObject *args)
    {
        int x, y;
        PyObject *pyim;

        if (!PyArg_ParseTuple(args, "Oii", &pyim, &x, &y))
        {
            return NULL;
        }

        IImage *i = image_fromcapsule(pyim);
        if (NULL == i)
        {
            return NULL;
        }

        bool ok = i->set_offset(x, y);
        if (!ok)
        {
            PyErr_SetString(PyExc_ValueError, "Offset out of bounds");
            return NULL;
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_clear(PyObject *self, PyObject *args)
    {
        PyObject *pyim;

        if (!PyArg_ParseTuple(args, "O", &pyim))
        {
            return NULL;
        }

        IImage *i = image_fromcapsule(pyim);
        if (NULL == i)
        {
            return NULL;
        }

        i->clear();

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_writer_create(PyObject *self, PyObject *args)
    {
        PyObject *pyim;
        char *filename;
        int file_type;
        if (!PyArg_ParseTuple(args, "Osi", &pyim, &filename, &file_type))
        {
            return NULL;
        }

        IImage *i = image_fromcapsule(pyim);

        FILE *fp = fopen(filename, "wb");

        if (!fp)
        {
            PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
            return NULL;
        }

        ImageWriter *writer = ImageWriter::create((image_file_t)file_type, fp, i);
        if (NULL == writer)
        {
            PyErr_SetString(PyExc_ValueError, "Unsupported file type");
            return NULL;
        }

        return PyCapsule_New(writer, OBTYPE_IMAGE_WRITER, pyimage_writer_delete);
    }

    PyObject * image_read(PyObject *self, PyObject *args)
    {
        PyObject *pyim;
        char *filename;
        int file_type;
        if (!PyArg_ParseTuple(args, "Osi", &pyim, &filename, &file_type))
        {
            return NULL;
        }

        IImage *i = image_fromcapsule(pyim);

        FILE *fp = fopen(filename, "rb");

        if (!fp || !i)
        {
            PyErr_SetFromErrnoWithFilename(PyExc_OSError, "filename");
            return NULL;
        }

        ImageReader *reader = ImageReader::create((image_file_t)file_type, fp, i);

        if (!reader->read())
        {
            PyErr_SetString(PyExc_IOError, "Couldn't read image contents");
            delete reader;
            return NULL;
        }
        delete reader;

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_save_header(PyObject *self, PyObject *args)
    {
        PyObject *pyimwriter;
        if (!PyArg_ParseTuple(args, "O", &pyimwriter))
        {
            return NULL;
        }

        ImageWriter *i = image_writer_fromcapsule(pyimwriter);

        if (!i || !i->save_header())
        {
            PyErr_SetString(PyExc_IOError, "Couldn't save file header");
            return NULL;
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_save_tile(PyObject *self, PyObject *args)
    {
        PyObject *pyimwriter;
        if (!PyArg_ParseTuple(args, "O", &pyimwriter))
        {
            return NULL;
        }

        ImageWriter *i = image_writer_fromcapsule(pyimwriter);

        if (!i || !i->save_tile())
        {
            PyErr_SetString(PyExc_IOError, "Couldn't save image tile");
            return NULL;
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_save_footer(PyObject *self, PyObject *args)
    {
        PyObject *pyimwriter;
        if (!PyArg_ParseTuple(args, "O", &pyimwriter))
        {
            return NULL;
        }

        ImageWriter *i = image_writer_fromcapsule(pyimwriter);

        if (!i || !i->save_footer())
        {
            PyErr_SetString(PyExc_IOError, "Couldn't save image footer");
            return NULL;
        }

        Py_INCREF(Py_None);
        return Py_None;
    }

    PyObject * image_buffer(PyObject *self, PyObject *args)
    {
        PyObject *pyim;
        PyObject *pybuf;

        int x = 0, y = 0;
        if (!PyArg_ParseTuple(args, "O|ii", &pyim, &x, &y))
        {
            return NULL;
        }

        image *i = (image *)image_fromcapsule(pyim);

    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : IM : BUF\n", i);
    #endif

        if (!i || !i->ok())
        {
            PyErr_SetString(PyExc_MemoryError, "image not allocated");
            return NULL;
        }

        if (x < 0 || x >= i->Xres() || y < 0 || y >= i->Yres())
        {
            PyErr_SetString(PyExc_ValueError, "request for buffer outside image bounds");
            return NULL;
        }
        int offset = 3 * (y * i->Xres() + x);
        assert(offset > -1 && offset < i->bytes());
        Py_buffer *buffer = new Py_buffer;
        PyBuffer_FillInfo(buffer, NULL, i->getBuffer() + offset, i->bytes() - offset, 0, PyBUF_WRITABLE);
        pybuf = PyMemoryView_FromBuffer(buffer);
        Py_XINCREF(pybuf);
        //Py_XINCREF(pyim);

        return pybuf;
    }

    PyObject * image_fate_buffer(PyObject *self, PyObject *args)
    {
        PyObject *pyim;
        PyObject *pybuf;

        int x = 0, y = 0;
        if (!PyArg_ParseTuple(args, "O|ii", &pyim, &x, &y))
        {
            return NULL;
        }

        image *i = (image *)image_fromcapsule(pyim);

    #ifdef DEBUG_CREATION
        fprintf(stderr, "%p : IM : BUF\n", i);
    #endif

        if (NULL == i)
        {
            PyErr_SetString(PyExc_ValueError,
                            "Bad image object");
            return NULL;
        }

        if (x < 0 || x >= i->Xres() || y < 0 || y >= i->Yres())
        {
            PyErr_SetString(PyExc_ValueError, "request for buffer outside image bounds");
            return NULL;
        }
        int index = i->index_of_subpixel(x, y, 0);
        int last_index = i->index_of_sentinel_subpixel();
        assert(index > -1 && index < last_index);

        Py_buffer *buffer = new Py_buffer;
        PyBuffer_FillInfo(buffer, NULL, i->getFateBuffer() + index, (last_index - index) * sizeof(fate_t), 0, PyBUF_WRITABLE);
        pybuf = PyMemoryView_FromBuffer(buffer);

        Py_XINCREF(pybuf);

        return pybuf;
    }

    PyObject * image_get_color_index(PyObject *self, PyObject *args)
    {
        PyObject *pyim;

        int x = 0, y = 0, sub = 0;
        if (!PyArg_ParseTuple(args, "Oii|i", &pyim, &x, &y, &sub))
        {
            return NULL;
        }

        image *i = (image *)image_fromcapsule(pyim);

        if (NULL == i)
        {
            PyErr_SetString(PyExc_ValueError,
                            "Bad image object");
            return NULL;
        }

        if (x < 0 || x >= i->Xres() ||
            y < 0 || y >= i->Yres() ||
            sub < 0 || sub >= image::N_SUBPIXELS)
        {
            PyErr_SetString(PyExc_ValueError,
                            "request for data outside image bounds");
            return NULL;
        }

        float dist = i->getIndex(x, y, sub);
        return Py_BuildValue("d", (double)dist);
    }

    PyObject * image_get_fate(PyObject *self, PyObject *args)
    {
        PyObject *pyim;

        int x = 0, y = 0, sub = 0;
        if (!PyArg_ParseTuple(args, "Oii|i", &pyim, &x, &y, &sub))
        {
            return NULL;
        }

        image *i = (image *)image_fromcapsule(pyim);

        if (NULL == i)
        {
            PyErr_SetString(PyExc_ValueError,
                            "Bad image object");
            return NULL;
        }

        if (x < 0 || x >= i->Xres() ||
            y < 0 || y >= i->Yres() ||
            sub < 0 || sub >= image::N_SUBPIXELS)
        {
            PyErr_SetString(PyExc_ValueError,
                            "request for data outside image bounds");
            return NULL;
        }

        fate_t fate = i->getFate(x, y, sub);
        if (fate == FATE_UNKNOWN)
        {
            Py_INCREF(Py_None);
            return Py_None;
        }
        int is_solid = fate & FATE_SOLID ? 1 : 0;
        return Py_BuildValue("(ii)", is_solid, fate & ~FATE_SOLID);
    }
}


void pyimage_delete(PyObject *pyimage)
{
    IImage *im = images::image_fromcapsule(pyimage);
    #ifdef DEBUG_CREATION
    fprintf(stderr, "%p : IM : DTOR\n", image);
#endif
    delete im;
}

void pyimage_writer_delete(PyObject *pyim)
{
    ImageWriter *im = image_writer_fromcapsule(pyim);
    delete im;
}

ImageWriter * image_writer_fromcapsule(PyObject *p)
{
    ImageWriter *iw = (ImageWriter *)PyCapsule_GetPointer(p, OBTYPE_IMAGE_WRITER);
    if (NULL == iw)
    {
        fprintf(stderr, "%p : IW : BAD\n", p);
    }

    return iw;
}