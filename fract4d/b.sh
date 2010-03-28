#!/bin/bash
pushd ..
rm -rf build
./setup.py build
popd
