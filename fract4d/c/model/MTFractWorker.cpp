#include "model/worker.h"

#include "model/colormap.h"
#include "model/image.h"
#include "model/site.h"

#include "pf.h"

MTFractWorker::MTFractWorker(
    int numThreads,
    pf_obj *pfo,
    ColorMap *cmap,
    IImage *im,
    IFractalSite *site)
    : m_workers()
{
    /* 0'th ftf is in this thread for calculations we don't want to offload */
    const auto numWorkers = numThreads > 1 ? numThreads + 1 : 1;

    m_workers.reserve(numWorkers);
    for (int i = 0; i < numWorkers; ++i)
    {
        m_workers.emplace_back(pfo, cmap, im, site);
    }
    if (numThreads > 1)
    {
        m_threads = std::make_unique<tpool<job_info_t, STFractWorker>>(numThreads, 1000, &m_workers[0]);
    }
}

void MTFractWorker::set_context(IWorkerContext *context)
{
    for (auto& worker: m_workers)
    {
        worker.set_context(context);
    }
}

void MTFractWorker::row_aa(int y, int n)
{
    if (m_threads && n > 8)
    {
        send_row_aa(y, n);
    }
    else
    {
        m_workers[0].row_aa(y, n);
    }
}

void MTFractWorker::row(int x, int y, int n)
{
    if (m_threads && n > 8)
    {
        send_row(x, y, n);
    }
    else
    {
        m_workers[0].row(x, y, n);
    }
}

void MTFractWorker::box_row(int w, int y, int rsize)
{
    if (m_threads)
    {
        send_box_row(w, y, rsize);
    }
    else
    {
        m_workers[0].box_row(w, y, rsize);
    }
}

void MTFractWorker::qbox_row(int w, int y, int rsize, int drawsize)
{
    if (m_threads)
    {
        send_qbox_row(w, y, rsize, drawsize);
    }
    else
    {
        m_workers[0].qbox_row(w, y, rsize, drawsize);
    }
}

void MTFractWorker::reset_counts()
{
    for (auto& worker: m_workers) {
        worker.reset_counts();
    }
}

const pixel_stat_t &MTFractWorker::get_stats() const
{
    // recompute the sums on the fly
    m_stats.reset();

    for (auto& worker: m_workers)
    {
        const pixel_stat_t &stat = worker.get_stats();
        m_stats.add(stat);
    }
    return m_stats;
}

void MTFractWorker::send_cmd(job_type_t job, int x, int y, int param, int param2)
{
    job_info_t work;
    work.job = job;
    work.x = x;
    work.y = y;
    work.param = param;
    work.param2 = param2;
    m_threads->add_work(worker, work);
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

void MTFractWorker::send_row_aa(int y, int w)
{
    //cout << "sent RAA" << y << "\n";
    send_cmd(JOB_ROW_AA, 0, y, w);
}

void MTFractWorker::flush()
{
    if (m_threads)
    {
        m_threads->flush();
    }
}
