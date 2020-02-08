import ctypes

ANON_NAME = '__anon__'

def map_complex(die, builder, complex_type):
    res_name = die.attributes['DW_AT_name'].value.decode('utf-8') if 'DW_AT_name' in die.attributes else 'unnamed_' + complex_type
    fields = []
    anonymous  = ()
    # constructors = []
    # functions = {}
    for subdie in die.iter_children():
        if subdie.tag == 'DW_TAG_member':
            if 'DW_AT_name' not in subdie.attributes:
                name = ANON_NAME + str(len(anonymous))
                anonymous = tuple(list(anonymous) + [name])
            else:
                name = subdie.attributes['DW_AT_name'].value.decode('utf-8')

            fields.append((name, builder.map(builder.get_die(subdie.attributes['DW_AT_type'].value))))

        elif subdie.tag == 'DW_TAG_subprogram':
            if 'DW_AT_name' in subdie.attributes and subdie.attributes['DW_AT_name'].value == res_name.encode('utf-8'):
                # add to constructor
                # first arg is a pointer to self - a struct
                pass
            elif 'DW_AT_name' in subdie.attributes:
                # print(subdie)
                res_func = builder.map(subdie)
                print(subdie.attributes['DW_AT_name'].value, res_func)
                # add to functions
                pass
    # fields = [(child.attributes['DW_AT_name'].value.decode('utf-8'), builder(cu, die_from_offset(cu, child.attributes['DW_AT_type'].value))) for child in die.iter_children()]

    fields = list(filter(lambda x: x[1] is not None, fields))
    parent_cls = {'struct': ctypes.Structure, 'union': ctypes.Union, 'class': ctypes.Structure}[complex_type]
    return type(res_name, (parent_cls,), {'_fields_': fields, '_anonymous_': anonymous})

def map_struct(die, builder):
    return map_complex(die, builder, 'struct')

def map_union(die, builder):
    return map_complex(die, builder, 'union')

def map_class(die, builder):
    return map_complex(die, builder, 'class')