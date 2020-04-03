
#ifndef __COLORUTILS_H_INCLUDED__
#define __COLORUTILS_H_INCLUDED__

/* functions called by compiled formulas */

extern "C"
{
    void rgb_to_hsv(
        double r, double g, double b,
        double *h, double *s, double *v);

    void gimp_rgb_to_hsv(
        double r, double g, double b,
        double *h, double *s, double *v);

    void rgb_to_hsl(
        double r, double g, double b,
        double *h, double *s, double *l);

    void hsl_to_rgb(
        double h, double s, double l,
        double *r, double *g, double *);

    void hsv_to_rgb(
        double h, double s, double v,
        double *r, double *g, double *b);

    void gimp_hsv_to_rgb(
        double h, double s, double v,
        double *r, double *g, double *b);

    double hue(double r, double g, double b);
    double sat(double r, double g, double b);
    double lum(double r, double g, double b);

    void gradient(
        void *grad_object, double index,
        double *r, double *g, double *b);
}

#endif /* __COLORUTILS_H_INCLUDED__ */
