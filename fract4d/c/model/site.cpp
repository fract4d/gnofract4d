#include "Python.h"

#include "site.h"

#include "model/stats.h"

/*********
* PySite *
**********/

#ifdef THREADS
#define GET_LOCK             \
    PyGILState_STATE gstate; \
    gstate = PyGILState_Ensure()
#define RELEASE_LOCK PyGILState_Release(gstate)
#else
#define GET_LOCK
#define RELEASE_LOCK
#endif

PySite::PySite(PyObject *site_)
{
    site = site_;
    has_pixel_changed_method = PyObject_HasAttrString(site, "pixel_changed");
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : SITE : CTOR\n", this);
#endif
    // Don't incref, that causes a loop with parent fractal
    //Py_INCREF(site);
}

void PySite::iters_changed(int numiters)
{
    GET_LOCK;
    PyObject *ret = PyObject_CallMethod(
        site,
        const_cast<char *>("iters_changed"),
        const_cast<char *>("i"),
        numiters);
    Py_XDECREF(ret);
    RELEASE_LOCK;
}

void PySite::tolerance_changed(double tolerance)
{
    GET_LOCK;
    PyObject *ret = PyObject_CallMethod(
        site,
        const_cast<char *>("tolerance_changed"),
        const_cast<char *>("d"),
        tolerance);
    Py_XDECREF(ret);
    RELEASE_LOCK;
}

// we've drawn a rectangle of image
void PySite::image_changed(int x1, int y1, int x2, int y2)
{
    GET_LOCK;
    PyObject *ret = PyObject_CallMethod(
        site,
        const_cast<char *>("image_changed"),
        const_cast<char *>("iiii"),
        x1, y1, x2, y2);
    Py_XDECREF(ret);
    RELEASE_LOCK;
}

// estimate of how far through current pass we are
void PySite::progress_changed(float progress)
{
    double d = (double)progress;

    GET_LOCK;
    PyObject *ret = PyObject_CallMethod(
        site,
        const_cast<char *>("progress_changed"),
        const_cast<char *>("d"),
        d);
    Py_XDECREF(ret);
    RELEASE_LOCK;
}

void PySite::stats_changed(pixel_stat_t &stats)
{
    GET_LOCK;
    PyObject *ret = PyObject_CallMethod(
        site,
        const_cast<char *>("stats_changed"),
        const_cast<char *>("[kkkkkkkkkk]"),
        stats.s[0], stats.s[1], stats.s[2], stats.s[3], stats.s[4],
        stats.s[5], stats.s[6], stats.s[7], stats.s[8], stats.s[9]);
    Py_XDECREF(ret);
    RELEASE_LOCK;
}

// one of the status values above
void PySite::status_changed(int status_val)
{
    assert(this != NULL && site != NULL);
    //fprintf(stderr,"sc: %p %p\n",this,this->status_changed_cb);
    GET_LOCK;
    PyObject *ret = PyObject_CallMethod(
        site,
        const_cast<char *>("status_changed"),
        const_cast<char *>("i"),
        status_val);
    if (PyErr_Occurred())
    {
        fprintf(stderr, "bad status 2\n");
        PyErr_Print();
    }
    Py_XDECREF(ret);
    RELEASE_LOCK;
}

// return true if we've been interrupted and are supposed to stop
bool PySite::is_interrupted()
{
    GET_LOCK;
    PyObject *pyret = PyObject_CallMethod(
        site,
        const_cast<char *>("is_interrupted"), NULL);
    bool ret = false;
    if (pyret != NULL && PyLong_Check(pyret))
    {
        long i = PyLong_AsLong(pyret);
        //fprintf(stderr,"ret: %ld\n",i);
        ret = (i != 0);
    }
    Py_XDECREF(pyret);
    RELEASE_LOCK;
    return ret;
}

// pixel changed
void PySite::pixel_changed(
    const double *params, int maxIters, int nNoPeriodIters,
    int x, int y, int aa,
    double dist, int fate, int nIters,
    int r, int g, int b, int a)
{
    if (has_pixel_changed_method)
    {
        GET_LOCK;
        PyObject *pyret = PyObject_CallMethod(
            site,
            const_cast<char *>("pixel_changed"),
            const_cast<char *>("(dddd)iiiiidiiiiii"),
            params[0], params[1], params[2], params[3],
            x, y, aa,
            maxIters, nNoPeriodIters,
            dist, fate, nIters,
            r, g, b, a);
        Py_XDECREF(pyret);
        RELEASE_LOCK;
    }
};

void PySite::interrupt()
{
    // FIXME? interrupted = true;
}

void PySite::start(pthread_t tid_)
{
    tid = tid_;
}

void PySite::wait()
{
    pthread_join(tid, NULL);
}

PySite::~PySite()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : SITE : DTOR\n", this);
#endif
    //Py_DECREF(site);
}

//PyThreadState *state;

/*********
* FDSite *
**********/

inline void FDSite::send(msg_type_t type, int size, void *buf)
{
    pthread_mutex_lock(&write_lock);
    write(fd, &type, sizeof(type));
    write(fd, &size, sizeof(size));
    write(fd, buf, size);
    pthread_mutex_unlock(&write_lock);
}

FDSite::FDSite(int fd_) : fd(fd_), tid((pthread_t)0), interrupted(false), params(NULL)
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FD : CTOR\n", this);
#endif
    pthread_mutex_init(&write_lock, NULL);
}

void FDSite::iters_changed(int numiters)
{
    send(ITERS, sizeof(int), &numiters);
}

void FDSite::tolerance_changed(double tolerance)
{
    send(TOLERANCE, sizeof(tolerance), &tolerance);
}

// we've drawn a rectangle of image
void FDSite::image_changed(int x1, int y1, int x2, int y2)
{
    if (!interrupted)
    {
        int buf[4] = {x1, y1, x2, y2};
        send(IMAGE, sizeof(buf), &buf[0]);
    }
}
// estimate of how far through current pass we are
void FDSite::progress_changed(float progress)
{
    if (!interrupted)
    {
        int percentdone = (int)(100.0 * progress);
        send(PROGRESS, sizeof(percentdone), &percentdone);
    }
}

void FDSite::stats_changed(pixel_stat_t &stats)
{
    if (!interrupted)
    {
        send(STATS, sizeof(stats), &stats);
    }
}

// one of the status values above
void FDSite::status_changed(int status_val)
{
    send(STATUS, sizeof(status_val), &status_val);
}

// return true if we've been interrupted and are supposed to stop
bool FDSite::is_interrupted()
{
    //fprintf(stderr,"int: %d\n",interrupted);
    return interrupted;
}

// pixel changed
void FDSite::pixel_changed(
    const double *params, int maxIters, int nNoPeriodIters,
    int x, int y, int aa,
    double dist, int fate, int nIters,
    int r, int g, int b, int a)
{
    /*
    fprintf(stderr,"pixel: <%g,%g,%g,%g>(%d,%d,%d) = (%g,%d,%d)\n",
        params[0],params[1],params[2],params[3],
        x,y,aa,dist,fate,nIters);
    */
    return; // FIXME
};

void FDSite::interrupt()
{
#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : INT(%p)\n", this, tid);
#endif
    interrupted = true;
}

void FDSite::start(calc_args *params_)
{
#ifdef DEBUG_THREADS
    fprintf(stderr, "clear interruption\n");
#endif
    interrupted = false;
    params = params_;
}

void FDSite::set_tid(pthread_t tid_)
{
#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : SET(%p)\n", this, tid_);
#endif
    tid = tid_;
}

void FDSite::wait()
{
    if (tid != 0)
    {
#ifdef DEBUG_THREADS
        fprintf(stderr, "%p : CA : WAIT(%p)\n", this, tid);
#endif
        pthread_join(tid, NULL);
    }
}

FDSite::~FDSite()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FD : DTOR\n", this);
#endif
    close(fd);
}
