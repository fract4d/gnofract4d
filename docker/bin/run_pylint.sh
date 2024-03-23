#!/bin/bash

docker-compose up -d --build
docker-compose exec server bash -c "rm -rf _build"
docker-compose exec server bash -c "meson setup --prefix ~/.local/ _build && \
									meson compile -C _build && \
                                    ./bin/pylint.sh"
docker-compose down
