FROM ubuntu:18.04

ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive

# project deps
RUN \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install libpng-dev libjpeg-dev python3-dev gtk3.0 libcairo2-dev python3-cairo python3-gi-cairo pkg-config python3-pip xvfb

# bin/run_builds.sh deps
RUN apt-get -y install software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get -y install python3.5 python3.5-dev python3.6 python3.6-dev python3.7 python3.7-dev python3.8 python3.8-dev

# bin/run_pylint.sh deps
RUN pip3 install pylint

# bin/run_pytest.sh deps
RUN pip3 install pytest

# bin/run_tox.sh deps
RUN apt-get -y install libgirepository1.0-dev
RUN pip3 install tox

# Xvfb (in memory x11 server) setup
ENV DISPLAY :99
RUN echo "Xvfb :99 -screen 0 640x480x8 -nolisten tcp &" > /root/xvfb.sh && chmod +x /root/xvfb.sh

WORKDIR /root/gnofract

CMD py3clean /root/gnofract && /root/xvfb.sh && tail -f /dev/null