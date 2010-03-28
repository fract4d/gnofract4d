#!/usr/bin/env python

# create a DocBook XML document documenting the standard library

from xml.sax.saxutils import escape, quoteattr

import fsymbol
import fracttypes
import sys

def strOfType(t):
    return fracttypes.strOfType(t).capitalize()

class SymbolPrinter:
    def __init__(self,f):
        self.f = f
        self.funcs = {}
        self.operators = {}
        self.vars = {}

    def add_symbol(self,key,val):
        if key.startswith("@_") or key.startswith("_"):
            # skip internal symbols
            return
        if isinstance(val,fracttypes.Var):
            self.vars[key] = val
        elif isinstance(val,fsymbol.OverloadList):
            if val.is_operator():
                self.operators[key] = val
            else:
                self.funcs[key] = val

    def output_entry(self,nrows=1):
        print >>self.f, \
           '<entry valign="top" align="left" morerows="%d">' % (nrows-1)
        
    def output_refentry_header(self,key,val,type,nrows=1):
        print >>self.f, '<row>'
        self.output_entry(nrows)
        print >>self.f, '%s</entry>' % escape(key)

    def output_overload(self,func):
        self.output_entry()
        print >>self.f,  ", ".join(map(strOfType,func.args))
        print >>self.f,  '</entry>'
        self.output_entry()
        print >>self.f,  '%s</entry>' % strOfType(func.ret)

    def output_function(self,val):
        nrows = len(val)

        self.output_overload(val[0])
        
        for func in val[1:]:
             print >>self.f,  '</row>'
             print >>self.f,  '<row>'
             self.output_overload(func)
        
    def output_refentry_footer(self):
        print >>self.f,  '</row>'
        #print >>self.f, '<row><entry>&nbsp;</entry></row>'
        
    def output_refentry_body(self,val,nrows=1):
        self.output_entry(nrows)
        text = val.__doc__ or "No documentation yet."
        print >>self.f,  escape(text)
        print >>self.f,  '</entry>'
        
    def output_symbol(self,key,val,type):
        if isinstance(val,fsymbol.OverloadList):
            nrows = len(val)
            self.output_refentry_header(key,val,type,nrows)
            self.output_refentry_body(val,nrows)
            self.output_function(val)            
        else:
            self.output_refentry_header(key,val,type)
            self.output_refentry_body(val)
            print >>self.f,  '<entry>%s</entry>' % strOfType(val.type)

        self.output_refentry_footer()

    def output_all(self):
        self.output_table(self.operators, "Operators", "operator")
        self.output_table(self.funcs,"Functions", "function")
        self.output_table(self.vars, "Symbols", "(symbol)")

        
    def output_table(self,table,name,type):
        print >>self.f,  '<sect2 id="%s">' % name
        print >>self.f,  '<title>%s</title>' % name
        print >>self.f,  '<para><informaltable frame="all">'
        print >>self.f, '<tgroup cols="4">'
        print >>self.f,  '''
<thead>
<row>
                    <entry>Name</entry>
                    <entry>Description</entry>
                    <entry>Argument Types</entry>
                    <entry>Return Type</entry>
</row>
</thead>'''
        print >>self.f,  '<tbody>'

        keys = table.keys()
        keys.sort()
        for k in keys:
            self.output_symbol(k,table[k],type)
        print >>self.f,  '</tbody>'
        print >>self.f,  '</tgroup>'
        print >>self.f,  '</informaltable></para>'
        print >>self.f,  '</sect2>'
        
def main(outfile):
    out = open(outfile,"w")
    d = fsymbol.T()
    printer = SymbolPrinter(out)

    for k in d.default_dict.keys():
        printer.add_symbol(d.demangle(k),d[k])

    printer.output_all()
    
if __name__ == '__main__':
    main(sys.argv[1])
    
