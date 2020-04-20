#!/bin/bash

docker-compose up -d
docker-compose exec server bash -c "rm -rf build && \
                                    rm fract4d/*.so && \
                                    rm -rf .pytest_cache && \
                                    rm -rf .tox"
docker-compose down
