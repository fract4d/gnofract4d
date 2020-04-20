#!/usr/bin/env python3

import os
import sys
project_path = os.path.dirname(os.path.abspath(__file__)) + '/../..'
sys.path.insert(0, project_path)

from fract4d_compiler import fc
from fract4d import fractconfig, fract4dc, image
from fract4d.tests.fractalsite import FractalSite

# 1st get the userConfig (containing compiler flags based on the platform among other things)
userConfig = fractconfig.userConfig()

# 2nd create the compiler instance with the config got from above
compiler = fc.Compiler(userConfig)

# 3rd compile the formula with the inside and outside color transfer algorithms
formula = compiler.get_formula("gf4d.frm", "Mandelbrot")
inside_transfer = compiler.get_formula("gf4d.cfrm", "zero", "cf1")
outside_transfer = compiler.get_formula("gf4d.cfrm", "continuous_potential", "cf0")
compiled_library = compiler.compile_all(formula, outside_transfer, inside_transfer, [])

# 4th get the formula and transfer algorithms params in a single list
formula_and_transfer_params = formula.symbols.default_params() + \
                            outside_transfer.symbols.default_params() + \
                            inside_transfer.symbols.default_params()

# 5th stablish the location params aka the perspective form which you view the fractal
location_params = [
    0.0, 0.0, 0.0, 0.0, # X Y Z W
    4.0, # Size or zoom
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0 # XY XZ XW YZ YW ZW planes (4D stuff)
]

# 6th create a controller: this one handles the calculation process and informs about progress
controller = fract4dc.create_controller(compiled_library, formula_and_transfer_params, location_params)

# 7th create a message handler to receive updates from controller
message_handler = FractalSite()
controller.set_message_handler(message_handler)

# 8th create a color map to convert point fates (iterations needed to determine if the point scapes) into colors
color_map = fract4dc.cmap_create(
    [
        (0.0, 0, 0, 0, 255),
        (1 / 256.0, 255, 255, 255, 255),
        (1.0, 255, 255, 255, 255)
    ]
)

# 9th create an image: this one will hold the final result and provide utilities to save it into a file
im = image.T(640, 480)

# 10th launch the calculation process through the controller
# there's some additional params taking default values here, like asynchronous, tolerance ...
controller.start_calculating(
    params=location_params,
    antialias=0,
    maxiter=100,
    yflip=0,
    nthreads=1,
    cmap=color_map,
    auto_deepen=0,
    periodicity=1,
    render_type=0,
    image=im._img,
)

# 11th the the job is done and save the image
if (message_handler.status_list[-1] == 0):
    im.save("examples/output/mandelbrot.png")
else:
    print("something went wrong")