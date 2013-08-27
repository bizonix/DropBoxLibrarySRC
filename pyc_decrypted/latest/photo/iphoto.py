#Embedded file name: photo/iphoto.py
from __future__ import absolute_import
import datetime
import errno
import os
import time
import plistlib
from pymac.helpers.core import get_preference
from dropbox.trace import TRACE, unhandled_exc_handler
from .stats import collectors
from .exceptions import NotInstalledError, DEBUG

class IPhoto(object):
    LOWEST_SUPPORTED_MAJOR_VERNO = 7
    BEGINNING_OF_TIME = datetime.datetime(2001, 1, 1)

    @staticmethod
    def get_photo_mtime(photo_dict):
        try:
            try:
                iphoto_time = IPhoto.BEGINNING_OF_TIME + datetime.timedelta(seconds=photo_dict['DateAsTimerIntervalGMT'])
            except KeyError:
                iphoto_time = IPhoto.BEGINNING_OF_TIME + datetime.timedelta(seconds=photo_dict['DateAsTimerInterval'])

            return iphoto_time.timetuple()
        except Exception:
            unhandled_exc_handler()
            return None

    def __init__(self):
        self.product = 'iPhoto'
        self.fn = get_iphoto_plist_path()
        self.reset()

    def reset(self):
        try:
            self.plist = plistlib.readPlist(self.fn)
        except EnvironmentError as e:
            if e.errno == errno.ENOENT:
                raise NotInstalledError()
            else:
                unhandled_exc_handler()

    def get_num_photos(self):
        return len(self.plist['Master Image List'])

    def get_version(self):
        return self.plist['Application Version']

    def get_num_albums(self):
        count = 0
        for x in self.plist['List of Albums']:
            if x.get('Album Type') == 'Regular':
                count += 1

        return count

    def get_last_modified(self):
        return int(os.stat(self.fn).st_mtime)

    def photos(self):
        return self.plist['Master Image List'].items()

    def get_albums_and_events(self):
        return [ album for album in self.plist['List of Albums'] if album.get('Album Type') == 'Regular' and album.get('GUID') != 'lastImportAlbum' or album.get('Album Type') == 'Event' ]

    def get_events(self):
        return self.plist['List of Rolls']


def get_iphoto_plist_path():
    try:
        pref = get_preference(u'com.apple.iPhoto', u'RootDirectory')
    except KeyError:
        raise NotInstalledError()

    return os.path.expanduser(os.path.join(pref, 'AlbumData.xml'))


def get_iphoto_last_modified():
    try:
        fn = get_iphoto_plist_path()
        return int(os.stat(fn).st_mtime)
    except NotInstalledError:
        pass
    except OSError as e:
        if e.errno != errno.ENOENT:
            unhandled_exc_handler()
        return None
    except Exception:
        unhandled_exc_handler()


def collect_stats_iphoto(csr):
    try:
        iphoto = IPhoto()
        version = iphoto.get_version()
        modified = iphoto.get_last_modified()
        num = iphoto.get_num_photos()
        albums = iphoto.get_num_albums()
        csr.report_stat('photo.iphoto.version', version)
        csr.report_stat('photo.iphoto.last-modified', modified)
        csr.report_stat('photo.iphoto.num-photos', num)
        csr.report_stat('photo.iphoto.num-albums', albums)
    except NotInstalledError:
        if DEBUG:
            unhandled_exc_handler()
    except Exception:
        unhandled_exc_handler()


collectors.append(collect_stats_iphoto)
