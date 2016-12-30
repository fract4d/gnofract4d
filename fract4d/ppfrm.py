#!/usr/bin/env python3

# pretty-print a formula in docbook or HTML format

# std modules
import sys
import os
import re

# kid
import elementtree.ElementTree
from elementtree.ElementTree import Element
import kid
kid.enable_import()

#kid templates
import frm_docbook 

# PLY
import lex

# my code
import fractlexer

def output_frm(toks,outbase, nfrms):
    if toks != []:
        outfile = open("%s%03d.xml" % (outbase, nfrms),"w")
        k = frm_docbook.Template(tokens=toks)
        print(k.serialize(), file=outfile)

# map from token types -> docbook element types
element_types = {
    "FORM_ID" : '<emphasis role="bold"/>',
    "SECT_SET" : '<emphasis role="bold"/>',
    "SECT_PARMS" : '<emphasis role="bold"/>',
    "SECT_STM" : '<emphasis role="bold"/>',
    "NUMBER" : '<literal/>',
    "COMMENT" : '<emphasis/>'
    }

# array of words to highlight for each formula in the tutorial
highlights = [
    {},
    {},
    {"#zwpixel": '<emphasis role="bold"/>'},
    {"@myfunc":  '<emphasis role="bold"/>',
     "@factor":  '<emphasis role="bold"/>'}
    ]

myfrm = re.compile('MyFormula\d+')

def processToken(tok, specialdict):
    element_type = element_types.get(tok.type)
    special_type = specialdict.get(tok.value)
    if special_type:
        val = elementtree.ElementTree.XML(special_type)
        val.text = tok.value
    elif element_type:
        val = elementtree.ElementTree.XML(element_type)
        val.text = tok.value
    else:
        val = tok.value
    return val

def main(infile,outbase):
    fractlexer.keep_all = True
    fractlexer.t_ignore = ""
    flex = lex.lex(fractlexer)
    
    flex.input(open(infile).read())

    # Tokenize
    toks = []
    nfrms = 0
    while 1:
        tok = flex.token()
        if not tok: break      # No more input
        
        #element.text = tok.value
        if tok.type == "FORM_ID":
            output_frm(toks,outbase,nfrms)
            toks = []
            nfrms += 1
            # special case for processing tutorial
            tok.value = myfrm.sub('MyFormula',tok.value)
            
        toks.append(processToken(tok, highlights[nfrms]))

    # print last formula
    output_frm(toks,outbase,nfrms)

        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: ppfrm.py foo.frm outbase")
        sys.exit(1)
        
    if(len(sys.argv) > 2):
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.argv[1])

