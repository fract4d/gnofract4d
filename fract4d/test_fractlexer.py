#!/usr/bin/env python3

import sys
import unittest

if sys.path[1] != "..": sys.path.insert(1, "..")

from fract4d import fractlexer
from fract4d import preprocessor

class Test(unittest.TestCase):
    def setUp(self):
        self.lexer = fractlexer.lexer
        self.lexer.lineno = 1
        
    # utility function - open file f, lex it, and return a list of
    # all the tokens therein
    
    def tokensFromFile(self, f):
        data = open(f,"r").read()
        return self.tokensFromString(self, data)

    def tokensFromString(self, data):
        # Give the lexer some input
        self.lexer.input(data)

        toklist = []
        # Tokenize
        while 1:
            tok = self.lexer.token()
            if not tok: break      # No more input
            #print tok
            toklist.append(tok)

        return toklist

    def testUGR(self):
        tokens = self.tokensFromString(
'''cl1rorangemixed {
gradient:
 title="cl1rorangemixed" smooth=no
 index=0 color=5153516
 index=2 color=5087212
 index=399 color=5349352
}
        ''')
        #print tokens
        self.assertEqual(tokens[0].type, "FORM_ID")
        self.assertEqual(tokens[2].type, "SECT_PARMS")

        self.assertEqual(tokens[9].type, "CONST")
        
    def testEmpty(self):
        self.assertEqual(self.tokensFromString(""),[])

    def testBasics(self):
        tokens = self.tokensFromString(
            '''; Formulas from Andre Vandergoten
; (2 + #hash foo ^|+| "hello" a coment containing expressions
AAA-5-grt{
init:
   z = #pixel
loop:
   if @soort ==  0
      z = z^@power/@een(#pixel)
   endif  
bailout:
   |z|>@bailout
default:
   title = "foo;bar\\
   baz"
}
''')
        self.assertTrue(tokens[0].type == tokens[1].type == "NEWLINE","first 2 should be newlines")

        str = [ tok for tok in tokens if tok.type == "STRING"]
        self.assertTrue(len(str) == 1 and str[0].value == "foo;barbaz", "string literal parsing problem" and str[0].lineno == 14)

        sections = [ tok for tok in tokens if tok.type == "SECT_STM"]
        self.assertEqual(len(sections),3, "wrong number of sections")
        self.assertEqual(sections[0].lineno, 4, "line counting wrong")
        self.assertEqual(sections[2].lineno, 10, "line counting wrong")

    def testBadChars(self):
        tokens = self.tokensFromString("$ hello ~\n ` ' goodbye")
        self.assertTrue(tokens[0].type == "error" and tokens[0].value == "$")
        self.assertEqual(tokens[4].type, "error")
        self.assertEqual(tokens[4].value, "`")
        self.assertEqual(tokens[4].lineno, 2)

    def testFormIDs(self):
        tokens = self.tokensFromString('''
=05 { }
0008 { }
-fred- { }
''')
        for token in tokens:
            self.assertTrue(token.type == "FORM_ID" or
                            token.type == "FORM_END" or
                            token.type == "NEWLINE")

    def testIDs(self):
        tokens = self.tokensFromString("@_bailout_part _314159 #__ hello f_i7")
        for t in tokens:
            self.assertTrue(t.type == "ID")
        
    def testCommentFormula(self):
        tokens = self.tokensFromString('''
;Comment {

@#$%554""}
myComment {}
''')
        tokens = [tok for tok in tokens if tok.type != "NEWLINE"]
        self.assertTrue(tokens[0].type == "FORM_ID" and
                        tokens[0].value == "myComment" and
                        tokens[0].lineno == 5)

    def testKeywords(self):
        ts = self.tokensFromString('if a elseif b else c')
        self.assertTrue(ts[0].type == "IF" and
                        ts[2].type == "ELSEIF" and
                        ts[4].type == "ELSE" and
                        ts[1].type == ts[3].type == ts[5].type == "ID")
    def testNumbers(self):
        ts = self.tokensFromString('1.0 0.5e+7 1i 1 i')
        self.assertTrue(ts[0].type == ts[1].type == ts[3].type == "NUMBER" and
                        ts[2].type == "COMPLEX" and ts[2].value == "1" and
                        ts[4].type == "ID")

    def testEscapedNewline(self):
        # fractint allows \ IN THE MIDDLE OF A TOKEN
        # this is handled by the preprocessor, not the lexer
        pp = preprocessor.T('&\\\n&')
        ts = self.tokensFromString(pp.out())
        self.assertTrue(ts[0].type == "BOOL_AND")
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
