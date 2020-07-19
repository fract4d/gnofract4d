#ifndef __PYSITE_H_INCLUDED__
#define __PYSITE_H_INCLUDED__

#include "model/site.h"

typedef struct _object PyObject;

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
#ifdef DEBUG_PIXEL
    void pixel_changed(
        const double *params, int maxIters, int nNoPeriodIters,
        int x, int y, int aa,
        double dist, int fate, int nIters,
        int r, int g, int b, int a);
#endif
    void interrupt();
    void start();
    ~PySite();
private:
    PyObject *site;
    bool has_pixel_changed_method;
};

#endif