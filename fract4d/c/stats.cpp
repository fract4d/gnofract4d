
#include "stats.h"

Statistics::Statistics()
{
    iterations = 0;
    pixels_calculated = 0;
    pixels_skipped = 0;
    pixels_inside = 0;
    pixels_outside = 0;
}

void
Statistics::combine(Statistics& other)
{
    iterations += other.iterations;
    pixels_calculated += other.pixels_calculated;
    pixels_skipped += other.pixels_skipped;
    pixels_inside += other.pixels_inside;
    pixels_outside += other.pixels_outside;
}
