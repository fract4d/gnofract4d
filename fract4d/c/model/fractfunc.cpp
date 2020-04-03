#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <cassert>

#include "fractfunc.h"

#include "model/image.h"

dmat4 rotated_matrix(double *params)
{
    d one = d(1.0);
    d zero = d(0.0);
    dmat4 id = identity3D<d>(params[MAGNITUDE], zero);
    return id *
           rotXY<d>(params[XYANGLE], one, zero) *
           rotXZ<d>(params[XZANGLE], one, zero) *
           rotXW<d>(params[XWANGLE], one, zero) *
           rotYZ<d>(params[YZANGLE], one, zero) *
           rotYW<d>(params[YWANGLE], one, zero) *
           rotZW<d>(params[ZWANGLE], one, zero);
}

// The eye vector is the line between the center of the screen and the
// point where the user's eye is deemed to be. It's effectively the line
// perpendicular to the screen in the -Z direction, scaled by the "eye distance"

dvec4 test_eye_vector(double *params, double dist)
{
    dmat4 mat = rotated_matrix(params);
    return mat[VZ] * -dist;
}

double gettimediff(struct timeval &startTime, struct timeval &endTime)
{
    long int diff_usec = endTime.tv_usec - startTime.tv_usec;
    if (diff_usec < 0)
    {
        endTime.tv_sec -= 1;
        diff_usec = 1000000 + diff_usec;
    }
    return (double)(endTime.tv_sec - startTime.tv_sec) + (double)diff_usec / 1000000.0;
}

fractFunc::fractFunc(
    d *params_,
    int eaa_,
    int maxiter_,
    int nThreads_,
    bool auto_deepen_,
    bool auto_tolerance_,
    double period_tolerance_,
    bool yflip,
    bool periodicity_,
    render_type_t render_type_,
    int warp_param_,
    IFractWorker *fw,
    IImage *im_,
    IFractalSite *site_)
{
    site = site_;
    im = im_;
    ok = true;
    debug_flags = 0;
    render_type = render_type_;
    //printf("render type %d\n", render_type);
    worker = fw;
    params = params_;
    eaa = eaa_;
    maxiter = maxiter_;
    nThreads = nThreads_;
    auto_deepen = auto_deepen_;
    auto_tolerance = auto_tolerance_;
    period_tolerance = period_tolerance_;
    periodicity = periodicity_;
    warp_param = warp_param_;
    set_progress_range(0.0, 1.0);
    /*
    printf("(%d,%d,%d,%d,%d,%d)\n",
	   im->Xres(), im->Yres(), im->totalXres(), im->totalYres(),
	   im->Xoffset(), im->Yoffset());
    */
    dvec4 center = dvec4(
        params[XCENTER], params[YCENTER],
        params[ZCENTER], params[WCENTER]);
    rot = rotated_matrix(params);

    eye_point = center + rot[VZ] * -10.0; // FIXME add eye distance parameter

    rot = rot / im->totalXres();
    // distance to jump for one pixel down or across
    deltax = rot[VX];
    // if yflip, draw Y axis down, otherwise up
    deltay = yflip ? rot[VY] : -rot[VY];

    // half that distance
    delta_aa_x = deltax / 2.0;
    delta_aa_y = deltay / 2.0;

    // topleft is now top left corner of top left pixel...
    topleft = center -
              deltax * im->totalXres() / 2.0 -
              deltay * im->totalYres() / 2.0;

    // offset to account for tiling, if any
    topleft += im->Xoffset() * deltax;
    topleft += im->Yoffset() * deltay;

    // .. then offset to center of pixel
    topleft += delta_aa_x + delta_aa_y;

    // antialias: offset to middle of top left quadrant of pixel
    aa_topleft = topleft - (delta_aa_y + delta_aa_x) / 2.0;

    worker->set_fractFunc(this);

    last_update_y = 0;
}

bool fractFunc::update_image(int i)
{
    bool done = try_finished_cond();
    if (!done)
    {
        image_changed(0, last_update_y, im->Xres(), i);
        progress_changed((float)i / (float)im->Yres());
    }
    last_update_y = i;
    return done;
}

// see if the image needs more (or less) iterations & tolerance to display properly
int fractFunc::updateiters()
{
    int flags = 0;
    // add up all the subtotals
    const pixel_stat_t &stats = worker->get_stats();

    if (auto_deepen)
    {
        double doublepercent = stats.better_depth_ratio() * AUTO_DEEPEN_FREQUENCY * 100;
        double halfpercent = stats.worse_depth_ratio() * AUTO_DEEPEN_FREQUENCY * 100;

        if (doublepercent > 1.0)
        {
            // more than 1% of pixels are the wrong colour!
            // quelle horreur!
            flags |= SHOULD_DEEPEN;
        }
        else if (doublepercent == 0.0 && halfpercent < 0.5 &&
                 maxiter > 32)
        {
            // less than .5% would be wrong if we used half as many iters
            // therefore we are working too hard!
            flags |= SHOULD_SHALLOWEN;
        }
    }

    if (!auto_tolerance)
    {
        // otherwise we might loosen without having gathered any stats
        return flags;
    }

    double tightenpercent = stats.better_tolerance_ratio() * AUTO_DEEPEN_FREQUENCY * 100;
    double loosenpercent = stats.worse_tolerance_ratio() * AUTO_DEEPEN_FREQUENCY * 100;

    if (tightenpercent > 0.1)
    {
        //printf("tightening\n");
        flags |= SHOULD_TIGHTEN;
    }
    else if (tightenpercent == 0.0 && loosenpercent < 0.5 &&
             period_tolerance < 1.0E-4)
    {
        //printf("relaxing\n");
        flags |= SHOULD_LOOSEN;
    }
    return flags;
}

void fractFunc::draw_aa(float min_progress, float max_progress)
{
    int w = im->Xres();
    int h = im->Yres();

    reset_counts();

    float delta = (max_progress - min_progress) / 2.0;

    // if we have multiple threads, make sure they don't modify
    // pixels the other thread will look at - that wouldn't be
    // an error per se but would make drawing nondeterministic,
    // which I'm trying to avoid
    // We do this by drawing every even line, then every odd one.

    for (int i = 0; i < 2; ++i)
    {
        set_progress_range(
            min_progress + delta * i,
            min_progress + delta * (i + 1));

        reset_progress(0.0);
        last_update_y = 0;

        for (int y = i; y < h; y += 2)
        {
            worker->row_aa(0, y, w);
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
    worker->reset_counts();
}

void fractFunc::reset_progress(float progress)
{
    worker->flush();
    image_changed(0, 0, im->Xres(), im->Yres());
    progress_changed(progress);
}

// change everything with a fate of IN to UNKNOWN, because
// image got deeper
void fractFunc::clear_in_fates()
{
    int w = im->Xres();
    int h = im->Yres();
    // FIXME can end up with some subpixels known and some unknown
    for (int y = 0; y < h; ++y)
    {
        for (int x = 0; x < w; ++x)
        {
            for (int n = 0; n < im->getNSubPixels(); ++n)
            {
                fate_t f = im->getFate(x, y, n);
                if (f & FATE_INSIDE)
                {
                    im->setFate(x, y, n, FATE_UNKNOWN);
                }
            }
        }
    }
}

void fractFunc::draw_all()
{
    struct timeval startTime, endTime;
    if (debug_flags & DEBUG_TIMING)
    {
        gettimeofday(&startTime, NULL);
    }
    status_changed(GF4D_FRACTAL_CALCULATING);

#ifndef NO_CALC
    // NO_CALC is used to stub out the actual fractal stuff so we can
    // profile & optimize the rest of the code without it confusing matters

    float minp = 0.0, maxp = 0.3;
    draw(16, 16, minp, maxp);

    minp = 0.5;
    maxp = (eaa == AA_NONE ? 0.9 : 0.5);
    int improvement_flags;
    while ((improvement_flags = updateiters()) & SHOULD_IMPROVE)
    {
        float delta = (1.0 - maxp) / 3.0;
        minp = maxp;
        maxp = maxp + delta;

        if (improvement_flags & SHOULD_DEEPEN)
        {
            maxiter *= 2;
            iters_changed(maxiter);
            status_changed(GF4D_FRACTAL_DEEPENING);
            clear_in_fates();
        }
        if (improvement_flags & SHOULD_TIGHTEN)
        {
            period_tolerance /= 10.0;
            tolerance_changed(period_tolerance);
            status_changed(GF4D_FRACTAL_TIGHTENING);
            clear_in_fates();
        }
        draw(16, 1, minp, maxp);
    }

    if (eaa > AA_NONE)
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
        maxiter /= 2;
        iters_changed(maxiter);
    }
    if (improvement_flags & SHOULD_LOOSEN)
    {
        period_tolerance *= 10.0;
        tolerance_changed(period_tolerance);
    }
#endif

    progress_changed(0.0);
    status_changed(GF4D_FRACTAL_DONE);

    if (debug_flags & DEBUG_TIMING)
    {
        gettimeofday(&endTime, NULL);

        double diff = gettimediff(startTime, endTime);
        printf("time:%g\n", diff);
    }
}

void fractFunc::draw(
    int rsize, int drawsize, float min_progress, float max_progress)
{
    if (debug_flags & DEBUG_QUICK_TRACE)
    {
        printf("drawing: %d\n", render_type);
    }
    reset_counts();

    // init RNG based on time before generating image
    time_t now;
    time(&now);
    srand((unsigned int)now);

    int y;
    int w = im->Xres();
    int h = im->Yres();

    /* reset progress indicator & clear screen */
    last_update_y = 0;
    reset_progress(min_progress);

    float mid_progress = (max_progress + min_progress) / 2.0;
    set_progress_range(min_progress, mid_progress);

    // first pass - big blocks and edges
    for (y = 0; y < h - rsize; y += rsize)
    {
        worker->qbox_row(w, y, rsize, drawsize);
        if (update_image(y))
        {
            goto done;
        }
    }

    // remaining lines
    for (; y < h; y++)
    {
        worker->row(0, y, w);
        if (update_image(y))
        {
            goto done;
        }
    }

    last_update_y = 0;
    reset_progress(0.0);
    set_progress_range(mid_progress, max_progress);

    // fill in gaps in the rsize-blocks
    for (y = 0; y < h - rsize; y += rsize)
    {
        worker->box_row(w, y, rsize);
        if (update_image(y))
        {
            goto done;
        }
    }

done:
    /* refresh entire image & reset progress bar */
    reset_progress(1.0);
    stats_changed();
}

void fractFunc::set_debug_flags(int debug_flags)
{
    this->debug_flags = debug_flags;
}

dvec4 fractFunc::vec_for_point(double x, double y)
{
    dvec4 point = topleft + x * deltax + y * deltay;
    dvec4 vec = point - eye_point;
    vec.norm();
    return vec;
}

void fractFunc::set_progress_range(float min, float max)
{
    min_progress = min;
    delta_progress = max - min;
    assert(delta_progress > 0.0);
}
