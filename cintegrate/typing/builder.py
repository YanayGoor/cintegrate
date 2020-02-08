import ctypes
from types import FunctionType

def die_from_offset(cu, offset):
    return [die for die in cu.iter_DIEs() if die.offset == offset][0]

def map_base_type(cu, die, builder):
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

def map_typedef(cu, die, builder):
    base_type_die = die_from_offset(cu, die.attributes['DW_AT_type'].value)
    res_cls = builder(cu, base_type_die)
    return type(die.attributes['DW_AT_name'].value.decode('utf-8'), (res_cls,), {})

def map_pointer(cu, die, builder):
    base_type_die = die_from_offset(cu, die.attributes['DW_AT_type'].value)
    res_cls = builder(cu, base_type_die)
    # c_char apperntly overrides `isinstance` behaviour.
    if res_cls is None: 
        return None
    if ctypes.c_char in res_cls.mro():
        return ctypes.c_char_p
    return type(res_cls.__name__ + '_pointer', (ctypes.POINTER(res_cls),), {})

def map_structure(cu, die, builder):
    name = 'unknown_struct' if 'DW_AT_name' not in die.attributes else die.attributes['DW_AT_name'].value.decode('utf-8')
    fields = [(child.attributes['DW_AT_name'].value.decode('utf-8'), builder(cu, die_from_offset(cu, child.attributes['DW_AT_type'].value))) for child in die.iter_children()]
    res_cls = type(name, (ctypes.Structure,), {'_fields_': fields})
    return res_cls

def map_union(cu, die, builder):
    name = 'unknown_union' if 'DW_AT_name' not in die.attributes else die.attributes['DW_AT_name'].value.decode('utf-8')
    fields = [(child.attributes['DW_AT_name'].value.decode('utf-8'), builder(cu, die_from_offset(cu, child.attributes['DW_AT_type'].value))) for child in die.iter_children()]
    res_cls = type(name, (ctypes.Union,), {'_fields_': fields})
    return res_cls

def is_declaration(cu, name, die):
    if die.tag == 'DW_TAG_variable':
        return False
    if 'DW_AT_declaration' in die.attributes and die.attributes['DW_AT_declaration'].value:
        return False
    if 'DW_AT_sibling' in die.attributes:
        sibling = die_from_offset(cu, die.attributes['DW_AT_sibling'].value)
        return 'DW_AT_name' in sibling.attributes and sibling.attributes['DW_AT_name'].value == name
    return 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == name


def map_declaration(cu, die, builder):
    res_name = die.attributes['DW_AT_name'].value
    res_types = [res_die for res_die in (cu.iter_DIEs()) if is_declaration(cu, res_name, res_die)]
    if len(res_types) > 1:
        raise ValueError
    res = builder(cu, res_types[0])
    res.__name__ = res_name.decode('utf-8')
    return res

TYPE_GETTERS = {
    'DW_TAG_typedef': map_typedef,
    'DW_TAG_base_type': map_base_type,
    'DW_TAG_pointer_type': map_pointer,
    'DW_TAG_array_type': None,
    'DW_TAG_class_type': None,
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
    'DW_TAG_structure_type': map_structure,
    'DW_TAG_subrange_type': None,
    'DW_TAG_subroutine_type': None,
    'DW_TAG_thrown_type': None,
    'DW_TAG_union_type': map_union,
    'DW_TAG_unspecified_type': None,
    'DW_TAG_volatile_type': None,
}

def get_class(cu, die):
    if 'DW_AT_declaration' in die.attributes and die.attributes['DW_AT_declaration'].value:
        return map_declaration(cu, die, get_class)
    if die.tag in TYPE_GETTERS and TYPE_GETTERS[die.tag]:
        return TYPE_GETTERS[die.tag](cu, die, get_class)
