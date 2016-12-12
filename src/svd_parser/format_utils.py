from functools import reduce
from operator import add
import re


######## CMSIS SVD-specific formatting utilities
#### IO

def padded_hex(n):
    # int n
    # return hex-encoded string with 8 digits
    return "{0:#0{1}x}".format(n,10)

def has_group(io):
    return 'group' in [x.string for x in io.find_all('type')]

def expand_ports(io):
    ports = io.find('ports').string

    if ',' in ports:
        return ports.split(',')
    elif '-' in ports:
        m = ports.split('-')
        if m[1].isdigit():
            return range(int(m[1]),int(m[2]))
        elif len(m[1]) == 1:
            return [chr(i) for i in range(ord(m[0][0]),ord(m[1][0])+1)]
    return [ports]

def port_number(port):
    if not port.isdigit():
        return ord(port)-ord('A')
    return port

# Technically this is a generic property function and should go in parser_utils
def lookup(properties, key, name):
    return [p for p in properties.find_all(key) if p.find('name') and p.find('name').string == name]

def io_address(io, key, device, port):
    peripheral_name = io.find('peripheral').string.replace('%s', port)
    register_name = key.register.string

    # Get the peripheral with this name
    peripheral = lookup(device, 'peripheral', peripheral_name)
    if len(peripheral) > 1:
        raise RuntimeError('non-unique peripheral found')
    if len(peripheral) == 0:
        raise RuntimeError('no peripheral named [' + peripheral_name + '] found')

    peripheral = peripheral[0]

    base_address = int(peripheral.baseAddress.string, 0)

    if base_address is None:
        raise RuntimeError(
                'No base address field found for peripheral ['
                + peripheral_name + ']' )

    address_offset = None
    for register in peripheral.find_all('register'):
        if register.find('name').string == register_name:
            address_offset = int(register.addressOffset.string, 0)
            break

    if address_offset is None:
        raise RuntimeError(
                'No address offset field found for peripheral ['
                + peripheral_name + ']' )

    return padded_hex(base_address + address_offset)

def clearBitsFromRange(msb, lsb, previous = 0):
    for ii in range(lsb,msb+1):
        previous &= ~(1<<ii)
    return previous

def setBitsFromRange(msb, lsb, previous = 0):
    for ii in range(lsb,msb+1):
        previous |= (1<<ii)
    return previous

# io_key: tag
# device: tag
# port: str
def reserved(io, key, device, port):
    peripheral_name = io.find('peripheral').string.replace('%s', port)
    register_name = key.register.string

    reserved = 0xFFFFFFFF

    peripheral = lookup(device, 'peripheral', peripheral_name)[0]
    register = lookup(device, 'register', register_name)[0]

    for field in register.find_all('field'):
        clearBitsFromRange(int(field.bitOffset.string) + int(field.bitWidth.string) - 1,
                int(field.bitOffset.string),
                reserved)
    return padded_hex(reserved)

def action(key):
    if key.name == 'read':
        return 'ReadAction'
    return 'WriteLiteralAction<{0} << Pin>'.format(key.value.string)

#### Registers
def format_namespace(x):
    r = re.compile('[^a-zA-Z0-9_]')
    return reduce(add, map(lambda s: s.lower(), r.sub('', x).lower().split('_')))

def format_register_name(peripheral, reg):
    x = peripheral.find('name').string + '_' + reg.find('name').string
    return format_namespace(x)

def register_address(peripheral, register, cluster):
    if cluster:
        return padded_hex(int(peripheral.baseAddress.string, 0)
                + int(cluster.addressOffset.string, 0)
                + int(register.addressOffset.string, 0))

    return padded_hex(int(peripheral.baseAddress.string, 0)
                + int(register.addressOffset.string, 0))

def register_type(register):
    if register.size and int(register.size.string) is 8:
        return 'unsigned char'
    return 'unsigned'

register_to_keys = {
    'name' : 'name',
    'description' : 'description',
    'modifiedWriteValues' : 'modifiedWriteValues',
    'writeConstraint' : 'writeConstraint',
    'readAction' : 'readAction',
    'addressOffset' : 'bitOffset'
}

def expand_register_as_field(register, root):
    from bs4 import BeautifulSoup
    # TODO Is there a fancy transformation we can do to map the register schema to the field schema
    # in a generic fashion?
    # TODO This could be a bit more succinct.
    field_tag = root.new_tag('field')
    register.append(field_tag)
    bitwidth = root.new_tag('bitWidth')
    field_tag.append(bitwidth)
    bitwidth.string = '8'  # TODO don't hardcode this?
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
        modified_write_values = field.modifiedWriteValues.string

    read_action = 'normal'
    if field.readAction:
        read_action = field.readAction.string

    access = 'read-write'
    if field.access:
        access = field.access.string
        access = dash_to_camel_case(field.access.string)

    access = access[0].lower() + access[1:]

    if access == 'readWrite' and modified_write_values == 'normal' and read_action == 'normal':
        return 'ReadWriteAccess'
    return 'Access<Register::AccessType::%s,Register::ReadActionType::%s,Register::ModifiedWriteValueType::%s>' % (
            access,read_action,modified_write_values)

def parse_bit_range(bit_range):
    if (len(bit_range.string) < 5):
        raise RuntimeError('bitRange field contained insufficient characters')
    return bit_range.string[1:-1].split(':')

def msb(field):
    if field.bitOffset and field.bitWidth:
        return int(field.bitOffset.string, 0) + int(field.bitWidth.string) - 1
    elif field.bitRange:
        return int(parse_bit_range(field.bitRange)[0])
    elif field.msb:
        return int(field.msb.string)
    else:
        raise RuntimeError('Bit offset/width style was not specified in field: ' + field.__str__())

def lsb(field):
    if field.bitOffset and field.bitWidth:
        return int(field.bitOffset.string, 0)
    elif field.bitRange:
        return int(parse_bit_range(field.bitRange)[1])
    elif field.lsb:
        return int(field.lsb.string)
    else:
        raise RuntimeError('Bit offset/width style was not specified')

def no_action_if_zero_bits(register):
    no_action = 0xFFFFFFFF
    for field in register.find_all('fields'):
        if 'oneTo' not in access(field):
            clearBitsFromRange(msb(field), lsb(field), no_action)
    return padded_hex(no_action)

def no_action_if_one_bits(register):
    no_action = 0x00000000
    for field in register.find_all('fields'):
        if 'zeroTo' in access(field):
            setBitsFromRange(msb(field), lsb(field), no_action)
    return padded_hex(no_action)

def use_enumerated_values(field):
    #if len(field.find_all('enumeratedValue')) > 4 or int(field.bitWidth.string) <= 2:
    # TODO there's a workaround we're missing here?
    if len(field.find_all('enumeratedValue')) > 4:
        return True
    return False

def format_variable(v):
    #all c++ keywords
    cppKeywords = ['alignas','alignof','and','asm','auto','bitand','bitor','bool','break','case',\
    'catch','char','class','compl','concept','const','constexpr','continue','decltype','default',\
    'delete','do','double','else','enum','explicit','export','extern','false','float','for'\
    'friend','goto','if','inline','int','long','mutable','namespace','new','noexcept','not'\
    'nullptr','operator','or','private','protected','public','register','requires','return'\
    'short','signed','sizeof','static','struct','switch','template','this','throw','true'\
    'try','typedef','typeid','typename','union','unsigned','using','virtual','void','volatile'\
    'while','xor']

    out = format_namespace(v)
    out = out[:1].lower()+out[1:]
    if out in cppKeywords:
        out += '_'              #suffix register names that are c++ keywords to prevent clash
    return out

def format_enum_value_name(v):
    value = v.find('name').string
    if value[:1].isdigit():
        value = 'v' + value
    return format_variable(value)

def format_enum_value(v):
    value = v.value.string
    # Freescale nonsense
    if value.startswith('#'):
        if 'x' in value:
            value = value.replace('x', '0')
        # Encode as binary
        return padded_hex(int(value[1:], 2))
    return padded_hex(int(value, 0))

def is_default(v):
    if v.isDefault:
        return True

# Make sure to filter out C++ keywords
def format_field_name(field):
    return format_variable(field.find('name').string)
