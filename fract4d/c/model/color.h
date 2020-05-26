#ifndef COLOR_H_
#define COLOR_H_

struct s_rgba
{
    unsigned char r,g,b,a;

    inline explicit operator int() const {
        return (r << 16) | (g << 8) | b;
    }
};

inline bool operator== (const s_rgba& a, const s_rgba& b) {
    // according to the original implementation "a" is not considered in the comparison
    return a.r == b.r && a.g == b.g && a.b == b.b;
}

typedef struct s_rgba rgba_t;

#endif /* COLOR_H_ */
