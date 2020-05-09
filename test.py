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
    def testSetupPyVersionMatches(self):
        doc = open("setup.py")
        content = doc.read()
        doc.close()
        doc_re = re.compile(r"gnofract4d_version = '(\S+)'")
        m = doc_re.search(content)

        self.assertTrue(m, "setup.py doesn't specify version")
        self.assertEqual(options.VERSION, m.group(1))

    def testDocVersionMatches(self):
        # check the docs
        doc = open("doc/gnofract4d-manual/C/gnofract4d-manual.xml")
        content = doc.read()
        doc.close()
        doc_re = re.compile(r'\<\!ENTITY version "(\S+)"\>')

        m = doc_re.search(content)
        self.assertTrue(m, "doc doesn't specify version")
        self.assertEqual(options.VERSION, m.group(1), "Version mismatch")

    def testWebsiteVersionMatches(self):
        if not os.path.exists("website"):
            # not included in source dist
            return
        mkweb = open("website/content/_index.md")
        content = mkweb.read()
        mkweb.close()
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
    return unittest.makeSuite(Test, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
