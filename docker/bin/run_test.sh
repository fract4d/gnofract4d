#!/bin/bash

docker-compose up -d --build
docker-compose exec server bash -c "rm -rf build"
docker-compose exec server bash -c "python3 setup.py build && \
                                    ./test.py"
docker-compose down
