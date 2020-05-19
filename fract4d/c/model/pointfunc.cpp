#ifdef HAVE_CONFIG_H
#include <config.h>
#endif
#include <unistd.h>
#include <dlfcn.h>
#include <cstdio>

#include "pointfunc.h"
#include "pf.h"
#include "model/colormap.h"
#include "model/color.h"


pointFunc *pointFunc::create(
    pf_obj *pfo,
    ColorMap *cmap)
{
    if (NULL == pfo || NULL == cmap)
    {
        return NULL;
    }
    return new pf_wrapper(pfo, cmap);
}

void pf_wrapper::calc(
    // in params
    const double *params, int nIters,
    // periodicity
    int min_period_iters, double period_tolerance,
    // warping
    int warp_param,
    // only used for debugging
    int x, int y, int aa,
    // out params
    rgba_t *color, int *pnIters, float *pIndex, fate_t *pFate) const
{
    double dist = 0.0;
    int fate = 0;
    int solid = 0;
    int fUseColors = 0;
    double colors[4] = {0.0};
    int inside = 0;
    m_pfo->vtbl->calc(
        m_pfo, params,
        nIters, warp_param,
        min_period_iters, period_tolerance,
        x, y, aa,
        pnIters, &fate, &dist, &solid,
        &fUseColors, &colors[0]);
    if (fate & FATE_INSIDE)
    {
        *pnIters = -1;
        inside = 1;
    }
    if (fUseColors)
    {
        *color = m_cmap->lookup_with_dca(solid, inside, colors);
        fate |= FATE_DIRECT;
    }
    else
    {
        *color = m_cmap->lookup_with_transfer(dist, solid, inside);
    }
    if (solid)
    {
        fate |= FATE_SOLID;
    }
    *pFate = (fate_t)fate;
    *pIndex = (float)dist;
}

inline rgba_t pf_wrapper::recolor(double dist, fate_t fate, rgba_t current) const
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
