# EXAMPLES

*Note: for all exmples make sure you have performed the setup previously:*
```
./setup.py build
```

## Python examples
### Creating a simple mandelbrot using fract4dc.controller

Execute:
```
examples/python/simple_mandelbrot.py
```
Then  you should see a new file `simple_mandelbrot.png` in the project root folder.


## C++ examples
### Creating a simple mandelbrot

For these examples you'll need [docker](https://docs.docker.com/get-docker/)

Execute:
```
./gnofract4d --nogui --buildonly mandelbrot -f gf4d.frm#Mandelbrot
docker build . -f examples/cpp/Dockerfile -t simple_mandelbrot:1.0.0
docker run --rm -it simple_mandelbrot:1.0.0
```
The resulting file is created inside the container. You can can copy using `docker cp` for example.