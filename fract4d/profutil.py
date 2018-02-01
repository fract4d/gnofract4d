#!/usr/bin/env python3

# A utility program used to create a standalone single-threaded
# statically-linked C program for profiling purposes

import sys
import subprocess

from . import fc
from . import fractal

class PC(fc.Compiler):
    def __init__(self):
        fc.Compiler.__init__(self)
        
        self.cfiles = [
        "profharness.cpp",
        "c/cmap.cpp",
        "c/image.cpp",
        "c/fractFunc.cpp",
        "c/fract_stdlib.cpp",
        "c/MTFractWorker.cpp",
        "c/pointFunc.cpp",
        "c/STFractWorker.cpp",
        "c/imageWriter.cpp"
        ]

def main(args):
    pc = PC()
    pc.add_func_path("../formulas")
    pc.load_formula_file("gf4d.frm")
    pc.load_formula_file("gf4d.cfrm")
    pc.compiler_name = "g++"
    pc.leave_dirty = True
    f = fractal.T(pc)
    f.loadFctFile(open(args[0]))
    outfile = f.compile()
    cfile = outfile[:-2] + "c"

    # compile the stub and the c file to create a program to profile
    files = " ".join(pc.cfiles + [cfile])
    
    cmd = "%s %s %s -o %s %s" % \
          (pc.compiler_name, files, "-g -pg -O3 -Ic -lpthread", "proftest", "")

    print(cmd)
    (status,output) = subprocess.getstatusoutput(cmd)
    if status != 0:
        raise Exception(
            "Error reported by C compiler:%s" % output)

    print(output)
    # compiled - hurrah! run it
    (status,output) = subprocess.getstatusoutput("./proftest")
    if status != 0:
        raise Exception(
            "Error reported by program:%s" % output)

    print(output)
    
if __name__ == "__main__":
    main(sys.argv[1:])
