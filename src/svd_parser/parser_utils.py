from bs4 import BeautifulSoup
import em
import json
import os

######## Generic parsing utilities
def parse_properties_from_xml(input_filename):
    with open(input_filename) as f:
        return BeautifulSoup(f.read(), 'xml')

# Read a JSON extension file
def get_json(input_filename):
    with open(input_filename) as f:
        return json.load(f)

def apply_extension(extension, properties):
    return apply_extension_impl(extension, properties, properties)

# Recursively propagate JSON extension map into the parsed soup
def apply_extension_impl(extension, properties, root):
    for element in extension:
        property_tags = properties.find_all(element, limit=1)
        # If the key "element" is already in the property tree:
        if len(property_tags) > 0:
            # Override the element
            for property_tag in property_tags:
                if type(extension[element]) == dict:
                    apply_extension_impl(extension[element], property_tag, root)
                else:
                    # leaf case
                    property_tag.string = extension[element]
        else:
            # Add the element to the property tree
            if type(extension[element]) == dict:
                # recursively call add_properties on the children of this 
                element_tag = root.new_tag(element)
                properties.append(element_tag)
                apply_extension_impl(extension[element], element_tag, root)
            else:
                # leaf case; the value is an element
                element_tag = root.new_tag(element)
                properties.append(element_tag)
                element_tag.string = str(extension[element])


######## Template expansion
def expand_template(in_filename, out_filename, context_pairs = None):
    interpreter = em.Interpreter(output=open(out_filename, 'w'))
    if context_pairs:
        for p in context_pairs:
            if len(p) != 2:
                raise RuntimeError('context_pairs input was incorrect size')
            interpreter.globals[p[0]] = p[1]

    # package the entire formatting utilities module in the interpreter context
    import format_utils
    for name, val in format_utils.__dict__.iteritems():
        interpreter.globals[name] = val

    interpreter.file(open(in_filename, 'r'))
    interpreter.shutdown()

def write_final_header(properties, output_headers, out_directory):
    with open(os.path.join(out_directory, properties.find('name').string + '.hpp'), 'w') as f:
        f.write('#pragma once\n')
        for header in output_headers:
            f.write('#include <{}>\n'.format(header))

def parse_device(in_filename, out_directory, ext_filename=None):
    output_headers = []
    template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')

    properties = parse_properties_from_xml(in_filename)
    if ext_filename:
        extension = get_json(ext_filename)
        apply_extension(extension, properties)
    io = properties.find('io')

    vendor_folder = os.path.split(os.path.dirname(in_filename))[-1]
    final_out_directory = os.path.join(
            out_directory,
            properties.device.cpu.find('name').string,
            vendor_folder,
            properties.device.find('name').string)

    if not os.path.exists(final_out_directory):
        os.makedirs(final_out_directory)

    if io:
        io_context = [('io', io), ('device', properties.device)]
        io_path = os.path.join(final_out_directory, 'Io.hpp')
        expand_template(os.path.join(template_dir, 'io.hpp.template'),
                io_path, context_pairs=io_context)
        output_headers.append(io_path)

    for peripheral in properties.find_all('peripheral'):
        if peripheral.find('name') is None:
            continue
        output_name = os.path.join(final_out_directory, peripheral.find('name').string + '.hpp')
        peripheral_context = [('peripheral', peripheral), ('properties', properties)]
        expand_template(
                os.path.join(template_dir, 'peripheral.hpp.template'),
                output_name, context_pairs=peripheral_context)
        output_headers.append(output_name)

    write_final_header(properties, output_headers, out_directory)
