#include "imagereader.h"

#include "model/image.h"

ImageReader *ImageReader::create(image_file_t file_type, FILE *fp, IImage *image)
{
    //printf("Creating reader for type %d\n", file_type);
    switch (file_type)
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

bool ImageReader::read()
{
    if (!read_header())
    {
        return false;
    }
    if (!read_tile())
    {
        return false;
    }
    if (!read_footer())
    {
        return false;
    }
    return true;
}

image_reader::~image_reader()
{
    fclose(fp);
}

image_reader::image_reader(FILE *fp_, IImage *image_)
{
    fp = fp_;
    im = image_;
}

/*******
 * PNG *
 *******/

#ifdef PNG_ENABLED

void user_error_fn(png_structp png_ptr, png_const_charp error_msg)
{
    printf("Error %s reading PNG file", error_msg);
}

void user_warning_fn(png_structp png_ptr, png_const_charp warning_msg)
{
    printf("Warning %s reading PNG file", warning_msg);
}

png_reader::png_reader(FILE *fp, IImage *image) : image_reader(fp, image)
{
    ok = false;
    png_ptr = png_create_read_struct(
        PNG_LIBPNG_VER_STRING,
        NULL, user_error_fn, user_warning_fn);
    if (png_ptr == NULL)
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

png_reader::~png_reader()
{
    //printf("shutdown\n");
    if (ok)
    {
        png_destroy_read_struct(&png_ptr, &info_ptr, (png_infopp)NULL);
    }
}

bool png_reader::read_header()
{
    png_uint_32 width, height;
    int bit_depth, color_type, interlace_type;
    //printf("read PNG info\n");
    png_read_info(png_ptr, info_ptr);
    //printf("get IHDR\n");
    png_get_IHDR(png_ptr, info_ptr, &width, &height, &bit_depth, &color_type,
                 &interlace_type, (int *)NULL, (int *)NULL);
    //printf("set res(%d,%d)\n",width,height);
    if (!im->set_resolution(width, height, -1, -1))
    {
        return false;
    }
    return true;
}

bool png_reader::read_tile()
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

bool png_reader::read_footer()
{
    //printf("read end\n");
    png_read_end(png_ptr, info_ptr);
    //printf("finished reading\n");
    return true;
}
#endif
