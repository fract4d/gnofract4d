#include "worker.h"

/* redirect back to a member function */
void worker(job_info_t& tdata, STFractWorker *pFunc)
{
    pFunc->work(tdata);
}

IFractWorker *IFractWorker::create(
    int numThreads, pf_obj *pfo, ColorMap *cmap, IImage *im_, IFractalSite *site)
{
    // can IFDEF here if threads are not available
    if (numThreads > 1)
    {
        return new MTFractWorker(numThreads, pfo, cmap, im_, site);
    }
    else
    {
        return new STFractWorker(pfo, cmap, im_, site);
    }
}