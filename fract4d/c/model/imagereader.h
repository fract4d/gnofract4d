#ifndef __IMAGEREADER_H_INCLUDED__
#define __IMAGEREADER_H_INCLUDED__

#include <stdio.h>

#include "model/enums.h"

class IImage;

class ImageReader
{
public:
    virtual ~ImageReader(){};
    static ImageReader *create(image_file_t type, FILE *fp, IImage *image);
    virtual bool read_header() = 0;
    virtual bool read_tile() = 0;
    virtual bool read_footer() = 0;
    bool read();
};

class image_reader : public ImageReader
{
public:
    virtual ~image_reader();
protected:
    image_reader(FILE *fp_, IImage *image_);
    FILE *fp;
    IImage *im;
};

#ifdef PNG_ENABLED
extern "C"
{
#define PNG_SKIP_SETJMP_CHECK 1
#include "png.h"
}
class png_reader : public image_reader
{
public:
    png_reader(FILE *fp, IImage *image);
    ~png_reader();
    bool read_header();
    bool read_tile();
    bool read_footer();
private:
    bool ok;
    png_structp png_ptr;
    png_infop info_ptr;
};
#endif

#endif