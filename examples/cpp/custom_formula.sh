#!/bin/sh

docker build . -f examples/cpp/Dockerfile -t custom_formula:1.0.0 \
    --build-arg main_source=custom_formula.cpp \
    --build-arg formula_source=examples/cpp/custom_mandelbrot_formula.c
docker run --rm -it -v ${PWD}/examples/output:/src/output custom_formula:1.0.0