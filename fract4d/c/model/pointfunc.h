#ifndef __POINTFUNC_H_INCLUDED__
#define __POINTFUNC_H_INCLUDED__

#include "pf.h"
#include "model/color.h"
#include "model/colormap.h"

/* interface for function object which computes and/or colors a single point */
class pointFunc
{
    pf_obj *m_pfo;
    ColorMap *m_cmap;
public:
    pointFunc(
        pf_obj *pfo,
        ColorMap *cmap) : m_pfo(pfo), m_cmap(cmap) {}

    void calc(
        // in params
        const double *params, int nIters,
        // periodicity
        int min_period_iters, double period_tolerance,
        // warping
        int warp_param,
        // only used for debugging
        int x, int y, int aa,
        // out params
        rgba_t *color, int *pnIters, float *pIndex, fate_t *pFate) const;

    inline rgba_t recolor(double dist, fate_t fate, rgba_t current) const
    {
        int solid = 0;
        int inside = 0;
        if (fate & FATE_DIRECT)
        {
            return current;
        }
        if (fate & FATE_SOLID)
        {
            solid = 1;
        }
        if (fate & FATE_INSIDE)
        {
            inside = 1;
        }
        return m_cmap->lookup_with_transfer(dist, solid, inside);
    }
};

#endif
