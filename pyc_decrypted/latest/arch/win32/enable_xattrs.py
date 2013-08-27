#Embedded file name: arch/win32/enable_xattrs.py
from __future__ import absolute_import

def needs_user_xattr(path):
    return False


def add_user_xattr(path):
    pass
