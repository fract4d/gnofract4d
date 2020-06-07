#!/bin/bash

if [ -x "$(command -v pylint3)" ]; then
  PYLINT=pylint3
else
  PLYINT=pylint
fi

$PYLINT --rcfile pylintrc *.py gnofract4d fract4d fract4d_compiler fract4dgui
if [[ $? > 0 ]]
then
  exit 1
fi

$PYLINT --rcfile pylintrc_new fract4d/fract4d_new
if [[ $? > 0 ]]
then
  exit 1
fi

echo "pylint passed successfully"
