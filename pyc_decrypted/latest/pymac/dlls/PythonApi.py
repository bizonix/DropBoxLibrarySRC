#Embedded file name: pymac/dlls/PythonApi.py
from ctypes import py_object, POINTER, c_char_p, pythonapi
from ..lazydll import LazyDLL, FakeDLL
from ..types import FILE, close_FILE_func_t

class LazyPythonAPI(LazyDLL):

    def __init__(self):
        super(LazyPythonAPI, self).__init__()
        self._func_defs = {}

        def F(name, ret = None, args = []):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        F('PyFile_FromFile', py_object, [POINTER(FILE),
         c_char_p,
         c_char_p,
         close_FILE_func_t])
        F('PyFile_AsFile', POINTER(FILE), [py_object])

    def init(self):
        self._dll = pythonapi


PythonAPI = FakeDLL(LazyPythonAPI)
