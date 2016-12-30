#!/usr/bin/env python3

# test configuration file parsing

import unittest
import sys
import os

import fractconfig, fc

class Test(unittest.TestCase):
    def testCreate(self):
        c = fractconfig.T("testprefs")

    def testGetDefaults(self):
        c = fractconfig.T("testprefs")
        self.assertEqual("gcc",c.get("compiler","name"))

    def testGetList(self):
        c = fractconfig.T("testprefs")
        l = c.get_list("map_path")
        self.assertEqual(4, len(l))
        self.assertEqual("maps", l[0])

    def testSetList(self):
        c = fractconfig.T("testprefs")
        l = ["fish"]

        c.set_list("map_path",l)

        l2 = c.get_list("map_path")
        self.assertEqual(l, l2)

    def testSetSize(self):
        c = fractconfig.T("testprefs")
        c.set_size(871, 313)
        self.assertEqual(871, c.getint("display","width"))
        self.assertEqual(313, c.getint("display","height"))

    def testSave(self):
        c = fractconfig.T("testprefs")
        c.set("compiler","options","-foo")
        self.assertEqual("-foo", c.get("compiler","options"))
        c.save()

        c.set("compiler","options","wibble")
        config2 = fractconfig.T("testprefs") #re-read
        self.assertEqual("-foo",config2.get("compiler","options"))
        os.remove("testprefs")

    def testInstance(self):
        dummy = fractconfig.instance
        self.assertEqual(".gnofract4d",os.path.basename(dummy.file))

    def testDataDir(self):
        c = fractconfig.T("testprefs")
        datadir = c.get("general","data_dir")
        self.assertEqual(
            os.path.expandvars("${HOME}/gnofract4d"), datadir)

    def testDarwin(self):
        c = fractconfig.DarwinConfig("testprefs")
        self.assertEqual("open -e", c.get_default_editor())

def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

