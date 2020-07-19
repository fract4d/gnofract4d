#ifndef __SITE_H_INCLUDED__
#define __SITE_H_INCLUDED__

#include <thread>
#include <mutex>
#include <atomic>

#include "model/enums.h"

typedef struct s_pixel_stat pixel_stat_t;

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
    virtual ~IFractalSite();
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
#ifdef DEBUG_PIXEL
    // per-pixel callback for debugging
    virtual void pixel_changed(
        const double *params, int maxIters, int min_period_iter,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a) = 0;
#endif
    // asynchronous support
    // return true if we've been interrupted and are supposed to stop
    virtual bool is_interrupted() = 0;
    // tell an asynchronous fractal to stop calculating
    virtual void interrupt() = 0;
    virtual void start() = 0;
    // having started it, set the thread id of the calc thread to wait for
    virtual void set_thread(std::thread t);
    // wait for it to finish
    virtual void wait();
protected:
    std::thread m_thread;
};

// write the callbacks to a file descriptor
class FDSite : public IFractalSite
{
public:
    FDSite(int fd_);
    void iters_changed(int numiters);
    void tolerance_changed(double tolerance);
    void image_changed(int x1, int y1, int x2, int y2);
    void progress_changed(float progress);
    void stats_changed(pixel_stat_t &stats);
    void status_changed(int status_val);
    bool is_interrupted();
#ifdef DEBUG_PIXEL
    void pixel_changed(
        const double *params, int maxIters, int nNoPeriodIters,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a);
#endif
    void interrupt();
    void start();
    ~FDSite();
private:
    int fd;
    std::atomic<bool> interrupted;
    std::mutex write_lock;

    inline void send(msg_type_t type, int size, void *buf);
};

#endif