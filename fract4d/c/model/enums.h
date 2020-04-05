#ifndef __ENUMS_H_INCLUDED__
#define __ENUMS_H_INCLUDED__

/************
 * CALCARGS *
 * **********/

typedef enum {
    RENDER_TWO_D, // standard mandelbrot view
    RENDER_LANDSCAPE, // heightfield
    RENDER_THREE_D // ray-traced 3D object
} render_type_t;

// current state of calculation
typedef enum {
    GF4D_FRACTAL_DONE,
    GF4D_FRACTAL_CALCULATING,
    GF4D_FRACTAL_DEEPENING,
    GF4D_FRACTAL_ANTIALIASING,
    GF4D_FRACTAL_PAUSED,
    GF4D_FRACTAL_TIGHTENING
} calc_state_t;

// kind of antialiasing to do
typedef enum {
    AA_NONE = 0,
    AA_FAST,
    AA_BEST,
    AA_DEFAULT /* used only for effective_aa - means use aa from fractal */
} e_antialias;

// basic parameters defining position and rotation in R4
typedef enum {
    XCENTER,
    YCENTER,
    ZCENTER,
    WCENTER,
    MAGNITUDE,
    XYANGLE,
    XZANGLE,
    XWANGLE,
    YZANGLE,
    YWANGLE,
    ZWANGLE,
} param_t;

// how to draw the image
typedef enum {
    DRAW_GUESSING, // several passes, starting with large boxes
    DRAW_TO_DISK   // complete all passes on one box_row before continuing
} draw_type_t;


/***************
 * IMAGE FILES *
 * *************/

typedef enum {
    FILE_TYPE_TGA,
    FILE_TYPE_PNG,
    FILE_TYPE_JPG,
} image_file_t;


/*********
 * STATS *
 * *******/

typedef enum
{
    // total number of iterations performed
    ITERATIONS,
    // pixels we processed
    PIXELS,
    // number of pixels we actually called calc() on
    PIXELS_CALCULATED,
    // number of pixels we guessed (calculated + skipped == pixels)
    PIXELS_SKIPPED,
    // number of pixels we guessed wrong
    PIXELS_SKIPPED_WRONG,
    // number of pixels we guessed right
    PIXELS_SKIPPED_RIGHT,
    // pixels which wound up inside
    PIXELS_INSIDE,
    // pixels which would up outside (inside + outside == pixels)
    PIXELS_OUTSIDE,
    // pixels which were found to be inside via periodicity
    PIXELS_PERIODIC,
    // n pixels correctly classified that would be wrong
    // if we calculated half the iterations
    WORSE_DEPTH_PIXELS,
    // n pixels currently misclassified that would be correct
    // if we doubled the iterations
    BETTER_DEPTH_PIXELS,
    // n pixels correctly classified that would be wrong
    // if we calculated with looser tolerance
    WORSE_TOLERANCE_PIXELS,
    // n pixels currently misclassified that would be correct
    // if we tightened the tolerance
    BETTER_TOLERANCE_PIXELS,
    // how many stats do we keep
    NUM_STATS
} stat_t;


/*********
 * SITES *
 * *******/

typedef enum
{
    ITERS,
    IMAGE,
    PROGRESS,
    STATUS,
    PIXEL,
    TOLERANCE,
    STATS,
} msg_type_t;

#endif