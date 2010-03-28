#!/usr/bin/env python

import sys

import translate
import fractparser
import fractlexer
import gradient

class T:
    def __init__(self):        
        pass
    
    def translateGradient(self,s):
        fractlexer.lexer.lineno = 1
        pt = fractparser.parser.parse(s)
        return pt

    def split(self,file):
        text = open(file).read()
        t = self.translateGradient(text)
        for grad in t.children:
            t = translate.GradientFunc(grad)
            g = gradient.Gradient()
            g.load_ugr(t)
            out_name = g.name + ".ggr"
            f = open("gradients/" + out_name, "w")
            print >>f, g.serialize()
            f.close()

def main(args):
    t = T()
    for arg in args:
        t.split(arg)

if __name__ == '__main__':
    main(sys.argv[1:])
