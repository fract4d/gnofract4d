#include "Python.h"

#include "fdsite.h"
#include "pysite.h"

#include "sites.h"
#include "common.h"


namespace sites {

    PyObject * pyfdsite_create(PyObject *self, PyObject *args)
    {
        int fd;
        if (!PyArg_ParseTuple(args, "i", &fd))
        {
            return NULL;
        }

        IFractalSite *site = new FDSite(fd);

        PyObject *pyret = PyCapsule_New(site, OBTYPE_SITE, pysite_delete);

        return pyret;
    }

    PyObject * pysite_create(PyObject *self, PyObject *args)
    {
        PyObject *pysite;
        if (!PyArg_ParseTuple(
                args,
                "O",
                &pysite))
        {
            return NULL;
        }

        IFractalSite *site = new PySite(pysite);

        //fprintf(stderr,"pysite_create: %p\n",site);
        PyObject *pyret = PyCapsule_New(site, OBTYPE_SITE, pysite_delete);

        return pyret;
    }

    void pysite_delete(PyObject *pysite)
    {
        IFractalSite *site = site_fromcapsule(pysite);
        delete site;
    }

    IFractalSite * site_fromcapsule(PyObject *pysite)
    {
        IFractalSite *site = (IFractalSite *)PyCapsule_GetPointer(pysite, OBTYPE_SITE);
        if (NULL == site)
        {
            fprintf(stderr, "%p : ST : BAD\n", pysite);
        }
        return site;
    }

}
