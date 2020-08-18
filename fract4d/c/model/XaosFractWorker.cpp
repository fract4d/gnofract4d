#include <cstdio>
#include <cstdlib>
#include <utility>
#include <map>

#include "model/worker.h"

#include "model/colormap.h"
#include "model/image.h"
#include "model/site.h"
#include "model/calcoptions.h"

#include "pf.h"

void XaosFractWorker::set_context(IWorkerContext *context)
{
    m_context = context;
    const fract_geometry &geometry_current = m_context->get_geometry();
    // this happens when the previous geometry doesn't exist (1st image spawm)
    if (m_geometry_previous.deltax[VX] == 0 || m_geometry_previous.deltay[VY] == 0) {
        m_im->clear();
        return;
    }

    // check whether we are zooming in our out by comparing the deltas (distance between pixels)
    bool is_zoom_in{std::abs(m_geometry_previous.deltax[VX]) >= std::abs(geometry_current.deltax[VX])};

    // collect the context data for calculations
    const auto w = m_im->Xres();
    const auto h = m_im->Yres();

    double x_offset, y_offset;
    if (is_zoom_in) {
        x_offset = m_geometry_previous.topleft[VX] - geometry_current.topleft[VX];
        y_offset = m_geometry_previous.topleft[VY] - geometry_current.topleft[VY];
    } else {
        x_offset = geometry_current.topleft[VX] - m_geometry_previous.topleft[VX];
        y_offset = geometry_current.topleft[VY] - m_geometry_previous.topleft[VY];
    }
    const double previous_delta_x = std::abs(m_geometry_previous.deltax[VX]);
    const double previous_delta_y = std::abs(m_geometry_previous.deltay[VY]);
    const double current_delta_x = std::abs(geometry_current.deltax[VX]);
    const double current_delta_y = std::abs(geometry_current.deltay[VY]);
    const int x_offset_pixels = std::floor(x_offset / std::max(previous_delta_x, current_delta_x));
    const int y_offset_pixels = std::floor(y_offset / std::max(previous_delta_y, current_delta_y));
    const int old_x_end = std::ceil((std::min(previous_delta_x, current_delta_x) * w + x_offset) / std::max(previous_delta_x, current_delta_x));
    const int old_y_end = std::ceil((std::min(previous_delta_y, current_delta_y) * h + y_offset) / std::max(previous_delta_y, current_delta_y));
    // fprintf(stderr, "x_offset_pixels: %d, y_offset_pixels: %d \n", x_offset_pixels, y_offset_pixels);
    // fprintf(stderr, "old_x_end: %d, old_y_end: %d \n", old_x_end, old_y_end);

    // Nearest neighbor value interpolation (reuse pixels from previous frame)
    // inspired by merge function from mergeSort as the series of values L and R are, by nature, ordered
    // columns: VY values keeps the same value within the same row
    std::map<int, int> reusable_columns;
    {
        int i, j, n1, n2;
        if (is_zoom_in) {
            i = std::max(x_offset_pixels, 0);
            n1 = std::min(old_x_end + 1, w);
            j = 0;
            n2 = w;
        } else {
            i = 0;
            n1 = w;
            j = std::max(x_offset_pixels, 0);
            n2 = std::min(old_x_end + 1, w);
        }
        while (i < n1 && j < n2) {
            const auto L = m_geometry_previous.vec_for_point_2d(i, 0)[VX];
            const auto R = geometry_current.vec_for_point_2d(j, 0)[VX];
            const double diff = std::abs(R - L);
            if (diff <= current_delta_x / 2) {
                // fprintf(stderr, "column approximation old: %d, new: %d, old_value: %f, new_value: %f \n", i, j, L, R);
                reusable_columns[j] = i;
            }
            if (L <= R) {
                ++i;
            } else {
                ++j;
            }
        }
    }

    // columns: VX values keeps the same value within the same column
    std::map<int, int> reusable_rows;
    {
        int i, j, n1, n2;
        if (is_zoom_in) {
            n1 = std::max(y_offset_pixels, 0);
            i = std::min(old_y_end, h - 1);
            n2 = 0;
            j = h - 1;
        } else {
            n1 = 0;
            i = h - 1;
            n2 = std::max(y_offset_pixels, 0);
            j = std::min(old_y_end, h - 1);
        }
        while (i >= n1 && j >= n2) {
            const auto L = m_geometry_previous.vec_for_point_2d(0, i)[VY];
            const auto R = geometry_current.vec_for_point_2d(0, j)[VY];
            const double diff = std::abs(R - L);
            if (diff <= std::abs(current_delta_y) / 2) {
                // fprintf(stderr, "row approximation old: %d, new: %d, old_value: %f, new_value: %f \n", i, j, L, R);
                reusable_rows[j] = i;
            }
            if (L <= R) {
                --i;
            } else {
                --j;
            }
        }
    }

    // print some statistics about reusage
    // const double pixels_reused = reusable_columns.size() * reusable_rows.size();
    // fprintf(stderr, "total pixels: %d, pixels reused: %f, reusage ratio: %f \n", w*h, pixels_reused, (pixels_reused / (w*h*1.0f)) * 100.0f);

    // copy reused pixels and metadata to a temp image "clone" (not actually a clone but a new one with same dimensions)
    if (image * actual_image = dynamic_cast<image *>(m_im)) {
        image im {*actual_image};
        for (auto y = 0; y < h; y++) {
            for (auto x = 0; x < w; x++) {
                if (reusable_columns.find(x) == reusable_columns.end() ||
                    reusable_rows.find(y) == reusable_rows.end()) continue;
                im.put(x, y, actual_image->get(reusable_columns[x], reusable_rows[y]));
                im.setIter(x, y, actual_image->getIter(reusable_columns[x], reusable_rows[y]));
                im.setFate(x, y, 0, actual_image->getFate(reusable_columns[x], reusable_rows[y], 0));
                im.setIndex(x, y, 0, actual_image->getIndex(reusable_columns[x], reusable_rows[y], 0));
            }
        }
        // swap the image buffers
        actual_image->swap_buffers(im);
        m_context->image_changed(0, 0, w, h);
    }
}

void XaosFractWorker::row(int x, int y, int n)
{
    for (auto i = 0; i < n; ++i)
    {
        pixel(x + i, y, 1, 1);
    }
}


void XaosFractWorker::pixel(int x, int y, int h, int w)
{
    const calc_options &options = m_context->get_options();
    const fract_geometry &geometry = m_context->get_geometry();
    rgba_t pixel;
    float index {0};
    fate_t fate = m_im->getFate(x, y, 0);
    if (fate == FATE_UNKNOWN)
    {
        int iter = 0;
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
        periodSet(iter);
        m_im->setIter(x, y, iter);
        m_im->setFate(x, y, 0, fate);
        m_im->setIndex(x, y, 0, index);
        rectangle(pixel, x, y, w, h);
    }
    else
    {
        // TODO: create this function in the image, so we can use a memset
        pixel = m_pf.recolor(m_im->getIndex(x, y, 0), fate, m_im->get(x, y));
        rectangle(pixel, x, y, w, h);
    }
}

inline void XaosFractWorker::rectangle(rgba_t pixel, int x, int y, int w, int h)
{
    // TODO: create this function in the image, so we can use a memset
    for (auto i = y; i < y + h; ++i)
    {
        for (auto j = x; j < x + w; ++j)
        {
            m_im->put(j, i, pixel);
        }
    }
}

// Period guessing

inline int XaosFractWorker::periodGuess()
{
    return periodGuess(m_lastPointIters);
}

inline int XaosFractWorker::periodGuess(int last)
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

inline void XaosFractWorker::periodSet(int ppos)
{
    m_lastPointIters = ppos;
}