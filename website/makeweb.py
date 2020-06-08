#!/usr/bin/env python3

# Update the website. The contents of /docs are the website -
# these are displayed as https://fract4d.github.io/gnofract4d

# this directory contains the Hugo input files which generate the website,
# except the manual, which is a separate Hugo project read from /manual.
# We generate that again because we want a different baseURL from when we install it

import subprocess
import os

myenv = os.environ.copy()
myenv["HUGO_PARAMS_StyleBase"] = 'https://fract4d.github.io'

# update the manual
subprocess.run(
    ["hugo", "-b", "https://fract4d.github.io/gnofract4d/manual", "-d", "../docs/manual"],
    cwd="../manual",
    env=myenv)

subprocess.run(
    ["hugo", "-b", "https://fract4d.github.io/gnofract4d/", "-d", "../docs"]
)
