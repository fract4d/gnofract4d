
#ifndef __PYSITE_H_INCLUDED__
#define __PYSITE_H_INCLUDED__


#include "../fract_public.h"


class PySite : public IFractalSite
{
public:
    PySite(PyObject *site_);

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
    // remove the warning about overload hidding, since the IFractalSite::start function has different arguments
    using IFractalSite::start;
    virtual void start(pthread_t tid_);
    virtual void wait();

    ~PySite();

private:
    PyObject *site;
    bool has_pixel_changed_method;
    pthread_t tid;
};

#endif