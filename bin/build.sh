#!/bin/bash

rm -rf _build
meson setup --prefix ~/.local/ _build
meson compile -C _build
