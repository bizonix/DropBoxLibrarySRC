#Embedded file name: dropbox/sync_engine/mac_finder_comment_attr_wrapper.py
import errno
import functools
from dropbox import fsutil
from dropbox.low_functions import add_inner_methods, add_inner_properties
from dropbox.misc import protect_closed
from dropbox.sync_engine_file_system.abstract_attributes_handle import AbstractAttributesHandle, AbstractPlatformHandle
from dropbox.sync_engine_file_system.util import FunctionBasedFile, WrappedFileSystem
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
try:
    from dropbox.mac.internal import osa_send_piped
    from Foundation import NSData, NSPropertyListSerialization, NSPropertyListImmutable, NSAutoreleasePool
except Exception:
    pass

_MAC_PLATFORM = 'mac'
_COMMENT_KEY = 'com.apple.metadata:kMDItemFinderComment'
_SET_COMMENT_ASCRIPT = '\non run argv\nset posixPath to item 1 of argv\nset commentString to item 2 of argv\nset pf to POSIX file posixPath\nset a to pf as alias\ntell application "Finder"\n  set comment of a to ""\n  set comment of a to commentString\nend tell\nend run\n'

def finder_set_comment(local_path, comment, timeout = None):
    return osa_send_piped(_SET_COMMENT_ASCRIPT, parse_results=True, args=[unicode(local_path), comment], timeout=timeout)


_SET_COMMENT_TIMEOUT = 5

def fs_get_comment(fs, local_path):
    try:
        return fsutil.get_attr(fs, local_path, _MAC_PLATFORM, _COMMENT_KEY)
    except EnvironmentError as e:
        if e.errno == errno.ENOENT:
            return ''
        raise


def fs_set_comment(fs, local_path, plstr):
    return fsutil.set_attr(fs, local_path, _MAC_PLATFORM, _COMMENT_KEY, plstr)


def set_comment(fs, local_path, plstr):
    pool = NSAutoreleasePool.alloc().init()
    try:
        pldata = NSData.dataWithBytes_length_(plstr, len(plstr))
        comment, format, error = NSPropertyListSerialization.propertyListFromData_mutabilityOption_format_errorDescription_(pldata, NSPropertyListImmutable, None, None)
        if error:
            raise Exception(error)
        comment = unicode(comment)
        try:
            finder_set_comment(local_path, comment, timeout=5.0)
        except Exception:
            unhandled_exc_handler()

    finally:
        del pool

    count = 1
    while fs_get_comment(fs, local_path) != plstr:
        if count > 5:
            fs_set_comment(fs, fs.make_path(local_path), plstr)
            report_bad_assumption("Couldn't write comment")
            break
        TRACE("Set comment didn't stick. Retrying.")
        try:
            finder_set_comment(local_path, comment, timeout=5.0)
        except Exception:
            unhandled_exc_handler()

        count += 1


def clear_comment(local_path):
    finder_set_comment(local_path, '', timeout=_SET_COMMENT_TIMEOUT)


def mac_finder_comment_file_system(fs):
    return MacFinderCommentFS(fs)


class MacFinderCommentFS(WrappedFileSystem):

    def open_attributes(self, path):
        return MacFinderCommentAttributesHandle(self.fs, path, self.fs.open_attributes(path))


@add_inner_methods('close', 'open_preserved', 'readplat', 'remove_preserved', 'reset')

@add_inner_properties('closed')

class MacFinderCommentAttributesHandle(AbstractAttributesHandle):

    def __init__(self, fs, path, inner):
        self.fs = fs
        self.path = path
        self.inner = inner
        self.reset()

    @protect_closed
    def open(self, plat):
        plat_handle = self.inner.open(plat)
        if plat == _MAC_PLATFORM:
            plat_handle = MacFinderCommentPlatformHandle(self.fs, self.path, plat_handle)
        return plat_handle

    @protect_closed
    def remove(self, plat, key):
        if (plat, key) == (_MAC_PLATFORM, _COMMENT_KEY):
            clear_comment(self.path)
        return self.inner.remove(plat, key)


@add_inner_methods('close', 'readattr', 'reset')

@add_inner_properties('closed', 'name')

class MacFinderCommentPlatformHandle(AbstractPlatformHandle):

    def __init__(self, fs, path, platform_handle):
        self.fs = fs
        self.path = path
        self.inner = platform_handle

    @protect_closed
    def open(self, key, mode = 'r'):
        if key == _COMMENT_KEY:
            return FunctionBasedFile(_COMMENT_KEY, mode, functools.partial(fs_get_comment, self.fs, self.path), functools.partial(set_comment, self.fs, unicode(self.path)))
        return self.inner.open(key, mode)
