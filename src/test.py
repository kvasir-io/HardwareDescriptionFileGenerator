from svd_parser import parser_utils as utils
from svd_parser import format_utils as fmt_utils

properties = utils.parse_properties_from_xml('../data/MK11D5WS.svd')
extension = utils.get_json('../data/extensions/MK11D5WS.json')

utils.apply_extension(extension, properties)

io_context = [('io', properties.find('io')), ('device', properties.device)]
utils.expand_template('../templates/io.hpp.template', 'Io.hpp', context_pairs=io_context)


for peripheral in properties.find_all('peripheral'):
    # TODO May need to sanitize the peripheral filename
    if peripheral.find('name') is None:
        continue
    output_name = peripheral.find('name').string + '.hpp'
    peripheral_context = [('peripheral', peripheral)]
    utils.expand_template('../templates/peripheral.hpp.template', output_name, context_pairs=peripheral_context)
