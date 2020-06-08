#!/bin/sh
/usr/bin/time -f "%Uuser %Ssystem %Eelapsed %PCPU (%Xtext+%Ddata %Mmax)k" ./gnofract4d -q -P testdata/valley_test.fct
