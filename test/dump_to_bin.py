#!/usr/bin/env python
import sys

for line in sys.stdin:
    values = line.split()[1:9]
    byte_values = ''.join(chr(int(v, 16)) for v in values)
    #print 'bytes:', byte_values
    sys.stdout.write(byte_values)
