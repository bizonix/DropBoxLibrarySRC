#Embedded file name: dropbox/mac/version.py
import platform

class MacVersion(object):
    ALL_NAMES = {}

    def __init__(self, major_minor_tuple, name = None, point_release = None):
        assert len(major_minor_tuple) == 2, 'major_minor_tuple must have length 2'
        assert isinstance(major_minor_tuple[0], int), 'major argument must be an integer'
        assert isinstance(major_minor_tuple[1], int), 'minor argument must be an integer'
        self._tuple = major_minor_tuple
        self._point_release = point_release
        if name:
            MacVersion.ALL_NAMES[major_minor_tuple] = name

    def __cmp__(self, other):
        assert isinstance(other, MacVersion)
        return cmp(self._tuple, other._tuple)

    def __repr__(self):
        name = self.name()
        name = 'MacOS ' + name if name is not None else 'unknown'
        vers_string = self.version_string()
        return '<MacVersion instance: %r [vers %s]>' % (name, vers_string)

    def name(self):
        return MacVersion.ALL_NAMES.get(self._tuple, None)

    def version_string(self):
        ret = '.'.join(map(str, self._tuple))
        if self._point_release is not None:
            ret += '.%s' % (self._point_release,)
        return ret

    def point_release(self):
        return self._point_release


def _get_version():
    info = platform.mac_ver()[0].split('.', 2)
    major, minor = info[:2]
    point_release = info[2] if len(info) >= 3 else 0
    return MacVersion((int(major), int(minor)), point_release=point_release)


TIGER = MacVersion((10, 4), 'Tiger')
LEOPARD = MacVersion((10, 5), 'Leopard')
SNOW_LEOPARD = MacVersion((10, 6), 'Snow Leopard')
LION = MacVersion((10, 7), 'Lion')
MOUNTAIN_LION = MacVersion((10, 8), 'Mountain Lion')
MAVERICKS = MacVersion((10, 9), 'Mavericks')
MAC_VERSION = _get_version()
