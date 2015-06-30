MAX_HEIGHT=9

%.huff: %
	python -m ffcrunch.huffman --max-height=$(MAX_HEIGHT) -o $@ $<

%.rle: %
	python -m ffcrunch.rle $< $@
