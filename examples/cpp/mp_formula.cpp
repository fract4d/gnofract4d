#include <cstdlib>
#include <cmath>
#include <new>

#include "pf.h"
#include "mp_double.h"

typedef struct
{
    pf_obj parent;
    struct s_param p[PF_MAXPARAMS];
} pf_real;

static void pf_get_defaults(
    struct s_pf_data *t__p_stub,
    double *pos_params,
    struct s_param *params,
    int nparams)
{
    // do nothing
}

static void pf_init(
    struct s_pf_data *p_stub,
    double *pos_params,
    struct s_param *params,
    int nparams)
{
    pf_real *pfo = (pf_real *)p_stub;
    if (nparams > PF_MAXPARAMS)
    {
        nparams = PF_MAXPARAMS;
    }
    for (int i = 0; i < nparams; ++i)
    {
        pfo->p[i] = params[i];
    }
}

static void pf_calc(
    // "object" pointer
    struct s_pf_data *t__p_stub,
    // in params
    const double *t__params, int maxiter, int t__warp_param,
    // periodicity params
    int min_period_iter, double period_tolerance,
    // only used for debugging
    int t__p_x, int t__p_y, int t__p_aa,
    // out params
    int *t__p_pnIters, int *t__p_pFate, double *t__p_pDist, int *t__p_pSolid,
    int *t__p_pDirectColorFlag, double *t__p_pColors)
{
    pf_real *t__pfo = (pf_real *)t__p_stub;

    // get the #pixel (x,y) and #zwpixel (z,w) from position params (x, y, z, w)
    MpDouble pixel_re = t__params[0];
    MpDouble pixel_im = t__params[1];
    MpDouble t__h_zwpixel_re = t__params[2];
    MpDouble t__h_zwpixel_im = t__params[3];

    // set some initial values (fate, color ...)
    MpDouble t__h_index {0.0};
    int t__h_solid = 0;
    int t__h_fate = 0;
    int t__h_inside = 0;
    MpDouble t__h_color_re {0.0};
    MpDouble t__h_color_i {0.0};
    MpDouble t__h_color_j {0.0};
    MpDouble t__h_color_k {0.0};

    // you could use direct color when using a #color variable in the function
    *t__p_pDirectColorFlag = 0;

    // warp param: still not sure how it works but the idea is to change the shape of the image somehow
    if (t__warp_param != -1)
    {
        t__pfo->p[t__warp_param].doubleval = static_cast<double>(t__h_zwpixel_re);
        t__pfo->p[t__warp_param + 1].doubleval = static_cast<double>(t__h_zwpixel_im);
        t__h_zwpixel_re = t__h_zwpixel_im = 0.0;
    }

    // formula params are stored in t__pfo->p array thanks to a previous call of pf_init
    /* variable declarations */
    int f__bailout = 0;
    void *t__a__gradient = t__pfo->p[0].gradient;
    MpDouble t__a_fbailout = t__pfo->p[1].doubleval;

    MpDouble z_re {0.0};
    MpDouble z_im {0.0};

    // those temporaries we need to keep them
    MpDouble t__f5 {0.0};
    MpDouble t__f6 {0.0};

    MpDouble t__a_cf0_offset = t__pfo->p[2].doubleval;
    MpDouble t__a_cf0_density = t__pfo->p[3].doubleval;
    MpDouble t__a_cf0bailout = t__pfo->p[4].doubleval;
    MpDouble cf0ed {0.0};

    MpDouble t__a_cf1_offset = t__pfo->p[5].doubleval;
    MpDouble t__a_cf1_density = t__pfo->p[6].doubleval;

    MpDouble old_z_re {0.0};
    MpDouble old_z_im {0.0};
    int period_iters = 0;
    int save_mask = 9;
    int save_incr = 1;
    int next_save_incr = 4;

    int t__h_numiter = 0;

t__start_finit:;
    // init: z = #zwpixel
    z_re = t__h_zwpixel_re;
    z_im = t__h_zwpixel_im;
    goto t__end_finit;
t__end_finit:;

    old_z_re = z_re;
    old_z_im = z_im;

    do
    {
    t__start_floop:;
        // loop: (z = sqr(z) + #pixel) same as (z = z*z + #pixel)
        // complex x complex -> (a+bi)⋅(c+di)=(ac−bd)+(ad+bc)i
        t__f5 = (z_re * z_re - z_im * z_im) + pixel_re;
        t__f6 = (2.00000000000000000 * z_re * z_im) + pixel_im;
        z_re = t__f5;
        z_im = t__f6;
        goto t__end_floop;
    t__end_floop:;

    t__start_fbailout:;
        // this is the bailout function, in this case "cmag" -> "square modulus"
        // cmag(a,bi) is equivalent to a*a+b*b
        f__bailout = (z_re * z_re + z_im * z_im) < t__a_fbailout;
        goto t__end_fbailout;
    t__end_fbailout:;

        // check the bailout -> if (cmag(z) > bailout) then finish loop
        if (!f__bailout)
            break;

        // period tolerance and min_period_iters:
        // until we reach the min_period_iter we do nothing
        // if the difference between the "old value" and the current value is inferior to the period tolerance
        //   then we finish the loop (the value is not changing too much) considering the value is inside the set (trapped)
        // we save the "old value" once every n-iterations after the min_period_iters -> this is achieved with the save_mask and save_incr
        if (t__h_numiter >= min_period_iter)
        {
            if ((t__h_numiter & save_mask) == 0)
            {
                /* save a value */
                old_z_re = z_re;
                old_z_im = z_im;

                if (--save_incr == 0)
                {
                    /* lengthen period check */
                    save_mask = (save_mask << 1) + 1;
                    save_incr = next_save_incr;
                }
            }
            else
            {
                /* compare to an older value */
                if ((fabs(static_cast<double>(z_re - old_z_re)) < period_tolerance) && (fabs(static_cast<double>(z_im - old_z_im)) < period_tolerance))
                {
                    period_iters = t__h_numiter;
                    //t__h_numiter = maxiter;
                    t__h_inside = 1;
                    *t__p_pFate = 1;

                    goto loop_done;
                }
            }
        }

        // increase the number of iterations performed
        t__h_numiter++;
    } while (t__h_numiter < maxiter);

    /* fate of 0 = escaped, 1 = trapped */
    t__h_inside = (t__h_numiter >= maxiter);
    *t__p_pFate = (t__h_numiter >= maxiter);

loop_done:

    // output the total iterations
    *t__p_pnIters = t__h_numiter;

    // outside transfer function: "continuous potential"
    if (t__h_inside == 0)
    {
    t__start_cf0final:;
        // ed = @bailout/(|z| + 1.0e-9)
        cf0ed = t__a_cf0bailout / ((z_re * z_re + z_im * z_im) + 0.00000000100000000);
        // #index = (#numiter + ed) / 256.0
        t__h_index = ((double)t__h_numiter + cf0ed) / 256.00000000000000000;
        // #index = #index * @density + @offset
        t__h_index = t__a_cf0_density * t__h_index + t__a_cf0_offset;
        goto t__end_cf0final;
    t__end_cf0final:;
    }
    else
    {
    // outside transfer function: "zero"
    t__start_cf1final:;
        // #solid = true
        t__h_solid = 1;
        // #index = #index * @density + @offset
        t__h_index = t__a_cf1_density * t__h_index + t__a_cf1_offset;
        goto t__end_cf1final;
    t__end_cf1final:;
    }

    *t__p_pFate = t__h_fate | (t__h_inside ? FATE_INSIDE : 0);
    *t__p_pDist = static_cast<double>(t__h_index);
    *t__p_pSolid = t__h_solid;


    return;
}

static void pf_kill(
    struct s_pf_data *p_stub)
{
    MpDouble::cleanUp();
    delete p_stub;
}

static struct s_pf_vtable vtbl =
{
    pf_get_defaults,
    pf_init,
    pf_calc,
    pf_kill
};

pf_obj *pf_new()
{
    MpDouble::setPreccisionInBits(432);
    pf_real *p = new (std::nothrow) pf_real;
    if (!p)
        return NULL;
    p->parent.vtbl = &vtbl;
    return (pf_obj *)p;
}