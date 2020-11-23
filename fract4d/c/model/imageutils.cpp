#include <cmath>

#include "imageutils.h"

#include "image.h"
#include "model/color.h"


double absfmod(double x, double range)
{
    /* return the modulo when x/range, wrap when x < 0 */
    x = std::fmod(x, range);
    if (x < 0)
    {
        x += range;
    }
    assert(0 <= x && x <= range);
    return x;
}

void blend(
    double r1, double g1, double b1,
    double r2, double g2, double b2,
    double factor,
    double &rres, double &gres, double &bres)
{
    /* blend 2 colors together in ratio given by factor
       (0.0 = all 1st color, 1.0 = all 2nd color)
    */
    double other_factor = 1.0 - factor;
    rres = r1 * other_factor + r2 * factor;
    gres = g1 * other_factor + g2 * factor;
    bres = b1 * other_factor + b2 * factor;
    //printf("blend(%g,%g,%g),(%g,%g,%g) by %g => (%g,%g,%g)\n",
    //	   r1,g1,b1, r2,g2,b2, factor, rres,gres,bres);
}

void blend(
    rgba_t &p1, rgba_t &p2,
    double factor,
    double &rres, double &gres, double &bres)
{
    blend(p1.r / 255.0,
          p1.g / 255.0,
          p1.b / 255.0,
          p2.r / 255.0,
          p2.g / 255.0,
          p2.b / 255.0,
          factor,
          rres, gres, bres);
}

/* compute the color of a point (x,y) on the image im.
   does bilinear interpolation

   image repeats indefinitely, so outside points are mapped in

   image extends from 0..1 in x axis, and 0..aspect in y axis
*/

void image_lookup(void *vim, double x, double y, double *pr, double *pg, double *pb)
{
    if (!vim || !std::isfinite(x) || !std::isfinite(y)) // check for no image or NaN
    {
        *pr = 0.0;
        *pb = 0.0;
        *pg = 1.0;
        return;
    }

    image *im = (image *)vim;
    //printf("im x y %p %g %g\n", im,x,y);
    /* map from x = [0,1.0], y = [0,aspect] (aspect <= 1.0) to
       pixel coordinates */
    int w = im->Xres();
    int h = im->Yres();
    double aspect = ((double)h) / w;   // aspect ratio of picture
    double xpos = absfmod(x, 1.0) * w; // wrap out-of-bounds points
    double ypos = absfmod(y, aspect) * h;
    //printf("aspect, xpos, ypos %g %g %g\n",aspect,xpos,ypos);
    /* addresses of 4 pixels bracketing this point */
    int lowx = int(std::floor(xpos - 0.5));
    if (lowx < 0)
        lowx += w;
    int highx = (lowx + 1);
    if (highx >= w)
        highx -= w;

    int lowy = int(std::floor(ypos - 0.5));
    if (lowy < 0)
        lowy += h;
    int highy = (lowy + 1);
    if (highy >= h)
        highy -= h;
    //printf("lowx, highx %d %d\n",lowx,highx);
    // how much of the color blend comes from left-hand pixel
    double xfactor = absfmod(xpos - 0.5, 1.0);
    // how much of the color blend comes from the top pixel
    double yfactor = absfmod(ypos - 0.5, 1.0);
    //printf("xfactor, yfactor  %g %g\n",xfactor,yfactor);
    // blend horizontally across the top
    rgba_t top_left_pixel = im->get(lowx, lowy);
    rgba_t top_right_pixel = im->get(highx, lowy);
    double top_mid_r, top_mid_g, top_mid_b;
    blend(top_left_pixel, top_right_pixel, xfactor,
          top_mid_r, top_mid_g, top_mid_b);
    //printf("top mid: %g %g %g\n",top_mid_r, top_mid_g, top_mid_b);
    // blend horizontally across the bottom
    rgba_t bot_left_pixel = im->get(lowx, highy);
    rgba_t bot_right_pixel = im->get(highx, highy);
    double bot_mid_r, bot_mid_g, bot_mid_b;
    blend(bot_left_pixel, bot_right_pixel, xfactor,
          bot_mid_r, bot_mid_g, bot_mid_b);
    //printf("bot mid: %g %g %g\n",bot_mid_r, bot_mid_g, bot_mid_b);
    double mid_r, mid_g, mid_b;
    // blend vertically between the 2 blended points
    blend(top_mid_r, top_mid_g, top_mid_b,
          bot_mid_r, bot_mid_g, bot_mid_b,
          yfactor,
          mid_r, mid_g, mid_b);
    //printf("mid: %g %g %g\n", mid_r, mid_g, mid_b);
    *pr = mid_r;
    *pg = mid_g;
    *pb = mid_b;
}
