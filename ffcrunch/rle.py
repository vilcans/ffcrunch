#!/usr/bin/env python
import argparse
from array import array

min_repeats = 3
max_repeats = 127 + min_repeats


def get_run_length(data, from_index, max_repeats):
    run_length = 1
    value = data[from_index]
    max_len = min(len(data) - from_index, max_repeats)
    while run_length < max_len and data[from_index + run_length] == value:
        run_length += 1
    return run_length


def find_runs(data, min_repeats=3, max_repeats=128):
    run_start = 0
    i = 0
    while run_start + i < len(data):
        run_length = get_run_length(data, run_start + i, max_repeats)
        if run_length >= min_repeats:
            #print 'Uncompressed', data[run_start:run_start+i]
            if i != 0:
                yield None, data[run_start:run_start+i]
            yield run_length, data[run_start + i]
            #print data[run_start + i], 'repeated', run_length
            run_start = run_start + i + run_length
            i = 0
        else:
            i += run_length
            # TODO: check for overflow in i

    if i != 0:
        yield None, data[run_start:run_start+i]


# 0 = repeat next byte 3 times (assuming min_repeats=3)
# 1 = repeat next byte 4 times
# 2 = repeat next byte 5 times
# .
# .
# 127 = repeat next byte 130 times
# 128 = repeat next byte 128 times
# 129 = repeat next byte 127 times
# .
# .
# 254 = repeat next byte 2 times
# 255 = repeat next byte 1 time


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
    result = array('B')
    #max_repeats = 10

    for compress, runs in find_runs(data, max_repeats=max_repeats):
        print 'compress', compress, 'runs', runs
        if compress:
            repeats, value = compress, runs
            # Format (repeats, value)
            # where repeats is numbers of repeats minus min_repeats.
            header = repeats - min_repeats
            assert 0 <= header <= 127, 'Out of range: ' + str(header)
            result.append(header)
            result.append(value)
        else:
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
