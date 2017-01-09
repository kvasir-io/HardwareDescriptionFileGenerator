from svd_parser import parser_utils

import os
import sys

if len(sys.argv) < 3:
    exit(-1)

# argv has the path to write to and the to all headers to include
in_path = sys.argv[1]
out_path = sys.argv[2]

headers = []
# Gather all headers under in_path
for root, dirs, files in os.walk(in_path):
    for f in files:
        if f.endswith('.hpp'):
            headers.append(f)

template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
parser_utils.expand_template(os.path.join(template_dir, 'test_headers.cpp.template'), out_path, [('headers', headers)])

