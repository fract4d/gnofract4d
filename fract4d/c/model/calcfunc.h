#ifndef __CALCFUNC_H_INCLUDED__
#define __CALCFUNC_H_INCLUDED__

#include "model/enums.h"

typedef struct s_pf_data pf_obj;
typedef double d;
class ColorMap;
class IImage;
class IFractalSite;


#ifdef __cplusplus
extern "C"
{
#endif

    void calc(
        d *params,
        int eaa,
        int maxiter,
        int nThreads_,
        pf_obj *pfo,
        ColorMap *cmap,
        bool auto_deepen,
        bool auto_tolerance,
        double tolerance,
        bool yflip,
        bool periodicity,
        bool dirty,
        int debug_flags,
        render_type_t render_type,
        int warp_param,
        IImage *im,
        IFractalSite *site);

#ifdef __cplusplus
}
#endif

#endif