![Gnofract 4d](./gnofract-4d.png)

A program for drawing beautiful mathematically-based images known as fractals.

---

## Basic installation

### General instructions & dependencies

First step is to compile the program by running:

```
./setup.py build
```

Then you can install it with:

```
./setup.py install
```

Or you can just run Gnofract 4D on your local directory with:

```
./gnofract4d
```

To compile, you will need Python 3.5 or higher, a C++ compiler such as g++, and header files for GTK3 and Python. Headers for Jpeglib and libpng are optional, but highly recommended - without them you can only use the extremely basic TGA file format.

At runtime, you will need PyGTK 3, and a C compiler (because that gets invoked to compile the fractal formula you have written).

Alternatively, you can download the [lastest version](https://github.com/fract4d/gnofract4d/releases) of the program and install it with `pip` running:

```
pip3 install gnofract4d-4.3.tar.gz
```

When the installation ends just run it by clicking on the desktop icon or typing:

```
gnofract4d
```

### Install on Ubuntu 15.04

Before running `./setup.py build` you have to install `python-dev`.

Either find it in synaptic, or run `sudo apt-get install python-dev` from the command line.

### Install on Ubuntu 16.04 and later supported releases

You can install pre-build packages from this [PPA](https://launchpad.net/~renbag/+archive/ubuntu/gnofract4d) following the instructions given there.

## Documentation

For more details you can visit the [website](https://fract4d.github.io/gnofract4d).

There you will find two manuals, one focused on basic users and other for developers.
