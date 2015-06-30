decomp_start EQU $0000
decomp_end EQU decomp_start+SIZE

	org $8000

	call do_test
	ret  ; must be at $8003, as breakpoint is set here

do_test:
	ld hl,packed_tree
	ld de,huffman_tree
	call construct_tree

	ld hl,huffman_data
	ld de,huffman_tree
	call init_decompress

	ld ix,decomp_start
decompress_loop:
	call get_next_byte
	ld (ix),a
	inc ix
	ld a,decomp_end>>8
	cp ixh
	jp nz,decompress_loop
	ld a,decomp_end&$ff
	cp ixl
	jp nz,decompress_loop
	ret

	include "../z80/huffman1.s"

	org $8200
huffman_tree:
	ds $800

	org $9000
packed_tree:
	incbin "testdata.bin.tree"
huffman_data:
	incbin "testdata.bin.huff"
