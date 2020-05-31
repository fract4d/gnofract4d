#include <utility>
#include <cstdio>

#include <mpfr.h>

class MpDouble final {
    mpfr_t value;
public:

    // copy constructor
    MpDouble(const MpDouble &original) noexcept {
        mpfr_init(value);
        mpfr_set(value, original.value, MPFR_RNDN);
    }
    // move constructor
    MpDouble(MpDouble &&original) noexcept {
        mpfr_init(value); // this is needed to keep original is a safe state for destruction
        swap(original);
    }
    // implicit constructor
    MpDouble(const double literal) noexcept {
        mpfr_init(value);
        mpfr_set_d(value, literal, MPFR_RNDN);
    }
    // explicit constructors
    explicit MpDouble(const char *literal) noexcept {
        mpfr_init(value);
        mpfr_set_str(value, literal, 10, MPFR_RNDN);
    }
    explicit MpDouble(mpfr_t val) noexcept {
        mpfr_swap(value, val);
    }
    // swap
    inline void swap(MpDouble &other) noexcept {
        mpfr_swap(value, other.value);
    }
    // destructor
    ~MpDouble() {
        mpfr_clear(value);
    }

    static void setPrecisionInBits(int bits) {
        mpfr_set_default_prec(bits);
    }

    static void cleanUp() {
        mpfr_free_cache();
    }

    // explicit static cast to double
    explicit operator double() const {
        return mpfr_get_d(value, MPFR_RNDN);
    }

    // assignment operation
    MpDouble &operator=(const MpDouble &other) noexcept {
        if(this == &other) return *this;
        mpfr_set(value, other.value, MPFR_RNDN);
        return *this;
    }
    // move assignment operation
    MpDouble &operator=(MpDouble &&other) noexcept {
        if(this == &other) return *this;
        swap(other);
        return *this;
    }

    // arithmetic operations
    MpDouble &operator+=(const MpDouble &other) {
        mpfr_add(value, value, other.value, MPFR_RNDN);
        return *this;
    }
    MpDouble &operator-=(const MpDouble &other) {
        mpfr_sub(value, value, other.value, MPFR_RNDN);
        return *this;
    }
    MpDouble &operator/=(const MpDouble &other) {
        mpfr_div(value, value, other.value, MPFR_RNDN);
        return *this;
    }
    MpDouble &operator*=(const MpDouble &other) {
        mpfr_mul(value, value, other.value, MPFR_RNDN);
        return *this;
    }

    friend MpDouble operator+(const MpDouble &a, const MpDouble &b);
    friend MpDouble operator-(const MpDouble &a, const MpDouble &b);
    friend MpDouble operator/(const MpDouble &a, const MpDouble &b);
    friend MpDouble operator*(const MpDouble &a, const MpDouble &b);

    friend bool operator>(const MpDouble &a, const MpDouble &b);
    friend bool operator<(const MpDouble &a, const MpDouble &b);
    friend bool operator>=(const MpDouble &a, const MpDouble &b);
    friend bool operator<=(const MpDouble &a, const MpDouble &b);
    friend bool operator!=(const MpDouble &a, const MpDouble &b);
    friend bool operator==(const MpDouble &a, const MpDouble &b);

    friend void swap(MpDouble &a, MpDouble &b);
};

void swap(MpDouble &a, MpDouble &b) {
    a.swap(b);
}

MpDouble operator+(const MpDouble &a, const MpDouble &b) {
    mpfr_t result;
    mpfr_init(result);
    mpfr_add(result, a.value, b.value, MPFR_RNDN);
    return MpDouble {result};
}

MpDouble operator-(const MpDouble &a, const MpDouble &b) {
    mpfr_t result;
    mpfr_init(result);
    mpfr_sub(result, a.value, b.value, MPFR_RNDN);
    return MpDouble {result};
}

MpDouble operator/(const MpDouble &a, const MpDouble &b) {
    mpfr_t result;
    mpfr_init(result);
    mpfr_div(result, a.value, b.value, MPFR_RNDN);
    return MpDouble {result};
}

MpDouble operator*(const MpDouble &a, const MpDouble &b) {
    mpfr_t result;
    mpfr_init(result);
    mpfr_mul(result, a.value, b.value, MPFR_RNDN);
    return MpDouble {result};
}

bool operator>(const MpDouble &a, const MpDouble &b) {
    return mpfr_greater_p(a.value, b.value);
}

bool operator<(const MpDouble &a, const MpDouble &b) {
    return mpfr_less_p(a.value, b.value);
}

bool operator>=(const MpDouble &a, const MpDouble &b) {
    return mpfr_greaterequal_p(a.value, b.value);
}

bool operator<=(const MpDouble &a, const MpDouble &b) {
    return mpfr_lessequal_p(a.value, b.value);
}

bool operator==(const MpDouble &a, const MpDouble &b) {
    return mpfr_equal_p(a.value, b.value);
}

bool operator!=(const MpDouble &a, const MpDouble &b) {
    return mpfr_lessgreater_p(a.value, b.value);
}
