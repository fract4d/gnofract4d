#!/bin/sh

docker build . -f examples/cpp/Dockerfile -t mp_mandelbrot:1.0.0 \
    --build-arg main_source=benchmark.cpp \
    --build-arg formula_source=examples/cpp/mp_formula.cpp \
    --build-arg gmp_support=1

# disable CPU frequency scaling during test for hopefully more consistent results
if [ -x "$(command -v cpupower)" ]; then
    sudo cpupower frequency-set --governor performance
fi

docker run --rm -it -v ${PWD}/examples/output:/src/output mp_mandelbrot:1.0.0

if [ -x "$(command -v cpupower)" ]; then
    sudo cpupower frequency-set --governor powersave
fi
