#!/usr/bin/env python3

# test fractmain

import os.path

from . import testbase

from fract4d import fractmain
from fract4d.options import Arguments


class Test(testbase.TestSetup):
    def testBasic(self):
        c = self.userConfig
        fm = fractmain.T(c)
        options = Arguments().parse_args(["--save", "foo.png"])
        fm.run(options)
        self.assertTrue(os.path.exists("foo.png"))
        os.remove("foo.png")

    def testBuildOnly(self):
        c = self.userConfig
        fm = fractmain.T(c)
        options = Arguments().parse_args(["--buildonly", "test.so"])

        fm.run(options)
        self.assertTrue(os.path.exists("test.so"))
        os.remove("test.so")
        if os.path.exists("test.so.c"):
            os.remove("test.so.c")

    def testSinglePoint(self):
        c = self.userConfig
        fm = fractmain.T(c)
        options = Arguments().parse_args(["--singlepoint"])

        fm.run(options)
