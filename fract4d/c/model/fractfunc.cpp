#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <cassert>

#include "fractfunc.h"
#include "model/image.h"

fractFunc::fractFunc(
    calc_options options,
    d *location_params,
    IFractWorker *fw,
    IImage *im,
    IFractalSite *site):
    m_debug_flags{0},
    m_options{options},
    m_geometry {
        location_params,
        static_cast<bool>(options.yflip),
        im->totalXres(),
        im->totalYres(),
        im->Xoffset(),
        im->Yoffset()
    },
    m_im{im}, m_worker{fw}, m_site{site},
    m_last_update_y{0},
    m_min_progress{0.0f}, m_delta_progress{1.0f},
    m_stats{}
{
    m_worker->set_context(this);
}

bool fractFunc::update_image(int i)
{
    const auto done = try_finished_cond();
    if (!done)
    {
        image_changed(0, m_last_update_y, m_im->Xres(), i);
        progress_changed(static_cast<float>(i) / static_cast<float>(m_im->Yres()));
    }
    m_last_update_y = i;
    return done;
}

// see if the image needs more (or less) iterations & tolerance to display properly
int fractFunc::updateiters()
{
    int flags = 0;
    // add up all the subtotals
    const pixel_stat_t &stats = m_worker->get_stats();
    if (m_options.auto_deepen)
    {
        const double doublepercent = stats.better_depth_ratio() * AUTO_DEEPEN_FREQUENCY * 100;
        const double halfpercent = stats.worse_depth_ratio() * AUTO_DEEPEN_FREQUENCY * 100;
        if (doublepercent > 1.0)
        {
            // more than 1% of pixels are the wrong colour!
            // quelle horreur!
            flags |= SHOULD_DEEPEN;
        }
        else if (doublepercent == 0.0 && halfpercent < 0.5 && m_options.maxiter > 32)
        {
            // less than .5% would be wrong if we used half as many iters
            // therefore we are working too hard!
            flags |= SHOULD_SHALLOWEN;
        }
    }
    if (m_options.auto_tolerance)
    {
        const double tightenpercent = stats.better_tolerance_ratio() * AUTO_DEEPEN_FREQUENCY * 100;
        const double loosenpercent = stats.worse_tolerance_ratio() * AUTO_DEEPEN_FREQUENCY * 100;
        if (tightenpercent > 0.1)
        {
            flags |= SHOULD_TIGHTEN;
        }
        else if (tightenpercent == 0.0 && loosenpercent < 0.5 && m_options.period_tolerance < 1.0E-4)
        {
            flags |= SHOULD_LOOSEN;
        }
    }
    return flags;
}

void fractFunc::draw_aa(float min_progress, float max_progress)
{
    const auto w = m_im->Xres();
    const auto h = m_im->Yres();

    reset_counts();

    const float delta = (max_progress - min_progress) / 2.0;

    // if we have multiple threads, make sure they don't modify
    // pixels the other thread will look at - that wouldn't be
    // an error per se but would make drawing nondeterministic,
    // which I'm trying to avoid
    // We do this by drawing every even line, then every odd one.

    for (auto i = 0; i < 2; ++i)
    {
        set_progress_range(
            min_progress + delta * i,
            min_progress + delta * (i + 1));

        reset_progress(0.0);
        m_last_update_y = 0;

        for (int y = i; y < h; y += 2)
        {
            m_worker->row_aa(y, w);
            if (update_image(y))
            {
                break;
            }
        }
        reset_progress(1.0);
    }
    stats_changed();
}

void fractFunc::reset_counts()
{
    m_worker->reset_counts();
}

void fractFunc::reset_progress(float progress)
{
    m_worker->flush();
    image_changed(0, 0, m_im->Xres(), m_im->Yres());
    progress_changed(progress);
}

// change everything with a fate of IN to UNKNOWN, because
// image got deeper
void fractFunc::clear_in_fates()
{
    const auto w = m_im->Xres();
    const auto h = m_im->Yres();
    // FIXME can end up with some subpixels known and some unknown
    for (auto y = 0; y < h; ++y)
    {
        for (auto x = 0; x < w; ++x)
        {
            for (auto n = 0; n < m_im->getNSubPixels(); ++n)
            {
                if (m_im->getFate(x, y, n) & FATE_INSIDE)
                {
                    m_im->setFate(x, y, n, FATE_UNKNOWN);
                }
            }
        }
    }
}

void fractFunc::draw_all()
{
    std::time_t startTime, endTime;
    if (m_debug_flags & DEBUG_TIMING)
    {
        std::time(&startTime);
    }

    status_changed(GF4D_FRACTAL_CALCULATING);

#ifndef NO_CALC
    // NO_CALC is used to stub out the actual fractal stuff so we can
    // profile & optimize the rest of the code without it confusing matters

    float minp = 0.0, maxp = 0.3;
    draw(16, 16, minp, maxp);

    maxp = m_options.eaa == AA_NONE ? 0.9 : 0.5;
    int improvement_flags;
    while ((improvement_flags = updateiters()) & SHOULD_IMPROVE)
    {
        const float delta = (1.0 - maxp) / 3.0;
        minp = maxp;
        maxp = maxp + delta;
        if (improvement_flags & SHOULD_DEEPEN)
        {
            m_options.maxiter *= 2;
            iters_changed(m_options.maxiter);
            status_changed(GF4D_FRACTAL_DEEPENING);
        }
        if (improvement_flags & SHOULD_TIGHTEN)
        {
            m_options.period_tolerance /= 10.0;
            tolerance_changed(m_options.period_tolerance);
            status_changed(GF4D_FRACTAL_TIGHTENING);
        }
        clear_in_fates();
        draw(16, 1, minp, maxp);
    }

    if (m_options.eaa > AA_NONE)
    {
        status_changed(GF4D_FRACTAL_ANTIALIASING);
        draw_aa(maxp, 1.0);
    }
    else
    {
        set_progress_range(0.0, 1.0);
        progress_changed(1.0);
    }

    // we do this after antialiasing because otherwise sometimes the
    // aa pass makes the image shallower, which is distracting
    if (improvement_flags & SHOULD_SHALLOWEN)
    {
        m_options.maxiter /= 2;
        iters_changed(m_options.maxiter);
    }
    if (improvement_flags & SHOULD_LOOSEN)
    {
        m_options.period_tolerance *= 10.0;
        tolerance_changed(m_options.period_tolerance);
    }
#endif

    progress_changed(0.0);
    status_changed(GF4D_FRACTAL_DONE);

    if (m_debug_flags & DEBUG_TIMING)
    {
        std::time(&endTime);
        printf("time:%g\n", std::difftime(startTime, endTime));
    }
}

void fractFunc::draw(int rsize, int drawsize, float min_progress, float max_progress)
{
    if (m_debug_flags & DEBUG_QUICK_TRACE)
    {
        printf("drawing: %d\n", m_options.render_type);
    }
    reset_counts();

    // init RNG based on time before generating image
    std::srand(static_cast<unsigned int>(std::time(nullptr)));

    const auto w = m_im->Xres();
    const auto h = m_im->Yres();

    /* reset progress indicator & clear screen */
    m_last_update_y = 0;
    reset_progress(min_progress);
    float mid_progress = (max_progress + min_progress) / 2.0;
    set_progress_range(min_progress, mid_progress);

    // first pass - big blocks and edges
    auto y = 0;
    while(y < h) {
        if ((h - y) > rsize) {
            m_worker->qbox_row(w, y, rsize, drawsize);
            y += rsize;
        } else {
            m_worker->row(0, y, w);
            ++y;
        }
        if (update_image(y)) {
            break;
        }
    }
    m_last_update_y = 0;
    reset_progress(0.0);
    set_progress_range(mid_progress, max_progress);

    // fill in gaps in the rsize-blocks
    for (auto y = 0; y < h - rsize; y += rsize)
    {
        m_worker->box_row(w, y, rsize);
        if (update_image(y))
        {
            break;
        }
    }

    /* refresh entire image & reset progress bar */
    reset_progress(1.0);
    stats_changed();
}

void fractFunc::set_debug_flags(int debug_flags)
{
    m_debug_flags = debug_flags;
}

void fractFunc::set_progress_range(float min, float max)
{
    m_min_progress = min;
    m_delta_progress = max - min;
    assert(m_delta_progress > 0.0);
}
