#!/usr/bin/env python3

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
os.environ["CFLAGS"] = distutils.sysconfig.get_config_var("CFLAGS").replace("-Wstrict-prototypes","")
os.environ["OPT"] = distutils.sysconfig.get_config_var("OPT").replace("-Wstrict-prototypes","")

from buildtools import my_install_lib

# Extensions need to link against appropriate libs
# We use pkg-config to find the appropriate set of includes and libs

def call_package_config(package,option,optional=False):
    '''invoke pkg-config, if it exists, to find the appropriate
    arguments for a library'''
    try:
        cp = subprocess.run(["pkg-config", package, option],
                            universal_newlines=True, stdout=subprocess.PIPE)
    except FileNotFoundError:
        print("Unable to check for %s, pkg-config not installed" % package, file=sys.stderr)
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
            print("Development files not found for: '%s'." % package, file=sys.stderr)
            sys.exit(1)

    return cp.stdout.split()

extra_macros = []

png_flags = call_package_config("libpng", "--cflags")
png_libs = call_package_config("libpng", "--libs")
extra_macros.append(('PNG_ENABLED', 1))

jpg_lib = "jpeg"
for path in "/usr/include/jpeglib.h", "/usr/local/include/jpeglib.h":
    if os.path.isfile(path):
        extra_macros.append(('JPG_ENABLED', 1))
        jpg_libs = [ jpg_lib ]
        break
else:
    raise SystemExit("NO JPEG HEADERS FOUND, you need to install libjpeg-dev")

# not ready yet.
have_gmp = False # os.path.isfile("/usr/include/gmp.h")

# use currently specified compilers, not ones from when Python was compiled
# this is necessary for cross-compilation
compiler = os.environ.get("CC","gcc")
cxxcompiler = os.environ.get("CXX","g++")

fract4d_sources = [
    'fract4d/c/fract4dmodule.cpp',
    'fract4d/c/cmap.cpp',
    'fract4d/c/pointFunc.cpp',
    'fract4d/c/fractFunc.cpp',
    'fract4d/c/STFractWorker.cpp',
    'fract4d/c/MTFractWorker.cpp',
    'fract4d/c/image.cpp',
    'fract4d/c/imageIO.cpp',
    'fract4d/c/fract_stdlib.cpp'
    ]

# this is a hack to build 2 versions of the same extension.
# we want to create a standard fract4dc which doesn't depend on gmp
# and a second fract4dcgmp which does. These are both built from the
# same source files but in the latter case with USE_GMP defined
# This is so I can ship a single binary for gnofract4d which supports
# both users with GMP and users without it, by conditionally loading
# the appropriate extension
fract4d_gmp_sources = []
if have_gmp:
    for sourcefile in fract4d_sources:
        # this particular part of the hack is so that each file gets
        # compiled twice
        gmp_sourcefile = sourcefile.replace(".cpp","_gmp.cpp")
        os.system("cp %s %s" % (sourcefile, gmp_sourcefile))
        fract4d_gmp_sources.append(gmp_sourcefile)

module_gmp = Extension(
    'fract4d.gmpy',
    sources = [
    'fract4d/gmpy/gmpy.c'
    ],
    libraries = ['gmp']
    )

defines = [ ('_REENTRANT',1),
            ('THREADS',1),
            #('STATIC_CALC',1),
            #('NO_CALC', 1),  # set this to not calculate the fractal
            #('DEBUG_CREATION',1), # debug spew for allocation of objects
            #('DEBUG_ALLOCATION',1), # debug spew for array handling
            ]

module_fract4dgmp = Extension(
    'fract4d.fract4dcgmp',
    sources = fract4d_gmp_sources,
    include_dirs = [
    'fract4d/c'
    ],
    libraries = [
    'stdc++', 'gmp'
    ] + jpg_libs,
    extra_compile_args = [
    '-Wall',
    ] + png_flags,
    extra_link_args = png_libs,
    define_macros = defines + [('USE_GMP',1)] + extra_macros,
    undef_macros = ['NDEBUG']
    )

warnings = '-Wall'
libs = [ 'stdc++' ]
osdep = []
extra_source = []
extra_link = []

fract4d_sources += extra_source

module_fract4dc = Extension(
    'fract4d.fract4dc',
    sources = fract4d_sources,
    include_dirs = [
    'fract4d/c'
    ],
    libraries = libs + jpg_libs,
    extra_compile_args = [
    warnings, '-O0'
    ] + osdep + png_flags,
    extra_link_args = extra_link + png_libs,
    define_macros = defines + extra_macros,
    #undef_macros = [ 'NDEBUG'],
    )

module_cmap = Extension(
    'fract4d.fract4d_stdlib',
    sources = [
    'fract4d/c/cmap.cpp',
    'fract4d/c/image.cpp',
    'fract4d/c/fract_stdlib.cpp'
    ] + extra_source,
    include_dirs = [
    'fract4d/c'
    ],
    libraries = libs,
    extra_link_args = extra_link,
    define_macros = [('_REENTRANT', 1)]
    )

modules = [module_fract4dc, module_cmap]
if have_gmp:
    modules.append(module_fract4dgmp)
    modules.append(module_gmp)

def get_files(dir,ext):
    return [os.path.join(dir,x) for x in os.listdir(dir) if x.endswith(ext)]

so_extension = distutils.sysconfig.get_config_var("EXT_SUFFIX")

with open("fract4d/c/cmap_name.h", "w") as fh:
    fh.write("""
#ifndef CMAP_NAME
#define CMAP_NAME "/fract4d_stdlib%s"
#endif
""" % so_extension)

setup (name = 'gnofract4d',
       version = gnofract4d_version,
       description = 'A program to draw fractals',
       long_description =
'''Gnofract 4D is a fractal browser. It can generate many different fractals, 
including some which are hybrids between the Mandelbrot and Julia sets,
and includes a Fractint-compatible parser for your own fractal formulas.''',
       author = 'Edwin Young',
       author_email = 'edwin@bathysphere.org',
       maintainer = 'Edwin Young',
       maintainer_email = 'edwin@bathysphere.org',
       keywords = "edwin@bathysphere.org",
       url = 'http://github.com/edyoung/gnofract4d/',
       packages = ['fract4d', 'fract4dgui'],
       package_data = { 'fract4dgui' : [ 'shortcuts-gnofract4d.ui', 'ui.xml'] },
       ext_modules = modules,
       scripts = ['gnofract4d'],
       data_files = [
           # style CSS
           ('share/gnofract4d',
            ['gnofract4d.css']),
           # color maps
           ('share/gnofract4d/maps',
            get_files("maps",".map") +
            get_files("maps",".cs") +
            get_files("maps", ".ugr")),

           # formulas
           ('share/gnofract4d/formulas',
            get_files("formulas","frm") +
            get_files("formulas", "ucl") +
            get_files("formulas", "uxf")),

           # documentation
           ('share/gnome/help/gnofract4d/C',
            get_files("doc/gnofract4d-manual/C", "xml")),
           ('share/gnome/help/gnofract4d/C/figures',
            get_files("doc/gnofract4d-manual/C/figures",".png")),
           ('share/gnome/help/gnofract4d/C',
            get_files("doc/gnofract4d-manual/C", "html")),
           ('share/gnome/help/gnofract4d/C',
            get_files("doc/gnofract4d-manual/C",".css")),

           # internal pixmaps
           ('share/gnofract4d/pixmaps',
            ['pixmaps/improve_now.png',
             'pixmaps/explorer_mode.png',
             'pixmaps/mail-forward.png',
             'pixmaps/draw-brush.png',
             'pixmaps/face-sad.png',
             'pixmaps/autozoom.png',
             'pixmaps/randomize_colors.png']),

           # icon
           ('share/pixmaps',
            ['pixmaps/gnofract4d-logo.png']),

           # .desktop file
           ('share/applications', ['gnofract4d.desktop']),

           # MIME type registration
           ('share/mime/packages', ['gnofract4d-mime.xml']),

           # doc files
           ('share/doc/gnofract4d/',
            ['COPYING', 'README']),
           ],
       cmdclass={
           "install_lib" : my_install_lib.my_install_lib
           }
       )

# I need to find the file I just built and copy it up out of the build
# location so it's possible to run without installing. Can't find a good
# way to extract the actual target directory out of distutils, hence
# this egregious hack

lib_targets = {
    "fract4dc" + so_extension : "fract4d",
    "fract4d_stdlib" + so_extension : "fract4d",
    "fract4dcgmp" + so_extension : "fract4d",
    "gmpy" + so_extension: "fract4d"
    }

def copy_libs(root, dirlist, namelist):
    for name in namelist:
        target = lib_targets.get(name)
        if target is not None:
            shutil.copy(os.path.join(root, name), target)

for root, dirs, files in os.walk("build"):
    copy_libs(root, dirs, files)
