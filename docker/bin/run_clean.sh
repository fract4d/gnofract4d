#!/bin/bash

docker-compose up -d
docker-compose exec server bash -c "rm -rf _build && \
                                    rm -rf .pytest_cache && \
                                    rm -rf .tox"
docker-compose down
