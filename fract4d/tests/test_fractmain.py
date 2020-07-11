#!/usr/bin/env python3

# test configuration file parsing

import os.path

from . import testbase

from fract4d import fractmain
from fract4d.options import Arguments


class Test(testbase.TestSetup):
    def testBasic(self):
        c = self.userConfig
        fm = fractmain.T(c)
        options = Arguments().parse_args(["--nogui"])
        fm.run(options)
