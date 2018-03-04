#!/usr/bin/env python3

# utility script. When compiled with DEBUG_CREATION and/or DEBUG_ALLOCATION,
# we output debug spew whenever C objects used from Python are created or deleted

# This script checks whether the creations and deletion match

# usage: ./test_fract4d.py 2>&1 | ./checkalloc.py

import sys
import re

alloc_re = re.compile(r'(?P<test>.*?... )?\.?(?P<ptr>0x[0-9a-f]+)\s*:\s*(?P<type>.*?)\s*:\s*(?P<op>[A-Z]+)')

if len(sys.argv) > 1:
    lines = open(sys.argv[1]).readlines()
else:
    lines = sys.stdin.readlines()
    
ops = {}

for line in lines:
    m = alloc_re.match(line)
    if m:
        if m.group("test"):
            test = m.group("test")
        pointer = m.group("ptr")
        type = m.group("type")
        op = m.group("op")
        if op == "REF":
            # it's OK to 'create' the same dlhandle several times
            # since those are refcounts
            ops[pointer] = ops.get(pointer,0) + 1
        elif op == "DEREF":
            x = ops.get(pointer)
            if x is None:
                raise Exception("deref on object with no refs: %s" % pointer)
            if x == 1:
                del ops[pointer]
            else:
                ops[pointer] = x - 1
        elif op == "CTOR":
            if ops.get(pointer):
                raise Exception("double alloc on %s" % pointer)
            ops[pointer] = type
        elif op == "DTOR":
            alloctype = ops.get(pointer)
            if not alloctype:
                raise Exception("dtor on unallocated pointer %s" % pointer)
            if type != alloctype:
                raise Exception("different dealloc type for %s" % pointer)
            del ops[pointer]
        else:
            print("unrecognized op %s" % op)
    else:
        print("skipped: %s" % line, end=' ')

print(list(ops.items()))
for (k,v) in list(ops.items()):
    raise Exception("%s(%s) never freed" % (k,v))

print("ok!")
