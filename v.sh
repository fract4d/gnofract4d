#!/bin/sh
/usr/bin/time -f "%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k" ./gnofract4d -q -p testdata/valley_test.fct
