#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import tempfile
import unittest

import pytest

from fract4d import options


class Test(unittest.TestCase):
    def testDocVersionMatches(self):
        # check the docs
        with open("manual/config.toml") as doc:
            content = doc.read()

        ver_re = re.compile(r'version = "(\S+)"')

        m = ver_re.search(content)
        self.assertTrue(m, "manual doesn't specify version")
        self.assertEqual(options.VERSION, m.group(1), "Version mismatch")

    def testWebsiteVersionMatches(self):
        if not os.path.exists("website"):
            # not included in source dist
            return

        with open("website/content/_index.md") as doc:
            content = doc.read()

        ver_re = re.compile(r'latest: "(\S+)"')

        m = ver_re.search(content)
        self.assertTrue(m, "doc doesn't specify version")
        self.assertEqual(options.VERSION, m.group(1), "Version mismatch")

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
