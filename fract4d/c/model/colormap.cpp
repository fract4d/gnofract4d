#include "colormap.h"

#include "colorutils.h"

#include <cassert>
#include <stdio.h>
#include <math.h>
#include <new>

#define EPSILON 1.0e-10

rgba_t black = {0, 0, 0, 255};

ColorMap::ColorMap()
{
    canary = 0xfeeefeee;
    ncolors = 0;
    solids[0] = solids[1] = black;
    transfers[0] = TRANSFER_LINEAR; // outer
    transfers[1] = TRANSFER_LINEAR; // inner
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : CM : CTOR\n", this);
#endif
}

void ColorMap::set_transfer(int which, e_transferType type)
{
    if (which >= 0 && which < 2)
    {
        if (type < TRANSFER_SIZE && type >= 0)
        {
            transfers[which] = type;
        }
        else
        {
            assert("bad transfer type" && 0);
        }
    }
    else
    {
        assert("bad transfer index" && 0);
    }
}

void ColorMap::set_solid(int which, int r, int g, int b, int a)
{
    rgba_t color;
    color.r = (unsigned char)r;
    color.g = (unsigned char)g;
    color.b = (unsigned char)b;
    color.a = (unsigned char)a;
    if (which >= 0 && which < 2)
    {
        solids[which] = color;
    }
    else
    {
        assert("set bad color" && 0);
    }
}

rgba_t ColorMap::get_solid(int which) const
{
    rgba_t color = {0, 0, 0, 1};
    if (which >= 0 && which < 2)
    {
        color = solids[which];
    }
    else
    {
        assert("get bad color" && 0);
    }
    return color;
}

void cmap_delete(ColorMap *cmap)
{
    assert(cmap->canary == 0xfeeefeee);
    delete cmap;
}

ColorMap::~ColorMap()
{
#ifdef DEBUG_CREATION
    fprintf(stderr, "%p : CM : DTOR\n", this);
#endif
    canary = 0xbaadf00d;
    // NO OP
}

/* finds the indices in t of the largest item which is <= key
   and the next item above it.
   If there are multiple identical items, returns one at random
 */

/* binary search algorithm from Programming Pearls.
   sadly C stdlib's bsearch is no good because it won't tell us the position
   of nearest match if there's no exact one */

int find(double key, list_item_t *array, int n)
{
    int left = 0, right = n - 1;
    do
    {
        int middle;
        if (left > right)
        {
            return left - 1 < 0 ? 0 : left - 1;
        }
        middle = (left + right) / 2;
        if (array[middle].index < key)
        {
            left = middle + 1;
        }
        else if (array[middle].index == key)
        {
            return middle;
        }
        else
        {
            right = middle - 1;
        }
    } while (1);
}

rgba_t ColorMap::lookup_with_dca(int solid, int inside, double *colors) const
{
    rgba_t new_color;
    if (solid)
    {
        return solids[inside];
    }
    e_transferType t = transfers[inside];
    switch (t)
    {
    case TRANSFER_NONE:
        return solids[inside];
    case TRANSFER_LINEAR:
        new_color.r = (unsigned char)(255.0 * colors[0]);
        new_color.g = (unsigned char)(255.0 * colors[1]);
        new_color.b = (unsigned char)(255.0 * colors[2]);
        new_color.a = (unsigned char)(255.0 * colors[3]);
        return new_color;
    default:
        assert("bad transfer type" && 0);
        return black;
    }
}

rgba_t ColorMap::lookup_with_transfer(double index, int solid, int inside) const
{
    if (solid)
    {
        return solids[inside];
    }
    e_transferType t = transfers[inside];
    switch (t)
    {
    case TRANSFER_NONE:
        return solids[inside];
    case TRANSFER_LINEAR:
        return lookup(index);
    default:
        assert("bad transfer type" && 0);
        return black;
    }
}

GradientColorMap::GradientColorMap() : ColorMap()
{
    items = NULL;
}

GradientColorMap::~GradientColorMap()
{
    delete[] items;
}

bool GradientColorMap::init(int ncolors_)
{
    if (ncolors_ == 0)
    {
        return false;
    }
    ncolors = ncolors_;
    items = new (std::nothrow) gradient_item_t[ncolors];
    if (!items)
    {
        return false;
    }
    for (int i = 0; i < ncolors; ++i)
    {
        gradient_item_t *p = &items[i];
        p->left = p->right = 0;
        p->bmode = BLEND_LINEAR;
        p->cmode = RGB;
    }
    return true;
}

void GradientColorMap::set(
    int i,
    double left, double right, double mid,
    double *left_col,
    double *right_col,
    e_blendType bmode, e_colorType cmode)
{
    items[i].left = left;
    items[i].right = right;
    items[i].mid = mid;
    for (int j = 0; j < 4; ++j)
    {
        items[i].left_color[j] = left_col[j];
        items[i].right_color[j] = right_col[j];
    }
    items[i].bmode = bmode;
    items[i].cmode = cmode;
    /*
    fprintf(stderr,"left: %g [%g,%g,%g,%g]\nright: %g [%g,%g,%g,%g]\n%d %d\n",
	   left, left_col[0], left_col[1], left_col[2], left_col[3],
	   right, right_col[0], right_col[1], right_col[2], right_col[3],
	   (int)bmode, (int)cmode);
    */
}

static void grad_dump(gradient_item_t *items, int ncolors)
{
    fprintf(stderr, "gradient dump: %d\n", ncolors);
    for (int i = 0; i < ncolors; ++i)
    {
        fprintf(stderr, "%d: %g\n", i, items[i].right);
    }
}

int grad_find(double index, gradient_item_t *items, int ncolors)
{
    for (int i = 0; i < ncolors; ++i)
    {
        if (index <= items[i].right)
        {
            return i;
        }
    }
    fprintf(stderr, "No gradient for %g\n", index);
    grad_dump(items, ncolors);
    assert(0 && "Didn't find an entry");
    return -1;
}

static double calc_linear_factor(double middle, double pos)
{
    if (pos <= middle)
    {
        if (middle < EPSILON)
            return 0.0;
        else
            return 0.5 * pos / middle;
    }
    else
    {
        pos -= middle;
        middle = 1.0 - middle;

        if (middle < EPSILON)
            return 1.0;
        else
            return 0.5 + 0.5 * pos / middle;
    }
}

static double calc_curved_factor(double middle, double pos)
{
    if (middle < EPSILON)
        middle = EPSILON;
    return pow(pos, log(0.5) / log(middle));
}

static double calc_sine_factor(double middle, double pos)
{
    pos = calc_linear_factor(middle, pos);
    return (sin((-M_PI / 2.0) + M_PI * pos) + 1.0) / 2.0;
}

static double calc_sphere_increasing_factor(double middle, double pos)
{
    pos = calc_linear_factor(middle, pos) - 1.0;
    return sqrt(1.0 - pos * pos);
}

static double calc_sphere_decreasing_factor(double middle, double pos)
{
    pos = calc_linear_factor(middle, pos);
    return 1.0 - sqrt(1.0 - pos * pos);
}

rgba_t GradientColorMap::lookup(double input_index) const
{
    assert(canary == 0xfeeefeee);
    double index = input_index == 1.0 ? 1.0 : fmod(input_index, 1.0);
    if (index < 0.0 || index > 1.0 || index != index)
    {
        // must be infinite or NaN
        return black;
    }
    int i = grad_find(index, items, ncolors);
    assert(i >= 0 && i < ncolors);
    gradient_item_t *seg = &items[i];
    double seg_len = seg->right - seg->left;
    double middle;
    double pos;
    if (seg_len < EPSILON)
    {
        middle = 0.5;
        pos = 0.5;
    }
    else
    {
        middle = (seg->mid - seg->left) / seg_len;
        pos = (index - seg->left) / seg_len;
    }
    double factor;
    switch (seg->bmode)
    {
    case BLEND_LINEAR:
        factor = calc_linear_factor(middle, pos);
        break;

    case BLEND_CURVED:
        factor = calc_curved_factor(middle, pos);
        break;

    case BLEND_SINE:
        factor = calc_sine_factor(middle, pos);
        break;

    case BLEND_SPHERE_INCREASING:
        factor = calc_sphere_increasing_factor(middle, pos);
        break;

    case BLEND_SPHERE_DECREASING:
        factor = calc_sphere_decreasing_factor(middle, pos);
        break;

    default:
        assert(0 && "Unknown gradient type");
        return black;
    }
    /* Calculate color components */
    rgba_t result;
    double *lc = seg->left_color;
    double *rc = seg->right_color;
    switch (seg->cmode)
    {
    case RGB:
        result.r = (unsigned char)(255.0 * (lc[0] + (rc[0] - lc[0]) * factor));
        result.g = (unsigned char)(255.0 * (lc[1] + (rc[1] - lc[1]) * factor));
        result.b = (unsigned char)(255.0 * (lc[2] + (rc[2] - lc[2]) * factor));
        break;
    case HSV_CCW:
    case HSV_CW:
        double lh, ls, lv;
        double rh, rs, rv;
        gimp_rgb_to_hsv(lc[0], lc[1], lc[2], &lh, &ls, &lv);
        gimp_rgb_to_hsv(rc[0], rc[1], rc[2], &rh, &rs, &rv);
        if (seg->cmode == HSV_CCW && lh >= rh)
        {
            rh += 1.0;
        }
        if (seg->cmode == HSV_CW && lh <= rh)
        {
            lh += 1.0;
        }
        double h, s, v;
        h = lh + (rh - lh) * factor;
        s = ls + (rs - ls) * factor;
        v = lv + (rv - lv) * factor;
        if (h > 1.0)
        {
            h -= 1.0;
        }
        //fprintf(stderr,"HSV  %f %f %f FACTOR %f POS %f\n", h,s,v,factor,pos);
        double r, g, b;
        gimp_hsv_to_rgb(h, s, v, &r, &g, &b);
        result.r = (unsigned char)(255.0 * r);
        result.g = (unsigned char)(255.0 * g);
        result.b = (unsigned char)(255.0 * b);
        break;
    default:
        assert(0 && "Unknown color type");
        result = black;
        break;
    }
    /* Calculate alpha */
    result.a = (unsigned char)(255.0 * (lc[3] + (rc[3] - lc[3]) * factor));
    return result;
}

ListColorMap::ListColorMap() : ColorMap()
{
    items = NULL;
}

ListColorMap::~ListColorMap()
{
    delete[] items;
}

bool ListColorMap::init(int ncolors_)
{
    if (ncolors_ == 0)
    {
        return false;
    }
    ncolors = ncolors_;
    items = new (std::nothrow) list_item_t[ncolors];
    if (!items)
    {
        return false;
    }
    for (int i = 0; i < ncolors; ++i)
    {
        items[i].color = black;
        items[i].index = 0;
    }
    return true;
}

void ListColorMap::set(int i, double d, int r, int g, int b, int a)
{
    rgba_t color;
    color.r = (unsigned char)r;
    color.g = (unsigned char)g;
    color.b = (unsigned char)b;
    color.a = (unsigned char)a;
    items[i].color = color;
    items[i].index = d;
}

rgba_t ListColorMap::lookup(double index) const
{
    int i, j;
    rgba_t mix, left, right;
    double dist, r;
    assert(canary == 0xfeeefeee);
    index = index == 1.0 ? 1.0 : fmod(index, 1.0);
    i = find(index, items, ncolors);
    assert(i >= 0 && i < ncolors);
    /* fprintf(stderr,"%g->%d\n",index,i); */
    if (index <= items[i].index || i == ncolors - 1)
    {
        return items[i].color;
    }
    j = i + 1;
    /* mix colors i & j in proportion to the distance between them */
    dist = items[j].index - items[i].index;
    /* fprintf(stderr,"dist: %g\n",dist); */
    if (dist == 0.0)
    {
        return items[i].color;
    }
    r = (index - items[i].index) / dist;
    /* fprintf(stderr,"r:%g\n",r); */
    left = items[i].color;
    right = items[j].color;
    mix.r = (unsigned char)((left.r * (1.0 - r) + right.r * r));
    mix.g = (unsigned char)((left.g * (1.0 - r) + right.g * r));
    mix.b = (unsigned char)((left.b * (1.0 - r) + right.b * r));
    mix.a = (unsigned char)((left.a * (1.0 - r) + right.a * r));
    return mix;
}
