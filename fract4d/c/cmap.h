
#ifndef CMAP_H_
#define CMAP_H_

#include "color.h"

typedef enum
{
    TRANSFER_NONE,
    TRANSFER_LINEAR,
    TRANSFER_SIZE
} e_transferType;

typedef enum
{
    BLEND_LINEAR, 
    BLEND_CURVED, 
    BLEND_SINE, 
    BLEND_SPHERE_INCREASING, 
    BLEND_SPHERE_DECREASING
} e_blendType;


typedef enum
{ 
    RGB, 
    HSV_CCW, 
    HSV_CW
} e_colorType;

class ColorMap
{
public:
    ColorMap();
    virtual ~ColorMap();

    virtual bool init(int n_colors) = 0;
    virtual void set_solid(int which, int r, int g, int b, int a);
    virtual void set_transfer(int which, e_transferType type);
 
    virtual rgba_t get_solid(int which) const;
    virtual rgba_t lookup(double index) const = 0;

    virtual rgba_t lookup_with_transfer(
	double index, int solid, int inside) const;
    virtual rgba_t lookup_with_dca(
	int solid, int inside, double *colors) const;

 public:
    unsigned int canary;

 protected:
    int ncolors;
    rgba_t solids[2];
    e_transferType transfers[2];
};

typedef struct 
{
    double index;
    rgba_t color;
} list_item_t;

class ListColorMap: public ColorMap
{
 public:
    ListColorMap();
    virtual ~ListColorMap();

    bool init(int n_colors);
    void set(int i, double d, int r, int g, int b, int a);
    rgba_t lookup(double index) const; 
 private:
    list_item_t *items;
};

typedef struct 
{
    double left;
    double left_color[4];
    double right;
    double right_color[4];
    double mid;
    e_blendType bmode;
    e_colorType cmode;
} gradient_item_t;


class GradientColorMap: public ColorMap
{
 public:
    GradientColorMap();
    virtual ~GradientColorMap();

    bool init(int n_colors);
    void set(int i,
	     double left, double right, double mid,
	     double *left_col,
	     double *right_col,
	     e_blendType bmode, e_colorType cmode);

    rgba_t lookup(double index) const; 
 private:
    gradient_item_t *items;

};

extern void cmap_delete(ColorMap *cmap);

/* functions called by compiled formulas */

extern "C" {

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

#endif /* CMAP_H_ */
