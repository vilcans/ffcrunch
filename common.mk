%.huff: %.bin
	python -m ffcrunch.huffman --stree $(basename $<)_tree.i --tree $(basename $<).hufftree --data $@ $<
