#!/bin/bash

docker-compose up -d --build
docker-compose exec server bash -c "rm -rf build && \
                                    rm fract4d/*.so"
docker-compose exec server bash -c "python3 setup.py build && \
                                    ./bin/pylint.sh"
docker-compose down
