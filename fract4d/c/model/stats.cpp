#include <cstring>

#include "stats.h"

s_pixel_stat::s_pixel_stat()
{
    reset();
}

void s_pixel_stat::reset()
{
    std::memset(&s, 0, sizeof(s));
}

void s_pixel_stat::add(const pixel_stat_t &other)
{
    for (auto i = 0; i < NUM_STATS; ++i)
    {
        s[i] += other.s[i];
    }
}

double s_pixel_stat::worse_depth_ratio() const
{
    return static_cast<double>(s[WORSE_DEPTH_PIXELS]) / s[PIXELS];
}

double s_pixel_stat::better_depth_ratio() const
{
    return static_cast<double>(s[BETTER_DEPTH_PIXELS]) / s[PIXELS];
}

double s_pixel_stat::worse_tolerance_ratio() const
{
    return static_cast<double>(s[WORSE_TOLERANCE_PIXELS]) / s[PIXELS];
}

double s_pixel_stat::better_tolerance_ratio() const
{
    return static_cast<double>(s[BETTER_TOLERANCE_PIXELS]) / s[PIXELS];
}
