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

You can then run Gnofract 4D in the local directory:

    ./gnofract4d

Alternatively to build and install Gnofract 4D type:

    pip3 install gnofract4d-4.3.tar.gz

You can then run it by clicking on the desktop icon or typing:

    gnofract4d

Requirements
============

Gnofract 4D requires these packages to run:

- Python version 3.6 or higher
- GTK version 3.18 or higher
- Pycairo
- PyGObject to access GTK from Python
- A C++ compiler (used at runtime to compile your fractal formulas)

On Ubuntu, these can be installed with:

    sudo apt install gcc gir1.2-gtk-3.0 python3-gi-cairo

To build from source you also need:

- headers for libpng and libjpeg
- Python headers
- pkg-config

On Ubuntu, these can be installed with:

    sudo apt install libjpeg-dev libpng-dev libpython3-dev pkg-config

If FFmpeg is installed it will be possible to create videos.

On MacOS, you can install the dependencies using brew:

    brew install librsvg python3 pkg-config cairo gtk+3 pygobject3 py3cairo libpng jpeg

Testing
=======

Testing requires pytest for Python 3. In some distributions, 'pytest' is for Python 2. Run

    pip3 install pytest

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

    $ pip3 install pylint
    $ ./bin/pylint.sh

 - Using docker (same environment as pipeline):

    $ ./docker/bin/run_lint.sh

Generating Documentation
========================

You can only regenerate the docs if you clone the Gnofract 4D git repo - the source dist packages contain the generated docs but not the input files for the generation process. To regenerate the docs:

1. Make sure you're starting from a git clone not a source .zip - you need the files under manual/content
2. The documentation theme is managed in a separate repository and embedded in manual/themes/book as a submodule. Initialize and update it with `git submodule update --init`
3. Install hugo
    * Ubuntu 18.04 has an older version. Run `snap install hugo --channel=extended` instead of `apt install hugo`
    * For MacOS you can install with `brew install hugo`
4. Run `./createdocs.py`
