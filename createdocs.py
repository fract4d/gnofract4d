#!/usr/bin/env python3

# Used to generate the documentation, in 2 phases:
# 1) run python script to list all the functions in the standard library
# 2) invoke Hugo static file generator to create HTML docs which are written to manual/public

# This is a separate step from the normal build because not everyone will want to
# install those tools. The 'sdist' packages (gnofract4d-4.2.zip etc) contain the output from this step
# but not all the input. To build the docs you need to clone the git repo

import subprocess

# create list of stdlib functions
from fract4d import createdocs as cd1
cd1.main("manual/content/stdlib.html")

print("Generating docs")
result = subprocess.run(
    ["hugo", "-b", ""],
    cwd="manual",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)

if result.returncode != 0:
    raise RuntimeError("Error generating docs: %d\nStderr\n%s\nStdout\n%s" %
        (result.returncode, result.stderr.decode('utf8'), result.stdout.decode('utf8')))