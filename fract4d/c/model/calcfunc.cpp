#include <cassert>
#include <memory>

#include "calcfunc.h"

#include "model/worker.h"
#include "model/fractfunc.h"
#include "model/image.h"


void calc(
    calc_options options,
    d *params,
    pf_obj *pfo,
    ColorMap *cmap,
    IFractalSite *site,
    IImage *im,
    int debug_flags)
{
    assert(im && site && cmap && pfo && params);

    std::unique_ptr<IFractWorker> worker {IFractWorker::create(options.nThreads, pfo, cmap, im, site)};
    if (worker)
    {
        fractFunc ff(
            options,
            params,
            worker.get(),
            im,
            site
        );

        ff.set_debug_flags(debug_flags);
        if (options.dirty)
        {
            im->clear();
        }
        ff.draw_all();
    }
}