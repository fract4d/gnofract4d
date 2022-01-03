#include <cstdio>
#include <cstdlib>
#include <utility>
#include <map>
#include <algorithm>

#include "model/worker.h"

#include "model/colormap.h"
#include "model/image.h"
#include "model/site.h"
#include "model/calcoptions.h"

#include "pf.h"

void XaosFractWorker::set_context(IWorkerContext *context)
{
    m_context = context;
}

void XaosFractWorker::change_geometry(fract_geometry &&new_geometry)
{
    m_geometry_previous = m_context->get_geometry();
    m_context->set_geometry(std::forward<fract_geometry>(new_geometry));
    reuse_pixels();
}

void XaosFractWorker::reuse_pixels()
{
    const fract_geometry &geometry_current = m_context->get_geometry();
    image * actual_image = dynamic_cast<image *>(m_im);
    if (!actual_image) return;

    const auto w = m_im->Xres();
    const auto h = m_im->Yres();

    m_zooming_in = std::abs(m_geometry_previous.deltax[VX]) > std::abs(geometry_current.deltax[VX]);

    // Nearest neighbor value interpolation (reuse pixels from previous frame)
    // inspired by merge function from mergeSort as the series of values L and R are, by nature, ordered

    // | is the center of the pixel in the complex plane
    // -- is the space beteen pixel centers (delta)
    // matching numbers are reused pixels

    // zoom in
    //     1   2   3   4   5    L(i)
    // |---|---|---|---|---|---|  old frame
    //    |--|--|--|--|--|--|     new frame
    //    1     2  3  4     5   R(j)

    // zoom out
    //    1     2  3  4     5   L(i)
    //    |--|--|--|--|--|--|     old frame
    // |---|---|---|---|---|---|  new frame
    //     1   2   3   4   5    R(j)

    // columns: VY values keeps the same value within the same row
    std::map<int, int> reusable_columns;
    std::map<int, double> reusale_column_values;
    {
        const auto delta = geometry_current.deltax[VX];
        int i = 0, j = 0;
        while (i < w && j < w)
        {
            double L = m_geometry_previous.vec_for_point_2d(i, 0)[VX];
            double R = geometry_current.vec_for_point_2d(j, 0)[VX];
            double reused_value;
            if (actual_image->get_reused_column_value(i, &reused_value)) L = reused_value;
            const double diff = std::abs(R - L);
            if (diff <= std::abs(delta) / 2) {
                // fprintf(stderr, "column approximation old: %d, new: %d, old_value: %f, new_value: %f \n", i, j, L, R);
                reusable_columns[j] = i;
                reusale_column_values[j] = L;
            }
            const auto condition = delta > 0 ? L <= R : L >= R;
            if (condition) {
                ++i;
            } else {
                ++j;
            }
        }
    }

    // columns: VX values keeps the same value within the same column
    std::map<int, int> reusable_rows;
    std::map<int, double> reusable_row_values;
    {
        const auto delta = geometry_current.deltay[VY];
        int i = 0, j = 0;
        while (i < h && j < h)
        {
            double L = m_geometry_previous.vec_for_point_2d(0, i)[VY];
            double R = geometry_current.vec_for_point_2d(0, j)[VY];
            double reused_value;
            if (actual_image->get_reused_row_value(i, &reused_value)) L = reused_value;
            const double diff = std::abs(R - L);
            if (diff <= std::abs(delta) / 2) {
                // fprintf(stderr, "row approximation old: %d, new: %d, old_value: %f, new_value: %f \n", i, j, L, R);
                reusable_rows[j] = i;
                reusable_row_values[j] = L;
            }
            const auto condition = delta > 0 ? L <= R : L >= R;
            if (condition) {
                ++i;
            } else {
                ++j;
            }
        }
    }

    // update the image reused column and row values for subsequent frames
    actual_image->set_reused_columns(reusale_column_values);
    actual_image->set_reused_rows(reusable_row_values);

    // print some statistics about reusage
    // const double pixels_reused = reusable_columns.size() * reusable_rows.size();
    // fprintf(stderr, "total pixels: %d, pixels reused: %f, reusage ratio: %f \n", w*h, pixels_reused, (pixels_reused / (w*h*1.0f)) * 100.0f);

    // copy reused pixels and metadata to a temp image "clone" (not actually a clone but a new one with same dimensions)
    // NOTE: have in mind this process would actually do a image clean (buffer, fates, indexes, iters), and this is needed for the next frame to be calculated
    image im {*actual_image};
    auto rc_iterator = reusable_columns.begin();
    while(rc_iterator != reusable_columns.end())
    {
        const auto x = rc_iterator->first;
        const auto x1 = rc_iterator->second;
        auto rr_iterator = reusable_rows.begin();
        while(rr_iterator != reusable_rows.end())
        {
            const auto y = rr_iterator->first;
            const auto y1 = rr_iterator->second;
            im.put(x, y, actual_image->get(x1, y1));
            im.setIter(x, y, actual_image->getIter(x1, y1));
            im.setFate(x, y, 0, actual_image->getFate(x1, y1, 0));
            im.setIndex(x, y, 0, actual_image->getIndex(x1, y1, 0));
            ++m_stats.s[PIXELS_SKIPPED];
            rr_iterator++;
        }
        rc_iterator++;
    }
    actual_image->swap_buffers(im);
}

void XaosFractWorker::work()
{
    for (;;)
    {
        std::function<void()> job;
        {
            std::unique_lock<std::mutex> lock(m_queue_mutex);
            m_condition.wait(lock, [this]{return !m_jobs.empty() || m_terminate_pool;});
            if (m_terminate_pool && m_jobs.empty()) return;
            // when doing spiral iteration, inner boxes are in the front of the list
            // when zooming in, inner boxes have more priority
            if (m_zooming_in)
            {
                job = m_jobs.front();
                m_jobs.pop_front();
            }
            else
            {
                job = m_jobs.back();
                m_jobs.pop_back();
            }
        }
        job();
    }
}

void XaosFractWorker::add_job(std::function<void()> &&job)
{
    {
        const std::unique_lock<std::mutex> lock(m_queue_mutex);
        m_jobs.push_back(std::forward<std::function<void()>>(job));
    }
    m_condition.notify_one();
}

void XaosFractWorker::flush()
{
    {
        const std::unique_lock<std::mutex> lock(m_queue_mutex);
        if (m_terminate_pool) return;
        m_terminate_pool = true;
        m_condition.notify_all();
    }
    for (auto &t: m_pool)
    {
        if (t.joinable()) t.join();
    }
    m_pool.clear();
}

void XaosFractWorker::row(int x, int y, int n)
{
    add_job(std::bind(&XaosFractWorker::row_internal, this, x, y, n));
}

void XaosFractWorker::row_internal(int x, int y, int n)
{
    for (auto i = 0; i < n; ++i)
    {
        pixel(x + i, y, 1, 1);
    }
}

void XaosFractWorker::box_row(int w, int y, int rsize)
{
    auto x = 0;
    // row boxes
    for (; x < w - rsize; x += rsize - 1)
    {
        // box(x, y, rsize);
        add_job(std::bind(&XaosFractWorker::box, this, x, y, rsize));
    }

    add_job(std::bind([this, x](int w, int y, int rsize){
        // extra pixels at the row
        for (auto y2 = y; y2 < y + rsize; ++y2)
        {
            row_internal(x, y2, w - x);
        }
    }, w, y, rsize));
}


void XaosFractWorker::box_spiral(int rsize)
{
    const int X = m_im->Xres();
    const int Y = m_im->Yres();
    // algorithm is coordinate center based, so we need the offset to refer to the actual pixels (where top-left is (0,0))
    const int x_offset = (X - 1) / 2;
    const int y_offset = (Y - 1) / 2;
    int x, y, dx, dy;
    x = y = dx = 0;
    dy = -rsize;
    // the actual image rectangle is contained in a square of max size. We add the rsize to include partial boxes at the edges
    int t = (std::max(X, Y) + rsize) / rsize;
    // number of boxes/iterations for a grid containing the actual image
    int maxI = t*t;
    for(int i = 0; i < maxI; i++)
    {
        add_job(std::bind(&XaosFractWorker::virtual_box, this, x + x_offset, y + y_offset, rsize, X, Y));
        // points where we should change direction
        if( (x == y) || ((x < 0) && (x == -y)) || ((x > 0) && (x == rsize-y)))
        {
            t = dx;
            dx = -dy;
            dy = t;
        }
        x += dx;
        y += dy;
    }
}

void XaosFractWorker::virtual_box(int x, int y, int rsize, int w, int h)
{
    bool quick_mode {false};
    if (hurry_up)
    {
        double pixel_ratio = static_cast<double>(m_stats.s[PIXELS_CALCULATED] + m_stats.s[PIXELS_SKIPPED]) / (w*h);
        quick_mode = pixel_ratio >= 0.7;
    }
    // check if box is contained inside image
    if (0 <= x && x + rsize <= w && 0 <= y && y + rsize <= h)
    {
        if (quick_mode)
        {
            approximate_box(x, y, rsize, w, h);
        }
        else
        {
            box(x, y, rsize);
        }
        return;
    }
    // if not inside just calculate the pixels inside the image
    auto x1 = x < 0 ? 0 : x;
    const auto x2 = std::min(x + rsize, w);
    const auto y2 = std::min(y + rsize, h);
    for (; x1 < x2; x1++)
    {
        auto y1 = y < 0 ? 0 : y;
        for (; y1 < y2; y1++)
        {
            pixel(x1, y1, 1, 1);
        }
    }
}

void XaosFractWorker::approximate_box(int x, int y, int rsize, int w, int h)
{
    // edges are shared between adjacent boxes
    const auto bottom_y = std::min(y + rsize, h - 1);
    const auto right_x = std::min(x + rsize, w - 1);

    // calculate top and bottom edges of the box
    for (int x2 = x; x2 <= right_x; ++x2)
    {
        pixel(x2, y, 1, 1);
        pixel(x2, bottom_y, 1, 1);
    }
    // calc left and right edges of the box
    for (int y2 = y; y2 <= bottom_y; ++y2)
    {
        pixel(x, y2, 1, 1);
        pixel(right_x, y2, 1, 1);
    }

    // bilinear interpolation
    // interpolate pixel colors between 2 calculated pixels
    // @TODO: avoid using a fixed max distance between 2 calculated pixels to interpolate the one's in the middle
    // phase 1: rows
    const auto interpolate_horizontal = [this](int x, int y, rgba_t *color, int left, int right)
    {
        const double factor = (x - left) / static_cast<double>(right - left);
        rgba_t result = color[0] * (1-factor) + color[1] * factor;
        m_im->put(x, y, result);
    };
    for (auto j = y; j <= bottom_y; j++)
    {
        int bookmark = x;
        rgba_t color[2];
        color[0] = m_im->get(x, j);
        for (auto i = x + 1; i <= right_x; i++)
        {
            if (i - bookmark > 4) pixel(i, j, 1, 1);
            if (m_im->getFate(i, j, 0) == FATE_UNKNOWN) continue;
            color[1] = m_im->get(i, j);
            for (auto k = bookmark + 1; k < i; k++) interpolate_horizontal(k, j, color, bookmark, i);
            color[0] = color[1];
            bookmark = i;
        }
    }
    // phase 1: columns
    // give each phase row/column a 50% weight
    const auto interpolate_vertical = [this](int x, int y, rgba_t *color, int top, int bottom)
    {
        const double factor = (y - top) / static_cast<double>(bottom - top);
        rgba_t result = (color[0] * (1-factor) + color[1] * factor) * 0.5 + m_im->get(x, y) * 0.5;
        m_im->put(x, y, result);
    };
    for (auto i = x; i <= right_x; i++)
    {
        int bookmark = y;
        rgba_t color[2];
        color[0] = m_im->get(i, y);
        for (auto j = y + 1; j <= bottom_y; j++)
        {
            if (j - bookmark > 4) pixel(i, j, 1, 1);
            if (m_im->getFate(i, j, 0) == FATE_UNKNOWN) continue;
            color[1] = m_im->get(i, j);
            for (auto k = bookmark + 1; k < j; k++) interpolate_vertical(i, k, color, bookmark, j);
            color[0] = color[1];
            bookmark = j;
        }
    }

}

void XaosFractWorker::box(int x, int y, int rsize)
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
        return;
    }
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
        // we do need to calculate the interior points individually
        for (auto y2 = y + 1; y2 < bottom_y; ++y2)
        {
            row_internal(x + 1, y2, rsize - 2);
        }
    }
}

inline int XaosFractWorker::Pixel2INT(int x, int y)
{
    return static_cast<int>(m_im->get(x, y));
}

inline bool XaosFractWorker::isTheSame(int targetIter, int targetCol, int x, int y)
{
    // does this point have the target # of iterations and same colour?
    if ((m_im->getIter(x, y) == targetIter) && (Pixel2INT(x, y) == targetCol)) {
        return true;
    }
    return false;
}

inline void XaosFractWorker::rectangle_with_iter(
    rgba_t pixel, fate_t fate, int iter, float index,
    int x, int y, int w, int h)
{
    for (auto i = y; i < y + h; ++i)
    {
        for (auto j = x; j < x + w; ++j)
        {
            m_im->put(j, i, pixel);
            m_im->setIter(j, i, iter);
            m_im->setFate(j, i, 0, fate);
            m_im->setIndex(j, i, 0, index);
        }
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
        const dvec4 pos = geometry.vec_for_point_2d(x, y); // m_ff->topleft + x * m_ff->deltax + y * m_ff->deltay;
        const int min_period_iters = periodGuess();
        m_pf.calc(
            pos.n,
            options.maxiter,
            min_period_iters,
            options.period_tolerance,
            options.warp_param,
            x, y, 0,
            &pixel, &iter, &index, &fate);
        ++m_stats.s[PIXELS_CALCULATED];
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