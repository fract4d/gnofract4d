FROM ubuntu:18.04

ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
	apt-get install -y build-essential git cmake autoconf libtool pkg-config libpng-dev libjpeg-dev

WORKDIR /src

ARG main_source
ARG formula_source

COPY examples/cpp/${main_source} ./main.cpp
COPY examples/cpp/CMakeLists.txt ./
COPY fract4d/c/fract_stdlib.cpp fract4d/c/fract_stdlib.h fract4d/c/pf.h  ./
COPY fract4d/c/model/ ./model
COPY ${formula_source} ./

ENV formula_source=$formula_source

RUN cmake . && make

CMD ["./example"]