#!/usr/bin/env python
import argparse
from array import array

min_repeats = 3
max_repeats = 127 + min_repeats
max_verbatim = 128


def get_run_length(data, from_index):
    run_length = 1
    value = data[from_index]
    max_len = min(len(data) - from_index, max_repeats)
    while run_length < max_len and data[from_index + run_length] == value:
        run_length += 1
    return run_length


def find_runs(data):
    run_start = 0
    i = 0
    while run_start + i < len(data):
        run_length = get_run_length(data, run_start + i)
        if run_length >= min_repeats:
            if i != 0:
                yield None, data[run_start:run_start + i]
            yield run_length, data[run_start + i]
            run_start = run_start + i + run_length
            i = 0
        else:
            i += run_length

    if i != 0:
        yield None, data[run_start:run_start + i]


# 0 = repeat next byte 3 times (assuming min_repeats=3)
# 1 = repeat next byte 4 times
# 2 = repeat next byte 5 times
# .
# .
# 127 = repeat next byte 130 times
# 128 = copy next 128 bytes verbatim
# 129 = copy next 127 bytes verbatim
# .
# .
# 254 = copy next 2 bytes verbatim
# 255 = copy next 1 byte verbatim


def decompress(data):
    result = array('B')
    i = 0
    while i < len(data):
        header = data[i]
        i += 1
        if header >= 128:
            count = 256 - header
            result += data[i:i+count]
            i += count
        else:
            count = header + min_repeats
            result.extend([data[i]] * count)
            i += 1
    return result


def compress(data):
    """
    Verbatim data is encoded as (256 - length) followed by the data.

    >>> compress(array('B', [42]))
    array('B', [255, 42])
    >>> compress(array('B', [2, 3, 4, 5]))
    array('B', [252, 2, 3, 4, 5])

    Long stretches of verbatim data are encoded as several blocks.
    For example, 130 values will be a block of 128 then a block of 2:

    >>> compress(array('B', range(130)))  # doctest: +ELLIPSIS
    array('B', [128, 0, 1, 2, ..., 127, 254, 128, 129])

    Repeated values are encoded as (number_of_repeats - min_repeats):

    >>> compress(array('B', [1, 1, 1, 1, 1]))
    array('B', [2, 1])
    >>> compress(array('B', [1, 1, 1]))
    array('B', [0, 1])

    Really long repeated values are encoded as several runs:
    >>> compress(array('B', [42] * 231))
    array('B', [127, 42, 98, 42])

    Repeated runs shorter than min_repeats are coded as verbatim data:

    >>> compress(array('B', [1, 1]))
    array('B', [254, 1, 1])
    """

    result = array('B')

    for compress, runs in find_runs(data):
        if compress:
            repeats, value = compress, runs
            # Format (repeats, value)
            # where repeats is numbers of repeats minus min_repeats.
            header = repeats - min_repeats
            assert 0 <= header <= 127, 'Out of range: ' + str(header)
            result.append(header)
            result.append(value)
        else:
            while len(runs) > max_verbatim:
                #print 'cutting off', max_verbatim, 'from', runs
                result.append(128)
                result += array('B', runs[:max_verbatim])
                runs = runs[max_verbatim:]
            #print 'cutting done; verbatim data left:', runs
            if runs != '':
                header = 256 - len(runs)
                assert 128 <= header <= 255, 'Out of range: ' + str(header)
                result.append(header)
                result += array('B', runs)
    return result


def main():
    parser = argparse.ArgumentParser(description='RLE encoder')
    parser.add_argument(
        'input', metavar='INPUT_FILE',
        help='File to compress')
    parser.add_argument(
        'output', metavar='OUTPUT_FILE',
        help='File to save to')

    args = parser.parse_args()

    raw_data = array('B', open(args.input).read())

    encoded = compress(raw_data)
    decoded = decompress(encoded)
    assert raw_data == decoded, 'raw_data=%s decoded=%s' % (raw_data, decoded)
    with open(args.output, 'wb') as out:
        out.write(encoded)

if __name__ == '__main__':
    main()
