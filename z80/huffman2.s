; Huffman decoder.
; Assumes tree is less than 256 bytes and page aligned.
; A magic value (PARENT) is used to mark a non-leaf node.
; This has the effect that the uncompressed data may not contain
; a byte with that value.

; Usage:
;   ld d,>huffman_tree    ; must be align 256
;   ld hl,compressed_data
;   call init_decompress
;   call get_next_byte

; NOTES
; Huffman tree is stored in an array which is constructed
; so that the child nodes of index i are at
; (2i+1) and (2i+2) for left and right child respectively.

; End of the loop, instantiated in two places to avoid jumps
AFTER_GOT_BIT MACRO
	; Get child node, 2i+1 for left node, 2i+2 for the right
	rl e      ; E = 2i+0 or 2i+1   8t
	inc e     ; E = 2i+1 or 2i+2   4t

	ld a,(de)
	cp PARENT
	ret nz

	jp traverse_loop
	ENDM

init_decompress:
	; C stores the current byte, shifted to the left one bit at a time
	; The final set bit marks the end of the byte.
	ld c,$80
	ret

_next_byte:
	; Carry is now set as the last bit to shift out is a 1
	ld c,(hl)
	inc hl  ; doesn't affect carry
	rl c  ; puts the 1 in the lowest bit as carry is still set

	AFTER_GOT_BIT

get_next_byte:
	ld e,0
traverse_loop:
	; Get next bit
	sla c
	jr z,_next_byte
.got_bit:
	AFTER_GOT_BIT
