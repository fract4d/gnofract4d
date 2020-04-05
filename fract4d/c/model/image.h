#ifndef __IMAGE_H_INCLUDED__
#define __IMAGE_H_INCLUDED__

#include <cassert>

#include "pf.h"

typedef struct s_rgba rgba_t;

class IImage
{
public:
    virtual ~IImage(){};
    // return true if this resulted in a change of size
    virtual bool set_resolution(int x, int y, int totalx, int totaly) = 0;
    // return true if this succeeded
    virtual bool set_offset(int x, int y) = 0;

    virtual bool ok() = 0;

    // return xres()/yres()
    virtual double ratio() const = 0;
    // set every iter value to -1. Other data need not be cleared
    virtual void clear() = 0;

    // return number of pixels wide this image is
    virtual int Xres() const = 0;
    // number of pixels wide
    virtual int Yres() const = 0;

    virtual int totalXres() const = 0;
    virtual int totalYres() const = 0;

    virtual int Xoffset() const = 0;
    virtual int Yoffset() const = 0;

    // accessors for color data
    virtual void put(int x, int y, rgba_t pixel) = 0;
    virtual rgba_t get(int x, int y) const = 0;

    // lower-level color data accessors for image_writer
    virtual char *getBuffer() const = 0;
    inline int row_length() const { return Xres() * 3; };

    // accessors for iteration data
    virtual int getIter(int x, int y) const = 0;
    virtual void setIter(int x, int y, int iter) = 0;

    // accessors for fate data
    virtual bool hasFate() const = 0;
    virtual fate_t getFate(int x, int y, int sub) const = 0;
    virtual void setFate(int x, int y, int sub, fate_t fate) = 0;
    // set all subpixels equal to zero'th one
    virtual void fill_subpixels(int x, int y) = 0;

    // accessors for index data
    virtual float getIndex(int x, int y, int sub) const = 0;
    virtual void setIndex(int x, int y, int sub, float index) = 0;

    virtual int getNSubPixels() const = 0;
    virtual bool hasUnknownSubpixels(int x, int y) const = 0;
};

class image : public IImage
{
    int m_Xres;
    int m_Yres;

    int m_totalXres, m_totalYres;
    int m_xoffset, m_yoffset;

    /* the RGB colours of the image */
    char *buffer;

    /* the iteration count for each pixel */
    int *iter_buf;

    /* the value of #index for each pixel */
    float *index_buf;

    /* the fate of each pixel */
    fate_t *fate_buf;

    void delete_buffers();
    bool alloc_buffers();
    void clear_fate(int x, int y);

public:
    static const int N_SUBPIXELS;

    image();
    image(const image &im);
    ~image();

    bool ok();
    int getNSubPixels() const;

    // a bunch on inline functions used outside so them body should be here
    inline bool hasUnknownSubpixels(int x, int y) const
    {
        if (!hasFate())
            return true;

        for (int i = 0; i < N_SUBPIXELS; ++i)
        {
            if (getFate(x, y, i) == FATE_UNKNOWN)
            {
                return true;
            }
        }
        return false;
    }
    inline int Xres() const { return m_Xres; }
    inline int Yres() const { return m_Yres; }
    inline int totalXres() const { return m_totalXres; }
    inline int totalYres() const { return m_totalYres; }
    inline int Xoffset() const { return m_xoffset; }
    inline int Yoffset() const { return m_yoffset; }
    inline char *getBuffer() const
    {
        assert(buffer != NULL);
        return buffer;
    }
    inline fate_t *getFateBuffer()
    {
        assert(fate_buf != NULL);
        return fate_buf;
    }

    // utilities

    int bytes() const;

    // accessors
    void put(int x, int y, rgba_t pixel);
    rgba_t get(int x, int y) const;

    int getIter(int x, int y) const;
    void setIter(int x, int y, int iter);
    bool hasFate() const;

    fate_t getFate(int x, int y, int subpixel) const;
    void setFate(int x, int y, int subpixel, fate_t fate);

    float getIndex(int x, int y, int subpixel) const;
    void setIndex(int x, int y, int subpixel, float index);

    int index_of_subpixel(int x, int y, int subpixel) const;

    // one beyond last pixel
    int index_of_sentinel_subpixel() const;

    void fill_subpixels(int x, int y);

    bool set_resolution(int x, int y, int totalx, int totaly);
    bool set_offset(int x, int y);

    double ratio() const;
    void clear();
};

extern "C"
{
    void image_lookup(void *im, double x, double y, double *pr, double *pg, double *pb);
}

#endif