FROM ubuntu:18.04

ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
	apt-get install -y build-essential git cmake autoconf libtool pkg-config libpng-dev libjpeg-dev
RUN apt-get install -y libmpfr-dev libgmp-dev

WORKDIR /src

# set up benchmark library
RUN git clone https://github.com/google/benchmark.git && \
	git clone https://github.com/google/googletest.git benchmark/googletest && \
	cd benchmark && \
	mkdir build && cd build && \
	cmake ../ && make && make install


ARG main_source
ARG formula_source
ARG gmp_support

COPY examples/cpp/${main_source} ./main.cpp
COPY examples/cpp/CMakeLists.txt ./
COPY fract4d/c/fract_stdlib.cpp fract4d/c/fract_stdlib.h fract4d/c/pf.h  ./
COPY fract4d/c/model/ ./model
COPY ${formula_source} ./

ENV formula_source=$formula_source
ENV gmp_support=$gmp_support
COPY examples/cpp/mp_double.h ./mp_double.h

RUN cmake . && make

CMD ["./example"]