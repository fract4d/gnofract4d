#include "colorutils.h"
#include "model/colormap.h"
#include "model/color.h"

#include <math.h>

/* Convert from rgb colorspace to hsv and hsl
   all components in [0,1] except hue in [0,6]

   Taken from Foley, van Dam, Feiner & Hughes
*/

#define MAX3(a, b, c) ((a) > (b) ? ((a) > (c) ? (a) : (c)) : ((b) > (c) ? (b) : (c)))
#define MIN3(a, b, c) ((a) < (b) ? ((a) < (c) ? (a) : (c)) : ((b) < (c) ? (b) : (c)))

void rgb_to_hsv(
    double r, double g, double b,
    double *h, double *s, double *v)
{
    double min = MIN3(r, g, b);
    double max = MAX3(r, g, b);
    *v = max;
    double delta = max - min;
    *s = (max == 0.0) ? 0.0 : (delta / max);
    if (*s == 0.0)
    {
        // achromatic
        *h = 0; // strictly, undefined. we choose 0
        return;
    }
    if (r == max)
    {
        *h = (g - b) / delta; // between yellow & magenta
    }
    else if (g == max)
    {
        *h = 2 + (b - r) / delta; // between cyan & yellow
    }
    else
    {
        *h = 4 + (r - g) / delta; // between magenta & cyan
    }
    if (*h < 0)
    {
        *h += 6.0;
    }
}

void gimp_rgb_to_hsv(double r, double g, double b, double *h, double *s, double *v)
{
    rgb_to_hsv(r, g, b, h, s, v);
    *h /= 6.0;
}

void rgb_to_hsl(
    double r, double g, double b,
    double *h, double *s, double *l)
{
    double min = MIN3(r, g, b);
    double max = MAX3(r, g, b);
    *l = (max + min) / 2.0;
    if (max == min)
    {
        // achromatic
        *s = 0;
        *h = 0;
    }
    else
    {
        double delta = max - min;
        *s = (*l <= 0.5) ? (delta / (max + min)) : (delta / (2.0 - (max + min)));
        if (r == max)
        {
            *h = (g - b) / delta; // between yellow & magenta
        }
        else if (g == max)
        {
            *h = 2 + (b - r) / delta; // between cyan & yellow
        }
        else
        {
            *h = 4 + (r - g) / delta; // between magenta & cyan
        }
        if (*h < 0)
        {
            *h += 6.0;
        }
    }
}

// hue is assumed to be in degrees
double rgb_component(double n1, double n2, double hue)
{
    hue = (hue > 6.0) ? (hue - 6.0) : (hue < 0.0) ? hue + 6.0 : hue;
    if (hue < 1.0)
    {
        return n1 + (n2 - n1) * hue;
    }
    if (hue < 3.0)
    {
        return n2;
    }
    if (hue < 4.0)
    {
        return n1 + (n2 - n1) * (4.0 - hue);
    }
    return n1;
}

void hsl_to_rgb(
    double h, double s, double l,
    double *r, double *g, double *b)
{
    if (s == 0.0)
    {
        // achromatic
        *r = *g = *b = l;
    }
    else
    {
        // chromatic
        double n2;
        if (l <= 0.5)
        {
            n2 = l * (1.0 + s);
        }
        else
        {
            n2 = l + s - l * s;
        }
        double n1 = 2.0 * l - n2;
        *r = rgb_component(n1, n2, h + 2.0);
        *g = rgb_component(n1, n2, h);
        *b = rgb_component(n1, n2, h - 2.0);
    }
    //fprintf(stderr,"hsl(%g,%g,%g) -> rgb(%g,%g,%g)\n", h,s,l,*r,*g,*b);
}

void hsv_to_rgb(
    double h, double s, double v,
    double *r, double *g, double *b)
{
    /* 0 <= h < 6 */
    if (s == 0)
    {
        *r = *g = *b = v;
        return;
    }
    h = fmod(h, 6.0);
    if (h < 0)
    {
        h += 6.0;
    }
    int i = int(h);
    double f = h - i; //Decimal bit of hue
    double p = v * (1 - s);
    double q = v * (1 - s * f);
    double t = v * (1 - s * (1 - f));
    switch (i)
    {
    case 0:
        *r = v;
        *g = t;
        *b = p;
        break;
    case 1:
        *r = q;
        *g = v;
        *b = p;
        break;
    case 2:
        *r = p;
        *g = v;
        *b = t;
        break;
    case 3:
        *r = p;
        *g = q;
        *b = v;
        break;
    case 4:
        *r = t;
        *g = p;
        *b = v;
        break;
    case 5:
        *r = v;
        *g = p;
        *b = q;
    }
}

void gimp_hsv_to_rgb(double h, double s, double v, double *r, double *g, double *b)
{
    h *= 6.0; // h*360/60
    hsv_to_rgb(h, s, v, r, g, b);
}

// accessors for hsl components
double hue(double r, double g, double b)
{
    double h, s, l;
    rgb_to_hsl(r, g, b, &h, &s, &l);
    return h;
}

double sat(double r, double g, double b)
{
    double h, s, l;
    rgb_to_hsl(r, g, b, &h, &s, &l);
    return s;
}

double lum(double r, double g, double b)
{
    double h, s, l;
    rgb_to_hsl(r, g, b, &h, &s, &l);
    return l;
}

void gradient(void *grad_object, double index, double *r, double *g, double *b)
{
    ColorMap *pmap = (ColorMap *)grad_object;
    //fprintf(stderr,"gradient %p\n", grad_object);
    rgba_t col = pmap->lookup(index);
    *r = ((double)col.r) / 255.0;
    *g = ((double)col.g) / 255.0;
    *b = ((double)col.b) / 255.0;
}
