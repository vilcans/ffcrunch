; Huffman decoder.
; A magic value (INTERNAL) is used to mark a non-leaf node.
; This has the effect that the uncompressed data may not contain
; a byte with that value.

; Usage:
;   ld hl,packed_tree
;   ld de,huffman_tree
;   call construct_tree
;
;   ld hl,compressed_data
;   ld de,huffman_tree
;   call init_decompress
;
;   call get_next_byte
;   .
;   .
;   call get_next_byte


; NOTES
; The Huffman tree is packed into an array which is constructed
; so that the child nodes of index i are at
; (2i+1) and (2i+2) for left and right child respectively.

; Unpack the Huffman tree into its runtime representation.
; Input:
;   HL = packed tree
;   DE = unpacked tree
construct_tree:
	ld (huff_construct_table_pointer),de
	ld a,(hl)   ; A = tree height
	ld (tree_height),a
	inc hl
	ld a,(hl)   ; internal node magic value
	ld (huff_construct_internal_node_marker),a
	ld (de),a   ; construct top node, always an internal node
	inc hl
	ld a,(hl)   ; number of symbols
	inc hl
	inc hl      ; skip dummy

	; HL = data pointer
	; C = current bits + end bit
	; A = symbol counter
	ld c,$80
.symbol_loop:
	ld (.symbol_counter),a
tree_height EQU $+1
	ld b,0      ; code length
	xor a
.get_code_length_loop:
	call get_next_bit
	rla
	djnz .get_code_length_loop

	ld b,a      ; B = code length counter
	; DE = node offset
	ld de,0     ; DE = node offset
.get_code_loop:
	call get_next_bit
	; Get child node, 2i+1 for left node, 2i+2 for the right
	; DE = 2i+0 or 2i+1
	rl e
	rl d
	inc de     ; DE = 2i+1 or 2i+2
huff_construct_table_pointer EQU $+2
	ld ix,$0000  ; TODO: remove these three; fill whole table with INTERNAL before instead
	add ix,de
huff_construct_internal_node_marker EQU $+3
	ld (ix),0
	djnz .get_code_loop

	ld b,8
.get_symbol_loop:
	call get_next_bit
	rla
	djnz .get_symbol_loop
	ld (ix),a

.symbol_counter EQU $+1
	ld a,0
	dec a
	jp nz,.symbol_loop
	ret

; Input:
;   C = current bits with end bit
;   HL = byte pointer
; Modifies C, HL. Returns bit in carry flag.
get_next_bit:
	sla c
	ret nz
	ld c,(hl)   ; C = bits
	inc hl
	scf
	rl c
	ret

; Initializes decompression
; Input:
;   DE = huffman tree (unpacked)
;   HL = compressed data
; Output:
;   C = current byte with a stop bit ($80)
;   A = modified
init_decompress:
	ld (huff_decode_table_pointer),de
	; Assume top node in tree is an internal node; use its value
	ld a,(de)
	ld (huff_decode_internal_node_marker),a
	; C stores the current byte, shifted to the left one bit at a time
	; The final set bit marks the end of the byte.
	ld c,$80
	ret

_next_byte:
	; Carry is now set as the last bit to shift out is a 1
	ld c,(hl)
	inc hl  ; doesn't affect carry
	rl c  ; puts the 1 in the lowest bit as carry is still set

	jp .got_bit

get_next_byte:
	ld de,0
traverse_loop:
	; Get next bit
	sla c
	jr z,_next_byte
.got_bit:
	; Get child node, 2i+1 for left node, 2i+2 for the right
	; DE = 2i+0 or 2i+1   8t
	rl e
	rl d
	inc de     ; DE = 2i+1 or 2i+2

	push hl
huff_decode_table_pointer EQU $+1
	ld hl,$2121
	add hl,de
	ld a,(hl)
	pop hl
huff_decode_internal_node_marker EQU $+1
	cp 0
	ret nz

	jp traverse_loop
