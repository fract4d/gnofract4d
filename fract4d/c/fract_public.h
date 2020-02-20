#ifndef _FRACT_PUBLIC_H_
#define _FRACT_PUBLIC_H_

#include <pthread.h>

#include "stats.h"

// current state of calculation
typedef enum {
    GF4D_FRACTAL_DONE,
    GF4D_FRACTAL_CALCULATING,
    GF4D_FRACTAL_DEEPENING,
    GF4D_FRACTAL_ANTIALIASING,
    GF4D_FRACTAL_PAUSED,
    GF4D_FRACTAL_TIGHTENING
} calc_state_t;

// kind of antialiasing to do
typedef enum {
    AA_NONE = 0,
    AA_FAST,
    AA_BEST,
    AA_DEFAULT /* used only for effective_aa - means use aa from fractal */
} e_antialias;

// basic parameters defining position and rotation in R4
typedef enum {
    XCENTER,
    YCENTER,
    ZCENTER,
    WCENTER,
    MAGNITUDE,
    XYANGLE,
    XZANGLE,
    XWANGLE,
    YZANGLE,
    YWANGLE,
    ZWANGLE,
} param_t;

// number of elements in enum above
#define N_PARAMS 11

// kind of image to draw
typedef enum {
    RENDER_TWO_D, // standard mandelbrot view
    RENDER_LANDSCAPE, // heightfield
    RENDER_THREE_D // ray-traced 3D object
} render_type_t;

// how to draw the image
typedef enum {
    DRAW_GUESSING, // several passes, starting with large boxes
    DRAW_TO_DISK   // complete all passes on one box_row before continuing
} draw_type_t;

// colorFunc indices
#define OUTER 0
#define INNER 1

//class colorizer;
class IImage;
typedef struct s_pixel_stat pixel_stat_t;

#include "pointFunc_public.h"

// a type which must be implemented by the user of
// libfract4d. We use this to inform them of the progress
// of an ongoing calculation

// WARNING: if nThreads > 1, these can be called back on a different
// thread, possibly several different threads at the same time. It is
// the callee's responsibility to handle mutexing.

// member functions are do-nothing rather than abstract in case you
// don't want to do anything with them
class calc_args;

class IFractalSite
{
 public:
    virtual ~IFractalSite() {};

    // the parameters have changed (usually due to auto-deepening)
    virtual void iters_changed(int numiters) {};
    // tolerance has changed due to auto-tolerance
    virtual void tolerance_changed(double tolerance) {};
    // we've drawn a rectangle of image
    virtual void image_changed(int x1, int y1, int x2, int y2) {};
    // estimate of how far through current pass we are
    virtual void progress_changed(float progress) {};
    // one of the status values above
    virtual void status_changed(int status_val) {};
    // statistics about image
    virtual void stats_changed(pixel_stat_t& stats) {};

    // per-pixel callback for debugging
    virtual void pixel_changed(
	const double *params, int maxIters, int min_period_iter,
	int x, int y, int aa,
	double dist, int fate, int nIters,
	int r, int g, int b, int a) {};

    // asynchronous support

    // return true if we've been interrupted and are supposed to stop
    virtual bool is_interrupted() { return false; };

    // tell an asynchronous fractal to stop calculating
    virtual void interrupt() { };

    // set things up before starting a new calc thread
    virtual void start(calc_args *params) {};

    // having started it, set the thread id of the calc thread to wait for
    virtual void set_tid(pthread_t tid) {};

    // wait for it to finish
    virtual void wait() {};
};


#endif /* _FRACT_PUBLIC_H_ */
