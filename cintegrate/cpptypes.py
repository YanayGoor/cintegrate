from pathlib import PurePath
from elftools.elf.elffile import ELFFile
from .typing import get_class
import ctypes

def die_from_offset(cu, offset):
    return [die for die in cu.iter_DIEs() if die.offset == offset][0]

def get_type_from_file(filename, name):
    with open(str(filename), 'rb') as f:
        elffile = ELFFile(f)
        dwarf_info = elffile.get_dwarf_info()
        cu = list(dwarf_info.iter_CUs())[0]
        die = [die for die in (cu.iter_DIEs()) if 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == name.encode('utf-8')][0]
        return get_die_type(filename, cu, die)

def get_die_type(filename, cu, die):
    name = die.attributes['DW_AT_name'].value.decode('utf-8')
    if die.tag == 'DW_TAG_subprogram':
        linkage_name = name if 'DW_AT_linkage_name' not in die.attributes else die.attributes['DW_AT_linkage_name'].value.decode('utf-8')
        func = getattr(ctypes.cdll.LoadLibrary(str(filename)), linkage_name)
        param = [subdie for subdie in die.iter_children() if subdie.tag == 'DW_TAG_formal_parameter']
        param_types = [get_class(cu, die_from_offset(cu, subdie.attributes['DW_AT_type'].value)) for subdie in param]
        func.argtypes = param_types
        func.restype = get_class(cu, die_from_offset(cu, die.attributes['DW_AT_type'].value))
        return func
    return get_class(cu, die)

def cmp_decl_file(filename, files, die):
    return 'DW_AT_decl_file' in die.attributes \
        and len(files) >= die.attributes['DW_AT_decl_file'].value \
            and files[die.attributes['DW_AT_decl_file'].value-1].name == filename.with_suffix('.c').name.encode('utf-8')

def get_all_user_types(filename):
    with open(str(filename), 'rb') as f:
        elffile = ELFFile(f)
        dwarf_info = elffile.get_dwarf_info()
        cu = list(dwarf_info.iter_CUs())[0]
        files = dwarf_info.line_program_for_CU(cu)['file_entry']
        dies = filter(lambda die: 'DW_AT_name' in die.attributes, cu.iter_DIEs())
        dies = filter(lambda die: cmp_decl_file(filename, files, die), dies)
        dies = map(lambda die: get_die_type(filename, cu, die), dies)
        dies = filter(lambda die: die is not None, dies)
        return list(dies)


if __name__ == "__main__":
    filename = './test/resources/cpp_test_file.so'
    with open(str(filename), 'rb') as f:
        elffile = ELFFile(f)
        dwarf_info = elffile.get_dwarf_info()
        cu = list(dwarf_info.iter_CUs())[0]
        die = [die for die in (cu.iter_DIEs()) if 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == 'do_stuff'.encode('utf-8')][0]
        print(die)