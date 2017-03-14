#!/usr/bin/env python

import parser_utils
from sys import argv
from sys import stderr

def main():
    if len(argv) < 2:
        print('Usage: parse_device.py <input_file> <output_directory>')
        exit(1)

    input_filename, output_directory = argv[1], argv[2]
    extension_filename = None
    if len(argv) > 3:
        extension_filename = argv[3]
    parser_utils.parse_device(
            input_filename, output_directory, ext_filename=extension_filename)

if __name__ == '__main__':
    main()
