#!/bin/bash

# Weird hack to build separate RPMs for different Python versions, due to
# incompatible Python API formats. (Fsckers).

# if you want to build your own RPM using this script, 
# change the paths to different python versions to something which works for you
# use an pre-g++-3.5 compiler to build binary distributions - 3.5 changes the 
# ABI again (groan) and hardly any of the distributions targeted have it

export ARCH=amd64
#export CC=/usr/local/bin/gcc33
#export CXX=/usr/local/bin/g++33
#
## python 2.2 version
#export BUILD_PYTHON_VERSION=2.2
#export BUILD_PYTHON=/usr/bin/python2.2
#export MIN=2.2
#export MAX=2.3
# 
#./mkrpm.sh $BUILD_PYTHON $MIN $MAX
#mv dist/gnofract4d-3.5-1.$ARCH.rpm dist/gnofract4d-python22-3.5-1.$ARCH.rpm 
#
## Python 2.3 version
#export BUILD_PYTHON_VERSION=2.3
#export BUILD_PYTHON=/usr/bin/python2.3
#export MIN=2.3
#export MAX=2.4
#
#./mkrpm.sh $BUILD_PYTHON $MIN $MAX
#mv dist/gnofract4d-3.5-1.$ARCH.rpm dist/gnofract4d-python23-3.5-1.$ARCH.rpm 
#
## use local gcc for Python 2.4, since that's the best match on my dev machine (FC4)
#export CC=/usr/bin/gcc
#export CXX=/usr/bin/g++

python createdocs.py

# Python 2.5 version
export BUILD_PYTHON_VERSION=2.5
export BUILD_PYTHON=/usr/bin/python2.5
export MIN=2.5
export MAX=2.6

scripts/mkrpm.sh $BUILD_PYTHON $MIN $MAX
mv dist/gnofract4d-3.12-1.$ARCH.rpm dist/gnofract4d-python25-3.12-1.$ARCH.rpm 

# Python 2.4 version
export BUILD_PYTHON_VERSION=2.4
export BUILD_PYTHON=/usr/bin/python2.4
export MIN=2.4
export MAX=2.5

scripts/mkrpm.sh $BUILD_PYTHON $MIN $MAX
mv dist/gnofract4d-3.12-1.$ARCH.rpm dist/gnofract4d-python24-3.12-1.$ARCH.rpm 


unset BUILD_PYTHON_VERSION
unset BUILD_PYTHON

# source version
./setup.py sdist

# .deb package
#make -f debian/rules binary
#mv ../*.deb dist

# make ISO image for testing on different OSes
pushd dist
mkisofs -J -R -o gf4d.iso *3.12*.gz *3.12*.rpm *3.12*.deb
popd dist



