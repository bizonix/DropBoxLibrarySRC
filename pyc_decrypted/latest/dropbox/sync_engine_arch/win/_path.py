#Embedded file name: dropbox/sync_engine_arch/win/_path.py
import ctypes
import pywintypes
import re
import win32con
from ctypes.wintypes import HWND, UINT, LPCWSTR, BOOL, DWORD, LPWSTR
from functools import wraps
from win32api import GetLongPathNameW
from win32file import GetFileAttributesW, SetFileAttributesW
from win32security import DACL_SECURITY_INFORMATION
from dropbox.functions import is_short_path
from dropbox.sync_engine.exceptions import PredictableError, UnreconstructableError
from dropbox.trace import report_bad_assumption, unhandled_exc_handler
from dropbox.sync_engine_file_system.windows import is_escaped_nt_path

def unicode_first_argument(fn):

    @wraps(fn)
    def wrapper(path, *args, **kwargs):
        return fn(unicode(path), *args, **kwargs)

    return wrapper


for func in ['GetLongPathNameW', 'GetFileAttributesW', 'SetFileAttributesW']:
    locals()[func] = unicode_first_argument(locals()[func])

def _check_filename_length(target_fn, is_dir):
    if is_escaped_nt_path(target_fn):
        if len(target_fn) > 32767:
            raise UnreconstructableError('path is too long')
        return
    if len(target_fn.dirname) > 247:
        raise UnreconstructableError('parent path is too long')
    if len(target_fn) > (247 if is_dir else 259):
        raise UnreconstructableError('path is too long')


_bad_filename_chars = u'/:"<>\\|\\?\\*' + ''.join((unichr(x) for x in xrange(1, 32)))
INVALID_FILENAME_CHARS_RE = u'[\\\\%s%s]' % (unichr(0), _bad_filename_chars)
_bad_chars = u'[^\\\\]*[%s][^\\\\]*' % _bad_filename_chars
_bad_path = u'(\\.|\\.\\.)'
_bad_filename = u'(([Cc][Oo][Nn])|([Pp][Rr][Nn])|([Aa][Uu][Xx])|([Nn][Uu][Ll])|([Cc][Oo][Mm][1-9])|([Ll][Pp][Tt][1-9]))(\\.[^\\\\]*)?'
_bad_filename_ending = u'[^\\\\]+[\\.\\s]'
_finale = u'\\\\(' + u'|'.join((u'(' + x + u')' for x in (_bad_chars,
 _bad_path,
 _bad_filename,
 _bad_filename_ending))) + u')(\\\\|$)'
_INVALID_WINDOWS_PATH_RE = re.compile(_finale)

def check_filename_localpath(localpath, is_delete, is_dir, case_insensitive = True):
    _check_filename_length(localpath, is_dir=is_dir)
    localpathu = unicode(localpath)
    if _INVALID_WINDOWS_PATH_RE.search(localpathu) is not None:
        raise UnreconstructableError('path contained invalid filename: %r' % (localpathu,))
    if is_short_path(localpathu):
        try:
            long_path = GetLongPathNameW(localpathu)
        except pywintypes.error as e:
            if e[0] not in (2, 3):
                raise PredictableError("can't do get GetLongPathNameW right now, let's wait " + str(e))
        else:
            if long_path.lower() != localpathu.lower() if case_insensitive else long_path != localpathu:
                report_bad_assumption('Long path / short bad conflict, is_delete: %r, %r vs %r', is_delete, localpathu, long_path)
                if is_delete:
                    return False
                raise UnreconstructableError("we won't reconstruct a shortpath when a longpath exists")
    return True
