#!/bin/bash

pylint *.py fract4d fract4d_compiler fract4dgui

if [[ $? == 0 ]]
then
  echo "pylint passed successfully"
else
  exit 1
fi
