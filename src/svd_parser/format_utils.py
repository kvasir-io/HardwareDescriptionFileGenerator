from bs4 import BeautifulSoup
import bs4.element
from functools import reduce
from operator import add
import math
import re

######## CMSIS SVD-specific formatting utilities
#### IO

def padded_hex(n):
    # return hex-encoded string with 8 digits
    return "{0:#0{1}x}".format(n, 10)


def has_group(io):
    if io.default:
        if io.default.type:
            return 'group' == io.default.type.string

    return False


def expand_ports(io):
    ports = get_str(io.find('ports'))

    if ',' in ports:
        return ports.split(',')
    elif '-' in ports:
        m = ports.split('-')
        if m[1].isdigit():
            return range(int(m[1]), int(m[2]))
        elif len(m[1]) == 1:
            return [chr(i) for i in range(ord(m[0][0]), ord(m[1][0]) + 1)]
    return [ports]


def port_number(port):
    if not port.isdigit():
        return ord(port) - ord('A')
    return port


def sanitize_int(s, base=0):
    # Find the consecutive leading zeros and strip them
    c = s[0]
    i = 0
    while c == '0' and i < len(s) - 1:
        i += 1
        c = s[i]

    if (c == 'x' or c == 'X') and i > 0:
        i -= 1

    return int(s[i:], base)


# Technically this is a generic property function and should go in parser_utils
def unique_lookup(properties, key, name, recursive=False):
    result = [p for p in properties.find_all(key, recursive=recursive)
            if p.find('name') and p.find('name').string == name]
    if len(result) > 1:
        raise RuntimeError('non-unique property found')
    if len(result) == 0:
        raise RuntimeError('no property named [' + name + '] found')
    return result[0]


def io_address(io, key, device, port):
    peripheral_name = get_str(io.find('peripheral')).replace('%s', port)
    register_name = get_str(key.register)

    # Get the peripheral with this name
    peripheral = unique_lookup(device.peripherals, 'peripheral', peripheral_name)

    base_address = get_base_address(peripheral)


    if base_address is None:
        raise RuntimeError(
                'No base address field found for peripheral ['
                + peripheral_name + ']')

    address_offset = None
    for register in peripheral.find_all('register'):
        if register.find('name').string == register_name:
            address_offset = sanitize_int(register.addressOffset.string, 0)
            break

    if address_offset is None:
        raise RuntimeError(
                'No address offset field found for peripheral ['
                + peripheral_name + ']')

    return padded_hex(base_address + address_offset)


def clearBitsFromRange(msb, lsb, previous=0):
    for ii in range(lsb, msb + 1):
        previous &= ~(1 << ii)
    return previous


def setBitsFromRange(msb, lsb, previous=0):
    for ii in range(lsb, msb + 1):
        previous |= (1 << ii)
    return previous


# io_key: tag
# device: tag
# port: str
def reserved(io, key, device, port):
    peripheral_name = get_str(io.find('peripheral')).replace('%s', port)
    register_name = get_str(key.register)

    reserved = 0xFFFFFFFF

    peripheral = unique_lookup(device.peripherals, 'peripheral', peripheral_name)
    register = unique_lookup(peripheral.registers, 'register', register_name)

    for field in register.find_all('field'):
        if field.bitOffset is not None and field.bitWidth is not None:
            clearBitsFromRange(sanitize_int(field.bitOffset.string) + sanitize_int(field.bitWidth.string) - 1,
                    sanitize_int(field.bitOffset.string),
                    reserved)
        elif field.bitRange is not None:
            bit_range = parse_bit_range(field.bitRange)
            clearBitsFromRange(sanitize_int(bit_range[0], 0), sanitize_int(bit_range[1], 0), reserved)
        elif field.msb is not None and field.lsb is not None:
            # return sanitize_int(field.msb.string, 0)
            clearBitsFromRange(sanitize_int(field.msb.string, 0), sanitize_int(field.lsb.string, 0), reserved)
    return padded_hex(reserved)


def action(key):
    if key.name == 'read':
        return 'ReadAction'
    return 'WriteLiteralAction<{0} << Pin>'.format(get_str(key.value))


#### Registers
def format_namespace(x):
    # TODO This strips out the underscore, which we might actually want
    r = re.compile('[^a-zA-Z0-9_]')
    # return reduce(add, map(lambda s: s.lower(), r.sub('', x).lower().split('_')))
    return '_'.join(map(lambda s: s.lower(), r.sub('', x).lower().split('_')))


def format_register_name(peripheral, reg):
    x = get_str(peripheral.find('name')) + '_' + get_str(reg.find('name'))
    return format_namespace(x)


def get_base_address(peripheral):
    return sanitize_int(peripheral.baseAddress.string, 0)

def register_address(peripheral, register, cluster):
    base_address = get_base_address(peripheral)
    registerOffset = 0
    if not register.addressOffset is None:
        registerOffset = sanitize_int(register.addressOffset.string, 0)

    address = base_address + registerOffset

    if cluster and not cluster.addressOffset is None:
        address += sanitize_int(cluster.addressOffset.string, 0)

    if address > 2**32 - 1:
        # TODO This is a dumb workaround
        return "static_cast<" + register_type(register) + ">(" + padded_hex(address) + ")"

    return padded_hex(address)

def parse_array(element):
    if element.dimIndex:
        # use custom indices
        # TODO
        if '-' in element.dimIndex.string:
            first, last = element.dimIndex.string.split('-')
            indices = range(int(first), int(last) + 1)
        else:
            indices = [int(i) for i in element.dimIndex.string.split(',')]
    else:
        indices = range(sanitize_int(element.dim.string))
    out = []
    increment = sanitize_int(element.dimIncrement.string, 0)
    for index in indices:
        entry = element
        entry.addressOffset.string = str(sanitize_int(entry.addressOffset.string, 0)
                + increment * (index - indices[0]))
        name = element.find('name').string.replace('%s', str(index))
        entry.find('name').string = name
        out.append(entry)
    return out

def get_registers(peripheral):
    # get all the registers for this peripheral
    registers = peripheral.find('registers')
    out = {}
    if registers is None:
        return out
    for register in registers:
        if register is None or not type(register) == bs4.element.Tag or not register.name == 'register':
            continue
        register_name = register.find('name').string
        # TODO This is valid for registers, clusters, and fields. need to generalize
        if '[%s]' in register_name:
            register_array = parse_array(register)
            for reg_element in register_array:
                out[reg_element.find('name').string] = reg_element
        elif register_name in out:
            original_reg = out[register_name]
            is_alternate = register.alternateGroup or register.alternateRegister
            original_is_alternate = original_reg.alternateGroup or original_reg.alternateRegister
            if is_alternate or original_is_alternate:
                # Intentional redefinition of previous register
                # Append fields to existing register
                out[register_name] = append_fields(out[register_name], register)
        else:
            out[register_name] = register

    return out.values()

def append_fields(dst, src):
    if dst.find('fields') is None:
        if src.find('fields') is None:
            return dst
        dst, src = src, dst
    for field in src.find_all('field'):
        dst.find('fields').append(field)
    return dst

def register_type(register):
    # TODO What if register.size is hex
    if register.size and sanitize_int(register.size.string, 0) is 8:
        return 'unsigned char'
    return 'unsigned'

register_to_keys = {
    'name': 'name',
    'description': 'description',
    'modifiedWriteValues': 'modifiedWriteValues',
    'writeConstraint': 'writeConstraint',
    'readAction': 'readAction',
    'addressOffset': 'bitOffset'
}


def expand_register_as_field(register, root):
    # TODO Is there a fancy transformation we can do to map the register schema to the field schema
    # in a generic fashion?
    # TODO This could be a bit more succinct.
    field_tag = root.new_tag('field')
    register.append(field_tag)

    bitwidth = root.new_tag('bitWidth')
    field_tag.append(bitwidth)
    bitwidth.string = '8'  # TODO don't hardcode this? actually, is this correct?

    bitoffset = root.new_tag('bitOffset')
    field_tag.append(bitoffset)
    # TODO Get bitoffset based on the address offset
    address_offset = sanitize_int(register.addressOffset.string, 0)
    lsb = 0
    if address_offset > 0:
        lsb = int(math.log(address_offset & -address_offset, 2))

    bitoffset.string = str(lsb)

    for child in register:
        if child.name in register_to_keys:
            child_tag = root.new_tag(register_to_keys[child.name])
            field_tag.append(child_tag)
            child_tag.string = child.string
    return field_tag


def dash_to_camel_case(x):
    return ''.join([y.capitalize() for y in x.split('-')])


def access(field):
    modified_write_values = 'normal'
    if field.modifiedWriteValues:
        modified_write_values = get_str(field.modifiedWriteValues)

    read_action = 'normal'
    if field.readAction:
        read_action = get_str(field.readAction)

    access = 'readWrite'
    if field.access:
        access = get_str(field.access)
        access = dash_to_camel_case(get_str(field.access))

    access = access[0].lower() + access[1:]

    if access.lower() == 'readwriteonce':
        access = 'readWriteOnce'

    if access == 'readWrite' and modified_write_values == 'normal' and read_action == 'normal':
        return 'ReadWriteAccess'
    return 'Access<bit::AccessType::%s,bit::ReadActionType::%s,bit::ModifiedWriteValueType::%s>' % (
            access, read_action, modified_write_values)


def parse_bit_range(bit_range):
    if (len(bit_range.string) < 5):
        raise RuntimeError('bitRange field contained insufficient characters')
    return get_str(bit_range)[1:-1].split(':')


def msb(field):
    if field.bitOffset and field.bitWidth:
        return sanitize_int(field.bitOffset.string, 0) + sanitize_int(field.bitWidth.string, 0) - 1
    elif field.bitRange:
        return sanitize_int(parse_bit_range(field.bitRange)[0], 0)
    elif field.msb:
        return sanitize_int(field.msb.string, 0)
    else:
        raise RuntimeError('Bit offset/width style was not specified in field: ' + field.__str__())


def lsb(field):
    if field.bitOffset and field.bitWidth:
        return sanitize_int(field.bitOffset.string, 0)
    elif field.bitRange:
        return sanitize_int(parse_bit_range(field.bitRange)[1], 0)
    elif field.lsb:
        return sanitize_int(field.lsb.string, 0)
    else:
        raise RuntimeError('Bit offset/width style was not specified')


def no_action_if_zero_bits(register):
    no_action = 0xFFFFFFFF
    for field in register.find_all('field'):
        if 'oneTo' not in access(field):
            no_action = clearBitsFromRange(msb(field), lsb(field), no_action)
    return padded_hex(no_action)


def no_action_if_one_bits(register):
    no_action = 0x00000000
    for field in register.find_all('fields'):
        if 'zeroTo' in access(field):
            no_action = setBitsFromRange(msb(field), lsb(field), no_action)
    return padded_hex(no_action)


def use_enumerated_values(field):
    # TODO: I think there's a workaround we're missing here
    return len(field.find_all('enumeratedValue')) > 1


def format_variable(v):
    #all c++ keywords
    cppKeywords = set(['alignas', 'alignof', 'and', 'asm', 'auto', 'bitand', 'bitor', 'bool', 'break', 'case', \
    'catch', 'char', 'class', 'compl', 'concept', 'const', 'constexpr', 'continue', 'decltype', 'default', \
    'delete', 'do', 'double', 'else', 'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', \
    'friend', 'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not', \
    'nullptr', 'operator', 'or', 'private', 'protected', 'public', 'register', 'requires', 'return', \
    'short', 'signed', 'sizeof', 'static', 'struct', 'switch', 'template', 'this', 'throw', 'true', \
    'try', 'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile' \
    'while', 'xor'])

    out = format_namespace(v)
    out = out[:1].lower() + out[1:]
    if out in cppKeywords:
        out += '_'              # suffix register names that are c++ keywords to prevent clash
    return out


def format_enum_value_name(v):
    value = get_str(v.find('name'))
    if value[:1].isdigit():
        value = 'v' + value
    return format_variable(value)


def format_enum_value(v):
    value = get_str(v.value)
    # Freescale nonsense
    if value.startswith('#'):
        if 'x' in value:
            value = value.replace('x', '0')
        # Encode as binary
        return padded_hex(sanitize_int(value[1:], 2))
    return padded_hex(sanitize_int(value, 0))


def is_default(v):
    return v.isDefault


# Make sure to filter out C++ keywords
def format_field_name(field):
    return format_variable(get_str(field.find('name')))


def get_str(prop):
    if prop:
        if hasattr(prop, 'string') and prop.string:
            # Strip the unicode characters
            stripped = ''.join(c for c in prop.string if ord(c) < 128)
            return stripped
    return ''

def override_peripheral(peripheral, parent):
    assert not parent is None
    assert not peripheral is None

    parent_copy = parent
    # For all the tags in peripheral that are specified, override them in parent_copy
    for child in peripheral.children:
        if type(child) is bs4.element.Tag:
            original = parent.find(child.name)
            original.replace_with(child)

    return parent_copy
