#Embedded file name: dropbox/native_threading.py
from __future__ import absolute_import
import sys
import functools
from dropbox.read_write_lock import LowRWLock
if sys.platform.startswith('win'):
    import dropbox.native_threading_win32 as implementation_module
elif sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
    import dropbox.native_threading_posix as implementation_module
else:
    raise Exception('Unsupported platform')
NativeRWLock = functools.partial(LowRWLock, implementation_module.NativeMutex, implementation_module.NativeCondition)

class _ModuleWrapper(object):

    def __init__(self, me, wrapped):
        object.__setattr__(self, 'wrapped', wrapped)
        object.__setattr__(self, 'me', me)

    def __getattr__(self, name):
        try:
            return getattr(self.me, name)
        except AttributeError:
            return getattr(self.wrapped, name)

    def __setattr__(self, name, value):
        return setattr(self.wrapped, name, value)


sys.modules[__name__] = _ModuleWrapper(sys.modules[__name__], implementation_module)
