#include <cstdio>
#include <cstdlib>
#include <utility>
#include <cassert>

#include "model/worker.h"

#include "model/colormap.h"
#include "model/image.h"
#include "model/site.h"
#include "model/calcoptions.h"

#include "pf.h"


void STFractWorker::set_context(IWorkerContext *context)
{
    m_context = context;
}

/* we're in a worker thread */
void STFractWorker::work(job_info_t &tdata)
{
    if (m_context->try_finished_cond())
    {
        // interrupted - just return without doing anything
        // this is less efficient than clearing the queue but easier
        return;
    }
    int nRows = 0;
    /* carry them out */
    switch (tdata.job)
    {
    case JOB_BOX:
        //printf("BOX(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        box(tdata.x, tdata.y, tdata.param);
        nRows = tdata.param;
        break;
    case JOB_ROW:
        //printf("ROW(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        row(tdata.x, tdata.y, tdata.param);
        nRows = 1;
        break;
    case JOB_BOX_ROW:
        //printf("BXR(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        box_row(tdata.x, tdata.y, tdata.param);
        nRows = tdata.param;
        break;
    case JOB_ROW_AA:
        //printf("RAA(%d,%d,%d) [%x]\n",x,y,param,(unsigned int)pthread_self());
        row_aa(tdata.y, tdata.param);
        nRows = 1;
        break;
    case JOB_QBOX_ROW:
        //printf("QBR(%d,%d,%d,%d) [%x]\n",x,y,param,param2,(unsigned int)pthread_self());
        qbox_row(tdata.x, tdata.y, tdata.param, tdata.param2);
        nRows = tdata.param;
        break;
    default:
        printf("Unknown job id %d ignored\n", static_cast<int>(tdata.job));
    }
    m_context->image_changed(0, tdata.y, m_im->Xres(), tdata.y + nRows);
    const float new_progress = static_cast<float>(tdata.y) / static_cast<float>(m_im->Yres());
    m_context->progress_changed(new_progress);
}

void STFractWorker::row_aa(int y, int w)
{
    for (auto x = 0; x < w; ++x)
    {
        pixel_aa(x, y);
    }
}

inline int STFractWorker::periodGuess()
{
    return periodGuess(m_lastPointIters);
}

inline int STFractWorker::periodGuess(int last)
{
    const calc_options &options = m_context->get_options();
    if (!options.periodicity)
    {
        return options.maxiter;
    }
    if (last == -1)
    {
        // we were captured last time so probably will be again
        return 0;
    }
    // we escaped, so don't try so hard this time
    return m_lastPointIters + 10;
}

inline void STFractWorker::periodSet(int ppos)
{
    m_lastPointIters = ppos;
}

void STFractWorker::row(int x, int y, int n)
{
    for (auto i = 0; i < n; ++i)
    {
        pixel(x + i, y, 1, 1);
    }
}

void STFractWorker::reset_counts()
{
    m_stats.reset();
}

const pixel_stat_t &STFractWorker::get_stats() const
{
    return m_stats;
}

inline int STFractWorker::Pixel2INT(int x, int y)
{
    return static_cast<int>(m_im->get(x, y));
}

inline bool STFractWorker::isTheSame(int targetIter, int targetCol, int x, int y)
{
    // does this point have the target # of iterations?
    // does it have the same colour too?
    if ((m_im->getIter(x, y) == targetIter) && (Pixel2INT(x, y) == targetCol)) {
        return true;
    }
    return false;
}

rgba_t STFractWorker::antialias(int x, int y)
{
    const calc_options &options = m_context->get_options();
    const fract_geometry &geometry = m_context->get_geometry();
    const dvec4 topleft = geometry.vec_for_point_2d_aa(x, y);
    dvec4 pos = topleft;
    rgba_t ptmp;
    unsigned int pixel_r_val = 0, pixel_g_val = 0, pixel_b_val = 0;
    int p;
    float index;
    fate_t fate;
    const int checkPeriod = periodGuess(m_im->getIter(x, y));
    if (m_context->get_debug_flags() & DEBUG_DRAWING_STATS)
    {
        printf("doaa %d %d\n", x, y);
    }
    const rgba_t last = m_im->get(x, y);
    // the reason we check hasUnknownSubpixels instead checking the subpixel 0 like in the other corners
    // it's because subpixel 0 does not contain the offset 0 subpixel for antialias (aa_topleft)
    // but instead the point in the middle of the 4 (topleft)
    // @TODO: (improvement) based on the previous statement we could check if there's unknown subpixels
    // and then calculate every subpixel, otherwise recolor based on the current subpixel values
    // top left
    if (m_im->hasUnknownSubpixels(x, y))
    {
        m_pf.calc(
            pos.n, options.maxiter,
            checkPeriod, options.period_tolerance,
            options.warp_param,
            x, y, 1,
            &ptmp, &p, &index, &fate);
        m_im->setFate(x, y, 0, fate);
        m_im->setIndex(x, y, 0, index);
    }
    else
    {
        fate = m_im->getFate(x, y, 0);
        ptmp = m_pf.recolor(m_im->getIndex(x, y, 0), fate, last);
    }
    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;
    // top right
    fate = m_im->getFate(x, y, 1);
    if (fate == FATE_UNKNOWN)
    {
        pos += geometry.delta_aa_x;
        m_pf.calc(
            pos.n, options.maxiter,
            checkPeriod, options.period_tolerance,
            options.warp_param,
            x, y, 2,
            &ptmp, &p, &index, &fate);
        m_im->setFate(x, y, 1, fate);
        m_im->setIndex(x, y, 1, index);
    }
    else
    {
        ptmp = m_pf.recolor(m_im->getIndex(x, y, 1), fate, last);
    }
    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;
    // bottom left
    fate = m_im->getFate(x, y, 2);
    if (fate == FATE_UNKNOWN)
    {
        pos = topleft + geometry.delta_aa_y;
        m_pf.calc(
            pos.n, options.maxiter,
            checkPeriod, options.period_tolerance,
            options.warp_param,
            x, y, 3,
            &ptmp, &p, &index, &fate);
        m_im->setFate(x, y, 2, fate);
        m_im->setIndex(x, y, 2, index);
    }
    else
    {
        ptmp = m_pf.recolor(m_im->getIndex(x, y, 2), fate, last);
    }
    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;
    // bottom right
    fate = m_im->getFate(x, y, 3);
    if (fate == FATE_UNKNOWN)
    {
        pos = topleft + geometry.delta_aa_y + geometry.delta_aa_x;
        m_pf.calc(
            pos.n, options.maxiter,
            checkPeriod, options.period_tolerance,
            options.warp_param,
            x, y, 4,
            &ptmp, &p, &index, &fate);
        m_im->setFate(x, y, 3, fate);
        m_im->setIndex(x, y, 3, index);
    }
    else
    {
        ptmp = m_pf.recolor(m_im->getIndex(x, y, 3), fate, last);
    }
    pixel_r_val += ptmp.r;
    pixel_g_val += ptmp.g;
    pixel_b_val += ptmp.b;
    ptmp.r = pixel_r_val / 4;
    ptmp.g = pixel_g_val / 4;
    ptmp.b = pixel_b_val / 4;
    return ptmp;
}

void STFractWorker::compute_stats(const dvec4 &pos, int iter, fate_t fate, int x, int y)
{
    const calc_options &options = m_context->get_options();
    m_stats.s[ITERATIONS] += iter;
    ++m_stats.s[PIXELS];
    ++m_stats.s[PIXELS_CALCULATED];
    if (fate & FATE_INSIDE)
    {
        ++m_stats.s[PIXELS_INSIDE];
        if (iter < options.maxiter - 1)
        {
            ++m_stats.s[PIXELS_PERIODIC];
        }
    }
    else
    {
        ++m_stats.s[PIXELS_OUTSIDE];
    }
    if (options.auto_deepen && m_stats.s[PIXELS] % AUTO_DEEPEN_FREQUENCY == 0)
    {
        compute_auto_deepen_stats(pos, iter, x, y);
    }
    if (options.periodicity && options.auto_tolerance &&
        m_stats.s[PIXELS] % AUTO_TOLERANCE_FREQUENCY == 0)
    {
        compute_auto_tolerance_stats(pos, iter, x, y);
    }
}

void STFractWorker::compute_auto_tolerance_stats(const dvec4 &pos, int iter, int x, int y)
{
    const calc_options &options = m_context->get_options();
    // convention: numIters is set to -1 when fate == FATE_INSIDE
    if (iter == -1)
    {
        // currently inside
        // Possibly we incorrectly classified this as inside due to
        // loose period tolerance. Try with a tighter bound and see if it helps
        rgba_t temp_pixel;
        float temp_index;
        fate_t temp_fate;
        int temp_iter;
        /* try again with 10x tighter tolerance */
        m_pf.calc(
            pos.n,
            options.maxiter,
            0,
            options.period_tolerance / 10.0,
            options.warp_param,
            x, y, -1,
            &temp_pixel, &temp_iter, &temp_index, &temp_fate);

        if (temp_iter != -1)
        {
            // current tolerance is too loose, we would get 1 more
            // pixel correct if we tightened it
            ++m_stats.s[BETTER_TOLERANCE_PIXELS];
        }
    }
    else
    {
        // currently outside
        // Possibly we're trying too hard, and we'd still get this right with a
        // looser period tolerance. Try it and see
        rgba_t temp_pixel;
        float temp_index;
        fate_t temp_fate;
        int temp_iter;
        /* try again with 10x looser tolerance */
        m_pf.calc(
            pos.n,
            options.maxiter,
            0,
            options.period_tolerance * 10.0,
            options.warp_param,
            x, y, -1,
            &temp_pixel, &temp_iter, &temp_index, &temp_fate);

        if (temp_iter == -1)
        {
            // if we loosened, we'd get this pixel wrong
            ++m_stats.s[WORSE_TOLERANCE_PIXELS];
        }
    }
}

void STFractWorker::compute_auto_deepen_stats(const dvec4 &pos, int iter, int x, int y)
{
    const calc_options &options = m_context->get_options();
    if (iter > options.maxiter / 2)
    {
        /* we would have got this wrong if we used
	    * half as many iterations */
        ++m_stats.s[WORSE_DEPTH_PIXELS];
    }
    else if (iter == -1)
    {
        rgba_t temp_pixel;
        float temp_index;
        fate_t temp_fate;
        int temp_iter;
        /* didn't bail out, try again with 2x as many iterations */
        m_pf.calc(
            pos.n,
            options.maxiter * 2,
            periodGuess(),
            options.period_tolerance,
            options.warp_param,
            x, y, -1,
            &temp_pixel, &temp_iter, &temp_index, &temp_fate);

        if (temp_iter != -1)
        {
            /* we would have got this right if we used twice as many iterations */
            ++m_stats.s[BETTER_DEPTH_PIXELS];
        }
    }
}

void STFractWorker::pixel(int x, int y, int w, int h)
{
    const calc_options &options = m_context->get_options();
    const fract_geometry &geometry = m_context->get_geometry();
    rgba_t pixel;
    float index {0};
    fate_t fate = m_im->getFate(x, y, 0);
    if (fate == FATE_UNKNOWN)
    {
        int iter = 0;
        switch (options.render_type) {
        case RENDER_TWO_D:
        {
            // calculate coords of this point
            const dvec4 pos =  geometry.vec_for_point_2d(x, y); //m_ff->topleft + x * m_ff->deltax + y * m_ff->deltay;
            const int min_period_iters = periodGuess();
            m_pf.calc(
                pos.n,
                options.maxiter,
                min_period_iters,
                options.period_tolerance,
                options.warp_param,
                x, y, 0,
                &pixel, &iter, &index, &fate);
            compute_stats(pos, iter, fate, x, y);
#ifdef DEBUG_PIXEL
            const int color_iters = (fate & FATE_INSIDE) ? -1 : iter;
            m_site->pixel_changed(
                pos.n, options.maxiter, min_period_iters,
                x, y, 0,
                index, fate, color_iters,
                pixel.r, pixel.g, pixel.b, pixel.a);
#endif
        }
        break;
        case RENDER_LANDSCAPE:
            assert(0 && "not supported");
            break;
        case RENDER_THREE_D:
        {
            const dvec4 look = geometry.vec_for_point_3d(x, y);
            dvec4 root;
            bool found = find_root(geometry.eye_point, look, root);
            if (found)
            {
                // intersected
                iter = -1;
                pixel.r = pixel.g = pixel.b = 0;
                fate = 1;
                index = 0.0;
            }
            else
            {
                // did not intersect
                iter = 1;
                pixel.r = pixel.g = pixel.b = 0xff;
                fate = 0;
                index = 1.0;
            }
        }
        break;
        }
        periodSet(iter);
        if (m_context->get_debug_flags() & DEBUG_DRAWING_STATS)
        {
            printf("pixel %d %d %d %d\n", x, y, fate, iter);
        }
        assert(fate != FATE_UNKNOWN);
        m_im->setIter(x, y, iter);
        m_im->setFate(x, y, 0, fate);
        m_im->setIndex(x, y, 0, index);
        rectangle(pixel, x, y, w, h);
    }
    else
    {
        pixel = m_pf.recolor(m_im->getIndex(x, y, 0), fate, m_im->get(x, y));
        rectangle(pixel, x, y, w, h);
    }
}

void STFractWorker::box_row(int w, int y, int rsize)
{
    // we increment by rsize-1 because we want to reuse the vertical bars
    // between the boxes - each box overlaps by 1 pixel
    auto x = 0;
    for (; x < w - rsize; x += rsize - 1)
    {
        box(x, y, rsize);
    }
    // extra pixels at end of lines: already calculated by qbox_row
}

void STFractWorker::qbox_row(int w, int y, int rsize, int drawsize)
{
    auto x = 0;
    // main large blocks
    for (; x < w - rsize; x += rsize - 1)
    {
        pixel(x, y, drawsize, drawsize);
    }
    // extra pixels at end of lines
    for (auto y2 = y; y2 < y + rsize; ++y2)
    {
        row(x, y2, w - x);
    }
}

void STFractWorker::pixel_aa(int x, int y)
{
    const int iter = m_im->getIter(x, y);
    // if aa type is fast, short-circuit some points
    if (m_context->get_options().eaa == AA_FAST &&
        x > 0 && x < m_im->Xres() - 1 && y > 0 && y < m_im->Yres() - 1)
    {
        // check to see if this point is surrounded by others of the same colour
        // if so, don't bother recalculating
        const int pcol = Pixel2INT(x, y);
        const bool bFlat =
            isTheSame(iter, pcol, x, y - 1) &&
            isTheSame(iter, pcol, x - 1, y) &&
            isTheSame(iter, pcol, x + 1, y) &&
            isTheSame(iter, pcol, x, y + 1);
        if (bFlat)
        {
            if (m_context->get_debug_flags() & DEBUG_DRAWING_STATS)
            {
                printf("noaa %d %d\n", x, y);
            }
            m_im->fill_subpixels(x, y);
            return;
        }
    }
    const rgba_t pixel = antialias(x, y);
    rectangle(pixel, x, y, 1, 1);
}

#ifdef EXPERIMENTAL_OPTIMIZATIONS
bool STFractWorker::isNearlyFlat(int x, int y, int rsize)
{
    rgba_t colors[2];
    const fate_t fate = m_im->getFate(x, y, 0);
    const int MAXERROR = 3;
    const int right_x = x + rsize - 1;
    const int bottom_y = y + rsize - 1;
    // can we predict the top edge close enough?
    colors[0] = m_im->get(x, y);
    colors[1] = m_im->get(right_x, y);
    for (auto x2 = x + 1; x2 < right_x; ++x2)
    {
        if (m_im->getFate(x2, y, 0) != fate)
            return false;
        const rgba_t predicted = predict_color(colors, (x2 - x) / static_cast<double>(rsize));
        const int diff = diff_colors(predicted, m_im->get(x2, y));
        if (diff > MAXERROR)
        {
            return false;
        }
    }
    // how about the bottom edge?
    colors[0] = m_im->get(x, bottom_y);
    colors[1] = m_im->get(right_x, bottom_y);
    for (auto x2 = x + 1; x2 < right_x; ++x2)
    {
        if (m_im->getFate(x2, bottom_y, 0) != fate)
            return false;
        const rgba_t predicted = predict_color(colors, (x2 - x) / static_cast<double>(rsize));
        const int diff = diff_colors(predicted, m_im->get(x2, bottom_y));
        if (diff > MAXERROR)
        {
            return false;
        }
    }
    // how about the left side?
    colors[0] = m_im->get(x, y);
    colors[1] = m_im->get(x, bottom_y);
    for (auto y2 = y + 1; y2 < bottom_y; ++y2)
    {
        if (m_im->getFate(x, y2, 0) != fate)
            return false;
        const rgba_t predicted = predict_color(colors, (y2 - y) / static_cast<double>(rsize));
        const int diff = diff_colors(predicted, m_im->get(x, y2));
        if (diff > MAXERROR)
        {
            return false;
        }
    }
    // and finally the right
    colors[0] = m_im->get(right_x, y);
    colors[1] = m_im->get(right_x, bottom_y);
    for (auto y2 = y + 1; y2 < bottom_y; ++y2)
    {
        if (m_im->getFate(right_x, y2, 0) != fate)
            return false;
        const rgba_t predicted = predict_color(colors, (y2 - y) / static_cast<double>(rsize));
        const int diff = diff_colors(predicted, m_im->get(right_x, y2));
        if (diff > MAXERROR)
        {
            return false;
        }
    }
    return true;
}

// linearly interpolate over a rectangle
void STFractWorker::interpolate_rectangle(int x, int y, int rsize)
{
    for (auto y2 = y; y2 < y + rsize - 1; ++y2)
    {
        interpolate_row(x, y2, rsize);
    }
}

void STFractWorker::interpolate_row(int x, int y, int rsize)
{
    const fate_t fate = m_im->getFate(x, y, 0);
    rgba_t colors[2];
    const int right_x = x + rsize - 1;
    colors[0] = m_im->get(x, y);
    colors[1] = m_im->get(right_x, y);
    int iters[2];
    iters[0] = m_im->getIter(x, y);
    iters[1] = m_im->getIter(right_x, y);
    int indexes[2];
    indexes[0] = m_im->getIndex(x, y, 0);
    indexes[1] = m_im->getIndex(right_x, y, 0);
    for (auto x2 = x; x2 < right_x; ++x2)
    {
        const double factor = (x2 - x) / static_cast<double>(rsize);
        const rgba_t predicted_color = predict_color(colors, factor);
        int predicted_iter = predict_iter(iters, factor);
        float predicted_index = predict_index(indexes, factor);
        //check_guess(x2,y,predicted_color,fate,predicted_iter,predicted_index);
        m_im->put(x2, y, predicted_color);
        m_im->setIter(x2, y, predicted_iter);
        m_im->setFate(x2, y, 0, fate);
        m_im->setIndex(x2, y, 0, predicted_index);
        ++m_stats.s[PIXELS];
        ++m_stats.s[PIXELS_SKIPPED];
    }
}

// linearly interpolate between colors to guess correct color
rgba_t STFractWorker::predict_color(rgba_t colors[2], double factor)
{
    rgba_t result;
    result.r = static_cast<int>(colors[0].r * (1.0 - factor) + colors[1].r * factor);
    result.g = static_cast<int>(colors[0].g * (1.0 - factor) + colors[1].g * factor);
    result.b = static_cast<int>(colors[0].b * (1.0 - factor) + colors[1].b * factor);
    result.a = static_cast<int>(colors[0].a * (1.0 - factor) + colors[1].a * factor);
    return result;
}

int STFractWorker::predict_iter(int iters[2], double factor)
{
    return static_cast<int>(iters[0] * (1.0 - factor) + iters[1] * factor);
}

float STFractWorker::predict_index(int indexes[2], double factor)
{
    return indexes[0] * (1.0 - factor) + indexes[1] * factor;
}

// sum squared differences between components of 2 colors
int STFractWorker::diff_colors(rgba_t a, rgba_t b)
{
    const int dr = a.r - b.r;
    const int dg = a.g - b.g;
    const int db = a.b - b.b;
    const int da = a.a - b.a;
    return dr * dr + dg * dg + db * db + da * da;
}

inline void STFractWorker::check_guess(int x, int y, rgba_t pixel)
{
    const calc_options &options = m_context->get_options();
    const dvec4 pos = m_context->get_geometry().vec_for_point_2d(x, y);
    rgba_t tpixel;
    int titer;
    float tindex;
    fate_t tfate;
    m_pf.calc(
        pos.n,
        options.maxiter,
        periodGuess(),
        options.period_tolerance,
        options.warp_param,
        x, y, 0,
        &tpixel, &titer, &tindex, &tfate);
    if (tpixel == pixel)
    {
        ++m_stats.s[PIXELS_SKIPPED_RIGHT];
    }
    else
    {
        ++m_stats.s[PIXELS_SKIPPED_WRONG];
    }
}
#endif // #ifdef EXPERIMENTAL_OPTIMIZATIONS

void STFractWorker::box(int x, int y, int rsize)
{
    // calculate edges of box to see if they're all the same colour
    // if they are, we assume that the box is a solid colour and
    // don't calculate the interior points
    bool bFlat = true;
    const int iter = m_im->getIter(x, y);
    const int pcol = Pixel2INT(x, y);
    // calculate top and bottom of box & check for flatness
    const auto bottom_y = y + rsize - 1;
    const auto right_x = x + rsize - 1;
    for (int x2 = x; x2 <= right_x; ++x2)
    {
        pixel(x2, y, 1, 1);
        bFlat = bFlat && isTheSame(iter, pcol, x2, y);
        pixel(x2, bottom_y, 1, 1);
        bFlat = bFlat && isTheSame(iter, pcol, x2, bottom_y);
    }
    // calc left and right of box & check for flatness
    for (int y2 = y; y2 <= bottom_y; ++y2)
    {
        pixel(x, y2, 1, 1);
        bFlat = bFlat && isTheSame(iter, pcol, x, y2);
        pixel(right_x, y2, 1, 1);
        bFlat = bFlat && isTheSame(iter, pcol, right_x, y2);
    }
    if (bFlat)
    {
        // just draw a solid rectangle
        const rgba_t pixel = m_im->get(x, y);
        const fate_t fate = m_im->getFate(x, y, 0);
        const float index = m_im->getIndex(x, y, 0);
        rectangle_with_iter(pixel, fate, iter, index, x + 1, y + 1, rsize - 2, rsize - 2);
    }
    else
    {
#ifdef EXPERIMENTAL_OPTIMIZATIONS
        if (isNearlyFlat(x, y, rsize))
        {
            interpolate_rectangle(x, y, rsize);
            return;
        }
#endif
        if (rsize > 4)
        {
            // divide into 4 sub-boxes and check those for flatness
            const int half_size = rsize / 2;
            box(x, y, half_size);
            box(x + half_size, y, half_size);
            box(x, y + half_size, half_size);
            box(x + half_size, y + half_size, half_size);
        }
        else
        {
            // we do need to calculate the interior
            // points individually
            for (auto y2 = y + 1; y2 < bottom_y; ++y2)
            {
                row(x + 1, y2, rsize - 2);
            }
        }
    }
}

inline void STFractWorker::rectangle(rgba_t pixel, int x, int y, int w, int h)
{
    for (auto i = y; i < y + h; ++i)
    {
        for (auto j = x; j < x + w; ++j)
        {
            m_im->put(j, i, pixel);
        }
    }
}

inline void STFractWorker::rectangle_with_iter(
    rgba_t pixel, fate_t fate, int iter, float index,
    int x, int y, int w, int h)
{
    for (auto i = y; i < y + h; ++i)
    {
        for (auto j = x; j < x + w; ++j)
        {
            if (m_context->get_debug_flags() & DEBUG_DRAWING_STATS)
            {
                printf("guess %d %d %d %d\n", j, i, fate, iter);
            }
            //check_guess(j,i,pixel,fate,iter,index);
            m_im->put(j, i, pixel);
            m_im->setIter(j, i, iter);
            m_im->setFate(j, i, 0, fate);
            m_im->setIndex(j, i, 0, index);
            ++m_stats.s[PIXELS];
            ++m_stats.s[PIXELS_SKIPPED];
        }
    }
}

// @TODO: this is used for RENDER_THREE_D mode and seems to be unfinished or at least worth to review
bool STFractWorker::find_root(const dvec4 &eye, const dvec4 &look, dvec4 &root)
{
    const calc_options &options = m_context->get_options();
    d dist = 0.0;
    rgba_t pixel;
    float index;
    fate_t fate = FATE_UNKNOWN;
    int iter;
    const int x = -1;
    const int y = -1;
    int steps = 0;
    d lastdist = dist;
    dvec4 pos;
    while (true)
    {
        if (dist > 1.0e3) // FIXME
        {
            // couldn't find anything
#ifdef DEBUG_ROOTS
            printf("not found after %d\n", steps);
#endif
            return false;
        }
        pos = eye + dist * look;
        m_pf.calc(
            pos.n,
            options.maxiter,
            periodGuess(),
            options.period_tolerance,
            options.warp_param,
            x, y, 0,
            &pixel, &iter, &index, &fate);
        ++steps;
        if (fate != 0) // FIXME
        {
            // inside
#ifdef DEBUG_ROOTS
            printf("bracketed after %d\n", steps);
#endif
            break;
        }
        lastdist = dist;
        dist += 0.1;
    }
    // the root must be between lastdist and dist
    // bisect a few times to polish the root
    while (fabs(lastdist - dist) > 1.0E-10) // FIXME
    {
        d mid = (lastdist + dist) / 2.0;
        pos = eye + mid * look;
        m_pf.calc(pos.n,
            options.maxiter,
            periodGuess(),
            options.period_tolerance,
            options.warp_param,
            x, y, 0,
            &pixel, &iter, &index, &fate);
        if (fate != 0) // FIXME
        {
            //inside, root must be further out
            dist = mid;
        }
        else
        {
            //outside, root must be further in
            lastdist = mid;
        }
        ++steps;
    }
#ifdef DEBUG_ROOTS
    printf("polished after %d\n", steps);
#endif
    root = pos;
    return true;
}
