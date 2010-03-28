#!/usr/bin/env python

# a minimal script to do nothing, reading in data then printing some out

import sys
import time

total_bytes = int(sys.argv[1])

if len(sys.argv) > 2:
    wait_time = float(sys.argv[2])
else:
    wait_time=0.001

bytes_read = 0
attempts = 0

input = ""
while bytes_read < total_bytes and not sys.stdin.closed and attempts < 10000:
    data = sys.stdin.read(1000)
    bytes_read += len(data)
    #print >>sys.stderr, bytes_read
    time.sleep(wait_time)
    input += data
    attempts += 1

if attempts == 10000:
    #print >>sys.stderr, "gave up"
    sys.exit(-1)

    
#print >>sys.stderr, bytes_read
#print >>sys.stderr, "writing to output"

bytes_written = 0
while bytes_written < len(input):
    bytes_to_write = min(1000, len(input) - bytes_written)
    time.sleep(wait_time)
    sys.stdout.write(input[bytes_written:bytes_written + bytes_to_write])
    bytes_written += bytes_to_write
    #print >>sys.stderr, "wrote %d" % bytes_written

#print >>sys.stderr, "DONE"

sys.stdout.flush()
sys.stdout.close()

#print >>sys.stderr, "double DONE"
#sys.exit(0)
