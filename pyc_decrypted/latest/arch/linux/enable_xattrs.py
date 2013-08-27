#Embedded file name: arch/linux/enable_xattrs.py
from __future__ import absolute_import
import os
import re
import tempfile
from dropbox.i18n import trans
from dropbox.trace import unhandled_exc_handler
from .internal import run_as_root
from .util import fs_supports_attrs
FSTAB_FILENAME = '/etc/fstab'
MTAB_FILENAME = '/etc/mtab'
TYPES_THAT_NEED_USER_XATTR = set(['ext2',
 'ext3',
 'ext4',
 'reiserfs'])
USER_XATTR_OPT = 'user_xattr'

def mountpoint(s):
    if os.path.ismount(s) or len(s) == 0:
        return s
    else:
        return mountpoint(os.path.split(s)[0])


class SimpleLine(object):

    def __init__(self, buf):
        self.line = buf

    def get_directory(self):
        return None

    def __str__(self):
        return self.line


class FileSystemLine(object):
    __slots__ = ('w1', 'fsname', 'w2', 'directory', 'w3', 'fstype', 'w4', 'opts', 'w5', 'freq', 'w6', 'passno', 'w7')
    fstab_re = re.compile('^(?P<%s>\\s*)(?P<%s>\\S+)(?P<%s>\\s+)(?P<%s>\\S+)(?P<%s>\\s+)(?P<%s>\\S+)(?P<%s>\\s+)(?P<%s>\\S+)(?P<%s>\\s+)(?P<%s>\\d+)(?P<%s>\\s+)(?P<%s>\\d+)(?P<%s>\\s*)$' % __slots__)

    def __init__(self, match):
        for attr in self.__slots__:
            setattr(self, attr, match.group(attr))

    @staticmethod
    def from_line(line):
        match = FileSystemLine.fstab_re.match(line)
        if match:
            return FileSystemLine(match)
        else:
            return SimpleLine(line)

    def get_directory(self):
        return self.directory.decode('unicode_escape')

    def get_fsname(self):
        return self.fsname.decode('unicode_escape')

    def get_fstype(self):
        return self.fstype

    def get_options(self):
        return self.opts.split(',')

    def set_options(self, options):
        self.opts = ','.join(options)

    def __str__(self):
        return ''.join((getattr(self, attr) for attr in self.__slots__))


class FstabFile(object):

    def __init__(self, fn):
        self.lines = []
        with open(fn, 'rb') as f:
            for line in f:
                self.lines.append(FileSystemLine.from_line(line))

    def write(self, fn):
        with open(fn, 'wb') as f:
            f.writelines(self.lines)

    def __str__(self):
        return ''.join((str(l) for l in self.lines))


def fix_user_xattr(mount, fn):
    ret = False
    fstab = FstabFile(fn)
    for line in fstab.lines:
        if line.get_directory() == mount and line.fstype in TYPES_THAT_NEED_USER_XATTR and USER_XATTR_OPT not in line.get_options():
            line.set_options(line.get_options() + [USER_XATTR_OPT])
            ret = fstab

    return ret


def needs_user_xattr(path):
    try:
        test_path = path
        while not os.path.isdir(test_path):
            test_path = os.path.dirname(test_path)

        if fs_supports_attrs(test_path):
            return False
    except Exception:
        unhandled_exc_handler()

    return any((fix_user_xattr(mountpoint(path), f) for f in [FSTAB_FILENAME, MTAB_FILENAME]))


def add_user_xattr(path):
    desc = trans(u'Please enter your password. This will enable Dropbox to sync extended file attributes.')
    mount = mountpoint(path)
    new_fstab = fix_user_xattr(mount, FSTAB_FILENAME)
    if not new_fstab:
        if fix_user_xattr(mount, MTAB_FILENAME):
            return run_as_root(['mount',
             '-o',
             'remount,user_xattr',
             mount], desc)
        return
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(str(new_fstab))
        tmp.flush()
        with tempfile.NamedTemporaryFile() as script:
            script.write('#!/bin/sh -e\ncp %(fstab)s %(fstab)s.bak &&\ncat %(tmp)s > %(fstab)s &&\nmount -o remount %(mount)s\n' % dict(fstab=FSTAB_FILENAME, tmp=tmp.name, mount=mount))
            script.flush()
            run_as_root(['sh', script.name], desc)
