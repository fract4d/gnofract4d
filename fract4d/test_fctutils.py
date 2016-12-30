#!/usr/bin/env python3

"Tests for fctutils"
import string
import io
import unittest
import gzip
import base64

import fctutils

class Test(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def testRoundTripData(self):
        comp = fctutils.Compressor()
        comp.write("""hello=goodbye
multiline=[
hello
fook
mimsy
]
parishioner=arse
""")
        comp.close()
        data = comp.getvalue()
        full_input = "fish=wiggle\n" + data
        in_f = io.StringIO(full_input)

        fct = fctutils.ParamBag()
        fct.load(in_f)

        self.assertEqual("goodbye", fct.dict["hello"])
        self.assertEqual("arse", fct.dict["parishioner"]) 
        self.assertEqual("wiggle", fct.dict["fish"])
        self.assertEqual("""hello
fook
mimsy
""",
                         fct.dict["multiline"])
        
def suite():
    return unittest.makeSuite(Test,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
