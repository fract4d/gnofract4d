#!/usr/bin/env python3

from fract4d.options import Arguments
from fract4dgui import main_window
from fract4d import fractmain, image, fractconfig
import gi
import sys
import os
import getopt
import operator
import gettext
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from time import time as now
from fract4d import fractmain, image
from fract4dgui import main_window
from functools import reduce
from fract4d import fractconfig

os.environ.setdefault('LANG', 'en')
if os.path.isdir('po'):
    gettext.install('gnofract4d', 'po')
else:
    gettext.install('gnofract4d')

gi.require_version('Gtk', '3.0')
try:
    from gi.repository import Gtk
except ImportError as err:
    print(_("Can't find Gtk. You need to install it before you can run Gnofract 4D."))
    sys.exit(1)

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

        userConfig = fractconfig.userConfig()
        window = main_window.MainWindow(userConfig)

        window.f.set_size(self.w, self.h)
        window.f.thaw()

        times = []
        self.last_time = now()

        def status_changed(f, status):
            if status == 0:
                # done
                new_time = now()
                times.append(new_time - self.last_time)
                self.last_time = new_time
                self.pos += 1
                if self.pos < len(files):
                    window.load(files[self.pos])
                else:
                    Gtk.main_quit()

        window.f.connect('status-changed', status_changed)
        window.load(files[0])
        Gtk.main()
        return times

    def run_nogui(self):
        userConfig = fractconfig.userConfig()
        main = fractmain.T(userConfig)
        times = []
        last_time = now()
        for file in files:
            main.load(file)
            opts = Arguments().parse_args(sys.argv[1:])
            main.run(opts)
            new_time = now()
            times.append(new_time - last_time)

        return times

    def run(self):
        if self.useGui:
            times = self.run_gui()
        else:
            times = self.run_nogui()

        for (file, time) in zip(files, times):
            print("%.4f %s" % (time, file))

        print(reduce(operator.__add__, times, 0))


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
