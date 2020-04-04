#!/usr/bin/env python

import os
import sys
import gettext

from fract4d import fractal, fractmain, fractconfig
from fract4d.options import Arguments


os.environ.setdefault('LANG', 'en')
if os.path.isdir('po'):
    gettext.install('gnofract4d', 'po')
else:
    gettext.install('gnofract4d')


def main(args):
    opts = Arguments()
    try:
        opts.parse_args(args)
    except SystemExit as err:
        print("Error parsing arguments: %s" % ', '.join(args))
        return 1

    userConfig = fractconfig.userConfig()
    t = fractmain.T(userConfig)

if __name__ == '__main__':
    main(sys.argv[1:])
