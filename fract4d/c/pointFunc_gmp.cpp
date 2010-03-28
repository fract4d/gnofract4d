#ifdef HAVE_CONFIG_H
#  include <config.h>
#endif


#include "pf.h"
#include "cmap.h"
#include "pointFunc_public.h"
#include "fract_public.h"

#include <unistd.h>
#include <dlfcn.h>
#include <stdio.h>

/* only here so it's visible to debugger */
typedef struct {
    pf_obj parent;
    struct s_param p[PF_MAXPARAMS];
    double period_tolerance;
} pf_real;

class pf_wrapper : public pointFunc
{
private:
    pf_obj *m_pfo;
    ColorMap *m_cmap;
    IFractalSite *m_site;
public:
    pf_wrapper(
	pf_obj *pfo,
	ColorMap *cmap,
	IFractalSite *site
	) : 
	m_pfo(pfo), m_cmap(cmap), m_site(site)
	{

	}
    virtual ~pf_wrapper()
	{
	    /* we don't own the member pointers, so we don't delete them */
	}
    virtual void calc(
        // in params
        const double *params, int nIters, bool checkPeriod, int warp_param,
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

	    if (checkPeriod)
	    {
		m_pfo->vtbl->calc_period(
		    m_pfo, params, nIters, warp_param,
		    x, y, aa,
		    pnIters, &fate, &dist, &solid,
		    &fUseColors, &colors[0]);
	    }
	    else
	    {
		m_pfo->vtbl->calc(
		    m_pfo, params, nIters, warp_param,
		    x, y, aa,
		    pnIters, &fate, &dist, &solid,
		    &fUseColors, &colors[0]);
	    }

	    if(fate & FATE_INSIDE)
	    {
		*pnIters = -1;
		inside = 1;
	    }

	    if(fUseColors)
	    {
		*color = m_cmap->lookup_with_dca(solid, inside, colors);
		fate |= FATE_DIRECT;
	    }
	    else
	    {
		*color = m_cmap->lookup_with_transfer(dist,solid, inside);
	    }

	    if (solid)
	    {
		fate |= FATE_SOLID;
	    }

	    *pFate = (fate_t) fate;
	    *pIndex = (float) dist;

	    m_site->pixel_changed(
		params,nIters, checkPeriod,
		x,y,aa,
		dist,fate,*pnIters,
		color->r, color->g, color->b, color->a);
	}
    inline rgba_t recolor(double dist, fate_t fate, rgba_t current) const
	{	    
	    int solid = 0;
	    int inside = 0;
	    if(fate & FATE_DIRECT)
	    {
		return current;
	    }
	    if(fate & FATE_SOLID)
	    {
		solid = 1;
	    }
	    if(fate & FATE_INSIDE)
	    {
		inside = 1;
	    }
	    return m_cmap->lookup_with_transfer(dist,solid, inside);
	}
};


pointFunc *pointFunc::create(
    pf_obj *pfo,
    ColorMap *cmap,
    IFractalSite *site)
{
    if(NULL == pfo || NULL == cmap)
    {
	return NULL;
    }

    return new pf_wrapper(pfo,cmap,site);
}

