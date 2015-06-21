include ../common.mk

ASM_Z80 = pasmo --hex

%.hex: %.s
	$(ASM_Z80) $< $@

z80_test.hex: z80_test.s testdata.huff

test: z80_test.hex
	./z80_test.sh

.PHONY: test
