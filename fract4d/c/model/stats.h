
#ifndef __STATS_H_INCLUDED__
#define __STATS_H_INCLUDED__

#include <string.h>

#include "model/enums.h"

typedef struct s_pixel_stat pixel_stat_t;

struct s_pixel_stat
{
    unsigned long s[NUM_STATS];
    s_pixel_stat();
    void reset();
    void add(const pixel_stat_t &other);
    double worse_depth_ratio() const;
    double better_depth_ratio() const;
    double worse_tolerance_ratio() const;
    double better_tolerance_ratio() const;
};

#endif