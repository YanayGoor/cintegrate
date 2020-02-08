from pathlib import PurePath
from elftools.elf.elffile import ELFFile
from .typing import Builder
import ctypes

def die_from_offset(cu, offset):
    return [die for die in cu.iter_DIEs() if die.offset == offset][0]

def get_type_from_file(filename, name):
    with open(str(filename), 'rb') as f:
        elffile = ELFFile(f)
        dwarf_info = elffile.get_dwarf_info()
        cu = list(dwarf_info.iter_CUs())[0]
        builder = Builder(filename, cu)
        die = [die for die in (cu.iter_DIEs()) if 'DW_AT_name' in die.attributes and die.attributes['DW_AT_name'].value == name.encode('utf-8')][0]
        return builder.map(die)

def cmp_decl_file(filename, files, die):
    c_name = filename.with_suffix('.c').name.encode('utf-8')
    cpp_name = filename.with_suffix('.cpp').name.encode('utf-8')
    return 'DW_AT_decl_file' in die.attributes \
        and len(files) >= die.attributes['DW_AT_decl_file'].value \
            and files[die.attributes['DW_AT_decl_file'].value-1].name in [c_name, cpp_name]

def get_all_user_types(filename):
    with open(str(filename), 'rb') as f:
        elffile = ELFFile(f)
        dwarf_info = elffile.get_dwarf_info()
        cu = list(dwarf_info.iter_CUs())[0]
        builder = Builder(filename, cu)
        files = dwarf_info.line_program_for_CU(cu)['file_entry']
        dies = filter(lambda die: 'DW_AT_name' in die.attributes, cu.iter_DIEs())
        dies = filter(lambda die: cmp_decl_file(filename, files, die), dies)
        dies = map(lambda die: builder.map(die), dies)
        dies = filter(lambda die: die is not None, dies)
        return list(dies)


if __name__ == "__main__":
    filename = './test/resources/cpp_test_file.so'
    print(get_type_from_file(filename, 'MyClass'))