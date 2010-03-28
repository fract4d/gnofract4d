#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include <new>

#include "image.h"

#define RED 0
#define GREEN 1
#define BLUE 2

#ifdef WIN32
#include <float.h>
#define finite _finite
#endif

const int 
image::N_SUBPIXELS = 4;

#define MAX_RECOLOR_SIZE (1024*768)

image::image()
{
    m_Xres = m_Yres = 0;
    m_totalXres = m_totalYres = 0;
    m_xoffset = m_yoffset = 0;
    buffer = NULL;
    iter_buf = NULL;
    fate_buf = NULL;
    index_buf = NULL;
}

image::image(const image& im)
{
    m_Xres = im.m_Xres;
    m_Yres = im.m_Yres;
    m_totalXres = im.m_totalXres;
    m_totalYres = im.m_totalYres;
    m_xoffset = im.m_xoffset;
    m_yoffset = im.m_yoffset;
    alloc_buffers();
}

image::~image()
{
    delete_buffers();
}


void
image::delete_buffers()
{
    delete[] buffer;
    delete[] iter_buf;
    delete[] fate_buf;
    delete[] index_buf;
    buffer = NULL;
    iter_buf = NULL;
    fate_buf = NULL;
    index_buf = NULL;
}

bool
image::alloc_buffers()
{
    buffer = new(std::nothrow) char[bytes()];
    iter_buf = new(std::nothrow) int[m_Xres * m_Yres];
    // FIXME remove true 
    if(true || m_Xres * m_Yres <= MAX_RECOLOR_SIZE)
    {
	index_buf = new(std::nothrow) float[m_Xres * m_Yres * N_SUBPIXELS];
	fate_buf = new(std::nothrow) fate_t[m_Xres * m_Yres * N_SUBPIXELS];
	if(!index_buf || !fate_buf)
	{
	    delete_buffers();
	    return false;
	}
    }
    else
    {
	// use less memory for big images. Sadly not working yet
	index_buf = NULL;
	fate_buf = NULL;
    }
    if(!buffer || !iter_buf)
    {
	delete_buffers();
	return false;
    }

    clear();

    return true;
}

int
image::bytes() const
{
    return row_length() * m_Yres;
}

void 
image::put(int x, int y, rgba_t pixel)
{
    int off = x*3 + y * m_Xres * 3;
    assert(off  + BLUE < bytes());
    char *start = buffer + off;
    start[RED] = pixel.r;
    start[GREEN] = pixel.g;
    start[BLUE] = pixel.b;
}

rgba_t 
image::get(int x, int y) const
{
    char *start = buffer + x*3 + y * m_Xres * 3;
    //assert(start  + 2 - buffer <= bytes());
    rgba_t pixel;
    pixel.r = start[RED];
    pixel.g = start[GREEN];
    pixel.b = start[BLUE];
    pixel.a = 0;
    return pixel;
}

bool 
image::set_resolution(int x, int y, int totalx, int totaly)
{
    totalx = totalx == -1 ? x : totalx;
    totaly = totaly == -1 ? y : totaly;

    if(buffer && 
       m_Xres == x && m_Yres == y && 
       m_totalXres == totalx && m_totalYres == totaly) 
    {
	// nothing to do
	return false;
    }

    m_Xres = x;
    m_Yres = y;
    m_totalXres = totalx;
    m_totalYres = totaly;

    delete_buffers();

    if(! alloc_buffers())
    {
	return true;
    }

    rgba_t pixel = { 
	0,0,0,255 // soothing black
    };

    for(int i = 0; i < y; ++i)
    {
	for(int j = 0; j < x; ++j)
	{
	    put(j,i,pixel);
	}
    }

    return true;
}

bool
image::set_offset(int x, int y)
{
    if(x < 0 || x + m_Xres > m_totalXres || y < 0 || y + m_Yres > m_totalYres)
    {
	return false;
    }
    if(x == m_xoffset && y == m_yoffset)
    {
	// nothing to do, succeed already
	return true;
    }

    m_xoffset = x; m_yoffset = y;
    clear();
    return true;
}

double 
image::ratio() const
{
    return ((double)m_Yres / m_Xres);
}

void 
image::fill_subpixels(int x, int y)
{
    fate_t fate = getFate(x,y,0);
    float index = getIndex(x,y,0);
    for(int i = 1; i < N_SUBPIXELS; ++i)
    {
	setFate(x,y,i,fate);
	setIndex(x,y,i,index);
    }
}

void
image::clear_fate(int x, int y)
{
    if(!fate_buf) return;

    int base = index_of_subpixel(x,y,0);
    for(int i = base; i < base+ N_SUBPIXELS; ++i)
    {
	fate_buf[i] = FATE_UNKNOWN;

#ifndef NDEBUG
	// index is only meaningful if fate is known, but set this for
	// testing purposes
	index_buf[i] = 1e30;
#endif
    }
}

fate_t
image::getFate(int x, int y, int subpixel) const
{
    assert(fate_buf != NULL);
    return fate_buf[index_of_subpixel(x,y,subpixel)];
}

void 
image::setFate(int x, int y, int subpixel, fate_t fate)
{
    assert(fate_buf != NULL);
    int i = index_of_subpixel(x,y,subpixel);
    fate_buf[i] = fate;
}

float
image::getIndex(int x, int y, int subpixel) const
{
    assert(index_buf != NULL);
    return index_buf[index_of_subpixel(x,y,subpixel)];
}

void 
image::setIndex(int x, int y, int subpixel, float index)
{
    assert(index_buf != NULL);
    int i = index_of_subpixel(x,y,subpixel);
    index_buf[i] = index;
}

void 
image::clear()
{
    int fate_pos = 0;
    // no need to clear image buffer, just iters and fate
    for(int y = 0; y < m_Yres; ++y) 
    {
	for(int x = 0; x < m_Xres; ++x)
	{
	    iter_buf[y * m_Xres + x]=-1;
	    for(int n = 0; n < N_SUBPIXELS; ++n)
	    {
		fate_buf[fate_pos++] = FATE_UNKNOWN;
	    }
	}
    }
}

double
absfmod(double x, double range)
{
    /* return the modulo when x/range, wrap when x < 0 */
    x = fmod(x,range);
    if(x < 0) 
    {
	x += range;
    }
    assert(0 <= x && x <= range);
    return x;
}

void
blend(
    double r1, double g1, double b1,
    double r2, double g2, double b2,
    double factor,
    double& rres, double& gres, double& bres)
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

void 
blend(
    rgba_t& p1, rgba_t& p2, 
    double factor,
    double& rres, double& gres, double& bres)
{
    blend(p1.r/255.0, 
	  p1.g/255.0,
	  p1.b/255.0,
	  p2.r/255.0,
	  p2.g/255.0,
	  p2.b/255.0,
	  factor,
	  rres, gres, bres);
}

/* compute the color of a point (x,y) on the image im.
   does bilinear interpolation

   image repeats indefinitely, so outside points are mapped in

   image extends from 0..1 in x axis, and 0..aspect in y axis
*/

void
image_lookup(void *vim, double x, double y, double *pr, double *pg, double *pb)
{
    if(NULL == vim || !finite(x) || !finite(y)) // check for no image or NaN
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
    double aspect = ((double)h)/w; // aspect ratio of picture
    double xpos = absfmod(x,1.0) * w; // wrap out-of-bounds points
    double ypos = absfmod(y,aspect) * h;
    
    //printf("aspect, xpos, ypos %g %g %g\n",aspect,xpos,ypos);

    /* addresses of 4 pixels bracketing this point */
    int lowx = int(floor(xpos-0.5));
    if(lowx < 0) lowx += w;
    int highx = (lowx+1);
    if(highx >= w) highx -= w;

    int lowy = int(floor(ypos-0.5));
    if(lowy < 0) lowy += h;
    int highy = (lowy+1);
    if(highy >= h) highy -= h;

    //printf("lowx, highx %d %d\n",lowx,highx);

    // how much of the color blend comes from left-hand pixel
    double xfactor = absfmod(xpos-0.5,1.0);
    // how much of the color blend comes from the top pixel
    double yfactor = absfmod(ypos-0.5,1.0);

    //printf("xfactor, yfactor  %g %g\n",xfactor,yfactor);

    // blend horizontally across the top
    rgba_t top_left_pixel = im->get(lowx,lowy);
    rgba_t top_right_pixel = im->get(highx,lowy);

    double top_mid_r, top_mid_g, top_mid_b;
    blend(top_left_pixel, top_right_pixel, xfactor,
	  top_mid_r, top_mid_g, top_mid_b);

    //printf("top mid: %g %g %g\n",top_mid_r, top_mid_g, top_mid_b);

    // blend horizontally across the bottom
    rgba_t bot_left_pixel = im->get(lowx,highy);
    rgba_t bot_right_pixel = im->get(highx,highy);
    double bot_mid_r, bot_mid_g, bot_mid_b;
    blend(bot_left_pixel, bot_right_pixel, xfactor,
	  bot_mid_r, bot_mid_g, bot_mid_b);

    //printf("bot mid: %g %g %g\n",bot_mid_r, bot_mid_g, bot_mid_b);

    double mid_r, mid_g, mid_b;
    // blend vertically between the 2 blended points
    blend(top_mid_r, top_mid_g, top_mid_b,
	  bot_mid_r, bot_mid_g, bot_mid_b,
	  yfactor,
	  mid_r,mid_g,mid_b);

    //printf("mid: %g %g %g\n", mid_r, mid_g, mid_b);

    *pr = mid_r;
    *pg = mid_g;
    *pb = mid_b;
}
