import sys
import os
from pathlib2 import Path
from importlib import import_module
from importlib.machinery import ModuleSpec
from .cpptypes import get_type_from_file, get_all_user_types

class FolderModule:
    pass

class IntegrationModule:
    def __init__(self, path, loader, dst_suffix, src_suffix=None, cmd=None):
        dst_file_path = path.resolve().with_suffix(dst_suffix)
        if not dst_file_path.exists() and cmd and src_suffix:
            src_file_path = path.resolve().with_suffix(src_suffix)
            return_code = os.system(cmd.format(src_file_path, dst_file_path))
            if return_code:
                raise ValueError('Couldn\'t find or compile {} file'.format(dst_suffix))
        self.__path__ = dst_file_path
        self.__loader__ = loader
        self.__name__ = path.name
        self.__package__ = ''
        self.all = get_all_user_types(dst_file_path)
        self.__all__ = [type.__name__ for type in self.all]

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            if name in self.__all__:
                return self.all[self.__all__.index(name)]
            return get_type_from_file(self.__path__, name)

class SOModule(IntegrationModule):
    def __init__(self, path, loader):
        super().__init__(path, loader, '.so')

class CModule(IntegrationModule):
    def __init__(self, path, loader):
        super().__init__(path, loader, '.so', '.c', 'gcc -gdwarf -shared -fPIC {} -o {}')

class CPPModule(IntegrationModule):
    def __init__(self, path, loader):
        super().__init__(path, loader, '.so', '.cpp', 'g++ -gdwarf -shared -fPIC {} -o {}')

class CintegrateLoader:
    def __init__(self, path, type=None):
        self.type = type
        self.path = path

    def create_module(self, spec):
        assert self.type in [None, 'c', 'c++', 'so']
        if not self.type:
            return FolderModule()
        if self.type == 'c':
            return CModule(self.path, self)
        if self.type == 'c++':
            return CPPModule(self.path, self)
        if self.type == 'so':
            return SOModule(self.path, self)
        return FolderModule()

    def exec_module(self, module):
        pass

class CintegrateFinder:
    def find_spec(self, name, path, target=None):
        path = Path('./' + name.replace('.', r'/'))
        if path.with_suffix('.c').exists():
            return ModuleSpec(name, CintegrateLoader(path, type='c'), is_package=True)
        if path.with_suffix('.cpp').exists():
            return ModuleSpec(name, CintegrateLoader(path, type='c++'), is_package=True)
        if path.with_suffix('.so').exists():
            return ModuleSpec(name, CintegrateLoader(path, type='so'), is_package=True)
        if path.is_dir():
            return ModuleSpec(name, CintegrateLoader(path), is_package=True)
        return None

sys.meta_path.insert(0, CintegrateFinder())

# from test.resources.test_file import do_stuff
