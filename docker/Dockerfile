FROM ubuntu:18.04

ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive

# project deps
RUN \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install gir1.2-gtk-3.0 libjpeg-dev libpng-dev pkg-config python3-gi-cairo python3-pip xvfb

# bin/run_builds.sh deps
RUN \
    apt-get update && \
    apt-get -y install software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get -y install python3.6-dev python3.7-dev python3.8-dev

# Gio.AppInfo.launch_default_for_uri() deps
RUN apt-get -y install firefox gvfs

# bin/run_pylint.sh deps
RUN pip3 install pylint

# bin/run_pytest.sh deps
RUN pip3 install pytest

# bin/run_tox.sh deps
RUN apt-get -y install libcairo2-dev libgirepository1.0-dev
RUN pip3 install tox

# Xvfb (in memory x11 server) setup
ENV DISPLAY :99
RUN echo "Xvfb :99 -screen 0 640x480x8 -nolisten tcp &" > /root/xvfb.sh && chmod +x /root/xvfb.sh

WORKDIR /root/gnofract

CMD py3clean /root/gnofract && /root/xvfb.sh && tail -f /dev/null
