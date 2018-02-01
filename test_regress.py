#!/usr/bin/env python

# compare output of fract4d with saved 'known good' files
# complain about anything different

# this requires the Python Imaging Library to run.

import os
import operator
from PIL import Image, ImageChops, ImageFilter, ImageStat
from functools import reduce

good_files = [
    # look ok
    "abyssal.fct", 
    "antialias_bug.fct", 
    "bailout_breaker.fct", 
    #"barnsley_t2_odd.fct", 
    "barnsley_worm.fct",
    "cathedral.fct",
    "chaos_engine.fct",
    "compass_rose.fct",
    "crest.fct",
    "cubicspiral.fct",
    "towers.fct",
    "valley_of_obvious_errors.fct",
    "shattered.fct",
    
]

bad_files = [
    # not equivalent
    "caduceus.fct",
    "caduceus_fixed.fct",
    "contrail.fct",
    "daisychain.fct",
]

def render(outfile, fctfile):
    cmd = "./gnofract4d --nogui --threads 4 -i 64 -j 48 -s %s -q %s" % (outfile,fctfile)
    #print cmd
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("error generating image")
    
def compare(fctfile):
    outbase = os.path.basename(fctfile) + ".png"
    outfile = "testdata/new_output/" + outbase
    render(outfile, fctfile)
    new_image = Image.open(outfile)
    old_image = Image.open("testdata/saved_output/" + outbase)

    diff = ImageChops.difference(new_image,old_image)

    diff_file = "testdata/diffs/" + outbase
    diff.save(diff_file)
    
    stats = ImageStat.Stat(diff)
    print("%f\t%d\t%f" % \
          (total(stats.mean), total(stats.median), total(stats.rms)))

def total(l):
    return reduce(operator.__add__,l)

def check_file(f):
    try:
        print("%s\t" % f, end=' ')
        compare(f)
    except Exception as err:
        print("Error %s" % err)

if __name__ == '__main__':
    import sys
    print("file\tmean\tmedian\trms")
    if len(sys.argv) > 1:
        for f in sys.argv[1:]:        
            check_file(f)
    else:
        for f in [ "testdata/" + x for x in good_files]:
            check_file(f)
        for f in [ "testdata/" + x for x in bad_files]:
            check_file(f)

