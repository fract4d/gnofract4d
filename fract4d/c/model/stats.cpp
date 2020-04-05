#include "stats.h"

s_pixel_stat::s_pixel_stat()
{
    reset();
}

void s_pixel_stat::reset()
{
    memset(&s, 0, sizeof(s));
}

void s_pixel_stat::add(const pixel_stat_t &other)
{
    for (int i = 0; i < NUM_STATS; ++i)
    {
        s[i] += other.s[i];
    }
}

double s_pixel_stat::worse_depth_ratio() const
{
    return ((double)s[WORSE_DEPTH_PIXELS]) / s[PIXELS];
}

double s_pixel_stat::better_depth_ratio() const
{
    return ((double)s[BETTER_DEPTH_PIXELS]) / s[PIXELS];
}

double s_pixel_stat::worse_tolerance_ratio() const
{
    return ((double)s[WORSE_TOLERANCE_PIXELS]) / s[PIXELS];
}

double s_pixel_stat::better_tolerance_ratio() const
{
    return ((double)s[BETTER_TOLERANCE_PIXELS]) / s[PIXELS];
}
