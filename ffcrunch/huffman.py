#!/usr/bin/env python

import sys
import argparse

from heapq import heappush, heappop, heapify
from collections import defaultdict
from array import array


def bits_to_bytes(bits):
    """
    Converts string of bit values to raw bytes.

    >>> bits_to_bytes('111111110000000010101010')
    array('B', [255, 0, 170])

    Right padding if number of bits not divisable by 8:

    >>> bits_to_bytes('0000000011')
    array('B', [0, 192])
    >>> bits_to_bytes('0000000011000000')
    array('B', [0, 192])
    """
    byte_count = (len(bits) + 7) // 8
    data = array('B')
    for n in range(byte_count):
        bits_in_byte = bits[n * 8:n * 8 + 8]
        bits_in_byte += '0' * (8 - len(bits_in_byte))
        data.append(int(bits_in_byte, 2))
    return data


def encode(symb2freq):
    """Huffman encode the given dict mapping symbols to weights

    >>> encode({'A': 2, 'B': 1, 'C': 1})
    [['A', '0'], ['B', '10'], ['C', '11']]
    """
    heap = [[wt, [sym, ""]] for sym, wt in symb2freq.items()]
    heapify(heap)
    while len(heap) > 1:
        lo = heappop(heap)
        hi = heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    return heappop(heap)[1:]


def canonicalize(tree):
    """Generate a "Canonical" Huffman tree.

    >>> canonicalize([['A', '11'], ['B', '0'], ['C', '101'], ['D', '100']])
    [('B', '0'), ('A', '10'), ('C', '110'), ('D', '111')]

    See
    https://en.wikipedia.org/wiki/Canonical_Huffman_code#Encoding_the_codebook
    """
    sorted_tree = sorted(tree, key=lambda p: (len(p[-1]), p))

    result = []
    new_code = 0
    for index in xrange(len(sorted_tree)):
        (symbol, old_code) = sorted_tree[index]

        code_str = bin(new_code).split('b')[1]
        code_str = '0' * (len(old_code) - len(code_str)) + code_str
        assert len(code_str) == len(old_code), \
            'Should have same length: ' + old_code + " and " + code_str
        #print 'Old code ', old_code, 'new code', code_str
        result.append((symbol, code_str))
        new_code += 1
        if index != len(sorted_tree) - 1:
            length_diff = len(sorted_tree[index + 1][1]) - len(old_code)
            new_code <<= length_diff

    return result


def create_tree(data, frequency_factor=1.0):
    """Returns list of [symbol, encoding]"""

    symb2freq = defaultdict(int)
    for ch in data:
        symb2freq[ch] += 1

    for symbol in symb2freq:
        freq = symb2freq[symbol]
        symb2freq[symbol] = int(
            freq * frequency_factor + .5 / frequency_factor
        )

    huff = encode(symb2freq)
    canonical = canonicalize(huff)
    return canonical


def compress(raw_data, tree):
    tree_dict = dict(tree)
    bits = ''.join(tree_dict[symbol] for symbol in raw_data)
    return bits_to_bytes(bits)


def get_tree_height(tree):
    """Gets the height of a tree

    Assumes the tree is sorted by symbol length.
    """
    return len(tree[-1][1])


def find_constrained_tree(raw_data, max_height):
    """Find the best tree with a given maximum height"""
    min_factor = 1e-9
    max_factor = 1.0

    factor = 1.0
    for iteration in range(30):
        tree = create_tree(raw_data, factor)
        height = get_tree_height(tree)
        print 'Factor', factor, 'height', height
        if height <= max_height:
            print 'trying right'
            min_factor = factor
        else:
            print 'trying left'
            max_factor = factor
        factor = (min_factor + max_factor) * .5
        print 'min', min_factor, 'max', max_factor, '=', factor
        if min_factor == max_factor:
            break

    tree = create_tree(raw_data, min_factor)
    height = get_tree_height(tree)
    print 'Found tree of height', height, 'factor', factor
    if height > max_height:
        raise RuntimeError(
            'Unable to find a tree with max height %s' % max_height
        )
    return tree


def save_tree(tree, tree_file):
    parent_node_value = 0xa5
    if parent_node_value in tree:
        print '"parent node indicator" value occurs in raw data; can not use it'
        sys.exit(1)

    tree_height = max(len(code) for (value, code) in tree)
    print 'Tree height', tree_height

    with open(tree_file, 'w') as out:
        out.write('; Tree of height {}:\n'.format(tree_height))
        out.write('; {}\n'.format(str(tree)))
        out.write('PARENT equ ${:0>2x}\n'.format(parent_node_value))
        for level in xrange(tree_height + 1):
            out.write('\t; Level {}\n'.format(level))
            level_values = [(parent_node_value, '')] * (1 << level)
            for (value, bits) in tree:
                if len(bits) == level:
                    level_values[int(bits, 2)] = (ord(value), bits)
            for v, b in level_values:
                out.write('\tdb ${:0>2x}  ; {:1}\n'.format(v, b))


def main():
    parser = argparse.ArgumentParser(description='Huffman encoder')
    parser.add_argument(
        '--tree', metavar='FILE', required=True,
        help='Save Huffman tree to this file')
    parser.add_argument(
        '--data', metavar='FILE', required=True,
        help='Save Huffman encoded data to this file')
    parser.add_argument(
        'input', metavar='INPUT_FILE',
        help='File to compress')
    parser.add_argument(
        '--max-height', type=int, help='Maximum height of Huffman tree'
    )

    args = parser.parse_args()

    raw_data = open(args.input).read()
    if args.max_height:
        tree = find_constrained_tree(raw_data, max_height=args.max_height)
    else:
        tree = create_tree(raw_data)
    #print tree
    encoded = compress(raw_data, tree)
    save_tree(tree, args.tree)
    with open(args.data, 'wb') as out:
        out.write(encoded)

if __name__ == '__main__':
    main()
