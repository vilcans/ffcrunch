#!/bin/sh -e

rm -f decompressed.dump
DECOMPRESSED_SIZE=$(wc -c <"testdata.bin")
END_ADDRESS=$((DECOMPRESSED_SIZE - 1))
echo "Decompressed size: $DECOMPRESSED_SIZE, end address $END_ADDRESS"

pasmo --hex --equ SIZE=$DECOMPRESSED_SIZE z80_test.s z80_test.hex

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
dch 0x0000 $END_ADDRESS >decompressed.dump
quit
EOF

./dump_to_bin.py <decompressed.dump >decompressed.bin

diff -q testdata.bin decompressed.bin
