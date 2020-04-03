#ifndef __FDSITE_H_INCLUDED__
#define __FDSITE_H_INCLUDED__

#include "../fract_public.h"

typedef enum
{
    ITERS,
    IMAGE,
    PROGRESS,
    STATUS,
    PIXEL,
    TOLERANCE,
    STATS,
} msg_type_t;

// write the callbacks to a file descriptor
class FDSite : public IFractalSite
{
public:
    FDSite(int fd_);

    inline void send(msg_type_t type, int size, void *buf);

    virtual void iters_changed(int numiters);
    virtual void tolerance_changed(double tolerance);
    virtual void image_changed(int x1, int y1, int x2, int y2);
    virtual void progress_changed(float progress);
    virtual void stats_changed(pixel_stat_t &stats);
    virtual void status_changed(int status_val);
    virtual bool is_interrupted();
    virtual void pixel_changed(
        const double *params, int maxIters, int nNoPeriodIters,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a);
    virtual void interrupt();
    virtual void start(calc_args *params_);
    virtual void set_tid(pthread_t tid_);
    virtual void wait();

    ~FDSite();

private:
    int fd;
    pthread_t tid;
    volatile bool interrupted;
    calc_args *params;
    pthread_mutex_t write_lock;
};


#endif