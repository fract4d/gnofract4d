#include <cstdlib>
#include <dlfcn.h>
#include <cstdio>
#include <fcntl.h>
#include <unistd.h>
#include <new>

#include "pf.h"

#include "model/colormap.h"
#include "model/image.h"
#include "model/enums.h"
#include "model/imagewriter.h"

#include "model/fractfunc.h"
#include "model/vectors.h"


int main() {
    // initial setup: load fract4_stdlib globally so the loaded formula has access to it
    void *fract_stdlib_handle = dlopen("./fract_stdlib.so", RTLD_GLOBAL | RTLD_NOW);
    if (!fract_stdlib_handle) {
        fprintf(stderr, "Error loading libfract_stdlib: %s", dlerror());
        return -1;
    }

    // load formula lib
    void *lib_handle = dlopen("./formula.so", RTLD_NOW);
    if (!lib_handle)
    {
        fprintf(stderr, "Error loading formula: %s", dlerror());
        return -1;
    }
    pf_obj *(*pfn)(void);
    pfn = (pf_obj * (*)(void)) dlsym(lib_handle, "pf_new");
    if (!pfn)
    {
        fprintf(stderr, "Error loading formula symbols: %s", dlerror());
        dlclose(lib_handle);
        return -1;
    }
    pf_obj *pf_handle = pfn();

    // formula params: [0, 4.0, 0.0, 1.0, 4.0, 0.0, 1.0]
    int param_len = 7;
    struct s_param *params = (struct s_param *)std::malloc(param_len * sizeof(struct s_param));
    params[0].t = INT;
    params[0].intval = 0;
    params[1].t = FLOAT;
    params[1].doubleval = 4.0;
    params[2].t = FLOAT;
    params[2].doubleval = 0.0;
    params[3].t = FLOAT;
    params[3].doubleval = 1.0;
    params[4].t = FLOAT;
    params[4].doubleval = 4.0;
    params[5].t = FLOAT;
    params[5].doubleval = 0.0;
    params[6].t = FLOAT;
    params[6].doubleval = 1.0;
    // position params
    double pos_params[N_PARAMS] {
        0.0, 0.0, 0.0, 0.0, // X Y Z W
        4.0, // Size or zoom
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0 // XY XZ XW YZ YW ZW planes (4D stuff)
    };

    // initialize the point function with the params
    pf_handle->vtbl->init(pf_handle, pos_params, params, param_len);

    // create the colormap with 3 colors
    ListColorMap *cmap = new (std::nothrow) ListColorMap();
    cmap->init(3);
    cmap->set(0, 0.0, 0, 0, 0, 255);
    cmap->set(1, 0.004, 255, 255, 255, 255);
    cmap->set(2, 1.0, 255, 255, 255, 255);

    // create the image (logic representation)
    IImage *im = new image();
    im->set_resolution(640, 480, -1, -1);

    // calculate the 4D vectors: topleft and deltas (x, y)
    dvec4 center = dvec4(
        pos_params[XCENTER], pos_params[YCENTER],
        pos_params[ZCENTER], pos_params[WCENTER]
    );
    dmat4 rot_matrix = rotated_matrix(pos_params);
    rot_matrix = rot_matrix / im->totalXres();
    dvec4 deltax = rot_matrix[VX];
    dvec4 deltay = rot_matrix[VY];
    dvec4 delta_aa_x = deltax / 2.0;
    dvec4 delta_aa_y = deltay / 2.0;
    dvec4 topleft = center - deltax * im->totalXres() / 2.0 - deltay * im->totalYres() / 2.0;
    topleft += delta_aa_x + delta_aa_y;

    int w = im->Xres();
    int h = im->Yres();
    // we put these variables out of the loop scope to use its previous value
    int iters_taken = 0;
    int min_period_iters = 0;
    // now we calculate every pixel (for a 2D image projection in a single tile)
    for (auto x = 0; x < w; x++) {
        for (auto y = 0; y < h; y++) {
            // calculate the position in 4D (x, y, z, w)
            dvec4 pos = topleft + x * deltax + y * deltay;
            // run the formula
            double dist = 0.0;
            int fate = 0;
            int solid = 0;
            int direct_color = 0;
            double colors[4] = {0.0};
            int inside = 0;
            if (iters_taken == -1) { // we got inside the last time so we'll probably do it again
                min_period_iters = 0;
            } else {
                min_period_iters += 10;
            }
            pf_handle->vtbl->calc(
                pf_handle,
                pos.n,
                100, // max iters
                -1, // wrap param
                min_period_iters, // min period iters (half the max)
                1.0E-9, // period tolerance
                x, y, 0, // x, y and aa: these values are not needed in the formula but required as arguments for debugging purposes
                &iters_taken, &fate, &dist, &solid,
                &direct_color, &colors[0]);
            // process the formula output and get the value from colormap
            rgba_t color;
            if (fate & FATE_INSIDE) {
                iters_taken = -1;
                inside = 1;
            }
            if (direct_color) {
                color = cmap->lookup_with_dca(solid, inside, colors);
                fate |= FATE_DIRECT;
            } else {
                color = cmap->lookup_with_transfer(dist, solid, inside);
            }
            if (solid)
            {
                fate |= FATE_SOLID;
            }
            // this is only needed for optimization and zooming
            im->setIter(x, y, iters_taken);
            im->setFate(x, y, 0, fate);
            im->setIndex(x, y, 0, dist);
            // put the pixel color into the image buffer position
            im->put(x, y, color);
        }
    }

    // save the image
    FILE *image_file = fopen("./output/mandelbrot.png", "wb");
    image_file_t image_file_type = FILE_TYPE_PNG;
    ImageWriter *image_writer = ImageWriter::create(image_file_type, image_file, im);
    if (NULL == image_writer)
    {
        fprintf(stderr, "Cannot save the image");
        return -1;
    }
    image_writer->save_header();
    image_writer->save_tile();
    image_writer->save_footer();

    // free resources
    delete image_writer;
    delete im;
    delete cmap;
    pf_handle->vtbl->kill(pf_handle);
    dlclose(lib_handle);
    dlclose(fract_stdlib_handle);
    std::free(params);
    return 0;
}