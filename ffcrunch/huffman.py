#!/usr/bin/env python

import sys
import argparse
import struct
import re

from heapq import heappush, heappop, heapify
from collections import defaultdict
from array import array

internal_node_value = 0xa5


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


def to_bits(value, length):
    s = bin(value).split('b')[1]
    assert len(s) <= length, 'Value ' + s + ' is longer than ' + str(length)
    s = '0' * (length - len(s)) + s
    assert len(s) == length
    return s


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

        if index != 0:
            new_code = _get_next_code(
                new_code, len(old_code) - len(sorted_tree[index - 1][1])
            )

        code_str = to_bits(new_code, len(old_code))
        assert len(code_str) == len(old_code), \
            'Should have same length: ' + old_code + " and " + code_str
        #print 'Old code ', old_code, 'new code', code_str
        result.append((symbol, code_str))

    return result


def _get_next_code(code, length_difference):
    """Get the next code in canonical code order.
    """
    assert length_difference >= 0
    return (code + 1) << length_difference


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
    """Find the best tree with a given maximum height

    To lower the tree height, we round the weights of the symbols
    so the weights does not form fibonacci-like sequences, as described in
    http://www.arturocampos.com/cp_ch3-4.html
    """

    min_factor = 1e-9
    max_factor = 1.0

    factor = 1.0
    for iteration in range(30):
        tree = create_tree(raw_data, factor)
        height = get_tree_height(tree)
        if height <= max_height:
            min_factor = factor
        else:
            max_factor = factor
        factor = (min_factor + max_factor) * .5
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


def pack_tree(tree):
    """Serialize the tree data.
    Requires a canonical tree.
    Returns: list of (code length delta, symbol)

    >>> pack_tree([('B', '0'), ('A', '10'), ('C', '110'), ('D', '111')])
    [(1, 'B'), (1, 'A'), (1, 'C'), (0, 'D')]
    """
    result = []
    length = 0
    for symbol, code in tree:
        delta = len(code) - length
        result.append((delta, symbol))
        length = len(code)
    return result


def unpack_tree(serialized):
    """
    >>> unpack_tree([(1, 'B'), (1, 'A'), (1, 'C'), (0, 'D')])
    [('B', '0'), ('A', '10'), ('C', '110'), ('D', '111')]
    """
    result = []
    code = 0
    code_length = 0
    for i, (delta_length, symbol) in enumerate(serialized):
        if i != 0:
            code = _get_next_code(code, delta_length)
        code_length += delta_length
        result.append((symbol, to_bits(code, code_length)))
    return result


def save_unpacked_tree_source(tree, out):
    tree_height = max(len(code) for (value, code) in tree)

    out.write('; Tree of height {}:\n'.format(tree_height))
    out.write('; {}\n'.format(str(tree)))
    for level in xrange(tree_height + 1):
        level_values = [(internal_node_value, '')] * (1 << level)
        for (value, bits) in tree:
            i = int(bits, 2)
            if len(bits) == level:
                level_values[int(bits, 2)] = (ord(value), bits)
        for i, (v, b) in enumerate(level_values):
            out.write(
                '\tdb ${:0>2x}  ; {}.{} {}\n'.format(v, level, i, b)
            )


def save_tree(tree, out):
    """Saves the packed tree in binary format.

    Format:
        1 byte: height of tree, i.e. max code length (little endian)
        1 byte: "internal node indicator"
        1 byte: number of symbols (n) (0 for 256)
        1 byte: filler
        n*2 bytes: (length delta, symbol)
    """
    if internal_node_value in tree:
        print '"internal node indicator" value occurs in raw data; can not use it'
        sys.exit(1)

    tree_height = get_tree_height(tree)
    print 'tree_height =', tree_height
    print 'internal_node_value =', internal_node_value
    print 'number_of_symbols =', len(tree)
    out.write(struct.pack(
        '<BBBB',
        tree_height,
        internal_node_value,
        len(tree) & 0xff,
        0xff
    ))

    bits = ''
    for (symbol, code) in tree:
        # code length, code (word, little endian), symbol
        bits += '[codelen]'
        bits += to_bits(len(code), tree_height)
        bits += '[code]'
        bits += code
        bits += '[symbol]'
        bits += to_bits(ord(symbol), 8)

    print 'bits:', bits
    bits = re.sub(r'[^01]', '', bits)
    out.write(bits_to_bytes(bits))


def main():
    parser = argparse.ArgumentParser(description='Huffman encoder')
    parser.add_argument(
        '--tree', metavar='FILE', required=True, type=argparse.FileType('wb'),
        help='Save Huffman tree to this file')
    parser.add_argument(
        '--stree', metavar='FILE', required=True, type=argparse.FileType('w'),
        help='Save unpacked Huffman tree to this assembly source file')
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
    if args.stree:
        save_unpacked_tree_source(tree, args.stree)
    with open(args.data, 'wb') as out:
        out.write(encoded)

if __name__ == '__main__':
    main()
