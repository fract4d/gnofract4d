#include "Python.h"

#include "utils.h"
#include "common.h"

#include "../vectors.h"
#include "../fract_public.h"
#include "../fractFunc.h"

#include "../fract_stdlib.h"


namespace utils {

    PyObject * rot_matrix(PyObject *self, PyObject *args)
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


    PyObject * eye_vector(PyObject *self, PyObject *args)
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


    PyObject * pyrgb_to_hsv(PyObject *self, PyObject *args)
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

    PyObject * pyrgb_to_hsl(PyObject *self, PyObject *args)
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

    PyObject * pyhsl_to_rgb(PyObject *self, PyObject *args)
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


    PyObject * pyarray_get(PyObject *self, PyObject *args)
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

    PyObject * pyarray_set(PyObject *self, PyObject *args)
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

}