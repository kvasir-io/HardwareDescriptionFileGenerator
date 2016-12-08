from svd_parser import parser_utils, format_utils

import os

# parser_utils.parse_device('../data/MK11D5WS.svd', '/tmp', ext_filename='../data/extensions/MK11D5WS.json')

in_filename = '../data/MK11D5WS.svd'
ext_filename = '../data/extensions/MK11D5WS.json'
out_directory = '/tmp'

properties = parser_utils.parse_properties_from_xml(in_filename)

register = format_utils.lookup(properties, 'register', 'BACKKEY3')[0]
if not register:
    raise RuntimeError('argh')

field_tag = format_utils.expand_register_as_field(register, properties)

if ext_filename:
    extension = parser_utils.get_json(ext_filename)
    parser_utils.apply_extension(extension, properties)
io = properties.find('io')

if io:
    io_context = [('io', io), ('device', properties.device)]
    parser_utils.expand_template('../templates/io.hpp.template',
            os.path.join(out_directory, 'Io.hpp'), context_pairs=io_context)

for peripheral in properties.find_all('peripheral'):
    # TODO May need to sanitize the peripheral filename
    if peripheral.find('name') is None:
        continue
    output_name = os.path.join(out_directory, peripheral.find('name').string + '.hpp')
    peripheral_context = [('peripheral', peripheral)]
    parser_utils.expand_template(
            '../templates/peripheral.hpp.template',
            output_name, context_pairs=peripheral_context)

