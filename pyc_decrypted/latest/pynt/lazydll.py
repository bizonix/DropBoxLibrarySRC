#Embedded file name: pynt/lazydll.py
import winerror
from ctypes import windll
from .constants import E_FAIL, ERROR_CALL_NOT_IMPLEMENTED, ERROR_INVALID_PARAMETER, ERROR_SUCCESS, ERROR_FILE_NOT_FOUND, INVALID_HANDLE_VALUE, INVALID_FILE_ATTRIBUTES

class FakeDLL(object):

    def __init__(self, proxied_class):
        self.proxied_class = proxied_class
        self.initted = None

    def __getattr__(self, name):
        if self.initted is None:
            self.initted = self.proxied_class()
        return getattr(self.initted, name)


class LazyDLL(object):

    def __init__(self, kernel32 = None):
        self._inst_funcs = dict()
        self._dll = None
        self._kernel32 = kernel32

    def __getattr__(self, name):
        if self._dll is None:
            self.init()
        if name in self._inst_funcs:
            return self._inst_funcs[name]
        try:
            func_def = self._func_defs[name]
        except KeyError:
            raise AttributeError("'%.50s' has no attribute '%.400s'" % (type(self).__name__, name))

        try:
            new_func = getattr(self._dll, name)
        except Exception:
            if 'when_not_found' in func_def:
                new_func = func_def['when_not_found']
            else:
                raise
        else:
            for attr in ['restype',
             'argtypes',
             'errcheck',
             '__doc__']:
                if attr in func_def:
                    setattr(new_func, attr, func_def[attr])

        self._inst_funcs[name] = new_func
        return new_func

    def init(self, unicode = True):
        try:
            self._dll = getattr(windll, self._dllname)
        except Exception as e:
            if hasattr(e, 'winerror') and e.winerror == winerror.ERROR_MOD_NOT_FOUND:
                self._dll = object()
            else:
                raise

        self._unicode = unicode

    def _set_not_implemented(self):
        if self._kernel32 is not None:
            self._kernel32.SetLastError(ERROR_CALL_NOT_IMPLEMENTED)

    def raise_not_implemented_error(self, *args, **kwargs):
        raise NotImplementedError('Function not exposed by %s!', self._dllname)

    def return_e_fail(self, *args, **kwargs):
        self._set_not_implemented()
        return E_FAIL

    def return_error_invalid_parameter(self, *args, **kwargs):
        self._set_not_implemented()
        return ERROR_INVALID_PARAMETER

    def return_error_not_found(self, *args, **kwargs):
        self._set_not_implemented()
        return ERROR_FILE_NOT_FOUND

    def return_error_success(self, *args, **kwargs):
        self._set_not_implemented()
        return ERROR_SUCCESS

    def return_false(self, *args, **kwargs):
        self._set_not_implemented()
        return False

    def return_invalid_handle(self, *args, **kwargs):
        self._set_not_implemented()
        return INVALID_HANDLE_VALUE

    def return_none(self, *args, **kwargs):
        self._set_not_implemented()

    def return_invalid_file_attributes(self, *args, **kwargs):
        self._set_not_implemented()
        return INVALID_FILE_ATTRIBUTES

    def return_zero(self, *args, **kwargs):
        self._set_not_implemented()
        return 0

    def F(self, name, ret = None, args = (), when_not_found = None, errcheck = None, doc = None):
        argtypes = []
        for arg in args:
            if isinstance(arg, tuple):
                argtype, _ = arg
            else:
                argtype = arg
            argtypes.append(argtype)

        self._func_defs[name] = {'restype': ret,
         'argtypes': argtypes}
        if when_not_found is not None:
            self._func_defs[name]['when_not_found'] = when_not_found
        if errcheck is not None:
            self._func_defs[name]['errcheck'] = errcheck
        if doc is not None:
            self._func_defs[name]['__doc__'] = errcheck
