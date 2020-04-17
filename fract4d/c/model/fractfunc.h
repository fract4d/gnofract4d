#ifndef __FRACTFUNC_H_INCLUDED__
#define __FRACTFUNC_H_INCLUDED__

#include "model/vectors.h"
#include "model/worker.h"
#include "model/site.h"
#include "model/stats.h"
#include "model/enums.h"

class IImage;

/* this contains stuff which is useful for drawing the fractal,
   but can be recalculated at will, so isn't part of the fractal's
   persistent state. We create a new one each time we start drawing. This one
   parcels up the work which is actually performed by the fractThreadFuncs
 */

// geometry utilities
dmat4 rotated_matrix(double *params);
dvec4 test_eye_vector(double *params, double dist);

enum
{
    DEBUG_QUICK_TRACE = 1,
    DEBUG_DRAWING_STATS = 2,
    DEBUG_TIMING = 4
};

class fractFunc
{
public:
    fractFunc(
        d *params,
        int eaa,
        int maxiter,
        int nThreads_,
        bool auto_deepen,
        bool auto_tolerance,
        double period_tolerance,
        bool yflip,
        bool periodicity,
        render_type_t render_type,
        int warp_param,
        IFractWorker *fw,
        IImage *_im,
        IFractalSite *_site);
    ~fractFunc(){};
    // additional flags controlling debugging & profiling options
    void set_debug_flags(int debug_flags);
    void draw_all();
    void draw(int rsize, int drawsize, float min_progress, float max_progress);
    void draw_aa(float min_progress, float max_progress);
    int updateiters();
    // a vector from the eye through the pixel at (x,y)
    dvec4 vec_for_point(double x, double y);
    // @TODO: review the need of having this coupling
    friend class STFractWorker;
    // callback wrappers
    inline void iters_changed(int iters)
    {
        site->iters_changed(iters);
    }
    inline void tolerance_changed(double tolerance)
    {
        site->tolerance_changed(tolerance);
    }
    inline void image_changed(int x1, int x2, int y1, int y2)
    {
        site->image_changed(x1, x2, y1, y2);
    }
    inline void progress_changed(float progress)
    {
        float adjusted_progress = min_progress + progress * delta_progress;
        site->progress_changed(adjusted_progress);
    }
    inline void stats_changed()
    {
        stats.add(worker->get_stats());
        site->stats_changed(stats);
    }
    inline void status_changed(int status_val)
    {
        site->status_changed(status_val);
    }
    inline bool try_finished_cond()
    {
        return site->is_interrupted();
    }
    // used for calculating (x,y,z,w) pixel coords
    dmat4 rot;                    // scaled rotation matrix
    dvec4 deltax, deltay;         // step from 1 pixel to the next in x,y directions
    dvec4 delta_aa_x, delta_aa_y; // offset between subpixels
    dvec4 topleft;                // top left corner of screen
    dvec4 aa_topleft;             // topleft - offset to 1st subpixel to draw
    dvec4 eye_point;              // where user's eye is (for 3d mode)

private:
    // MEMBER VARS
    bool ok; // did this instance get constructed ok?
    // (* this should really be done with exns but they are unreliable
    //  * in the presence of pthreads - grrr *)
    // do every nth pixel twice as deep as the others to
    // see if we need to auto-deepen
    enum
    {
        AUTO_DEEPEN_FREQUENCY = 30,
        AUTO_TOLERANCE_FREQUENCY = 30
    };
    // flags for controlling auto-improvement
    enum
    {
        SHOULD_DEEPEN = 1,
        SHOULD_SHALLOWEN = 2, // yes, I know this isn't a word
        SHOULD_LOOSEN = 4,
        SHOULD_TIGHTEN = 8,
        SHOULD_IMPROVE = (SHOULD_DEEPEN | SHOULD_TIGHTEN),
        SHOULD_RELAX = (SHOULD_SHALLOWEN | SHOULD_LOOSEN)
    };
    // params from ctor
    int eaa;
    int maxiter;
    int nThreads;
    bool auto_deepen;
    bool auto_tolerance;
    bool periodicity;
    double period_tolerance;
    int debug_flags;
    render_type_t render_type;
    int warp_param;
    d *params;
    IImage *im;
    IFractWorker *worker;
    // for callbacks
    IFractalSite *site;
    // last time we redrew the image to this line
    int last_update_y;
    float min_progress;
    float delta_progress;
    pixel_stat_t stats;
    void set_progress_range(float min, float max);
    // private drawing methods
    void send_quit();
    // redraw the image to this line
    // also checks for interruptions & returns true if we should stop
    bool update_image(int i);
    // prepare for deepening by clearing 'in'-fated pixels
    void clear_in_fates();
    // clear auto-deepen and last_update
    void reset_counts();
    void reset_progress(float progress);
};

#endif /* _FRACTFUNC_H_ */
