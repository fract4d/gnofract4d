#include "worker.h"

/* redirect back to a member function */
void worker(job_info_t& tdata, STFractWorker *pFunc)
{
    pFunc->work(tdata);
}

IFractWorker *IFractWorker::create(
    int nThreads, pf_obj *pfo, ColorMap *cmap, IImage *im_, IFractalSite *site)
{
    // can IFDEF here if threads are not available
    if (nThreads > 1)
    {
        return new MTFractWorker(nThreads, pfo, cmap, im_, site);
    }
    else
    {
        STFractWorker *w = new STFractWorker();
        if (!w)
            return w;
        w->init(pfo, cmap, im_, site);
        return w;
    }
}