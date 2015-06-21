#!/bin/sh -e

rm -f decompressed.dump

sz80 <<EOF
memory createchip ram 65536
memory createaddressdecoder rom 0 0xffff ram 0
fill ram 0 0xffff 0x55
load "z80_test.hex"
pc 0x8000
break 0x8003
go
statistic
state
dch 0x0000 0x3fff >decompressed.dump
quit
EOF

./dump_to_bin.py <decompressed.dump >decompressed.bin

diff -q testdata.bin decompressed.bin
