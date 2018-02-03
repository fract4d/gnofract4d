#!/usr/bin/env python

import sys
import os
import getopt
import operator
from time import time as now

# gettext
import gettext
from functools import reduce
os.environ.setdefault('LANG', 'en')
if os.path.isdir('po'):
    gettext.install('gnofract4d','po')
else:
    gettext.install('gnofract4d')

import gtk

from fract4d import fractmain, image
from fract4dgui import main_window

files = [
    'testdata/std.fct',
    'testdata/param.fct',
    'testdata/valley_test.fct',
    'testdata/trigcentric.fct',
    'testdata/zpower.fct'
    ]

class Benchmark:
    def __init__(self, useGui):
        self.last_time = None
        self.pos = 0
        self.useGui = useGui
        self.w = 320
        self.h = 240
        
    def run_gui(self):

        window = main_window.MainWindow()

        window.f.set_size(self.w,self.h)
        window.f.thaw()

        times = []
        self.last_time = now()

        def status_changed(f,status):
            if status == 0:
                # done
                new_time = now()
                times.append(new_time - self.last_time)
                self.last_time = new_time
                self.pos += 1
                if self.pos < len(files):
                    window.load(files[self.pos])
                else:
                    gtk.main_quit()

        window.f.connect('status-changed', status_changed)
        window.load(files[0])
        gtk.main()
        return times

    def run_nogui(self):
        main = fractmain.T()
        print(main.compiler.path_lists)
        times = []
        last_time = now()
        for file in files:
            main.load(file)
            im = image.T(self.w,self.h)
            main.draw(im)
            im.save(file + ".png")
            new_time = now()
            times.append(new_time - last_time)

        return times

    def run(self):
        if self.useGui:
            times = self.run_gui()
        else:
            times = self.run_nogui()

        for (file,time) in zip(files,times):
            print("%.4f %s" % (time,file))

        print(reduce(operator.__add__,times,0))

useGui = True
repeats = 1
for arg in sys.argv[1:]:
    if arg == "--nogui":
        useGui = False
    if arg == "--repeat":
        repeats = 3

for i in range(repeats):
    bench = Benchmark(useGui)
    bench.run()



