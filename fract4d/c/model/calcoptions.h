#ifndef __CALCOPTIONS_H_INCLUDED__
#define __CALCOPTIONS_H_INCLUDED__

#include "model/enums.h"

struct calc_options
{
    int
        eaa = AA_NONE, // antialiasing level
        maxiter =  1024, // max iterations taken per point
        nThreads = 1, // this traduces into number of threads/workers created in the threadpool
        auto_deepen = false, // dinamically adjust the maxiter value (based on statistics of the current process)
        yflip = false, // flip the image on the y axis
        periodicity = true, // enables "period checking" technique to find values which vary within an interval before reaching maxiter
        dirty = 1, // clears the image fate and iters buffers
        auto_tolerance = false, // dinamically adjust period_tolerance value (based on statistics of the current process)
        warp_param = -1; // index of the param to be warped
    double period_tolerance = 1.0E-9; // value used by the preiod checking technique
    render_type_t render_type = RENDER_TWO_D; // redenring mode, 2d as default (3d is also supported but experimental)
};

#endif