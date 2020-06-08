
About this Program
==================

Gnofract 4D is a program for drawing beautiful mathematically-based
images known as fractals. See the manual for more details.

The most recent version may be obtained from
https://github.com/fract4d/gnofract4d

Examples, screenshots etc are at https://fract4d.github.io/gnofract4d

Basic Installation
==================

Run:

 ./setup.py build

You can then run Gnofract4D in the local directory:

./gnofract4d

You can also install it:

sudo ./setup.py install

You can then run it as:

gnofract4d

Requirements
============

Gnofract 4D requires these packages to run:

- Python version 3.5 or higher
- GTK version 3.18 or higher
- A C++ compiler (used at runtime to compile your fractal formulas)

To build from source you also need:
- headers for libpng and libjpeg
- Python headers
- Pkg-Config

On Ubuntu, these can be installed with:

sudo apt-get install libpng-dev libjpeg-dev libcairo2-dev python3-dev gtk3.0 python3-cairo python3-gi-cairo pkg-config libgirepository1.0-dev

If you're not sure if you have these or not, just try running
"./setup.py build" and see if it complains.

If FFmpeg is installed it will be possible to create videos.

On MacOS, you can install the dependencies using brew:

brew install librsvg python3 pkg-config cairo gtk+3 pygobject3 py3cairo libpng jpeg

Testing
=======

Testing requires pytest for python3.x. In some distributions, 'pytest' is for python 2.x. Run

sudo pip3 install pytest

To get the latest.

Run individual tests from the top-level directory using pytest, e.g.:
pytest fract4d/test_absyn.py

Optionally, install tox and test with all supported Python versions by running:
tox

On MacOS you might find an error regarding the number of opened files, you can increase the system limit with `ulimit -Sn 10000`

Linting
=======

Pylint is being used to detect code that doesn't follow the [PEP8 style](https://www.python.org/dev/peps/pep-0008/) guide and potentially erroneous code in Python.
You can run it in two ways:
 - Directly (firstly you should install pylint through pip3):
```
$ sudo pip3 install pylint
$ ./bin/pylint.sh
```
 - Using docker (same environment as pipeline):
```
$ ./docker/bin/run_lint.sh
```

Generating Documentation
========================

You can only regenerate the docs if you clone the Gnofract 4D git repo - the source dist packages contain the generated docs but not the input files for the generation process. To regenerate the docs:

1. Make sure you're starting from a git clone not a source .zip - you need the files under manual/content
1. Install hugo (Ubuntu 18.04 has an older version. Run `snap install hugo` instead of apt-get install hugo)
1. Run `./createdocs.py`

