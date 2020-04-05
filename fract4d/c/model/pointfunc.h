#ifndef __POINTFUNC_H_INCLUDED__
#define __POINTFUNC_H_INCLUDED__

class IFractalSite;
class ColorMap;
typedef struct s_pf_data pf_obj;
typedef unsigned char fate_t;
typedef struct s_rgba rgba_t;

/* interface for function object which computes and/or colors a single point */
class pointFunc
{
public:
    /* factory method for making new pointFuncs */
    static pointFunc *create(
        pf_obj *pfo,
        ColorMap *cmap,
        IFractalSite *site);
    virtual ~pointFunc(){}
    virtual void calc(
        // in params. params points to [x,y,cx,cy]
        const double *params, int nIters,
        // periodicity params
        int min_period_iters, double period_tolerance,
        // warping
        int warp_param,
        // only used for debugging
        int x, int y, int aa,
        // out params
        rgba_t *color, int *pnIters, float *pIndex, fate_t *pFate) const = 0;
    virtual rgba_t recolor(double dist, fate_t fate, rgba_t current) const = 0;
};

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
        IFractalSite *site) : m_pfo(pfo), m_cmap(cmap), m_site(site) {}
    /* we don't own the member pointers, so we don't delete them */
    ~pf_wrapper() {}
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
    inline rgba_t recolor(double dist, fate_t fate, rgba_t current) const;
};

#endif
