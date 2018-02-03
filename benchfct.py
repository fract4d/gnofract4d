#!/usr/bin/env python

import sys
import os
from time import time as now

class Benchmark:
    def __init__(self, command, args):
        self.last_time = None
        self.pos = 0
        self.args = args        
        self.command = command

    def build(self):
        cmd = self.command + " --buildonly foo.so " + self.args
        print(cmd)
        result = os.system(cmd)
        assert result == 0

    def run(self):
        last_time = now()
        result = os.system(self.command + " --usebuilt ./foo.so " + self.args)
        assert result == 0
        new_time = now()
        return new_time - last_time

repeats = 1
command = "./gnofract4d -i 2560 -j 2048 --nogui "
args = ""
for arg in sys.argv[1:]:
    if arg == "--repeat":
        repeats = 5
    else:
        args += " " + arg

bench = Benchmark(command, args)
bench.build()
times = []
for i in range(repeats):
    t = bench.run()
    print(t)
    times.append(t)

print("stats")
print("min:(%.4f), max(%.4f), average(%.4f)" % (min(times), max(times), sum(times)/len(times)))
    



