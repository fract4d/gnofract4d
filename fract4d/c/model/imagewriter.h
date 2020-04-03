#ifndef __IMAGEWRITER_H_INCLUDED__
#define __IMAGEWRITER_H_INCLUDED__

#include <stdio.h>

#include "model/enums.h"

class IImage;

class ImageWriter
{
public:
    virtual ~ImageWriter(){};
    static ImageWriter *create(image_file_t type, FILE *fp, IImage *image);
    virtual bool save_header() = 0;
    virtual bool save_tile() = 0;
    virtual bool save_footer() = 0;
    bool save();
};

class image_writer : public ImageWriter
{
public:
    virtual ~image_writer();
protected:
    image_writer(FILE *fp_, IImage *image_);
    FILE *fp;
    IImage *im;
};

class tga_writer : public image_writer
{
public:
    tga_writer(FILE *fp, IImage *image);
    bool save_header();
    bool save_tile();
    bool save_footer();
};

#ifdef PNG_ENABLED
extern "C"
{
#include "png.h"
}
class png_writer : public image_writer
{
public:
    png_writer(FILE *fp, IImage *image);
    ~png_writer();
    bool save_header();
    bool save_tile();
    bool save_footer();
private:
    bool ok;
    png_structp png_ptr;
    png_infop info_ptr;
};
#endif


#ifdef JPG_ENABLED
extern "C"
{
#include "jpeglib.h"
}
class jpg_writer : public image_writer
{
public:
    jpg_writer(FILE *fp, IImage *image);
    ~jpg_writer(){}

    bool save_header();
    bool save_tile();
    bool save_footer();

private:
    bool ok;

    struct jpeg_compress_struct cinfo;
    struct jpeg_error_mgr jerr;
};
#endif

#endif