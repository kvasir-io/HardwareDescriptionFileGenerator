from svd_parser import parser_utils

import os
import sys

if len(sys.argv) < 3:
    exit(-1)

# argv has the path to write to and the to all headers to include
# 1 header per device.
# in_path specifies where the cmsis_svd files are
out_path = sys.argv[1]
svd_file = sys.argv[2]
device_name = parser_utils.get_device_name(svd_file)

# Parse the name out of the svd file
headers = device_name + '.hpp'

out_dir = os.path.dirname(out_path)
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
parser_utils.expand_template(
        os.path.join(template_dir, 'test_headers.hpp.template'), out_path, [('headers', headers)])
