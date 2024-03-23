#!/bin/bash

docker-compose up -d --build
docker-compose exec server bash -c "rm -rf build"
docker-compose exec server bash -c "meson setup --prefix ~/.local/ _build && \
									meson compile -C _build && \
                                    tox"
docker-compose down
