
#include <string.h>

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

typedef struct s_pixel_stat pixel_stat_t;

struct s_pixel_stat{
    unsigned long s[NUM_STATS];

    s_pixel_stat() {
	reset();
    };

    void reset() {
	memset(&s,0,sizeof(s));
    };

    void add(const pixel_stat_t& other) {
	for (int i = 0; i < NUM_STATS; ++i)
	{
	    s[i] += other.s[i];
	}
    };

    double worse_depth_ratio() const { 
	return ((double)s[WORSE_DEPTH_PIXELS])/s[PIXELS]; 
    }
    double better_depth_ratio() const { 
	return ((double)s[BETTER_DEPTH_PIXELS])/s[PIXELS]; 
    }

    double worse_tolerance_ratio() const { 
	return ((double)s[WORSE_TOLERANCE_PIXELS])/s[PIXELS]; 
    }
    double better_tolerance_ratio() const { 
	return ((double)s[BETTER_TOLERANCE_PIXELS])/s[PIXELS]; 
    }
};

