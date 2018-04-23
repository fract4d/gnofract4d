#include <stdlib.h>
#include <stdio.h>

#include "image_public.h"

class image_writer : public ImageWriter
{
public:
    virtual ~image_writer() {
	fclose(fp);
    };
protected:
    image_writer(FILE *fp_, IImage *image_) {
	fp = fp_;
	im = image_;
    }

    FILE *fp;
    IImage *im;
};

class image_reader : public ImageReader
{
public:
    virtual ~image_reader() {
	fclose(fp);
    };
protected:
    image_reader(FILE *fp_, IImage *image_) {
	fp = fp_;
	im = image_;
    }

    FILE *fp;
    IImage *im;
};

class tga_writer : public image_writer 
{
public:
    tga_writer(FILE *fp, IImage *image) : image_writer(fp,image) {};
  
    bool save_header();
    bool save_tile();
    bool save_footer();
};

bool tga_writer::save_header()
{
    unsigned char tga_header[] = {
	0, // 0: imageid len
	0, // 1: cmap type
	2, // 2: image type = uncompressed 24 bit color
	0,0,0,0,0, // 3 cmap spec
	0,0,0,0, // 8: ?
	0,0,0,0, // 12: filled in with width, height
	24, 32 // 16: ?
    };
    tga_header[12] = im->totalXres() & 0xFF;
    tga_header[13] = im->totalXres() >> 8;
    tga_header[14] = im->totalYres() & 0xFF;
    tga_header[15] = im->totalYres() >> 8;

    int written = fwrite(tga_header, 1, sizeof(tga_header), fp);
    if(written != sizeof(tga_header)) 
    {
	return false;
    }	
    return true;
}

bool tga_writer::save_tile()
{
    for (int y = 0; y < im->Yres(); y++)
    {
        for (int x = 0; x < im->Xres(); x++)
	{
            rgba_t pixel = im->get(x, y);
            fputc(pixel.b,fp);
	    fputc(pixel.g,fp);
	    fputc(pixel.r,fp);
	}
    }
    return true;
}
	
bool tga_writer::save_footer()
{
    static unsigned char tga_footer[] = {
	0, 0, //extoffs
	0, 0, //?
	'T', 'R', 'U', 'E', 'V', 'I', 'S', 'I', 'O','N',
	'-', 'X', 'F', 'I', 'L', 'E', '.'
    };

    int written = fwrite(tga_footer, 1, sizeof(tga_footer), fp);
    if(written != sizeof(tga_footer))
    {
	return false;
    }
    return true;
}

#ifdef PNG_ENABLED
extern "C" {
#include "png.h"
}

class png_writer : public image_writer 
{
public:
    png_writer(FILE *fp, IImage *image) : image_writer(fp,image) {
	ok = false;
	png_ptr = png_create_write_struct(
	    PNG_LIBPNG_VER_STRING,
	    NULL, NULL, NULL); // FIXME do more error handling

	if(NULL == png_ptr)
	{
	    return;
	}

	info_ptr = png_create_info_struct(png_ptr);
	if(NULL == info_ptr)
	{
	    png_destroy_write_struct(&png_ptr, (png_infopp)NULL);
	    return;
	}

	if (setjmp(png_jmpbuf(png_ptr)))
	{
	    /* If we get here, we had a problem writing the file */
	    png_destroy_write_struct(&png_ptr, &info_ptr);
	    return;
	}

	png_init_io(png_ptr, fp);

	ok = true;
    };
    ~png_writer() {
	if(ok)
	{
	    png_destroy_write_struct(&png_ptr, &info_ptr);
	}
    }

    bool save_header();
    bool save_tile();
    bool save_footer();

private:
    bool ok;
    png_structp png_ptr;
    png_infop info_ptr;
};

bool
png_writer::save_header()
{
    png_set_IHDR(
	png_ptr, info_ptr, 
	im->totalXres(), im->totalYres(), // width, height
	8, PNG_COLOR_TYPE_RGB, // bit depth, color type
	PNG_INTERLACE_NONE, 
	PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
    
    png_write_info(png_ptr, info_ptr);

    return true;
}

bool 
png_writer::save_tile()
{
    for (int y = 0; y < im->Yres(); y++)
    {
	png_bytep row = (png_bytep)(im->getBuffer() + im->row_length() * y); 
	png_write_rows(png_ptr, &row, 1);
    }
    return true;
}

bool
png_writer::save_footer()
{
   png_write_end(png_ptr, info_ptr);
   return true;
}

#endif

#ifdef JPG_ENABLED
extern "C" {
#include "jpeglib.h"
}

class jpg_writer : public image_writer 
{
public:
    jpg_writer(FILE *fp, IImage *image) : image_writer(fp,image) {
	ok = true;
    };
    ~jpg_writer() {

    }

    bool save_header();
    bool save_tile();
    bool save_footer();

private:
    bool ok;

    struct jpeg_compress_struct cinfo;
    struct jpeg_error_mgr jerr;

};

bool
jpg_writer::save_header()
{
    cinfo.err = jpeg_std_error(&jerr);
    jpeg_create_compress(&cinfo);
  
    jpeg_stdio_dest(&cinfo, fp);
  
    cinfo.image_width = im->Xres(); 	/* image width and height, in pixels */
    cinfo.image_height = im->totalYres();
    cinfo.input_components = 3;		/* # of color components per pixel */
    cinfo.in_color_space = JCS_RGB; 	/* colorspace of input image */

    jpeg_set_defaults(&cinfo);
    //jpeg_set_quality(&cinfo, quality, TRUE);
  
    jpeg_start_compress(&cinfo, TRUE);
  
    return true;
}

bool 
jpg_writer::save_tile()
{
    for (int y = 0; y < im->Yres(); y++)
    {
	JSAMPROW row = (JSAMPROW)(im->getBuffer() + im->row_length() * y); 
	jpeg_write_scanlines(&cinfo, &row, 1);
    }

    return true;
}

bool
jpg_writer::save_footer()
{
    jpeg_finish_compress(&cinfo);
    jpeg_destroy_compress(&cinfo);
  
    return true;
}

#endif

ImageWriter *
ImageWriter::create(image_file_t file_type, FILE *fp, IImage *image)
{
    switch(file_type)
    {
    case FILE_TYPE_TGA:
	return new tga_writer(fp, image);
    case FILE_TYPE_PNG:
      #ifdef PNG_ENABLED
	return new png_writer(fp, image);
      #endif
	break;
    case FILE_TYPE_JPG:
      #ifdef JPG_ENABLED
	return new jpg_writer(fp, image);
      #endif
	break;
    }
    return NULL; // unknown file type
}

#ifdef PNG_ENABLED
extern "C" {
#include "png.h"
}


void 
user_error_fn(png_structp png_ptr, png_const_charp error_msg)
{
    printf("Error %s reading PNG file", error_msg);
}

void 
user_warning_fn(png_structp png_ptr, png_const_charp warning_msg)
{
    printf("Warning %s reading PNG file", warning_msg);
}

class png_reader : public image_reader 
{
public:
    png_reader(FILE *fp, IImage *image) : image_reader(fp,image) {
	ok = false;

	png_ptr = png_create_read_struct(
	    PNG_LIBPNG_VER_STRING,
	    NULL, user_error_fn, user_warning_fn);
	
	if(png_ptr == NULL)
	{
	    return;
	}
	
	info_ptr = png_create_info_struct(png_ptr);
	if (info_ptr == NULL)
	{
	    png_destroy_read_struct(&png_ptr, (png_infopp)NULL, (png_infopp)NULL);
	    return;
	}

	png_init_io(png_ptr, fp);

	//printf("Init went OK\n");
	ok = true;
    };
    ~png_reader() {
	//printf("shutdown\n");
	if(ok)
	{
	    png_destroy_read_struct(&png_ptr, &info_ptr, (png_infopp)NULL);
	}
    }

    bool read_header();
    bool read_tile();
    bool read_footer();

private:
    bool ok;
    png_structp png_ptr;
    png_infop info_ptr;
};


bool
png_reader::read_header()
{
    png_uint_32 width, height;
    int bit_depth, color_type, interlace_type;
    
    //printf("read PNG info\n");
    png_read_info(png_ptr, info_ptr);
    
    //printf("get IHDR\n");
    png_get_IHDR(png_ptr, info_ptr, &width, &height, &bit_depth, &color_type,
		 &interlace_type, (int *)NULL, (int *)NULL);

    //printf("set res(%d,%d)\n",width,height);
    if(!im->set_resolution(width, height, -1, -1))
    {
	return false;
    }

    return true;
}

bool 
png_reader::read_tile()
{
    int number_passes = png_set_interlace_handling(png_ptr);

    for (int pass = 0; pass < number_passes; pass++)
    {
	for (int y = 0; y < im->Yres(); y++)
	{
	    png_bytep row = (png_bytep)(im->getBuffer() + im->row_length() * y); 
	    png_read_rows(png_ptr, &row, (png_bytepp)NULL, 1);
	}
    }
    return true;
}

bool
png_reader::read_footer()
{
    //printf("read end\n");
    png_read_end(png_ptr, info_ptr);
    //printf("finished reading\n");
    return true;
}
#endif

ImageReader *
ImageReader::create(image_file_t file_type, FILE *fp, IImage *image)
{
    //printf("Creating reader for type %d\n", file_type);
    switch(file_type)
    {
    case FILE_TYPE_PNG:
      #ifdef PNG_ENABLED
	return new png_reader(fp, image);
      #endif
	break;
    case FILE_TYPE_JPG:
    case FILE_TYPE_TGA:
	break;
    }
    return NULL; // unknown file type
}
