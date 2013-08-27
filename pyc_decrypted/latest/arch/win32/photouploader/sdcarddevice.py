#Embedded file name: arch/win32/photouploader/sdcarddevice.py
from errno import ENOENT, EACCES
import os.path
import win32file
from contextlib import contextmanager
from ctypes import byref, create_unicode_buffer, sizeof
from ctypes.wintypes import ULONG, MAX_PATH, HANDLE
from dropbox.camera import PhotoImportDisconnected
from dropbox.camera.util import find_dcim, get_images
from dropbox.camera.uuidstore import SDCardUUIDStore, SDCardDevice
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.win32.version import WINDOWS_VERSION, VISTA
from PhotoUploaderLib import tagFORMATETC
from pynt.constants import ERROR_FILE_CORRUPT
from pynt.dlls.kernel32 import kernel32
from pynt.dlls.shell32 import shell32
from pynt.helpers.general import windows_error
from .autoplay_defaults import any_volume_defaults_are_dropbox, change_autoplay_default
from .constants import DROPBOX_AUTOPLAY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME, VOLUME_EVENTS

class WinSDCardDevice(SDCardDevice):
    DISCONNECT_ERROR_THRESHOLD = 5

    def __init__(self, data_obj, handler, user_id):
        self.exception = None
        try:
            super(WinSDCardDevice, self).__init__(id(data_obj), user_id)
            self.handler = handler
            self.data_obj = data_obj
            self._get_mount_point()
        except Exception as e:
            self.exception = e
            unhandled_exc_handler()
        finally:
            handler.connected(self)

    def override_disabled(self):
        if any_volume_defaults_are_dropbox():
            return False
        return True

    def handle_disconnect_exceptions(self, exc):
        if isinstance(exc, IOError):
            if not exc.args or exc.args[0] not in (ENOENT, EACCES):
                return
        elif isinstance(exc, WindowsError):
            if not exc.args or exc.args[0] not in (ERROR_FILE_CORRUPT,):
                return
        elif isinstance(exc, PhotoImportDisconnected):
            raise exc
        else:
            return
        if not exc.filename:
            return
        try:
            self.num_disconnected_errors += 1
        except AttributeError:
            self.num_disconnected_errors = 1

        if self.num_disconnected_errors >= self.DISCONNECT_ERROR_THRESHOLD:
            drive, _ = os.path.splitdrive(exc.filename)
            if drive and not os.path.isdir(drive):
                TRACE('SD Card root no longer accessible. Raising PhotoImportDisconnected')
                raise PhotoImportDisconnected()
            else:
                self.num_disconnected_errors = 0

    def make_default(self):
        if WINDOWS_VERSION < VISTA:
            TRACE("Can't change AutoPlay for removable devices on XP!")
            return
        TRACE('Making device %s default to Dropbox on AutoPlay.', self)
        try:
            for event in VOLUME_EVENTS:
                if WINDOWS_VERSION > VISTA:
                    handler = DROPBOX_AUTOPLAY_HANDLER_NAME
                else:
                    handler = DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME
                change_autoplay_default(event, handler)

        except Exception:
            unhandled_exc_handler()

    @contextmanager
    def files(self):
        if self.exception != None:
            raise self.exception
        else:
            yield get_images(self.root, self.paths, blacklist_nonphotos=self.blacklist_nonphotos, is_path_hidden=_is_hidden)

    def _get_mount_point(self):
        CF_HDROP = 15
        DVASPECT_CONTENT = 1
        TYMED_HGLOBAL = 1
        fmte = tagFORMATETC(CF_HDROP, None, DVASPECT_CONTENT, -1, TYMED_HGLOBAL)
        medium = self.data_obj.GetData(byref(fmte))
        hGlobal = HANDLE(medium.DUMMYUNIONNAME.u.hGlobal.contents.fContext)
        count = shell32.DragQueryFileW(hGlobal, ULONG(-1), None, 0)
        if count != 1:
            report_bad_assumption('Did not detect exactly one dropped file from device mount (win32)')
        self.blacklist_nonphotos = False
        if count >= 1:
            size = shell32.DragQueryFileW(hGlobal, 0, None, 0)
            if size < 0:
                raise windows_error(size)
            path = create_unicode_buffer(size + 1)
            ret = shell32.DragQueryFileW(hGlobal, 0, path, sizeof(path))
            if ret < 0:
                raise windows_error(ret)
            self.root = path.value
            self.name = _name_from_mountpoint(self.root)
            self.paths = find_dcim(self.root)
            if self.paths:
                self.init_uuid_store(os.path.join(self.root, u'DCIM'), alternate_paths=[self.root])
            else:
                self.paths = None
                self.blacklist_nonphotos = True
                self.init_uuid_store(self.root, nest_in_subdir=False)

    def release(self):
        self.handler.disconnected(self)


def _name_from_mountpoint(mount_point):
    vol_name = create_unicode_buffer(MAX_PATH + 1)
    ret = kernel32.GetVolumeInformationW(mount_point, vol_name, sizeof(vol_name), None, None, None, None, 0)
    if ret:
        return vol_name.value


def _uid_from_mointpoint(mount_point):
    MAX_GUID_PATH = 64
    volume_guid = create_unicode_buffer(MAX_GUID_PATH)
    ret = kernel32.GetVolumeNameForVolumeMountPointW(unicode(mount_point), volume_guid, MAX_GUID_PATH)
    volume_guid = volume_guid.value
    if ret:
        return volume_guid
    else:
        TRACE("!!Couldn't get real UID of mounted volume, using drive letter %r", mount_point)
        return unicode(mount_point)


GetFileExInfoStandard = 0
FILE_ATTRIBUTE_HIDDEN = 2

def _is_hidden(path):
    file_attrs = win32file.GetFileAttributesExW(path, GetFileExInfoStandard)[0]
    return file_attrs & FILE_ATTRIBUTE_HIDDEN
