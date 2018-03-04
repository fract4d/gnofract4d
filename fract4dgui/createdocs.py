#!/usr/bin/env python3

# create a DocBook XML document documenting the keyboard shortcuts & mouse clicks
# by interrogating the code

from xml.sax.saxutils import escape
import os
import re
import tempfile

import gettext
os.environ.setdefault('LANG', 'en')
gettext.install('gnofract4d')

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from fract4d import fractconfig
from . import main_window

sort_re = re.compile(r'(?P<mod1><.*?>)?(?P<mod2><.*?>)?(?P<key>[^<>]*)')

ctrl_re = re.compile(r'<control>')
shift_re = re.compile(r'<shift>')

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
        print('<row>', file=self.f)
        print('<entry>%s</entry>' % escape(key), file=self.f)
        print('<entry>%s</entry>' % escape(command.val), file=self.f)
        print('</row>', file=self.f)

    def output_all(self):
        self.output_table(self.mouse_commands, "Mouse Commands", "Button")
        keys = sorted(self.commands.keys(), key=key_fix)
        self.output_table([self.commands[k] for k in keys],"Keyboard Shortcuts","Key")
        
    def output_table(self,commands,name,type):
        nospacename = name.replace(' ', '')
        print('<sect2 id="%s">' % nospacename, file=self.f)
        print('<title>%s</title>' % name, file=self.f)
        print('<para><informaltable>', file=self.f)
        print('<tgroup cols="2">', file=self.f)
        print('''<thead><row>
                    <entry>%s</entry>
                    <entry>Action</entry>
                 </row></thead>''' % type, file=self.f)
        print('<tbody>', file=self.f)

        for cmd in commands:
            self.output_command(cmd,type)

        print('</tbody>', file=self.f)
        print('</tgroup>', file=self.f)
        print('</informaltable>', file=self.f)
        print('</para>', file=self.f)

        print('</sect2>', file=self.f)
        
def main(outfile):
    out = open(outfile,"w")
    printer = CommandPrinter(out)

    tmpdir = tempfile.TemporaryDirectory(prefix="fract4d_")
    config = fractconfig.T("")
    config.set("general","cache_dir",
               os.path.join(tmpdir.name, "gnofract4d-cache"))
    mw = main_window.MainWindow(config, ["../formulas"])

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
    out.close()
    tmpdir.cleanup()
    
if __name__ == '__main__':
    main('../doc/gnofract4d-manual/C/commands.xml')
