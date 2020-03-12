#!/bin/sh
pylint \
  -d all \
  -e bad-whitespace, \
     trailing-whitespace, \
     bad-indentation, \
     wrong-import-position, \
     unnecessary-semicolon, \
     trailing-newlines, \
     bare-except \
  -s n \
  fract4d fract4d_compiler fract4dgui
