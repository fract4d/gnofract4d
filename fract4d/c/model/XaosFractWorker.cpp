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
    // this happens when the previous geometry doesn't exist (1st image spawm)
    if (m_geometry_previous.deltax[VX] == 0 || m_geometry_previous.deltay[VY] == 0) {
        m_im->clear();
        return;
    }

    const fract_geometry &geometry_current = m_context->get_geometry();
    image * actual_image = dynamic_cast<image *>(m_im);
    if (!actual_image) return; // how so?

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
            double L = m_geometry_previous.vec_for_point_2d(i, 0)[VX];
            double R = geometry_current.vec_for_point_2d(j, 0)[VX];

            double reused_value;
            if (actual_image->get_reused_column_value(i, &reused_value)) L = reused_value;

            const double diff = std::abs(R - L);
            if (diff <= std::min(previous_delta_x, current_delta_x) / 2) {
                // fprintf(stderr, "column approximation old: %d, new: %d, old_value: %f, new_value: %f \n", i, j, L, R);
                reusable_columns[j] = i;
                reusale_column_values[j] = L;
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
    std::map<int, double> reusable_row_values;
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
            double L = m_geometry_previous.vec_for_point_2d(0, i)[VY];
            double R = geometry_current.vec_for_point_2d(0, j)[VY];

            double reused_value;
            if (actual_image->get_reused_row_value(i, &reused_value)) L = reused_value;

            const double diff = std::abs(R - L);
            if (diff <= std::min(previous_delta_y, current_delta_y) / 2) {
                // fprintf(stderr, "row approximation old: %d, new: %d, old_value: %f, new_value: %f \n", i, j, L, R);
                reusable_rows[j] = i;
                reusable_row_values[j] = L;
            }
            if (L <= R) {
                --i;
            } else {
                --j;
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
            job = m_jobs.front();
            m_jobs.pop();
        }
        job();
    }
}

void XaosFractWorker::add_job(std::function<void()> &&job)
{
    {
        const std::unique_lock<std::mutex> lock(m_queue_mutex);
        m_jobs.push(job);
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

// TODO: pass a lambda as a parameter called finish_cond
void XaosFractWorker::box_spiral(int rsize)
{
    //1- spiral loop from the center/corner to calculate boxes
    // TODO:
    //2- if the process should be sttoped, pixels not calculated or reused (fate_unknown) are approximated with the closest (reused or calculated)
    //3- mark approximated pixels as reused with the value of the reused pixel so in next iteration this is considered
    // ?? approximation or interpolation ??
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
    int maxI = t*t;
    for(int i = 0; i < maxI; i++)
    {
        // if ((-(X+1)/2 < x) && (x <= X/2) && (-(Y+1)/2 < y) && (y <= Y/2))
        // {
        //     // pixel(x + x_offset, y + y_offset, 1, 1);
        // }
        add_job(std::bind(&XaosFractWorker::virtual_box, this, x + x_offset, y + y_offset, rsize, X, Y));

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
    // check if box is contained inside image
    if (0 <= x && x + rsize <= w && 0 <= y && y + rsize <= h)
    {
        box(x, y, rsize);
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
    // TODO: this unit of work would decide to call box or approximate pixels depending on an atomic property (hurry_up?)
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