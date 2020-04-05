#include "Python.h"
#include <new>

#include "colormaps.h"

#include "fract4dc/common.h"
#include "model/colormap.h"
#include "model/color.h"

namespace colormaps {

    PyObject * cmap_create(PyObject *self, PyObject *args)
    {
        /* args = an array of (index,r,g,b,a) tuples */
        PyObject *pyarray, *pyret;
        int len, i;
        ListColorMap *cmap;

        if (!PyArg_ParseTuple(args, "O", &pyarray))
        {
            return NULL;
        }

        if (!PySequence_Check(pyarray))
        {
            return NULL;
        }

        len = PySequence_Size(pyarray);
        if (len == 0)
        {
            PyErr_SetString(PyExc_ValueError, "Empty color array");
            return NULL;
        }

        cmap = new (std::nothrow) ListColorMap();

        if (!cmap)
        {
            PyErr_SetString(PyExc_MemoryError, "Can't allocate colormap");
            return NULL;
        }
        if (!cmap->init(len))
        {
            PyErr_SetString(PyExc_MemoryError, "Can't allocate colormap array");
            delete cmap;
            return NULL;
        }
        for (i = 0; i < len; ++i)
        {
            double d;
            int r, g, b, a;
            PyObject *pyitem = PySequence_GetItem(pyarray, i);
            if (!pyitem)
            {
                delete cmap;
                return NULL;
            }
            if (!PyArg_ParseTuple(pyitem, "diiii", &d, &r, &g, &b, &a))
            {
                Py_DECREF(pyitem);
                delete cmap;
                return NULL;
            }
            cmap->set(i, d, r, g, b, a);
            Py_DECREF(pyitem);
        }
        pyret = PyCapsule_New(cmap, OBTYPE_CMAP, pycmap_delete);

        return pyret;
    }

    PyObject * cmap_create_gradient(PyObject *self, PyObject *args)
    {
        /* args = a gradient object:
        an array of objects with:
        float: left,right,mid
        int: bmode, cmode
        [f,f,f,f] : left_color, right_color
        */
        PyObject *pyarray, *pyret;

        if (!PyArg_ParseTuple(args, "O", &pyarray))
        {
            return NULL;
        }

        if (!PySequence_Check(pyarray))
        {
            return NULL;
        }

        ColorMap *cmap = cmap_from_pyobject(pyarray);

        if (NULL == cmap)
        {
            return NULL;
        }

        pyret = PyCapsule_New(cmap, OBTYPE_CMAP, pycmap_delete);

        return pyret;
    }


    PyObject * pycmap_set_solid(PyObject *self, PyObject *args)
    {
        PyObject *pycmap;
        int which, r, g, b, a;
        ColorMap *cmap;

        if (!PyArg_ParseTuple(args, "Oiiiii", &pycmap, &which, &r, &g, &b, &a))
        {
            return NULL;
        }

        cmap = cmap_fromcapsule(pycmap);
        if (!cmap)
        {
            return NULL;
        }

        cmap->set_solid(which, r, g, b, a);

        Py_INCREF(Py_None);
        return Py_None;
    }


    PyObject * pycmap_set_transfer(PyObject *self, PyObject *args)
    {
        PyObject *pycmap;
        int which;
        e_transferType transfer;
        ColorMap *cmap;

        if (!PyArg_ParseTuple(args, "Oii", &pycmap, &which, &transfer))
        {
            return NULL;
        }

        cmap = cmap_fromcapsule(pycmap);
        if (!cmap)
        {
            return NULL;
        }

        cmap->set_transfer(which, transfer);

        Py_INCREF(Py_None);
        return Py_None;
    }


    PyObject * cmap_pylookup(PyObject *self, PyObject *args)
    {
        PyObject *pyobj, *pyret;
        double d;
        rgba_t color;
        ColorMap *cmap;

        if (!PyArg_ParseTuple(args, "Od", &pyobj, &d))
        {
            return NULL;
        }

        cmap = cmap_fromcapsule(pyobj);
        if (!cmap)
        {
            return NULL;
        }

        color = cmap->lookup(d);

        pyret = Py_BuildValue("iiii", color.r, color.g, color.b, color.a);

        return pyret;
    }


    PyObject * cmap_pylookup_with_flags(PyObject *self, PyObject *args)
    {
        PyObject *pyobj, *pyret;
        double d;
        rgba_t color;
        ColorMap *cmap;
        int inside;
        int solid;

        if (!PyArg_ParseTuple(args, "Odii", &pyobj, &d, &solid, &inside))
        {
            return NULL;
        }

        cmap = cmap_fromcapsule(pyobj);
        if (!cmap)
        {
            return NULL;
        }

        color = cmap->lookup_with_transfer(d, solid, inside);

        pyret = Py_BuildValue("iiii", color.r, color.g, color.b, color.a);

        return pyret;
    }


    ColorMap * cmap_from_pyobject(PyObject *pyarray)
    {
        int len, i;
        GradientColorMap *cmap;

        len = PySequence_Size(pyarray);
        if (len == 0)
        {
            PyErr_SetString(PyExc_ValueError, "Empty color array");
            return NULL;
        }

        cmap = new (std::nothrow) GradientColorMap();

        if (!cmap)
        {
            PyErr_SetString(PyExc_MemoryError, "Can't allocate colormap");
            return NULL;
        }
        if (!cmap->init(len))
        {
            PyErr_SetString(PyExc_MemoryError, "Can't allocate colormap array");
            delete cmap;
            return NULL;
        }

        for (i = 0; i < len; ++i)
        {
            double left, right, mid, left_col[4], right_col[4];
            int bmode, cmode;
            PyObject *pyitem = PySequence_GetItem(pyarray, i);
            if (!pyitem)
            {
                delete cmap;
                return NULL;
            }

            if (!get_double_field(pyitem, "left", &left) ||
                !get_double_field(pyitem, "right", &right) ||
                !get_double_field(pyitem, "mid", &mid) ||
                !get_int_field(pyitem, "cmode", &cmode) ||
                !get_int_field(pyitem, "bmode", &bmode) ||
                !get_double_array(pyitem, "left_color", left_col, 4) ||
                !get_double_array(pyitem, "right_color", right_col, 4))
            {
                Py_DECREF(pyitem);
                delete cmap;
                return NULL;
            }

            cmap->set(i, left, right, mid,
                    left_col, right_col,
                    (e_blendType)bmode, (e_colorType)cmode);

            Py_DECREF(pyitem);
        }
        return cmap;
    }


    ColorMap * cmap_fromcapsule(PyObject *capsule)
    {
        ColorMap *cmap = (ColorMap *)PyCapsule_GetPointer(capsule, OBTYPE_CMAP);
        if (NULL == cmap)
        {
            fprintf(stderr, "%p : CM : BAD", capsule);
        }
        return cmap;
    }


    void pycmap_delete(PyObject *capsule)
    {
        ColorMap *cmap = cmap_fromcapsule(capsule);
        cmap_delete(cmap);
    }

}


// @TODO: this util functions are only used within this module, but may make sense to move then to an utils module

void * get_double_field(PyObject *pyitem, const char *name, double *pVal)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem, name);
    if (pyfield == NULL)
    {
        PyErr_SetString(PyExc_ValueError, "Bad segment object");
        return NULL;
    }
    *pVal = PyFloat_AsDouble(pyfield);
    Py_DECREF(pyfield);

    return pVal;
}

void * get_int_field(PyObject *pyitem, const char *name, int *pVal)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem, name);
    if (pyfield == NULL)
    {
        PyErr_SetString(PyExc_ValueError, "Bad segment object");
        return NULL;
    }
    *pVal = PyLong_AsLong(pyfield);
    Py_DECREF(pyfield);

    return pVal;
}

/* member 'name' of pyitem is a N-element list of doubles */
void * get_double_array(PyObject *pyitem, const char *name, double *pVal, int n)
{
    PyObject *pyfield = PyObject_GetAttrString(pyitem, name);
    if (pyfield == NULL)
    {
        PyErr_SetString(PyExc_ValueError, "Bad segment object");
        return NULL;
    }

    if (!PySequence_Check(pyfield))
    {
        PyErr_SetString(PyExc_ValueError, "Bad segment object");
        Py_DECREF(pyfield);
        return NULL;
    }

    if (!(PySequence_Size(pyfield) == n))
    {
        PyErr_SetString(PyExc_ValueError, "Bad segment object");
        Py_DECREF(pyfield);
        return NULL;
    }

    for (int i = 0; i < n; ++i)
    {
        PyObject *py_subitem = PySequence_GetItem(pyfield, i);
        if (!py_subitem)
        {
            PyErr_SetString(PyExc_ValueError, "Bad segment object");
            Py_DECREF(pyfield);
            return NULL;
        }
        *(pVal + i) = PyFloat_AsDouble(py_subitem);

        Py_DECREF(py_subitem);
    }

    Py_DECREF(pyfield);

    return pVal;
}