#include <cstdlib>
#include <dlfcn.h>
#include <cstdio>
#include <fcntl.h>
#include <unistd.h>
#include <new>
#include <pthread.h>
#include <thread>

#include "pf.h"

#include "model/site.h"
#include "model/colormap.h"
#include "model/image.h"
#include "model/calcfunc.h"
#include "model/enums.h"
#include "model/imagewriter.h"

struct calcargs {
    pf_obj *pf_handle;
    double *pos_params;
    IFractalSite *site;
    ColorMap *cmap;
    IImage *im;
};

void * calculation_thread(void *vdata) {
    const auto processor_count = std::thread::hardware_concurrency();
    fprintf(stdout, "Running with %d threads\n", processor_count);
    calcargs *args = (calcargs *)vdata;
    calc(
        args->pos_params,
        0, // antialiasing
        100, // max iterations
        processor_count, // number of threads
        args->pf_handle,
        args->cmap,
        0, // auto deepen
        0, // auto tolerance
        1.0E-9, // tolerance
        0, // y flip
        1, // periodicity
        1, // dirty
        0, // debug flags
        RENDER_TWO_D, // render type
        -1, // wrap param
        args->im,
        args->site
    );
    delete args;
}

void * watching_thread(void *vdata) {
    int file = *((int *)vdata);
    // todo: we're doing unsafe read here, but it's ok for a quick example
    while(true) {
        msg_type_t message_type;
        read(file, &message_type, sizeof(message_type));
        int message_size;
        read(file, &message_size, sizeof(message_size));
        fprintf(stdout, "Message read: message_type: %d, size: %d\n", message_type, message_size);
        void *message;
        read(file, message, message_size);
        if (message_type == STATUS) {
            calc_state_t status = *((calc_state_t *)message);
            if (status == GF4D_FRACTAL_DONE) {
                fprintf(stdout, "Calculation finished\n");
                break;
            }
        }
    }
}

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

    // create the site instance (message handler)
    int messages_pipe[2];
    pipe(messages_pipe);
    if (pipe (messages_pipe)) {
        fprintf (stderr, "Pipe failed.\n");
        return EXIT_FAILURE;
    }
    IFractalSite *site = new FDSite(messages_pipe[1]);

    // create the colormap with 3 colors
    ListColorMap *cmap = new (std::nothrow) ListColorMap();
    cmap->init(3);
    cmap->set(0, 0.0, 0, 0, 0, 255);
    cmap->set(1, 0.004, 255, 255, 255, 255);
    cmap->set(2, 1.0, 255, 255, 255, 255);

    // create the image (logic representation)
    IImage *im = new image();
    im->set_resolution(640, 480, -1, -1);

    // Launch a thread to read from fd being written from the calculation thread
    pthread_t tid_read;
    pthread_create(&tid_read, nullptr, watching_thread, (void *)&messages_pipe[0]);
    // LAUNCH CALCULATION
    calcargs *args = new calcargs {pf_handle, pos_params, site, cmap, im};
    pthread_t tid;
    pthread_create(&tid, nullptr, calculation_thread, (void *)args);
    site->set_tid(tid);
    site->wait();
    pthread_join(tid_read, NULL);

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
    delete site;
    close(messages_pipe[0]);
    close(messages_pipe[1]);
    pf_handle->vtbl->kill(pf_handle);
    dlclose(lib_handle);
    dlclose(fract_stdlib_handle);
    std::free(params);
    return 0;
}