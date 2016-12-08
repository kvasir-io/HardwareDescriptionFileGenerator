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

def parse_device(in_filename, out_directory, ext_filename = None):
    properties = parse_properties_from_xml(in_filename)
    if ext_filename:
        extension = get_json(ext_filename)
        apply_extension(extension, properties)
    io = properties.find('io')

    if io:
        io_context = [('io', io), ('device', properties.device)]
        expand_template('../templates/io.hpp.template',
                os.path.join(out_directory, 'Io.hpp'), context_pairs=io_context)

    for peripheral in properties.find_all('peripheral'):
        # TODO May need to sanitize the peripheral filename
        if peripheral.find('name') is None:
            continue
        output_name = os.path.join(out_directory, peripheral.find('name').string + '.hpp')
        peripheral_context = [('peripheral', peripheral)]
        expand_template(
                '../templates/peripheral.hpp.template',
                output_name, context_pairs=peripheral_context)

