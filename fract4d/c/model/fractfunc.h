#ifndef __FRACTFUNC_H_INCLUDED__
#define __FRACTFUNC_H_INCLUDED__

#include "model/vectors.h"
#include "model/worker.h"
#include "model/site.h"
#include "model/stats.h"
#include "model/enums.h"
#include "model/calcoptions.h"

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
        calc_options,
        d *params,
        IFractWorker *,
        IImage *,
        IFractalSite *);
    ~fractFunc(){};
    // additional flags controlling debugging & profiling options
    void set_debug_flags(int);
    void draw_all();

    // a vector from the eye through the pixel at (x,y)
    dvec4 vec_for_point(double x, double y);
    // @TODO: review the need of having this coupling
    friend class STFractWorker;
    // callback wrappers
    inline void iters_changed(int iters)
    {
        m_site->iters_changed(iters);
    }
    inline void tolerance_changed(double tolerance)
    {
        m_site->tolerance_changed(tolerance);
    }
    inline void image_changed(int x1, int x2, int y1, int y2)
    {
        m_site->image_changed(x1, x2, y1, y2);
    }
    inline void progress_changed(float progress)
    {
        const float adjusted_progress = m_min_progress + progress * m_delta_progress;
        m_site->progress_changed(adjusted_progress);
    }
    inline void stats_changed()
    {
        m_stats.add(m_worker->get_stats());
        m_site->stats_changed(m_stats);
    }
    inline void status_changed(int status_val)
    {
        m_site->status_changed(status_val);
    }
    inline bool try_finished_cond()
    {
        return m_site->is_interrupted();
    }
    // used for calculating (x,y,z,w) pixel coords
    dvec4 deltax, deltay;         // step from 1 pixel to the next in x,y directions
    dvec4 delta_aa_x, delta_aa_y; // offset between subpixels
    dvec4 topleft;                // top left corner of screen
    dvec4 aa_topleft;             // topleft - offset to 1st subpixel to draw
    dvec4 eye_point;              // where user's eye is (for 3d mode)

private:

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

    int m_debug_flags;
    calc_options m_options;
    d *m_params;
    IImage *m_im;
    IFractWorker *m_worker;
    IFractalSite *m_site;
    // last time we redrew the image to this line
    int m_last_update_y;
    float m_min_progress;
    float m_delta_progress;
    pixel_stat_t m_stats;

    void draw(int rsize, int drawsize, float min_progress, float max_progress);
    void draw_aa(float min_progress, float max_progress);
    int updateiters();
    void set_progress_range(float min, float max);
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
