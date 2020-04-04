#!/usr/bin/python

import os
import sys

dir = sys.argv[1]
file = sys.argv[2]

print(dir)
os.chdir(dir)

os.system("tar xzvf %s" % file)
