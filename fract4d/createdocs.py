#!/usr/bin/env python3

# create HTML document documenting the standard library
# this gets included into the main manual

import sys
from xml.sax.saxutils import escape

from fract4d_compiler import fracttypes, fsymbol


def strOfType(t):
    return fracttypes.strOfType(t).capitalize()


class SymbolPrinter:
    def __init__(self, f):
        self.f = f
        self.funcs = {}
        self.operators = {}
        self.vars = {}

    def add_symbol(self, key, val):
        if key.startswith("@_") or key.startswith("_"):
            # skip internal symbols
            return
        if isinstance(val, fracttypes.Var):
            self.vars[key] = val
        elif isinstance(val, fsymbol.OverloadList):
            if val.is_operator():
                self.operators[key] = val
            else:
                self.funcs[key] = val

    def output_entry(self, nrows=1):
        print(
            '<td valign="top" align="left" rowspan="%d">' %
            nrows, file=self.f)

    def output_refentry_header(self, key, val, type, nrows=1):
        print('<tr>', file=self.f)
        self.output_entry(nrows)
        print('%s</td>' % escape(key), file=self.f)

    def output_overload(self, func):
        self.output_entry()
        print(", ".join(map(strOfType, func.args)), file=self.f)
        print('</td>', file=self.f)
        self.output_entry()
        print('%s</td>' % strOfType(func.ret), file=self.f)

    def output_function(self, val):
        self.output_overload(val[0])

        for func in val[1:]:
            print('</tr>', file=self.f)
            print('<tr>', file=self.f)
            self.output_overload(func)

    def output_refentry_footer(self):
        print('</tr>', file=self.f)
        #print >>self.f, '<row><entry>&nbsp;</entry></row>'

    def output_refentry_body(self, val, nrows=1):
        self.output_entry(nrows)
        text = val.__doc__ or "No documentation yet."
        print(escape(text), file=self.f)
        print('</td>', file=self.f)

    def output_symbol(self, key, val, type):
        if isinstance(val, fsymbol.OverloadList):
            nrows = len(val)
            self.output_refentry_header(key, val, type, nrows)
            self.output_refentry_body(val, nrows)
            self.output_function(val)
        else:
            self.output_refentry_header(key, val, type)
            self.output_refentry_body(val)
            print('<td>%s</td>' % strOfType(val.type), file=self.f)

        self.output_refentry_footer()

    def output_all(self):
        self.output_table(self.operators, "Operators", "operator")
        self.output_table(self.funcs, "Functions", "function")
        self.output_table(self.vars, "Symbols", "(symbol)")

    def output_table(self, table, name, type):
        print('<h2>%s</h2>' % escape(name), file=self.f)
        print('<table>', file=self.f)
        #print('<colgroup cols="4"/>', file=self.f)
        print('''
<thead>
<tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Argument Types</th>
                    <th>Return Type</th>
</tr>
</thead>''', file=self.f)
        print('<tbody>', file=self.f)

        keys = list(table.keys())
        keys.sort()
        for k in keys:
            self.output_symbol(k, table[k], type)
        print('</tbody>', file=self.f)
        print('</table>', file=self.f)

def main(outfile):
    with open(outfile, "w") as out:
        # insert front matter
        print('''---
title: "Standard Library Reference"
draft: false
---
''', file=out)
        d = fsymbol.T()
        printer = SymbolPrinter(out)

        for k in list(d.default_dict.keys()):
            printer.add_symbol(d.demangle(k), d[k])

        printer.output_all()


if __name__ == '__main__':
    main(sys.argv[1])
