#ifndef __FRACTFUNC_H_INCLUDED__
#define __FRACTFUNC_H_INCLUDED__

#include "model/vectors.h"
#include "model/worker.h"
#include "model/site.h"
#include "model/stats.h"
#include "model/enums.h"
#include "model/calcoptions.h"
#include "model/fractgeometry.h"

class IImage;

/* this contains stuff which is useful for drawing the fractal,
   but can be recalculated at will, so isn't part of the fractal's
   persistent state. We create a new one each time we start drawing. This one
   parcels up the work which is actually performed by the fractThreadFuncs
 */

class fractFunc final: public IWorkerContext
{
public:
    fractFunc(
        calc_options,
        d *location_params,
        IFractWorker *,
        IImage *,
        IFractalSite *);
    ~fractFunc() = default;

    // additional flags controlling debugging & profiling options
    void set_debug_flags(int);

    void draw_all();

    // callback wrappers
    inline void iters_changed(int iters)
    {
        m_site->iters_changed(iters);
    }
    inline void tolerance_changed(double tolerance)
    {
        m_site->tolerance_changed(tolerance);
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

    // IWorkerContext
    inline void image_changed(int x1, int x2, int y1, int y2) const
    {
        m_site->image_changed(x1, x2, y1, y2);
    }
    inline void progress_changed(float progress) const
    {
        const float adjusted_progress = m_min_progress + progress * m_delta_progress;
        m_site->progress_changed(adjusted_progress);
    }
    inline bool try_finished_cond() const
    {
        return m_site->is_interrupted();
    }
    inline int get_debug_flags() const {
        return m_debug_flags;
    }
    inline const fract_geometry& get_geometry() const {
        return m_geometry;
    }
    inline const calc_options& get_options() const {
        return m_options;
    }

private:

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
    fract_geometry m_geometry;
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

    // redraw the image to this line
    // also checks for interruptions & returns true if we should stop
    bool update_image(int i);

    // prepare for deepening by clearing 'in'-fated pixels
    void clear_in_fates();

    // clear auto-deepen and last_update
    void reset_counts();
    int updateiters();

    void reset_progress(float progress);
    void set_progress_range(float min, float max);
};

#endif /* _FRACTFUNC_H_ */
