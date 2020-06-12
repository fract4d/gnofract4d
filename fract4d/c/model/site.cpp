#include <unistd.h>

#include "site.h"

#include "model/stats.h"


IFractalSite::IFractalSite() {
    tid = (pthread_t)0;
}

void IFractalSite::set_tid(pthread_t tid_)
{
#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : SET(%p)\n", this, tid_);
#endif
    tid = tid_;
}

void IFractalSite::wait()
{
    if (tid != 0)
    {
#ifdef DEBUG_THREADS
        fprintf(stderr, "%p : CA : WAIT(%p)\n", this, tid);
#endif
        pthread_join(tid, NULL);
    }
}

/*********
* FDSite *
**********/

inline void FDSite::send(msg_type_t type, int size, void *buf)
{
    pthread_mutex_lock(&write_lock);
    write(fd, &type, sizeof(type));
    write(fd, &size, sizeof(size));
    write(fd, buf, size);
    pthread_mutex_unlock(&write_lock);
}

FDSite::FDSite(int fd_) : fd(fd_), interrupted(false)
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : FD : CTOR\n", this);
#endif
    pthread_mutex_init(&write_lock, NULL);
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
    if (!interrupted)
    {
        int buf[4] = {x1, y1, x2, y2};
        send(IMAGE, sizeof(buf), &buf[0]);
    }
}
// estimate of how far through current pass we are
void FDSite::progress_changed(float progress)
{
    if (!interrupted)
    {
        int percentdone = (int)(100.0 * progress);
        send(PROGRESS, sizeof(percentdone), &percentdone);
    }
}

void FDSite::stats_changed(pixel_stat_t &stats)
{
    if (!interrupted)
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

// pixel changed
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

void FDSite::interrupt()
{
#ifdef DEBUG_THREADS
    fprintf(stderr, "%p : CA : INT(%p)\n", this, tid);
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
