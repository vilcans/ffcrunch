; Huffman decoder.
; A magic value (PARENT) is used to mark a non-leaf node.
; This has the effect that the uncompressed data may not contain
; a byte with that value.

; Usage:
;   ld de,huffman_tree
;   ld hl,compressed_data
;   call init_decompress
;   call get_next_byte

; NOTES
; Huffman tree is stored in an array which is constructed
; so that the child nodes of index i are at
; (2i+1) and (2i+2) for left and right child respectively.

; Value that never occurs in uncompressed data, means non-leaf node
;PARENT EQU $a5

init_decompress:
	ld (huffman_table_pointer),de
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
huffman_table_pointer EQU $+1
	ld hl,$2121
	add hl,de
	ld a,(hl)
	pop hl
	cp PARENT
	ret nz

	jp traverse_loop
