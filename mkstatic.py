#!/usr/bin/env python

# gettext
import gettext
os.environ.setdefault('LANG', 'en')
if os.path.isdir('po'):
    gettext.install('gnofract4d','po')
else:
    gettext.install('gnofract4d')

# nogui modules
from fract4d import fractal, fractmain, options

def main(args):
    opts = options.T()
    try:
        opts.parse(args)
    except options.OptionError as err:
        print(get_version_info())
        print(opts.help())

        print("Error parsing arguments: %s" % err)
        return 1

    t = fractmain.T()
    
