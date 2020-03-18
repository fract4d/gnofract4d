#!/usr/bin/env python3

from buildtools import my_install_lib
from distutils.core import setup, Extension
import distutils.sysconfig
import os
import shutil
import subprocess
import sys

gnofract4d_version = '4.0'

if sys.version_info < (3, 5):
    print("Sorry, you need Python 3.5 or higher to run Gnofract 4D.")
    print("You have version %s. Please upgrade." % sys.version)
    sys.exit(1)

if not os.path.exists(os.path.join(distutils.sysconfig.get_python_inc(), "Python.h")):
    print("Python header files are required.")
    print("Please install libpython3-dev")
    sys.exit(1)

# by default python uses all the args which were used to compile it. But Python is C and some
# extension files are C++, resulting in annoying '-Wstrict-prototypes is not supported' messages.
# tweak the cflags to override
os.environ["CFLAGS"] = distutils.sysconfig.get_config_var(
    "CFLAGS").replace("-Wstrict-prototypes", "")
os.environ["OPT"] = distutils.sysconfig.get_config_var(
    "OPT").replace("-Wstrict-prototypes", "")


# Extensions need to link against appropriate libs
# We use pkg-config to find the appropriate set of includes and libs
def call_package_config(package, option, optional=False):
    '''invoke pkg-config, if it exists, to find the appropriate
    arguments for a library'''
    try:
        cp = subprocess.run(["pkg-config", package, option],
                            universal_newlines=True, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print("Unable to check for %s, pkg-config not installed" %
              package, file=sys.stderr)
        if optional:
            return []
        else:
            sys.exit(1)

    if cp.returncode != 0:
        if optional:
            print("Can't find '%s'" % package, file=sys.stderr)
            print("Some functionality will be disabled", file=sys.stderr)
            return []
        else:
            print("Development files not found for: '%s'." %
                  package, file=sys.stderr)
            sys.exit(1)

    return cp.stdout.split()


png_flags = call_package_config("libpng", "--cflags")
png_libs = call_package_config("libpng", "--libs")

extra_macros = [('PNG_ENABLED', 1)]

jpg_lib = "jpeg"
for path in "/usr/include/jpeglib.h", "/usr/local/include/jpeglib.h":
    if os.path.isfile(path):
        extra_macros.append(('JPG_ENABLED', 1))
        jpg_libs = [jpg_lib]
        break
else:
    raise SystemExit("NO JPEG HEADERS FOUND, you need to install libjpeg-dev")


fract4d_sources = [
    'fract4d/c/fract4dmodule.cpp',

    'fract4d/c/fract4dc/colormaps.cpp',
    'fract4d/c/fract4dc/loaders.cpp',
    'fract4d/c/fract4dc/pysite.cpp',
    'fract4d/c/fract4dc/fdsite.cpp',
    'fract4d/c/fract4dc/sites.cpp',
    'fract4d/c/fract4dc/images.cpp',
    'fract4d/c/fract4dc/calcs.cpp',
    'fract4d/c/fract4dc/workers.cpp',
    'fract4d/c/fract4dc/functions.cpp',
    'fract4d/c/fract4dc/arenas.cpp',
    'fract4d/c/fract4dc/utils.cpp',

    'fract4d/c/cmap.cpp',
    'fract4d/c/pointFunc.cpp',
    'fract4d/c/fractFunc.cpp',
    'fract4d/c/STFractWorker.cpp',
    'fract4d/c/MTFractWorker.cpp',
    'fract4d/c/image.cpp',
    'fract4d/c/imageIO.cpp',
    'fract4d/c/fract_stdlib.cpp'
]

defines = [
    ('_REENTRANT', 1),
    ('THREADS', 1),
    # ('STATIC_CALC',1),
    # ('NO_CALC', 1),  # set this to not calculate the fractal
    # ('DEBUG_CREATION',1), # debug spew for allocation of objects
    # ('DEBUG_ALLOCATION',1), # debug spew for array handling
]

libraries = ['stdc++']
extra_compile_args = ['-Wall', '-O0'] + png_flags
define_macros = defines + extra_macros

module_fract4dc = Extension(
    name='fract4d.fract4dc',
    sources=fract4d_sources,
    include_dirs=['fract4d/c', 'fract4d/c/fract4dc'],
    libraries=libraries + jpg_libs,
    extra_compile_args=extra_compile_args,
    extra_link_args=png_libs,
    define_macros=define_macros,
    #undef_macros = [ 'NDEBUG'],
)

module_cmap = Extension(
    'fract4d.fract4d_stdlib',
    sources=[
        'fract4d/c/cmap.cpp',
        'fract4d/c/image.cpp',
        'fract4d/c/fract_stdlib.cpp'
    ],
    include_dirs=['fract4d/c'],
    libraries=libraries,
    define_macros=[('_REENTRANT', 1)]
)

modules = [module_fract4dc, module_cmap]


def get_files(dir, ext):
    return [os.path.join(dir, x) for x in os.listdir(dir) if x.endswith(ext)]


so_extension = distutils.sysconfig.get_config_var("EXT_SUFFIX")

with open("fract4d/c/cmap_name.h", "w") as fh:
    fh.write("""
#ifndef CMAP_NAME
#define CMAP_NAME "/fract4d_stdlib%s"
#endif
""" % so_extension)

setup(
    name='gnofract4d',
    version=gnofract4d_version,
    description='A program to draw fractals',
    long_description='''Gnofract 4D is a fractal browser. It can generate many different fractals,
including some which are hybrids between the Mandelbrot and Julia sets,
and includes a Fractint-compatible parser for your own fractal formulas.''',
    author='Edwin Young',
    author_email='edwin@bathysphere.org',
    maintainer='Edwin Young',
    maintainer_email='edwin@bathysphere.org',
    keywords="edwin@bathysphere.org",
    url='http://github.com/edyoung/gnofract4d/',
    packages=['fract4d_compiler', 'fract4d', 'fract4dgui'],
    package_data={'fract4dgui': ['shortcuts-gnofract4d.ui', 'ui.xml']},
    ext_modules=modules,
    scripts=['gnofract4d'],
    data_files=[
        # style CSS
        ('share/gnofract4d', ['gnofract4d.css']),
        # color maps
        (
            'share/gnofract4d/maps',
            get_files("maps", ".map") +
            get_files("maps", ".cs") +
            get_files("maps", ".ugr")
        ),
        # formulas
        (
            'share/gnofract4d/formulas',
            get_files("formulas", "frm") +
            get_files("formulas", "ucl") +
            get_files("formulas", "uxf")
        ),
        # documentation
        (
            'share/gnome/help/gnofract4d/C',
            get_files("doc/gnofract4d-manual/C", "xml")
        ),
        (
            'share/gnome/help/gnofract4d/C/figures',
            get_files("doc/gnofract4d-manual/C/figures", ".png")
        ),
        (
            'share/gnome/help/gnofract4d/C',
            get_files("doc/gnofract4d-manual/C", "html")
        ),
        (
            'share/gnome/help/gnofract4d/C',
            get_files("doc/gnofract4d-manual/C", ".css")
        ),
        # internal pixmaps
        (
            'share/gnofract4d/pixmaps',
            [
                'pixmaps/improve_now.png',
                'pixmaps/explorer_mode.png',
                'pixmaps/mail-forward.png',
                'pixmaps/draw-brush.png',
                'pixmaps/face-sad.png',
                'pixmaps/autozoom.png',
                'pixmaps/randomize_colors.png'
            ]
        ),
        # icon
        ('share/pixmaps', ['pixmaps/gnofract4d-logo.png']),
        # .desktop file
        ('share/applications', ['gnofract4d.desktop']),
        # MIME type registration
        ('share/mime/packages', ['gnofract4d-mime.xml']),
        # doc files
        ('share/doc/gnofract4d/', ['COPYING', 'README.md']),
    ],
    cmdclass={
        "install_lib": my_install_lib.my_install_lib
    }
)

# I need to find the file I just built and copy it up out of the build
# location so it's possible to run without installing. Can't find a good
# way to extract the actual target directory out of distutils, hence
# this egregious hack

lib_targets = {
    "fract4dc" + so_extension: "fract4d",
    "fract4d_stdlib" + so_extension: "fract4d",
}


def copy_libs(root, dirlist, namelist):
    for name in namelist:
        target = lib_targets.get(name)
        if target is not None:
            shutil.copy(os.path.join(root, name), target)


for root, dirs, files in os.walk("build"):
    copy_libs(root, dirs, files)
