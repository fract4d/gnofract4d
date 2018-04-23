#!/usr/bin/env python3

import sys
import unittest

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d import preprocessor

class Test(unittest.TestCase):
    def testEmpty(self):
        pp = preprocessor.T('')

    def testIfdef(self):
        pp = preprocessor.T('''
        $IFDEF wibble
        >>><<<
        $ENDIF
        wobble
        ''')

        self.assertEqual(pp.out(), '''



        wobble
        ''')

    def testUndef(self):
        pp = preprocessor.T('''
        $DEFINE foo
        $UNDEF foo
        $IFDEF foo
        poo
        $ENDIF
        ''')
        self.assertEqual(pp.out(),'''





        ''')

    def testContinuationFix(self):
        pp = preprocessor.T('''
        z = 1.0\\
        5
        ''')
        
        self.assertEqual(pp.out(),'''
        z = 1.05

        ''')

    def testContinuation2(self):
        pp = preprocessor.T('''
; The normal library that comes with Ultra Fractal includes much more advanced routines. \\

; Most of the routines includes something called "Iteration trap".
''')
        self.assertEqual(pp.out(),'''
; The normal library that comes with Ultra Fractal includes much more advanced routines. 

; Most of the routines includes something called "Iteration trap".
''')

    def testBadUndef(self):
        pp = preprocessor.T('''
        $UNDEF foo
        ''')
        self.assertEqual(pp.out(),'''

        ''')

        try:
            pp = preprocessor.T('''
            $UNDEF
            ''')
            self.fail("should've raised an exception")
        except preprocessor.Error as err:
            self.assertEqual(str(err), "2: $UNDEF without variable")
                    
    def testIfWithoutEndif(self):
        try:
            pp = preprocessor.T('''
            $IFDEF foople
            ''')
            self.fail("Should have raised an exception")
        except preprocessor.Error as err:
            self.assertEqual(str(err), "2: $IFDEF without $ENDIF")

    def testEndifWithoutIf(self):
        try:
            pp = preprocessor.T('''
            $IFDEF foogle

            $IFDEF bargle
            $ENDIF
            $ENDIF
            $ENDIF
            ''')
            self.fail("Should have raised an exception")
        except preprocessor.Error as err:
            self.assertEqual(str(err), "7: $ENDIF without $IFDEF")

    def testIfdefWithoutVar(self):
        try:
            pp = preprocessor.T('''
            $IFDEF
            foo
            $ENDIF
            ''')
            self.fail("Should have raised an exception")
        except preprocessor.Error as err:
            self.assertEqual(str(err), "2: $IFDEF without variable")

    def testDefine(self):
        pp = preprocessor.T('$define foo\nbar')

        self.assertEqual(pp.out(), "\nbar")

    def testDefineWithoutVar(self):
        try:
            pp = preprocessor.T('$define !!!\n')
            self.fail("Should have raised an exception")
        except preprocessor.Error as err:
            self.assertEqual(str(err), "1: $DEFINE without variable")

    def testDefineWorks(self):
        pp = preprocessor.T('''
        $define wibble
        $IFDEF wibble
        >>><<<
        $ENDIF
        wobble
        ''')

        self.assertEqual(pp.out(), '''


        >>><<<

        wobble
        ''')

    def testNestedIfdef(self):
        pp = preprocessor.T('''
        $define bar
        $IFDEF foo
           foo
           $IFDEF bar
           foobar
           $ENDIF
        $ENDIF
        $IFDEF bar
           bar
           $IFDEF foo
           barfoo
           $ENDIF
        $ENDIF
        ''')

        self.assertEqual(pp.out(), '''








           bar




        ''')

    def testNestedDefine(self):
        pp = preprocessor.T('''
        $IFDEF foo
           $deFine bar
           $define
        $ENDIF
        $IFDEF bar
           foobar
        $ENDIF
        ''')

        self.assertEqual(pp.out(), '''







        ''')

    def testElse(self):
        pp = preprocessor.T('''
        $define bar
        $IFDEF foo
           foo
        $ELSE
           not foo
           $ifdef bar
               notfoo,bar
           $else
               notfoo,notbar
           $endif
        $ENDIF
        ''')

        self.assertEqual(pp.out(), '''




           not foo

               notfoo,bar




        ''')

    def testCompressed(self):
        pp = preprocessor.T('''
        ExampleFractal2 {
::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
  3w7AuhzA3wlhb4E42/p/vV4fBwn5qoH=
}
''')
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

        
