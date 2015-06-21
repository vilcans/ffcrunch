%.huff: %.bin
	python -m ffcrunch.huffman --tree $(basename $<)_tree.i --data $@ $<
