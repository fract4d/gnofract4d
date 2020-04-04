docker-compose up -d --build
docker-compose exec server bash -c "rm -rf build && python3 setup.py build && tox"
docker-compose down
