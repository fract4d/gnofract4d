#ifndef __FRACTGEOMETRY_H_INCLUDED__
#define __FRACTGEOMETRY_H_INCLUDED__

#include "model/vectors.h"
#include "model/enums.h"

/*
    this class performs the geometry calculations to give each point
    within a 2d slice or 3d projection its corresponding 4-dimensional
    space value in the form of a 4d vector
*/

class fract_geometry final
{
public:
    // used for calculating (x,y,z,w) pixel coords
    dvec4 deltax, deltay;         // step from 1 pixel to the next in x,y directions
    dvec4 delta_aa_x, delta_aa_y; // offset between subpixels
    dvec4 topleft;                // top left corner of screen
    dvec4 aa_topleft;             // topleft - offset to 1st subpixel to draw
    dvec4 eye_point;              // where user's eye is (for 3d mode)

    fract_geometry(
        double *location, // x, y, z, w, magnitude, xy, xz, xw, yz, yw, zw
        bool y_flip,
        int width,
        int height,
        int x_offset,
        int y_offset) noexcept
    {
        const dvec4 center = dvec4(
            location[XCENTER], location[YCENTER],
            location[ZCENTER], location[WCENTER]
        );
        dmat4 rot = rotated_matrix(location);
        eye_point = center + rot[VZ] * -10.0; // FIXME add eye distance parameter
        rot = rot / width;
        // distance to jump for one pixel down or across
        deltax = rot[VX];
        // if yflip, draw Y axis down, otherwise up
        deltay = y_flip ? rot[VY] : -rot[VY];
        // half that distance
        delta_aa_x = deltax / 2.0;
        delta_aa_y = deltay / 2.0;
        // topleft is now top left corner of top left pixel...
        topleft = center -
                deltax * width / 2.0 -
                deltay * height / 2.0;
        // offset to account for tiling, if any
        topleft += x_offset * deltax;
        topleft += y_offset * deltay;
        // .. then offset to center of pixel
        topleft += delta_aa_x + delta_aa_y;
        // antialias: offset to middle of top left quadrant of pixel
        aa_topleft = topleft - (delta_aa_y + delta_aa_x) / 2.0;
    }

    inline dvec4 vec_for_point_2d(double x, double y) const
    {
        return topleft + x * deltax + y * deltay;
    }

    inline dvec4 vec_for_point_2d_aa(double x, double y) const
    {
        return aa_topleft + x * deltax + y * deltay;
    }

    // a vector from the eye through the pixel at (x,y)
    inline dvec4 vec_for_point_3d(double x, double y) const
    {
        dvec4 vec = vec_for_point_2d(x, y) - eye_point;
        vec.norm();
        return vec;
    }

    // The eye vector is the line between the center of the screen and the
    // point where the user's eye is deemed to be. It's effectively the line
    // perpendicular to the screen in the -Z direction, scaled by the "eye distance"
    static dvec4 eye_vector(double *location, double dist)
    {
        return rotated_matrix(location)[VZ] * -dist;
    }

    // produces the scaled rotation matrix from the location params
    static dmat4 rotated_matrix(double *location)
    {
        return identity3D<double>(location[MAGNITUDE]) *
            rotXY<double>(location[XYANGLE]) *
            rotXZ<double>(location[XZANGLE]) *
            rotXW<double>(location[XWANGLE]) *
            rotYZ<double>(location[YZANGLE]) *
            rotYW<double>(location[YWANGLE]) *
            rotZW<double>(location[ZWANGLE]);
    }
};

#endif