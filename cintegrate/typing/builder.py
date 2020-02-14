import ctypes
from types import FunctionType
from .utils import die_from_offset
from .complex import map_struct, map_union, map_class

def map_base_type(die, builder):
    encoding = die.attributes['DW_AT_encoding'].value
    byte_size = die.attributes['DW_AT_byte_size'].value
    name = die.attributes['DW_AT_name'].value

    #float
    if encoding == 4:
        return ctypes.c_float

    #double
    if b'double' in name:
        if byte_size == 8:
            return ctypes.c_double
        elif byte_size == 12:
            return ctypes.c_longdouble

    #integer / char
    is_signed = encoding in [5, 6, 0xd]
    is_char = encoding in [6, 8]
    return getattr(ctypes, 'c_{}{}{}'.format('' if is_signed else 'u','char' if is_char else 'int', '' if is_char else byte_size * 8))

def map_typedef(die, builder):
    base_type_die = builder.get_die(die.attributes['DW_AT_type'].value)
    res_cls = builder.map(base_type_die)
    return type(die.attributes['DW_AT_name'].value.decode('utf-8'), (res_cls,), {})

def map_pointer(die, builder):
    base_type_die = builder.get_die(die.attributes['DW_AT_type'].value)
    res_cls = builder.map(base_type_die)
    # c_char apperntly overrides `isinstance` behaviour.
    if res_cls is None: 
        return None
    if ctypes.c_char in res_cls.mro():
        return ctypes.c_char_p
    return type(res_cls.__name__ + '_pointer', (ctypes.POINTER(res_cls),), {})

def is_declaration(cu, name, die):
    if die.tag == 'DW_TAG_variable':
        return False
    if 'DW_AT_declaration' in die.attributes and die.attributes['DW_AT_declaration'].value:
        return False
    if 'DW_AT_sibling' in die.attributes:
        sibling = die_from_offset(cu, die.attributes['DW_AT_sibling'].value)
        return 'DW_AT_name' in sibling.attributes and sibling.attributes['DW_AT_name'].value == name
    return 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == name


def map_declaration(die, builder):
    res_name = die.attributes['DW_AT_name'].value
    res_types = [res_die for res_die in (builder.cu.iter_DIEs()) if is_declaration(builder.cu, res_name, res_die)]
    if len(res_types) != 1:
        raise ValueError
    res = builder.map(res_types[0])
    res.__name__ = res_name.decode('utf-8')
    return res

def map_subprogram(die, builder):
    if 'DW_AT_linkage_name' not in die.attributes and 'DW_AT_name' not in die.attributes:
        raise TypeError
    linkage_name = die.attributes['DW_AT_name'].value.decode('utf-8') if 'DW_AT_linkage_name' not in die.attributes else die.attributes['DW_AT_linkage_name'].value.decode('utf-8')
    try:
        func = getattr(ctypes.cdll.LoadLibrary(str(builder.filename)), linkage_name)
    except AttributeError:
        return None
    param = [subdie for subdie in die.iter_children() if subdie.tag == 'DW_TAG_formal_parameter']
    param_types = [builder.map(builder.get_die(subdie.attributes['DW_AT_type'].value)) for subdie in param]
    func.argtypes = param_types
    func.restype = builder.map(builder.get_die(die.attributes['DW_AT_type'].value))
    return func

TYPE_GETTERS = {
    'DW_TAG_subprogram': map_subprogram,
    'DW_TAG_typedef': map_typedef,
    'DW_TAG_base_type': map_base_type,
    'DW_TAG_pointer_type': map_pointer,
    'DW_TAG_array_type': None,
    'DW_TAG_class_type': map_class,
    'DW_TAG_const_type': None,
    'DW_TAG_enumeration_type': None,
    'DW_TAG_interface_type': None,
    'DW_TAG_packed_type': None,
    'DW_TAG_ptr_to_member_type': None,
    'DW_TAG_reference_type': None,
    'DW_TAG_restrict_type': None,
    'DW_TAG_rvalue_reference_type': None,
    'DW_TAG_set_type': None,
    'DW_TAG_shared_type': None,
    'DW_TAG_string_type': None,
    'DW_TAG_structure_type': map_struct,
    'DW_TAG_subrange_type': None,
    'DW_TAG_subroutine_type': None,
    'DW_TAG_thrown_type': None,
    'DW_TAG_union_type': map_union,
    'DW_TAG_unspecified_type': None,
    'DW_TAG_volatile_type': None,
}

IGNORE_DECLARATION = ['DW_TAG_subprogram']

class Builder:
    def __init__(self, filename, cu):
        self.filename = filename
        self.cu = cu
        self.cache = {}

    def get_die(self, offset):
        return die_from_offset(self.cu, offset)

    def map(self, die):
        print(die.offset)
        if die.offset in self.cache:
            return self.cache[die.offset]
        res = None
        if die.tag not in IGNORE_DECLARATION and 'DW_AT_declaration' in die.attributes and die.attributes['DW_AT_declaration'].value:
            res = map_declaration(die, self)
        if die.tag in TYPE_GETTERS and TYPE_GETTERS[die.tag]:
            res = TYPE_GETTERS[die.tag](die, self)
        if res:
            self.cache[die.offset] = res
            return res