from svd_parser import format_utils
from svd_parser.parser_utils import *

import os

# parser_utils.parse_device('../data/MK11D5WS.svd', '/tmp', ext_filename='../data/extensions/MK11D5WS.json')

#in_filename = '../data/MK11D5WS.svd'
#ext_filename = '../data/extensions/MK11D5WS.json'
#in_filename = '../data/nrf52.svd'
#ext_filename = None

in_filename = '../data/STMicro/STM32L4x6.svd'
ext_filename = None


out_directory = '/tmp'

output_headers = []
template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'svd_parser/templates')

properties = parse_properties_from_xml(in_filename)

if ext_filename:
    extension = get_json(ext_filename)
    apply_extension(extension, properties)
io = properties.find('io')

vendor_folder = os.path.split(os.path.dirname(in_filename))[-1]

final_out_directory = out_directory

if properties.device.cpu:
    cpuname = properties.device.cpu.find('name')
    if cpuname:
        final_out_directory = os.path.join(final_out_directory, cpuname.string)

final_out_directory = os.path.join(
        final_out_directory,
        vendor_folder,
        properties.device.find('name').string)

if not os.path.exists(final_out_directory):
    os.makedirs(final_out_directory)

if io:
    io_path = os.path.join(final_out_directory, 'Io.hpp')
    output_headers.append(io_path)

    # This takes a long time.
    io_context = [('io', io), ('device', properties.device)]
    expand_template(os.path.join(template_dir, 'io.hpp.template'),
            io_path, context_pairs=io_context)

for peripheral in properties.find_all('peripheral'):
    if peripheral.find('name') is None:
        continue
    output_name = os.path.join(final_out_directory, peripheral.find('name').string + '.hpp')
    output_headers.append(output_name)

    peripheral_context = [('peripheral', peripheral), ('properties', properties)]
    expand_template(
            os.path.join(template_dir, 'peripheral.hpp.template'),
            output_name, context_pairs=peripheral_context)

