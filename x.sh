#!/bin/sh
/usr/bin/time -f "%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k" ./gnofract4d -i 640 -j 480 -q testdata/param.fct
