#Embedded file name: dropbox/keystore/keystore_linux.py
from __future__ import absolute_import
import ctypes
import ctypes.util
import os
from .keystore_posix import KeyStoreFileBacked
from dropbox.trace import TRACE
from client_api.hashing import dropbox_hash

class S(ctypes.Structure):
    _fields_ = [('r1', ctypes.c_ulong),
     ('r2', ctypes.c_ulong),
     ('b1', ctypes.c_ulong),
     ('b2', ctypes.c_ulong),
     ('b3', ctypes.c_ulong),
     ('f1', ctypes.c_ulong),
     ('f2', ctypes.c_ulong),
     ('f3', ctypes.c_ulong),
     ('s1', ctypes.c_ulong),
     ('s2', ctypes.c_int * 128)]


c = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
s = c.statvfs
s.restype = ctypes.c_int
s.argtypes = [ctypes.c_char_p, ctypes.POINTER(S)]

class KeyStore(KeyStoreFileBacked):

    def unique_id(self, path):
        inode = os.stat(path).st_ino
        v = S()
        ret = s(path, ctypes.byref(v))
        if ret < 0:
            raise Exception('statvfs failed with retval %s' % (ret,))
        TRACE('KEYSTORE: unique_id = %r %s %s ', path, dropbox_hash('%d' % inode), dropbox_hash('%d' % v.s1))
        return '%d_%d' % (inode, v.s1)
