FROM ubuntu:18.04

ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive

# project deps
RUN \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install libpng-dev libjpeg-dev python3-dev gtk3.0 libcairo2-dev python3-cairo python3-gi-cairo pkg-config python3-pip xvfb

RUN pip3 install pytest tox

# other deps
RUN apt-get -y install libgirepository1.0-dev gir1.2-gtk-3.0

# Xvfb (in memory x11 server) setup
ENV DISPLAY :99
RUN echo "Xvfb :99 -screen 0 640x480x8 -nolisten tcp &" > /root/xvfb.sh && chmod +x /root/xvfb.sh

WORKDIR /root/gnofract

CMD py3clean /root/gnofract && /root/xvfb.sh && tail -f /dev/null