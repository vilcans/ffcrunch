MAX_HEIGHT=9

%.huff: %
	python -m ffcrunch.huffman --max-height=$(MAX_HEIGHT) --stree $(basename $<)_tree.i --tree $<.tree --data $@ $<

%.rle: %
	python -m ffcrunch.rle $< $@
