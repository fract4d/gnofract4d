#!/usr/bin/env python3

import os.path
from pathlib import Path
import time
import pickle

from fract4d import fractconfig
from fract4d.tests import testbase

from fract4d_compiler import cache


class Test(testbase.TestSetup):
    def setUp(self):
        super().setUp()
        self.cache_dir = os.path.join(self.tmpdir.name, "experiment")

    def testCacheCreation(self):
        c = cache.T(fractconfig.T("").get("general","cache_dir"))
        self.assertEqual(
            os.path.expandvars("${HOME}/.gnofract4d-cache"), c.dir)
        self.assertEqual({},c.files)

        c = cache.T(self.cache_dir)
        self.assertEqual(self.cache_dir,c.dir)

        self.assertEqual(False,os.path.exists(self.cache_dir))

        c.init()
        self.assertTrue(os.path.isdir(self.cache_dir))

        file1_name = os.path.join(self.cache_dir, "file1.txt")
        f = open(file1_name,"w")
        f.close()
        self.assertTrue(os.path.exists(file1_name))

        c.clear()
        self.assertEqual(False, os.path.exists(file1_name))

    def testMakeFilename(self):
        c = cache.T(self.cache_dir)
        c.init()
        self.assertEqual(os.path.join(self.cache_dir, "fract4d_blah.x"),
            c.makefilename("blah",".x"))

    def readall(self,file):
        self.readall_called = True
        return file.read()

    def testAddFile(self):
        c = cache.T(self.cache_dir)
        c.init()
        file1_name = os.path.join(self.tmpdir.name, "file1.txt")
        with open(file1_name,"w") as f:
            f.write("fish")
        self.readall_called = False

        contents = c.getcontents(file1_name, self.readall)
        self.assertEqual("fish",contents)
        self.assertTrue(self.readall_called, "Should have called readall")

        self.readall_called = False
        contents = c.getcontents(file1_name, self.readall)
        self.assertEqual("fish",contents)
        self.assertTrue(
            not self.readall_called, "Should not have called readall")

    def testUpdateFileOnDisk(self):
        c = cache.T(self.cache_dir)
        c.init()
        file1_name = os.path.join(self.tmpdir.name, "file1.txt")
        with open(file1_name,"w") as f:
            f.write("fish")

        self.readall_called = False

        contents = c.getcontents(file1_name, self.readall)
        self.assertEqual("fish",contents)
        self.assertTrue(self.readall_called, "Should have called readall")

        self.readall_called = False
        time.sleep(1.0) # ensure filesystem will have a different time

        with open(file1_name,"w") as f:
            f.write("wibble")

        contents = c.getcontents(file1_name, self.readall)
        self.assertEqual("wibble",contents)
        self.assertTrue(
            self.readall_called, "Should have called readall")

    def disabled_testPickleFile(self):
        c = cache.T(self.cache_dir)
        c.init()
        file1_name = os.path.join(self.tmpdir.name, "file1.txt")
        with open(file1_name,"w") as f:
            f.write("fish")

        contents = c.getcontents(file1_name, self.readall)
        pkl_name = os.path.join(self.cache_dir, "0de8fb66544e4ae95935a50ab783fdba.pkl")
        self.assertEqual(
            pkl_name,
            c.files[file1_name].cache_file)
        self.assertTrue(
            os.path.exists(pkl_name),
            "no pickled file found")
        val = pickle.load(Path(pkl_name).read_text())
        self.assertEqual(contents, val)

        c.save()

        c2 = cache.T(self.cache_dir)
        c2.init()
        self.readall_called = False
        contents2 = c2.getcontents(file1_name, self.readall)

        self.assertEqual(False, self.readall_called)
        self.assertEqual(contents,contents2)

    def testHashCode(self):
        c = cache.T(self.cache_dir)
        c.init()
        self.assertEqual("acbd18db4cc2f85cedef654fccc4a4d8", c.hashcode("foo"))
        self.assertEqual(
            "b34231a85737d0b078d7ffb17e6bb3b5",c.hashcode("foo","flag"))
