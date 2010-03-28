#!/bin/sh
cp ~/gnofract4d/doc/gnofract4d-manual/C/*.xml .
cp ~/gnofract4d/doc/gnofract4d-manual/C/figures/*.png manual/figures
pushd in/manual
xsltproc --param use.id.as.filename 1 ../../gnofract4d.xsl ../../gnofract4d-manual.xml
popd
