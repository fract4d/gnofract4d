#!/usr/bin/env python

# create a DocBook XML document documenting the keyboard shortcuts & mouse clicks
# by interrogating the code

from xml.sax.saxutils import escape, quoteattr
import os
import sys
import StringIO
import re

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')
sys.path.insert(1, "..")

import main_window

sort_re = re.compile(r'(?P<mod1><.*?>)?(?P<mod2><.*?>)?(?P<key>[^<>]*)')

ctrl_re = re.compile(r'<control>')
shift_re = re.compile(r'<shift>')

def strOfType(t):
    return fracttypes.strOfType(t).capitalize()

class Command:
    def __init__(self,key,val):
        self.key = key
        self.val = val or ""

def key_fix(k):
    m = sort_re.match(k)
    if m:
        k = m.group("key")
        if k[0] == "F" and len(k) > 1:
            func = "_"
        else:
            func = ""
        fixed = "%s%s%s%s" % (func, m.group("key"),m.group("mod1") or "",m.group("mod2") or "")
        #print k,"=>",fixed
        return fixed
    return k

def key_cmp(a,b):    
    a,b = key_fix(a),key_fix(b)
    return cmp(a,b)

class CommandPrinter:
    def __init__(self,f):
        self.f = f
        self.commands = {}
        self.mouse_commands = []
        
    def add_command(self,key, val):
        self.commands[key] = Command(key,val)

    def add_mouse(self,key,val):
        self.mouse_commands.append(Command(key,val))
        
    def output_command(self,command,type):
        key = ctrl_re.sub('Ctrl+',command.key)
        key = shift_re.sub('Shift+',key)
        print >>self.f,  '<row>'
        print >>self.f,  '<entry>%s</entry>' % escape(key)
        print >>self.f,  '<entry>%s</entry>' % escape(command.val)
        print >>self.f,  '</row>'

    def output_all(self):
        self.output_table(self.mouse_commands, "Mouse Commands", "Button")
        keys = self.commands.keys()
        keys.sort(key_cmp)
        self.output_table([self.commands[k] for k in keys],"Keyboard Shortcuts","Key") 
        
    def output_table(self,commands,name,type):
        nospacename = name.replace(' ', '')
        print >>self.f, '<sect2 id="%s">' % nospacename
        print >>self.f, '<title>%s</title>' % name
        print >>self.f, '<para><informaltable>'
        print >>self.f, '<tgroup cols="2">'
        print >>self.f, '''<thead><row>
                    <entry>%s</entry>
                    <entry>Action</entry>
                 </row></thead>''' % type
        print >>self.f,  '<tbody>'

        for cmd in commands:
            self.output_command(cmd,type)

        print >>self.f,  '</tbody>'
        print >>self.f,  '</tgroup>'
        print >>self.f,  '</informaltable>'
        print >>self.f,  '</para>'

        print >>self.f,  '</sect2>'
        
def main(outfile):
    out = open(outfile,"w")
    printer = CommandPrinter(out)

    mw = main_window.MainWindow(["../formulas"])

    menu_items = mw.get_all_actions()
    for item in menu_items:
        if len(item) < 4: continue
        key = item[3]
        if not key:
            continue
        func = item[5]
        printer.add_command(key,func.__doc__)

    # hard-code ones which are too hard to extract from main code
    printer.add_command("(arrow)","Pan image in indicated direction.")
    printer.add_command("<control>(arrow)","Pan more quickly in indicated direction.")
    printer.add_command("<shift>(arrow)","Mutate image in Z or W directions.")
    printer.add_command("<shift><control>(arrow)", "Mutate more quickly.")
    printer.add_command("Escape", "Quit full-screen mode.")

    printer.add_mouse("Left-click","Zoom in")
    printer.add_mouse("Left-click and drag", "Draw rectangle to zoom into.")
    printer.add_mouse("Shift-Left-click", "Recenter image on point clicked.")

    printer.add_mouse("Middle-click", "Flip to Julia set (or back to Mandelbrot).")
    printer.add_mouse("Right-click", "Zoom out.")
    printer.add_mouse("Control-Right-click", "Zoom out more quickly.")
    
    printer.output_all()
    
if __name__ == '__main__':
    main('../doc/gnofract4d-manual/C/commands.xml')
    
