#!/bin/bash

pylint3 --rcfile pylintrc *.py gnofract4d fract4d fract4d_compiler fract4dgui
if [[ $? > 0 ]]
then
  exit 1
fi

pylint3 --rcfile pylintrc_new fract4d/fract4d_new
if [[ $? > 0 ]]
then
  exit 1
fi

echo "pylint passed successfully"
