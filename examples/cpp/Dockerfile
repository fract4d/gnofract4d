FROM ubuntu:18.04

ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
	apt-get install -y build-essential git cmake autoconf libtool pkg-config libpng-dev libjpeg-dev

WORKDIR /src

COPY examples/cpp/CMakeLists.txt examples/cpp/simple_mandelbrot.cpp ./
COPY fract4d/c/fract_stdlib.cpp fract4d/c/fract_stdlib.h fract4d/c/pf.h  ./
COPY fract4d/c/model/ ./model
COPY mandelbrot.c ./

RUN cmake . && make

CMD ["./simple_mandelbrot"]