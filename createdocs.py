#!/usr/bin/env python3

# run this to update some tables in the documentation

# making this a separate cmd (not part of setup.py) because importing
# gtk was causing "setup.py build" to crash - inexplicable...

# also the other python versions don't have gtk as a module,
# so were reporting errors.

import sys
import os

def create_stdlib_docs():
    'Autogenerate docs'
    try:
        # create list of stdlib functions
        from fract4d import createdocs as cd1
        cd1.main("doc/gnofract4d-manual/C/stdlib.xml")

        # create list of mouse and GUI commands
        import fract4dgui.createdocs
        fract4dgui.createdocs.main("doc/gnofract4d-manual/C/commands.xml")

        # create HTML version of docs for them as don't have yelp
        os.chdir("doc/gnofract4d-manual/C")        
        retval = os.system("xsltproc --nonet --output gnofract4d-manual.html --stringparam html.stylesheet docbook.css gnofract4d.xsl gnofract4d-manual.xml")
        if retval != 0:
            raise Exception("error processing xslt")
    except Exception as err:
        print("Problem creating docs. Online help will be incomplete.", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

create_stdlib_docs()
