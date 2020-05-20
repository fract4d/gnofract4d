#ifndef __CALCOPTIONS_H_INCLUDED__
#define __CALCOPTIONS_H_INCLUDED__

#include "model/enums.h"

struct calc_options
{
    int
        eaa = AA_NONE,
        maxiter =  1024,
        nThreads = 1,
        auto_deepen = false,
        yflip = false,
        periodicity = true,
        dirty = 1,
        auto_tolerance = false,
        asynchronous = false,
        warp_param = -1;
    double period_tolerance = 1.0E-9;
    render_type_t render_type = RENDER_TWO_D;
};

#endif