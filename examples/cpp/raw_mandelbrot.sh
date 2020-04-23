#!/bin/sh

./gnofract4d --nogui --buildonly mandelbrot -f gf4d.frm#Mandelbrot
docker build . -f examples/cpp/Dockerfile -t raw_mandelbrot:1.0.0 \
    --build-arg main_source=raw_mandelbrot.cpp \
    --build-arg formula_source=mandelbrot.c
docker run --rm -it -v ${PWD}/examples/output:/src/output raw_mandelbrot:1.0.0