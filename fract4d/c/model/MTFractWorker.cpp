#include "model/worker.h"

#include "model/colormap.h"
#include "model/image.h"
#include "model/site.h"
#include "model/threadpool.h"

#include "pf.h"

MTFractWorker::MTFractWorker(
    int n,
    pf_obj *pfo,
    ColorMap *cmap,
    IImage *im,
    IFractalSite *site)
    : nWorkers{n > 1 ? n + 1 : 1}, ptf(), m_ok{true}
{
    /* 0'th ftf is in this thread for calculations we don't want to offload */
    ptf.reserve(nWorkers);
    for (int i = 0; i < nWorkers; ++i)
    {
        STFractWorker &stfw = ptf.emplace_back(pfo, cmap, im, site);
        if (!stfw.ok())
        {
            m_ok = false;
        }
    }
    if (n > 1)
    {
        ptp = std::make_unique<tpool<job_info_t, STFractWorker>>(n, 1000, &ptf[0]);
    }
}

MTFractWorker::~MTFractWorker()
{
}

void MTFractWorker::set_fractFunc(fractFunc *ff_)
{
    for (int i = 0; i < nWorkers; ++i)
    {
        ptf[i].set_fractFunc(ff_);
    }
}

void MTFractWorker::row_aa(int x, int y, int n)
{
    if (nWorkers > 1 && n > 8)
    {
        send_row_aa(x, y, n);
    }
    else
    {
        ptf[0].row_aa(x, y, n);
    }
}

void MTFractWorker::row(int x, int y, int n)
{
    if (nWorkers > 1 && n > 8)
    {
        send_row(x, y, n);
    }
    else
    {
        ptf[0].row(x, y, n);
    }
}

void MTFractWorker::box(int x, int y, int rsize)
{
    ptf[0].box(x, y, rsize);
}

void MTFractWorker::box_row(int w, int y, int rsize)
{
    if (nWorkers > 1)
    {
        send_box_row(w, y, rsize);
    }
    else
    {
        ptf[0].box_row(w, y, rsize);
    }
}

void MTFractWorker::qbox_row(int w, int y, int rsize, int drawsize)
{
    if (nWorkers > 1)
    {
        send_qbox_row(w, y, rsize, drawsize);
    }
    else
    {
        ptf[0].qbox_row(w, y, rsize, drawsize);
    }
}

void MTFractWorker::pixel(int x, int y, int w, int h)
{
    //assert(0 && "unexpected");
    ptf[0].pixel(x, y, w, h);
}

void MTFractWorker::pixel_aa(int x, int y)
{
}

void MTFractWorker::reset_counts()
{
    for (int i = 0; i < nWorkers; ++i)
    {
        ptf[i].reset_counts();
    }
}

const pixel_stat_t &MTFractWorker::get_stats() const
{
    // recompute the sums on the fly
    stats.reset();

    for (int i = 0; i < nWorkers; ++i)
    {
        const pixel_stat_t &stat = ptf[i].get_stats();
        stats.add(stat);
    }
    return stats;
}

void MTFractWorker::send_cmd(job_type_t job, int x, int y, int param)
{
    job_info_t work;
    work.job = job;
    work.x = x;
    work.y = y;
    work.param = param;
    work.param2 = 0;
    ptp->add_work(worker, work);
}

void MTFractWorker::send_cmd(job_type_t job, int x, int y, int param, int param2)
{
    job_info_t work;
    work.job = job;
    work.x = x;
    work.y = y;
    work.param = param;
    work.param2 = param2;
    ptp->add_work(worker, work);
}

void MTFractWorker::send_row(int x, int y, int w)
{
    //cout << "sent ROW" << y << "\n";
    send_cmd(JOB_ROW, x, y, w);
}

void MTFractWorker::send_box_row(int w, int y, int rsize)
{
    //cout << "sent BXR" << y << "\n";
    send_cmd(JOB_BOX_ROW, w, y, rsize);
}

void MTFractWorker::send_qbox_row(int w, int y, int rsize, int drawsize)
{
    //cout << "sent QBR" << y << "\n";
    send_cmd(JOB_QBOX_ROW, w, y, rsize, drawsize);
}

void MTFractWorker::send_box(int x, int y, int rsize)
{
    //cout << "sent BOX" << y << "\n";
    send_cmd(JOB_BOX, x, y, rsize);
}

void MTFractWorker::send_row_aa(int x, int y, int w)
{
    //cout << "sent RAA" << y << "\n";
    send_cmd(JOB_ROW_AA, x, y, w);
}

void MTFractWorker::flush()
{
    if (ptp)
    {
        ptp->flush();
    }
}

bool MTFractWorker::ok()
{
    return m_ok;
}

bool MTFractWorker::find_root(const dvec4 &eye, const dvec4 &look, dvec4 &root)
{
    return ptf[0].find_root(eye, look, root);
}
