#!/usr/bin/env python

import unittest

#import test_makemap
#import test_flickr
import test_slave

def suite():
    tests = (
        #test_makemap.suite(),
        #test_flickr.suite(), #not yet universally-runnable 
        test_slave.suite(),
        )
    return unittest.TestSuite(tests)

def main():
    unittest.main(defaultTest='suite')
    
def profile():
    import hotshot
    prof = hotshot.Profile("makemap.prof")
    prof.runcall(main)
    prof.close()

if __name__ == '__main__':    
    main()

