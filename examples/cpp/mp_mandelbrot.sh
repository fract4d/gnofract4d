#!/bin/sh

docker build . -f examples/cpp/Dockerfile -t mp_mandelbrot:1.0.0 \
    --build-arg main_source=custom_formula.cpp \
    --build-arg formula_source=examples/cpp/mp_formula.cpp \
    --build-arg gmp_support=1
docker run --rm -it -v ${PWD}/examples/output:/src/output mp_mandelbrot:1.0.0