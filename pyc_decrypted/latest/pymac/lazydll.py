#Embedded file name: pymac/lazydll.py
import ctypes
import ctypes.util

class FakeDLL(object):

    def __init__(self, proxied_class):
        self.proxied_class = proxied_class
        self.initted = None

    def __getattr__(self, name):
        if self.initted is None:
            self.initted = self.proxied_class()
        return getattr(self.initted, name)


class LazyDLL(object):

    def __init__(self, debug = False):
        self._inst_funcs = dict()
        self._dll = None
        self._dllname = None
        self._debug = debug
        self._func_defs = {}
        self._const_defs = {}

    def __getattr__(self, name):
        if self._dll is None:
            self.init()
        if name in self._inst_funcs:
            return self._inst_funcs[name]
        try:
            return self._create_func(name, self._func_defs[name])
        except KeyError:
            if name not in self._const_defs:
                raise AttributeError('%r DLL has no attribute %r' % (self._dllname, name))
            return self._create_const(name, self._const_defs[name])

    def _create_func(self, name, func_def):
        try:
            new_func = getattr(self._dll, name)
        except Exception:
            new_func = func_def['when_not_found']
        else:
            for attr in ['restype',
             'argtypes',
             'errcheck',
             '__doc__']:
                if attr in func_def:
                    setattr(new_func, attr, func_def[attr])

        if self._debug:

            def new_new_func(*n, **kw):
                print 'calling %s(%s,%s)' % (name, ','.join(map(repr, n)), ','.join(('%r=%r' % tup for tup in kw.iteritems())))
                ret = new_func(*n, **kw)
                print 'return => %r' % (ret,)
                return ret

        else:
            new_new_func = new_func
        self._inst_funcs[name] = new_new_func
        return new_new_func

    def _create_const(self, const_name, const_type):
        try:
            self._inst_funcs[const_name] = const_type.in_dll(self._dll, const_name)
        except Exception:
            raise AttributeError("%r DLL can't create const %r" % (self._dllname, const_name))

        return self._inst_funcs[const_name]

    def return_false(self, *args, **kwargs):
        return False

    def return_none(self, *args, **kwargs):
        return None

    def init(self):
        raise NotImplementedError('Implement me in a subclass, please.')


class LazyCDLL(LazyDLL):

    def init(self):
        self._dll = ctypes.cdll.LoadLibrary(ctypes.util.find_library(self._dllname))
