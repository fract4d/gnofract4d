#!/usr/bin/env python3

# run this to update some tables in the documentation

# making this a separate cmd (not part of setup.py) because importing
# gtk was causing "setup.py build" to crash - inexplicable...

# also the other python versions don't have gtk as a module,
# so were reporting errors.

import sys
import os
import re

def create_stdlib_docs():
    'Autogenerate docs'
    try:
        # create list of stdlib functions
        from fract4d import createdocs as cd1
        cd1.main("manual/content/stdlib.html")

        # create list of mouse and GUI commands
        import fract4dgui.createdocs
        fract4dgui.createdocs.main("manual/content/commands.html")  # pylint: disable=no-value-for-parameter


    except Exception as err:
        print("Problem creating docs. Online help will be incomplete.", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

create_stdlib_docs()
insert_docs("doc/manual.md","doc/fuil-manual.md")