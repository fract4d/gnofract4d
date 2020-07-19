#include <unistd.h>
#include <iostream>

#include "site.h"
#include "model/stats.h"

IFractalSite::~IFractalSite() {
    wait();
}

void IFractalSite::set_thread(std::thread t)
{
#ifdef DEBUG_THREADS
    std::cerr << this << " : CA : SET(" << t.get_id() << ")\n";
#endif
    m_thread = std::move(t);
}

void IFractalSite::wait()
{
    if (m_thread.joinable())
    {
#ifdef DEBUG_THREADS
        std::cerr << this << " : CA : WAIT(" << m_thread.get_id() << ")\n";
#endif
        m_thread.join();
    }
}

/*********
* FDSite *
**********/

inline void FDSite::send(msg_type_t type, int size, void *buf)
{
    const std::lock_guard<std::mutex> lock(write_lock);
    write(fd, &type, sizeof(type));
    write(fd, &size, sizeof(size));
    write(fd, buf, size);
}

FDSite::FDSite(int fd_) : fd(fd_), interrupted(false)
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FD : CTOR\n", this);
#endif
}

void FDSite::iters_changed(int numiters)
{
    send(ITERS, sizeof(int), &numiters);
}

void FDSite::tolerance_changed(double tolerance)
{
    send(TOLERANCE, sizeof(tolerance), &tolerance);
}

// we've drawn a rectangle of image
void FDSite::image_changed(int x1, int y1, int x2, int y2)
{
    if (!is_interrupted())
    {
        int buf[4] = {x1, y1, x2, y2};
        send(IMAGE, sizeof(buf), &buf[0]);
    }
}
// estimate of how far through current pass we are
void FDSite::progress_changed(float progress)
{
    if (!is_interrupted())
    {
        int percentdone = (int)(100.0 * progress);
        send(PROGRESS, sizeof(percentdone), &percentdone);
    }
}

void FDSite::stats_changed(pixel_stat_t &stats)
{
    if (!is_interrupted())
    {
        send(STATS, sizeof(stats), &stats);
    }
}

// one of the status values above
void FDSite::status_changed(int status_val)
{
    send(STATUS, sizeof(status_val), &status_val);
}

// return true if we've been interrupted and are supposed to stop
bool FDSite::is_interrupted()
{
    //fprintf(stderr,"int: %d\n",interrupted);
    return interrupted;
}

#ifdef DEBUG_PIXEL
void FDSite::pixel_changed(
    const double *params, int maxIters, int nNoPeriodIters,
    int x, int y, int aa,
    double dist, int fate, int nIters,
    int r, int g, int b, int a)
{
    /*
    fprintf(stderr,"pixel: <%g,%g,%g,%g>(%d,%d,%d) = (%g,%d,%d)\n",
        params[0],params[1],params[2],params[3],
        x,y,aa,dist,fate,nIters);
    */
    return; // FIXME
}
#endif

void FDSite::interrupt()
{
#ifdef DEBUG_THREADS
    std::cerr << this << " : CA : INT(" << m_thread.get_id() << ")\n";
#endif
    interrupted = true;
}

void FDSite::start() {
    interrupted = false;
}

FDSite::~FDSite()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FD : DTOR\n", this);
#endif
    // close(fd); // don't close something you didn't open
}
