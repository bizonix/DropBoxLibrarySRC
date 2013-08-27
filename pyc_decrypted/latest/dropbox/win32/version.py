#Embedded file name: dropbox/win32/version.py
import sys

class WindowsVersion(object):
    ALL_NAMES = {}

    def __init__(self, major_minor_tuple, name = None, service_pack = None):
        assert len(major_minor_tuple) == 2, 'major_minor_tuple must have length 2'
        assert isinstance(major_minor_tuple[0], int), 'major argument must be an integer'
        assert isinstance(major_minor_tuple[1], int), 'minor argument must be an integer'
        self._tuple = major_minor_tuple
        self._sp = service_pack
        if name:
            WindowsVersion.ALL_NAMES[major_minor_tuple] = name

    def __cmp__(self, other):
        assert isinstance(other, WindowsVersion)
        return cmp(self._tuple, other._tuple)

    def __repr__(self):
        name = self.name()
        name = 'Windows ' + name if name is not None else 'unknown'
        if self._sp:
            name += ' %s' % (self._sp,)
        return '<WindowsVersion instance: %r [vers %r]>' % (name, self._tuple)

    def name(self):
        return WindowsVersion.ALL_NAMES.get(self._tuple, None)

    def version_string(self):
        return '.'.join(map(str, self._tuple))

    def service_pack(self):
        return self._sp


def _get_version():
    info = sys.getwindowsversion()
    major, minor = info[:2]
    return WindowsVersion((major, minor), service_pack=info[4])


def _get_windows_version_string():
    return WindowsVersion.ALL_NAMES.get(sys.getwindowsversion()[:2], 'unknown')


WIN2K = WindowsVersion((5, 0), '2000')
WINXP = WindowsVersion((5, 1), 'XP')
WIN2K3 = WindowsVersion((5, 2), '2003')
VISTA = WindowsVersion((6, 0), 'Vista')
WIN7 = WindowsVersion((6, 1), '7')
WIN8 = WindowsVersion((6, 2), '8')
WINDOWS_VERSION = _get_version()
WINDOWS_VERSION_STRING = _get_windows_version_string()
