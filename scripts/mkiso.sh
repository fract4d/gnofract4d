#!/bin/bash
pushd dist
mkisofs -J -R -o gf4d.iso *.gz *.deb
popd dist
