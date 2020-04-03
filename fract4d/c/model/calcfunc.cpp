#include <cassert>

#include "calcfunc.h"

#include "model/worker.h"
#include "model/fractfunc.h"
#include "model/image.h"

void calc(
    d *params,
    int eaa,
    int maxiter,
    int nThreads,
    pf_obj *pfo,
    ColorMap *cmap,
    bool auto_deepen,
    bool auto_tolerance,
    double tolerance,
    bool yflip,
    bool periodicity,
    bool dirty,
    int debug_flags,
    render_type_t render_type,
    int warp_param,
    IImage *im,
    IFractalSite *site)
{
    assert(NULL != im && NULL != site &&
           NULL != cmap && NULL != pfo && NULL != params);
    IFractWorker *worker = IFractWorker::create(nThreads, pfo, cmap, im, site);

    if (worker && worker->ok())
    {
        fractFunc ff(
            params,
            eaa,
            maxiter,
            nThreads,
            auto_deepen,
            auto_tolerance,
            tolerance,
            yflip,
            periodicity,
            render_type,
            warp_param,
            worker,
            im,
            site);

        ff.set_debug_flags(debug_flags);
        if (dirty)
        {
            im->clear();
        }
        ff.draw_all();
    }
    delete worker;
}