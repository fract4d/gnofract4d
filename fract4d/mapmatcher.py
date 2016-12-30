#!/usr/bin/env python3

# Usage: python mapmatcher.py *.map

import sys
import re

rgb_re = re.compile(r'\s*(\d+)\s+(\d+)\s+(\d+)')

def build_list(mapfile):
    colorlist = []
    solid = (0,0,0,255)
    for line in mapfile:
        m = rgb_re.match(line)
        if m != None:
            (r,g,b) = (min(255, int(m.group(1))),
                       min(255, int(m.group(2))),
                       min(255, int(m.group(3))))
            colorlist.append((r,g,b))
    return colorlist

def rotate_list_by(l,n):
    return l[n:] + l[:n]

sets = {}

for f in sys.argv[1:]:
    l = build_list(open(f))
    min_list = l
    for i in range(len(l)):
        rotated_list = rotate_list_by(l,i)
        if rotated_list < min_list:
            min_list = rotated_list

    # min_list is now the canonical rotation

    # convert the list to a string since lists can't be used as hash keys
    key = "%s" % min_list
    
    # add the filename to a hash indexed by the rotated list
    sets.setdefault(key, []).append(f)

for (k,v) in list(sets.items()):
    if len(v) > 1:
        # some dups
        print("These files contain the same map:")
        print("\n".join(v))

