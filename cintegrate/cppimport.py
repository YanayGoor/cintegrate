import sys
import os
from pathlib2 import Path
from importlib import import_module
from importlib.machinery import ModuleSpec
from .cpptypes import get_type_from_file, get_all_user_types

class FolderModule:
    pass

class CModule:
    def __init__(self, path, loader):
        c_file_path = path.resolve().with_suffix('.c')
        so_file_path = path.resolve().with_suffix('.so')
        if not so_file_path.exists():
            return_code = os.system('gcc -gdwarf -shared -fPIC {} -o {}'.format(c_file_path, so_file_path))
            if return_code:
                raise ValueError('Couldn\'t find or compile .so file')
        self.__path__ = so_file_path
        self.__loader__ = loader
        self.__name__ = path.name
        self.__package__ = ''
        self.all = get_all_user_types(so_file_path)
        self.__all__ = [type.__name__ for type in self.all]

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            if name in self.__all__:
                return self.all[self.__all__.index(name)]
            return get_type_from_file(self.__path__, name)

class CPPModule:
    pass

class CintegrateLoader:
    def __init__(self, path, type=None):
        self.type = type
        self.path = path

    def create_module(self, spec):
        assert self.type in [None, 'c', 'c++']
        if not self.type:
            return FolderModule()
        elif self.type == 'c':
            return CModule(self.path, self)
        return CPPModule()

    def exec_module(self, module):
        pass

class CintegrateFinder:
    def find_spec(self, name, path, target=None):
        path = Path('./' + name.replace('.', r'/'))
        if path.resolve().with_suffix('.c').exists():
            return ModuleSpec(name, CintegrateLoader(path, type='c'), is_package=True)
        if path.with_suffix('.c').exists() or path.is_dir():
            return ModuleSpec(name, CintegrateLoader(path), is_package=True)
        return None

sys.meta_path.insert(0, CintegrateFinder())

# from test.resources.test_file import do_stuff
