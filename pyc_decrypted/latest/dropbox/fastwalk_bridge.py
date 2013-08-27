#Embedded file name: dropbox/fastwalk_bridge.py
from __future__ import absolute_import
import functools
import os
from dropbox.platform import platform
from dropbox.fastwalk import fastwalk as fastwalk_fs, fastwalk_strict as fastwalk_strict_fs, fastwalk_with_exception_handling as fastwalk_with_exception_handling_fs
from dropbox.low_functions import add_inner_methods

def make_fs():
    if platform == 'win':
        from dropbox.sync_engine_arch.win._file_system import WindowsFileSystem as FileSystem
    elif platform == 'mac':
        from dropbox.sync_engine_arch.macosx._file_system import MacOSXFileSystem as FileSystem
    elif platform == 'linux':
        from dropbox.sync_engine_arch.linux._file_system import LinuxFileSystem as FileSystem
    else:
        from dropbox.sync_engine_file_system.pythonos import FileSystem
    return FileSystem()


class AugmentedDirent(object):

    def __init__(self, fs, path, dirent):
        self.fs = fs
        self.path = path
        self.dirent = dirent

    @property
    def type(self):
        try:
            return self.dirent.type
        except AttributeError:
            return self.fs.indexing_attributes(self.fullpath, resolve_link=False).type

    @property
    def name(self):
        return self.dirent.name

    @property
    def size(self):
        try:
            return self.dirent.size
        except AttributeError:
            return self.lstat.st_size

    @property
    def inode(self):
        if platform not in ('mac', 'linux'):
            raise Exception('dirent.inode not supported on platform %r' % platform)
        return self.dirent.file_id

    @property
    def win32_reparse_type(self):
        if platform != 'win':
            raise Exception('dirent.inode not supported on platform %r' % platform)
        return self.dirent.win32_reparse_type

    @property
    def fullpath(self):
        return unicode(self.path.join(self.dirent.name))

    @property
    def stat(self):
        try:
            return self._stat
        except AttributeError:
            self._stat = os.stat(self.fullpath)
            return self._stat

    @property
    def lstat(self):
        try:
            return self._lstat
        except AttributeError:
            self._lstat = os.lstat(self.fullpath)
            return self._lstat


@add_inner_methods('__enter__', '__exit__', 'reset', 'close')

class MappedDirectory(object):

    def __init__(self, fn, inner):
        self.fn = fn
        self.inner = inner

    def __iter__(self):
        return self

    def readdir(self):
        ret = self.inner.readdir()
        if ret is not None:
            return self.fn(ret)
        else:
            return ret

    def next(self):
        return self.fn(self.inner.next())


def fastwalk_bridge(fastwalk_func):

    def fastwalk_bridge_func(*n, **kw):
        if 'follow_symlinks' not in kw:
            kw['follow_symlinks'] = True
        fs = make_fs()
        try:
            dfut = kw['dont_follow_up_to']
        except KeyError:
            pass
        else:
            kw['dont_follow_up_to'] = fs.make_path(dfut)

        n = [fs.make_path(n[0])] + list(n[1:])
        for dirpath, ents in fastwalk_func(fs, *n, **kw):
            fn = functools.partial(AugmentedDirent, fs, dirpath)
            yield (unicode(dirpath), MappedDirectory(fn, ents))

    return fastwalk_bridge_func


fastwalk = fastwalk_bridge(fastwalk_fs)
fastwalk_strict = fastwalk_bridge(fastwalk_strict_fs)
fastwalk_with_exception_handling = fastwalk_bridge(fastwalk_with_exception_handling_fs)
