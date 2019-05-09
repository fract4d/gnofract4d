#!/usr/bin/env python3

import unittest
import sys
import io

from fract4d.options import Arguments, Formula

class Test(unittest.TestCase):
    def testDefaults(self):
        o = Arguments()
        ns = o.parse_args("")
        
        for x in [ns.formula.name, ns.formula.func,
                  ns.inner.name, ns.inner.func, ns.outer.name, ns.outer.func, ns.map]:
            self.assertEqual(None,x)
        
        for flag in [ns.trace, ns.tracez, ns.quit_when_done,
                     ns.explore, ns.nogui]:
            self.assertEqual(False, flag)
            
        self.assertEqual(-1,ns.maxiter)
        self.assertEqual({},ns.paramchanges)
        self.assertEqual([],ns.extra_paths)

        self.assertEqual(None,ns.width)
        self.assertEqual(None,ns.height)

    def testBadOption(self):
        o = Arguments()
        realSysErr = sys.stderr
        try:
            sys.stderr = io.StringIO()
            with self.assertRaises(SystemExit) as cm:
                o.parse_args("--fish")
        finally:
            sys.stderr = realSysErr

    def testHelp(self):
        o = Arguments()
        help = o.format_help()
        self.assertEqual(1, help.count("To generate an image"))

    def testGeneralOptions(self):
        o = Arguments()
        ns = o.parse_args(["-P", "foo", "bar", "-f", "baz/baz.frm#wibble"])
        self.assertEqual(["foo", "bar", "baz"],ns.extra_paths)
        self.assertEqual("baz.frm",ns.formula.name)
        self.assertEqual("wibble",ns.formula.func)

    def testBadSplit(self):
        realSysErr = sys.stderr
        try:
            sys.stderr = io.StringIO()
            o = Arguments()
            with self.assertRaises(SystemExit) as cm:
                o.parse_args(["-f", "bar"])
        finally:
            sys.stderr = realSysErr
        
    def testHeightWidth(self):
        o = Arguments()
        ns = o.parse_args(["-i", "780", "-j", "445"])

        self.assertEqual(780, ns.width)
        self.assertEqual(445, ns.height)

    def testArgument(self):
        o = Arguments()
        ns = o.parse_args(["foo"])

        self.assertEqual("foo", ns.paramfile)

    def testTransforms(self):
        o = Arguments()
        ns = o.parse_args(["--transforms", "a#b,x#y"])
        self.assertEqual([Formula("", "a","b"), Formula("", "x","y")], ns.transforms)
