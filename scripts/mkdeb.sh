#!/bin/bash
make -f debian/rules clean
make -f debian/rules binary
mv ../*.deb dist
pushd dist
mkisofs -J -R -o gf4ddeb.iso *.deb
popd