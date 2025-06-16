#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
import unittest

import pytest


class Test(unittest.TestCase):
    @pytest.mark.skipif(os.path.expandvars("${HOME}") == "${HOME}",
                        reason="cache_dir requires $HOME to be set")
    def testGenerateMandelbrot(self):
        with tempfile.TemporaryDirectory(prefix="fract4d_") as tmpdir:
            test_file = os.path.join(tmpdir, "test.png")
            subprocess.run([
                os.path.join(os.path.dirname(sys.modules[__name__].__file__),
                             "gnofract4d"), "--nogui", "-s", test_file,
                "--width", "24", "-j", "12", "-q"], check=True)
            self.assertTrue(os.path.exists(test_file))


def suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(Test)


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
