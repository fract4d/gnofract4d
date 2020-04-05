#ifndef __SITE_H_INCLUDED__
#define __SITE_H_INCLUDED__

#include <pthread.h>

#include "model/enums.h"

typedef struct _object PyObject;
typedef struct s_pixel_stat pixel_stat_t;
struct calc_args;

// a type which must be implemented by the user of
// libfract4d. We use this to inform them of the progress
// of an ongoing calculation

// WARNING: if nThreads > 1, these can be called back on a different
// thread, possibly several different threads at the same time. It is
// the callee's responsibility to handle mutexing.

// member functions are do-nothing rather than abstract in case you
// don't want to do anything with them
class IFractalSite
{
public:
    virtual ~IFractalSite(){};
    // the parameters have changed (usually due to auto-deepening)
    virtual void iters_changed(int numiters) = 0;
    // tolerance has changed due to auto-tolerance
    virtual void tolerance_changed(double tolerance) = 0;
    // we've drawn a rectangle of image
    virtual void image_changed(int x1, int y1, int x2, int y2) = 0;
    // estimate of how far through current pass we are
    virtual void progress_changed(float progress) = 0;
    // one of the status values above
    virtual void status_changed(int status_val) = 0;
    // statistics about image
    virtual void stats_changed(pixel_stat_t &stats) = 0;
    // per-pixel callback for debugging
    virtual void pixel_changed(
        const double *params, int maxIters, int min_period_iter,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a) = 0;
    // asynchronous support
    // return true if we've been interrupted and are supposed to stop
    virtual bool is_interrupted() = 0;
    // tell an asynchronous fractal to stop calculating
    virtual void interrupt() = 0;
    // set things up before starting a new calc thread
    virtual void start(calc_args *params){};
    // having started it, set the thread id of the calc thread to wait for
    virtual void set_tid(pthread_t tid){};
    // wait for it to finish
    virtual void wait() = 0;
};

// @TODO: this sub-class should be moved out of this model into the Python interface to keep this module portable
class PySite : public IFractalSite
{
public:
    PySite(PyObject *site_);
    void iters_changed(int numiters);
    void tolerance_changed(double tolerance);
    void image_changed(int x1, int y1, int x2, int y2);
    void progress_changed(float progress);
    void stats_changed(pixel_stat_t &stats);
    void status_changed(int status_val);
    bool is_interrupted();
    void pixel_changed(
        const double *params, int maxIters, int nNoPeriodIters,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a);
    void interrupt();
    // remove the warning about overload hidding, since the IFractalSite::start function has different arguments
    using IFractalSite::start;
    void start(pthread_t tid_);
    void wait();
    ~PySite();

private:
    PyObject *site;
    bool has_pixel_changed_method;
    pthread_t tid;
};



// write the callbacks to a file descriptor
class FDSite : public IFractalSite
{
public:
    FDSite(int fd_);
    inline void send(msg_type_t type, int size, void *buf);
    void iters_changed(int numiters);
    void tolerance_changed(double tolerance);
    void image_changed(int x1, int y1, int x2, int y2);
    void progress_changed(float progress);
    void stats_changed(pixel_stat_t &stats);
    void status_changed(int status_val);
    bool is_interrupted();
    void pixel_changed(
        const double *params, int maxIters, int nNoPeriodIters,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a);
    void interrupt();
    void start(calc_args *params_);
    void set_tid(pthread_t tid_);
    void wait();
    ~FDSite();

private:
    int fd;
    pthread_t tid;
    volatile bool interrupted;
    calc_args *params;
    pthread_mutex_t write_lock;
};

#endif