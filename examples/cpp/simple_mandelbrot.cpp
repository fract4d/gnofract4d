#include <cstdlib>
#include <dlfcn.h>
#include <cstdio>
#include <fcntl.h>
#include <unistd.h>
#include <new>
#include <memory>

#include "pf.h"

#include "model/site.h"
#include "model/colormap.h"
#include "model/image.h"
#include "model/calcfunc.h"
#include "model/enums.h"
#include "model/imagewriter.h"

#define MAX_ITERATIONS 100

constexpr double pos_params[N_PARAMS] {
    0.0, 0.0, 0.0, 0.0, // X Y Z W
    4.0, // Size or zoom
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0 // XY XZ XW YZ YW ZW planes (4D stuff)
};

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
    pfn = reinterpret_cast<pf_obj * (*)(void)>(dlsym(lib_handle, "pf_new"));
    if (!pfn)
    {
        fprintf(stderr, "Error loading formula symbols: %s", dlerror());
        dlclose(lib_handle);
        return -1;
    }
    pf_obj *pf_handle = pfn();

    // formula params: [0, 4.0, 0.0, 1.0, 4.0, 0.0, 1.0]
    int param_len = 7;
    auto params{std::make_unique<s_param []>(param_len)};
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

    // initialize the point function with the params
    pf_handle->vtbl->init(pf_handle, const_cast<double *>(pos_params), params.get(), param_len);

    // create the site instance (message handler)
    int fd = open("./output.txt", O_RDWR | O_CREAT);
    if (fd == -1) {
        fprintf(stderr, "Cannot open the output file");
        return -1;
    }
    auto site{std::make_unique<FDSite>(fd)};

    // create the colormap with 3 colors
    std::unique_ptr<ListColorMap> cmap{new (std::nothrow) ListColorMap{}};
    cmap->init(3);
    cmap->set(0, 0.0, 0, 0, 0, 255);
    cmap->set(1, 0.004, 255, 255, 255, 255);
    cmap->set(2, 1.0, 255, 255, 255, 255);

    // create the image (logic representation)
    auto im{std::make_unique<image>()};
    im->set_resolution(640, 480, -1, -1);

    // LAUNCH CALCULATION
    calc(
        const_cast<double *>(pos_params),
        0, // antialiasing
        MAX_ITERATIONS,
        1, // number of threads
        pf_handle,
        cmap.get(),
        0, // auto deepen
        0, // auto tolerance
        1.0E-9, // tolerance
        0, // y flip
        1, // periodicity
        1, // dirty
        0, // debug flags
        RENDER_TWO_D, // render type
        -1, // wrap param
        im.get(),
        site.get()
    );

    // save the image
    FILE *image_file = fopen("./output/mandelbrot.png", "wb");
    image_file_t image_file_type = FILE_TYPE_PNG;
    std::unique_ptr<ImageWriter> image_writer{ImageWriter::create(image_file_type, image_file, im.get())};
    if (!image_writer || !image_writer->save())
    {
        fprintf(stderr, "Cannot save the image");
        return -1;
    }

    // free resources
    close(fd);
    pf_handle->vtbl->kill(pf_handle);
    dlclose(lib_handle);
    dlclose(fract_stdlib_handle);
    return 0;
}