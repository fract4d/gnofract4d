#!/bin/bash

if ! ls fract4d/fract4dc.*.so 1> /dev/null 2>&1;
then
  ./bin/build.sh
fi

pylint *.py fract4d fract4d_compiler fract4dgui

if [[ $? == 0 ]]
then
  echo "pylint passed successfully"
fi
