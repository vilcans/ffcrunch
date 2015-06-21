#!/usr/bin/env python
import sys

for line in sys.stdin:
    values = line.split(' ')[1:9]
    for v in values:
        if v == '':
            break  # data ends with spaces
        sys.stdout.write(chr(int(v, 16)))
