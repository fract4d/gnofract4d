#!/usr/bin/env python

# run all the tests
import os
import subprocess
import sys
import tempfile
import unittest
import re

from fract4d import options

print("Running all unit tests. This may take several minutes.")

class Test(unittest.TestCase):
    def testSetupPyVersionMatches(self):
        doc = Path("setup.py").read_text()
        doc_re = re.compile(r"gnofract4d_version = '(\S+)'")
        m = doc_re.search(doc)

        self.assertTrue(m,"setup.py doesn't specify version")
        self.assertEqual(options.VERSION, m.group(1))

    def testDocVersionMatches(self):
        # check the docs
        doc = Path("doc/gnofract4d-manual/C/gnofract4d-manual.xml").read_text()
        doc_re = re.compile(r'\<\!ENTITY version "(\S+)"\>')

        m = doc_re.search(doc)
        self.assertTrue(m,"doc doesn't specify version")
        self.assertEqual(options.VERSION,m.group(1), "Version mismatch")

    def testWebsiteVersionMatches(self):
        if not os.path.exists("website"):
            # not included in source dist
            return
        mkweb = Path("website/mkweb.py").read_text()
        ver_re = re.compile(r'text="Version (\S+) released.')

        m = ver_re.search(mkweb)
        self.assertTrue(m,"doc doesn't specify version")
        self.assertEqual(options.VERSION,m.group(1), "Version mismatch")

    def testGenerateMandelbrot(self):
        with tempfile.TemporaryDirectory(prefix="fract4d_") as tmpdir:
            test_file = os.path.join(tmpdir, "test.png")
            subprocess.run(["./gnofract4d", "--nogui", "-s", test_file,
                            "--width", "24", "-j", "12", "-q"], check=True)
            self.assertTrue(os.path.exists(test_file))


def suite():
    return unittest.makeSuite(Test,'test')

def main():
    os.chdir('fract4d')
    os.system('./test.py')
    os.chdir('../fract4dgui')
    os.system('./test.py')
    os.chdir('..')

    unittest.main(defaultTest='suite')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--thisonly":
        sys.argv.remove("--thisonly")
        unittest.main(defaultTest='suite')
    else:
        main()
