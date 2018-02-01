#!/usr/bin/env python3
import unittest
import sys

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d import options

class Test(unittest.TestCase):
    def testDefaults(self):
        o = options.T()
        
        for x in [o.basename, o.func,
                  o.innername, o.innerfunc, o.outername, o.outerfunc, o.map]:
            self.assertEqual(None,x)
        
        for flag in [o.trace, o.tracez, o.print_version,
                     o.quit_now, o.quit_when_done,
                     o.explore, o.nogui]:
            self.assertEqual(False, flag)
            
        self.assertEqual(-1,o.maxiter)
        self.assertEqual({},o.paramchanges)
        self.assertEqual("",o.output)
        self.assertEqual([],o.extra_paths)

        self.assertEqual(0,o.width)
        self.assertEqual(0,o.height)

    def testBadOption(self):
        o = options.T()
        self.assertRaises(options.OptionError, o.parse,["--fish"])

    def testHelp(self):
        o = options.T()
        o.parse(["-h"])
        self.assertEqual(1, o.output.count("To generate an image"))
        self.assertEqual(True, o.quit_now)

    def testGeneralOptions(self):
        o = options.T()
        o.parse(["-P", "foo", "-f", "bar/baz.frm#wibble"])

        self.assertEqual(["foo","bar"],o.extra_paths)
        self.assertEqual("baz.frm",o.basename)
        self.assertEqual("wibble",o.func)

    def testBadSplit(self):
        o = options.T()
        self.assertRaises(options.OptionError,o.parse,["-f", "bar"])
        
    def testHeightWidth(self):
        o = options.T()
        o.parse(["-i", "780", "-j", "445"])

        self.assertEqual(780, o.width)
        self.assertEqual(445, o.height)

    def testArgument(self):
        o = options.T()
        o.parse(["--params", "foo"])

        self.assertEqual(["foo"], o.args)

    def testTransforms(self):
        o = options.T()
        o.parse(["--transforms", "a#b,x#y"])
        self.assertEqual([("a","b"), ("x","y")], o.transforms)
        
    def testAllOptionsHaveHelp(self):
        o = options.T()
        help = o.help()

        names = ["--" + x.rstrip("=") for x in options.T.longparams]
        for name in names:
            self.assertNotEqual(0, help.count(name), "%s has no help" % name)
            
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

