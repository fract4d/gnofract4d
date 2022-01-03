#include <cmath>

#ifndef COLOR_H_
#define COLOR_H_

struct s_rgba
{
    unsigned char r,g,b,a;

    inline explicit operator int() const {
        return (r << 16) | (g << 8) | b;
    }

    inline s_rgba operator+(const s_rgba& other) const {
        s_rgba result;
        result.a = other.a + a;
        result.r = other.r + r;
        result.g = other.g + g;
        result.b = other.b + b;
        return result;
    }

    inline s_rgba operator*(double factor) const {
        s_rgba result;
        result.a = static_cast<unsigned char>(std::round(a * factor));
        result.r = static_cast<unsigned char>(std::round(r * factor));
        result.g = static_cast<unsigned char>(std::round(g * factor));
        result.b = static_cast<unsigned char>(std::round(b * factor));
        return result;
    }
};

inline bool operator== (const s_rgba& a, const s_rgba& b) {
    // according to the original implementation "a" is not considered in the comparison
    return a.r == b.r && a.g == b.g && a.b == b.b;
}

typedef struct s_rgba rgba_t;

#endif /* COLOR_H_ */
