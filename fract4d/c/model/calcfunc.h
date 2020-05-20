#ifndef __CALCFUNC_H_INCLUDED__
#define __CALCFUNC_H_INCLUDED__

#include "model/calcoptions.h"

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
        calc_options,
        d *params,
        pf_obj *,
        ColorMap *,
        IFractalSite *,
        IImage *,
        int debug_flags
    );

#ifdef __cplusplus
}
#endif

#endif