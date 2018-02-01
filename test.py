#!/usr/bin/env python

# run all the tests
import os
import sys
import unittest
import re
import getopt

from fract4d import options

try:
    # a hack, but seems easy enough
    os.system("cp gnofract4d gnofract4d.py")    
    import gnofract4d
finally:
    os.remove("gnofract4d.py")

print("Running all unit tests. This may take several minutes.")

class Test(unittest.TestCase):
    def testSetupPyVersionMatches(self):
        doc = open("setup.py").read()
        doc_re = re.compile(r"gnofract4d_version = '(\S+)'")
        m = doc_re.search(doc)

        self.assertTrue(m,"setup.py doesn't specify version")
        self.assertEqual(options.version, m.group(1))

    def testDocVersionMatches(self):        
        # check the docs
        doc = open("doc/gnofract4d-manual/C/gnofract4d-manual.xml").read()
        doc_re = re.compile(r'\<\!ENTITY version "(\S+)"\>')

        m = doc_re.search(doc)
        self.assertTrue(m,"doc doesn't specify version")
        self.assertEqual(options.version,m.group(1), "Version mismatch")

    def testWebsiteVersionMatches(self):
        if not os.path.exists("website"):
            # not included in source dist
            return
        mkweb = open("website/mkweb.py").read()
        ver_re = re.compile(r'text="Version (\S+) released.')

        m = ver_re.search(mkweb)
        self.assertTrue(m,"doc doesn't specify version")
        self.assertEqual(options.version,m.group(1), "Version mismatch")

    def testGenerateMandelbrot(self):
        if os.path.exists("test.png"):
            os.remove("test.png")
        try:
            gnofract4d.main(["-s", "test.png", "--width", "24", "-j", "12", "-q"])
            self.assertTrue(os.path.exists("test.png"))
        finally:
            if os.path.exists("test.png"):
                os.remove("test.png")
            

    def testVersionChecks(self):
        self.assertEqual(False, gnofract4d.test_version(2,6,0))
        self.assertEqual(True, gnofract4d.test_version(2,12,0))
        self.assertEqual(True, gnofract4d.test_version(3,0,0))
        
        self.assertEqual(False, gnofract4d.test_version(1,99,0))
        self.assertEqual(False, gnofract4d.test_version(2,0,0))
        self.assertEqual(False, gnofract4d.test_version(2,11,0))
    
def suite():
    return unittest.makeSuite(Test,'test')

def main():        
    os.chdir('fract4d')
    os.system('./test.py')
    os.chdir('../fract4dgui')
    os.system('./test.py')
    os.chdir('../fractutils')
    os.system('./test.py')
    os.chdir('..')

    unittest.main(defaultTest='suite')

    
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--thisonly":
        sys.argv.remove("--thisonly")
        unittest.main(defaultTest='suite')
    else:
        main()

