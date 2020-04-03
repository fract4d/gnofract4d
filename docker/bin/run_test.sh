docker-compose up -d --build
# docker-compose exec server bash -c "pytest -s test.py::Test::testGenerateMandelbrot"
docker-compose exec server bash -c "rm -rf build && python3 setup.py build && ./test.py"
docker-compose down
