#!/usr/bin/env python

import unittest
import string
import commands
import re
import os
import time
import cPickle

import testbase

import cache


class Test(testbase.TestBase):
    def setUp(self):
        pass
        
    def tearDown(self):
        if os.path.exists("experiment"):
            for f in os.listdir("experiment"):
                os.remove("experiment/" + f)
            os.rmdir("experiment")

    def testCacheCreation(self):
        c = cache.T()
        self.assertEqual(
            os.path.expandvars("${HOME}/.gnofract4d-cache"), c.dir)
        self.assertEqual({},c.files)

        c = cache.T("experiment")
        self.assertEqual("experiment",c.dir)

        self.assertEqual(False,os.path.exists("experiment"))
        
        c.init()
        self.failUnless(os.path.isdir("experiment"))

        f = open("experiment/file1.txt","w")
        f.close()
        self.failUnless(os.path.exists("experiment/file1.txt"))

        c.clear()
        self.assertEqual(False, os.path.exists("experiment/file1.txt"))

    def testMakeFilename(self):
        c = cache.T("foo")
        self.assertEqual("foo/fract4d_blah.x", c.makefilename("blah",".x"))

    def readall(self,file):
        self.readall_called = True
        return file.read()

    def testAddFile(self):
        c = cache.T("experiment")
        c.init()
        f = open("experiment/file1.txt","w").write("fish")

        self.readall_called = False
        
        contents = c.getcontents("experiment/file1.txt", self.readall)        
        self.assertEqual("fish",contents)
        self.failUnless(self.readall_called, "Should have called readall")

        self.readall_called = False
        contents = c.getcontents("experiment/file1.txt", self.readall)
        self.assertEqual("fish",contents)
        self.failUnless(
            not self.readall_called, "Should not have called readall")

    def testUpdateFileOnDisk(self):
        c = cache.T("experiment")
        c.init()
        f = open("experiment/file1.txt","w").write("fish")

        self.readall_called = False
        
        contents = c.getcontents("experiment/file1.txt", self.readall)        
        self.assertEqual("fish",contents)
        self.failUnless(self.readall_called, "Should have called readall")

        self.readall_called = False
        time.sleep(1.0) # ensure filesystem will have a different time
        
        open("experiment/file1.txt","w").write("wibble")

        contents = c.getcontents("experiment/file1.txt", self.readall)
        self.assertEqual("wibble",contents)
        self.failUnless(
            self.readall_called, "Should have called readall")

    def disabled_testPickleFile(self):
        c = cache.T("experiment")
        c.init()
        f = open("experiment/file1.txt","w").write("fish")

        contents = c.getcontents("experiment/file1.txt", self.readall)        
        self.assertEqual(
            "experiment/0de8fb66544e4ae95935a50ab783fdba.pkl",
            c.files["experiment/file1.txt"].cache_file)
        self.failUnless(
            os.path.exists("experiment/0de8fb66544e4ae95935a50ab783fdba.pkl"),
            "no pickled file found")
        val = cPickle.load(open("experiment/0de8fb66544e4ae95935a50ab783fdba.pkl"))
        self.assertEqual(contents, val)

        c.save()

        c2 = cache.T("experiment")
        c2.init()
        self.readall_called = False
        contents2 = c2.getcontents("experiment/file1.txt", self.readall)        

        self.assertEqual(False, self.readall_called)
        self.assertEqual(contents,contents2)
        
        
    def testHashCode(self):
        c = cache.T("experiment")
        c.init()
        self.assertEqual("acbd18db4cc2f85cedef654fccc4a4d8", c.hashcode("foo"))
        self.assertEqual(
            "b34231a85737d0b078d7ffb17e6bb3b5",c.hashcode("foo","flag"))
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

