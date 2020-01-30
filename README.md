
About this Program
==================

Gnofract 4D is a program for drawing beautiful mathematically-based
images known as fractals. See the manual for more details.

The most recent version may be obtained from
http://github.com/edyoung/gnofract4d

Examples, screenshots etc are at http://edyoung.github.io/gnofract4d

Basic Installation
==================

Run:

 ./setup.py build

If you would like a copy of the manual:

./createdocs.py

You can then run Gnofract4D in the local directory:

./gnofract4d

You can also install it (you'll normally need to be root to do this):

./setup.py install

You can then run it as:

gnofract4d

You can verify that your installation is working correctly by running

./test.py

Requirements
============

Gnofract 4D requires these packages to run:

o Python version 3.5 or higher
o GTK version 3.18 or higher
o A C++ compiler (used at runtime to compile your fractal formulas)

To build from source you also need:
o headers for libpng and libjpeg
o Python headers
o Pkg-Config

On Ubuntu, these can be installed with:

sudo apt-get install libpng-dev libjpeg-dev python3-dev gtk3.0 cairo python3-cairo python3-gi-cairo pkg-config

If you're not sure if you have these or not, just try running
"./setup.py build" and see if it complains.

If FFmpeg is installed it will be possible to create videos.

On MacOS, you can install the dependencies using brew:

brew install librsvg python3 pkg-config cairo gtk+3 pygobject3 py3cairo libpng jpeg

Testing
=======

Testing requires pytest.

Run individual tests from the top-level directory using pytest, e.g.:
pytest fract4d/test_absyn.py

Optionally, install tox and test with all supported Python versions by running:
tox

On MacOS you might find an error regarding the number of opened files, you can increase the system limit with `ulimit -Sn 10000`
