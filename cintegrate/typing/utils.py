def die_from_offset(cu, offset):
    return [die for die in cu.iter_DIEs() if die.offset == offset][0]
