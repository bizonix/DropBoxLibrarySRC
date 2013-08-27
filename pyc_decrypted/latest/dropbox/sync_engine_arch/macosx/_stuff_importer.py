#Embedded file name: dropbox/sync_engine_arch/macosx/_stuff_importer.py
import errno
import functools
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from build_number import BRANCH
from dropbox.camera import Device, AlbumInfo
from dropbox.camera.util import OnDiskFile
from dropbox.client.notifications_exceptions import StickyNotificationKeyError
from dropbox.client.photo_constants import CU_QUOTA_UNEARNED
from dropbox.client.photocontroller import GalleryImportController
from dropbox.client.photoimporter import MAYBE_OUT_OF_SPACE, NOT_OUT_OF_SPACE, OUT_OF_QUOTA, OUT_OF_DISK_SPACE
from dropbox.debugging import easy_repr
from dropbox.event import report
from dropbox.features import feature_enabled
from dropbox.functions import handle_exceptions
from dropbox.preferences import OPT_IMPORTED_IPHOTOS_ONCE
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from photo.exceptions import NotInstalledError
from photo.iphoto import IPhoto, get_iphoto_last_modified, get_iphoto_plist_path
from ui.common.notifications import PhotoGalleryStickyNotification
NUM_PHOTOS_THRESHOLD = 20
IPHOTO_UUID = str(uuid.UUID('93bba361-7267-406e-a99e-bb7f7e4423c3'))

class IPhotoInsideDropboxError(Exception):
    pass


class UnsupportedIPhotoVerno(Exception):
    pass


class IPhotoFile(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('id', '_name', '_size', '_time', '_path', '_iphoto_time', '_event_id')

    def __init__(self, id, name, size, mtime, path, iphoto_time, event_id):
        self.id = id
        self._name = name
        self._size = size
        self._time = mtime
        self._path = path
        self._iphoto_time = iphoto_time
        self._event_id = event_id

    def __repr__(self):
        return easy_repr(self, *self.__slots__)

    @contextmanager
    def open(self, fs, *n, **kw):
        with fs.open(self._path, 'r') as fobj:
            yield fobj.read

    def name(self):
        return self._name

    def size(self):
        return self._size

    def time(self):
        return self._time

    def iphoto_time(self):
        return self._iphoto_time

    def event_id(self):
        return self._event_id


class IPhotoDevice(Device):

    def __init__(self, handler, app, fn = None):
        super(IPhotoDevice, self).__init__(IPHOTO_UUID)
        self.uid = self.id
        self.handler = handler
        self.app = app
        self._events = None
        iphoto_path = get_iphoto_plist_path()
        try:
            dropbox_path = app.config['dropbox_path']
        except Exception:
            unhandled_exc_handler()
        else:
            if os.path.commonprefix([iphoto_path, dropbox_path]) == app.config['dropbox_path']:
                raise IPhotoInsideDropboxError()

        self.iphoto = IPhoto()
        TRACE('IPHOTOIMPORT: Using %s', self.iphoto_version())
        verno = int(self.iphoto.get_version().split('.')[0])
        if verno < IPhoto.LOWEST_SUPPORTED_MAJOR_VERNO:
            raise UnsupportedIPhotoVerno('Unsupported iPhoto version %s' % self.iphoto.get_version())
        self.get_num_photos = self.iphoto.get_num_photos
        handler.connected(self)
        self.name = 'iPhoto'
        self.model = self.iphoto_version()

    def photos_in_reverse_event_order(self):
        photos = self.iphoto.photos()
        events = self.events()

        def sortfn(photo_pair):
            try:
                return events[photo_pair[1]['Roll']].album_time
            except KeyError:
                return 0

        photos.sort(key=sortfn, reverse=True)
        return photos

    def get_iphoto_photos(self):
        photos = self.photos_in_reverse_event_order()
        for iphoto_id, photo_dict in photos:
            try:
                photo_path = photo_dict['ImagePath']
                fobj = IPhotoFile(id=iphoto_id, name=photo_path, size=os.path.getsize(photo_path), mtime=get_photo_mtime(photo_path), path=photo_path, iphoto_time=IPhoto.get_photo_mtime(photo_dict), event_id=photo_dict['Roll'])
                yield fobj
            except OSError as e:
                if e.errno == errno.ENOENT:
                    TRACE('!! IPHOTOIMPORT: Unable to process photo %s', photo_path)
                else:
                    unhandled_exc_handler()
                    continue
            except Exception:
                unhandled_exc_handler()
                continue

    @contextmanager
    def files(self):
        yield self.get_iphoto_photos()

    def iphoto_version(self):
        return '%s %s' % ('iPhoto', self.iphoto.get_version())

    def events(self):
        if self._events:
            return self._events
        events = {}
        try:
            raw_events = self.iphoto.get_events()
        except Exception:
            unhandled_exc_handler()
        else:
            for event in raw_events:
                try:
                    events[event['RollID']] = AlbumInfo(uid=event['RollID'], name=event['RollName'], photos_list=event['KeyList'], album_time=event['RollDateAsTimerInterval'])
                except Exception:
                    unhandled_exc_handler()
                    continue

            self._events = events

        return events

    def albums(self):
        albums = {}
        try:
            raw_albums = self.iphoto.get_albums_and_events()
        except Exception:
            unhandled_exc_handler()
        else:
            for album in raw_albums:
                try:
                    albums[album['GUID']] = AlbumInfo(uid=album['GUID'], name=album['AlbumName'], photos_list=album['KeyList'])
                except Exception:
                    unhandled_exc_handler()
                    continue

        return albums


def get_photo_mtime(path):
    try:
        st_mtime = os.stat(path).st_mtime
        if st_mtime < 0:
            raise Exception('st_mtime for file(%r) is negative (%r), the m_time will be invalid' % (path, st_mtime))
        mtime = datetime.fromtimestamp(st_mtime)
    except Exception:
        TRACE('!! IPHOTOIMPORT: Unable to get the mtime on this file: %r', path)
        unhandled_exc_handler()
        mtime = None

    return mtime


class PhotoGalleryImporter(object):
    CONFIG_KEY_DISABLED = 'gallery_import_disabled'
    CONFIG_KEY_LAST_IMPORT = 'gallery_import_last_import'
    CONFIG_KEY_LAST_SCAN = 'gallery_import_last_scan'
    CONFIG_KEY_NUM_FILES_FOUND = 'gallery_import_num_files_found'
    CONFIG_KEY_NUM_EVENTS = 'gallery_import_num_events'
    CONFIG_KEY_SHOW_STICKY = 'gallery_import_show_sticky'
    CONFIG_KEY_SHOW_PREFS_BUTTON = 'gallery_import_show_prefs_button'
    CONFIG_KEY_OUT_OF_SPACE_QUOTA = 'gallery_import_out_of_space_quota'

    def __init__(self, app):
        self.app = app
        self.iphoto = None
        self.num_photos = None
        self.num_events = None
        if feature_enabled('iphoto-importer') and self.app.gandalf.info_received(self._startup):
            self._startup()

    @staticmethod
    def show_import_button(app):
        try:
            if not app.gandalf.allows('desktop-photo-gallery-importer-iphoto'):
                TRACE('IPHOTOIMPORT: show_import_button returning False because of gandalf')
                return False
            ret = app.config.get(PhotoGalleryImporter.CONFIG_KEY_SHOW_PREFS_BUTTON, False)
            TRACE('IPHOTOIMPORT: show_import_button returning %r based on config', ret)
            return ret
        except Exception:
            unhandled_exc_handler()

        return False

    @handle_exceptions
    def _startup(self):
        if not self.app.gandalf.allows('desktop-photo-gallery-importer-iphoto'):
            return
        self.app.on_quota_changed.add_handler(self._on_quota_changed)
        self._on_quota_changed(old_quota=self.app.quota, new_quota=self.app.quota)
        if self.app.config.get(self.CONFIG_KEY_DISABLED) or self.app.config.get(self.CONFIG_KEY_LAST_IMPORT):
            TRACE('IPHOTOIMPORT: Import disabled. Disabled key: %r, out of space: %r, last import: %r', self.app.config.get(self.CONFIG_KEY_DISABLED), self.app.config.get(self.CONFIG_KEY_OUT_OF_SPACE_QUOTA), self.app.config.get(self.CONFIG_KEY_LAST_IMPORT))
            return
        self._refresh_iphoto_scanned_data()
        if self.app.config.get(self.CONFIG_KEY_SHOW_STICKY):
            self.show_sticky()

    def _refresh_iphoto_scanned_data(self, check_space = True):
        self.num_photos = self.app.config.get(self.CONFIG_KEY_NUM_FILES_FOUND, self.num_photos)
        self.num_events = self.app.config.get(self.CONFIG_KEY_NUM_EVENTS, self.num_events)
        try:
            iphoto_last_modified = get_iphoto_last_modified()
        except Exception:
            unhandled_exc_handler()
            return

        if any((self.CONFIG_KEY_SHOW_STICKY not in self.app.config,
         self.num_photos is None,
         self.num_events is None,
         iphoto_last_modified and self.app.config.get(self.CONFIG_KEY_LAST_SCAN, 0) < iphoto_last_modified)):
            self._scan_for_photos(check_space)
        else:
            TRACE('IPHOTOIMPORT: %s photos in iPhoto, %sshowing sticky notification', self.num_photos, '' if self.app.config[self.CONFIG_KEY_SHOW_STICKY] else 'not ')

    def _scan_for_photos(self, check_space = True):
        TRACE('IPHOTOIMPORT: Scanning iPhoto to see if we should prompt to import')
        del self.app.config[self.CONFIG_KEY_SHOW_STICKY]
        del self.app.config[self.CONFIG_KEY_SHOW_PREFS_BUTTON]
        self.app.config[self.CONFIG_KEY_LAST_SCAN] = int(time.time())
        try:
            self.iphoto = IPhotoDevice(handler=self, app=self.app)
        except Exception as e:
            if isinstance(e, NotInstalledError):
                TRACE('IPHOTOIMPORT: IPhoto is not installed on this system. Disabling iPhoto importer')
            elif isinstance(e, IPhotoInsideDropboxError):
                report('iphoto-import', error='iPhoto lib in Dropbox')
                TRACE('IPHOTOIMPORT: iPhoto library is inside Dropbox already!')
            elif isinstance(e, UnsupportedIPhotoVerno):
                report('iphoto-import', error=str(e))
                TRACE('IPHOTOIMPORT: %s', str(e))
            elif isinstance(e, OSError) and e.errno == errno.ENOENT:
                report('iphoto-import', error='iPhoto lib not found')
                TRACE('IPHOTOIMPORT: iPhoto library file not found')
            else:
                unhandled_exc_handler()
                TRACE('IPHOTOIMPORT: iPhoto error. Temporarily disabling iPhoto importer')
            self.app.config[self.CONFIG_KEY_SHOW_STICKY] = False
            self.app.config[self.CONFIG_KEY_SHOW_PREFS_BUTTON] = False
            self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = 0
            return

        self.app.config[self.CONFIG_KEY_SHOW_PREFS_BUTTON] = True
        self.num_photos = self.iphoto.get_num_photos()
        self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = self.num_photos
        self.num_events = len(self.iphoto.events())
        self.app.config[self.CONFIG_KEY_NUM_EVENTS] = self.num_events
        report('iphoto-import', num_photos=self.num_photos)
        if self.num_photos < NUM_PHOTOS_THRESHOLD:
            self.app.config[self.CONFIG_KEY_SHOW_STICKY] = False
            TRACE('IPHOTOIMPORT: Only found %s photos in iPhoto', self.num_photos)
            report('iphoto-import', error='not enough photos')
        elif check_space:
            self.controller = GalleryImportController(app=self.app, done_cb=self.import_done, check_space_callback=self.import_space_usage_callback, import_albums=False, create_subdirs=False)
            self.controller.handle_start(self.iphoto)

    @handle_exceptions
    def _on_quota_changed(self, old_quota, new_quota):
        if self.app.config.get(self.CONFIG_KEY_OUT_OF_SPACE_QUOTA) and (new_quota > self.app.config[self.CONFIG_KEY_OUT_OF_SPACE_QUOTA] or new_quota > old_quota):
            TRACE('IPHOTOIMPORT: Quota changed! Quota in config: %r, old quota: %r, new_quota %r. Rescanning on next startup', self.app.config[self.CONFIG_KEY_OUT_OF_SPACE_QUOTA], old_quota, new_quota)
            del self.app.config[self.CONFIG_KEY_DISABLED]
            del self.app.config[self.CONFIG_KEY_OUT_OF_SPACE_QUOTA]
            del self.app.config[self.CONFIG_KEY_SHOW_STICKY]
            del self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND]
            del self.app.config[self.CONFIG_KEY_NUM_EVENTS]

    @handle_exceptions
    def prompt_import(self, source = 'prefs'):
        TRACE('IPHOTOIMPORT: Prompt import - user is trying import from iPhoto')
        self._refresh_iphoto_scanned_data(check_space=False)
        del self.app.config[self.CONFIG_KEY_DISABLED]
        num_albums = 0
        TRACE('IPHOTOIMPORT: Showing iPhoto splash screen')
        report('iphoto-import', action='%s show splash' % source)
        self.prompt_cb = self.app.ui_kit.show_gallery_import_dialog(self.num_photos, num_albums, self.num_events, import_cb=self._import_from_iphoto, cancel_cb=self._handle_cancel, never_cb=self._never_import, show_quota_promo=self._show_quota_promo(), app=self.app)
        self._remove_iphoto_sticky()

    def _show_quota_promo(self):
        if self.app.mbox.is_dfb_user_without_linked_pair:
            return False
        return self._has_unearned_quota()

    def _has_unearned_quota(self):
        return bool(self.app.photo_uploader.photodb.get_config(CU_QUOTA_UNEARNED))

    def _handle_cancel(self):
        TRACE('IPHOTOIMPORT: User canceled from the iPhoto splash')
        report('iphoto-import', action='splash cancel')
        self.prompt_cb = None

    @handle_exceptions
    def connected(self, device):
        device.ready = True

    @handle_exceptions
    def _import_from_iphoto(self):
        TRACE('IPHOTOIMPORT: User chose to import %r photos from iPhoto!', self.num_photos)
        if not self.app.pref_controller[OPT_IMPORTED_IPHOTOS_ONCE]:
            self.app.pref_controller.update({OPT_IMPORTED_IPHOTOS_ONCE: True})
        self.prompt_cb = None
        if self.iphoto is None:
            self.iphoto = IPhotoDevice(handler=self, app=self.app)
        create_subdirs = self.num_events > 1
        self.controller = GalleryImportController(self.app, self.import_done, check_space_callback=None, import_albums=False, create_subdirs=create_subdirs)
        self.controller.handle_start(self.iphoto)

    @handle_exceptions
    def _never_import(self, source = 'splash'):
        TRACE("IPHOTOIMPORT: User chose 'Never', will not prompt to import again.")
        report('iphoto-import', action='%s never import' % source)
        self.app.config[self.CONFIG_KEY_DISABLED] = True
        self._remove_iphoto_sticky()
        self.prompt_cb = None
        return True

    def _remove_iphoto_sticky(self):
        try:
            self.app.notification_controller.remove_sticky(PhotoGalleryStickyNotification.STICKY_KEY)
            TRACE('IPHOTOIMPORT: Removed sticky notification prompting iPhoto import')
        except StickyNotificationKeyError:
            TRACE('IPHOTOIMPORT: No sticky to remove')
        except Exception:
            unhandled_exc_handler()

    @handle_exceptions
    def import_done(self, device, error, failed_files, transferred_files):
        if error or failed_files:
            TRACE('IPHOTOIMPORT: iPhoto import error - failed to import %d files, error was %r', len(failed_files), error)
            if failed_files:
                self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = self.num_photos = len(failed_files)
            elif transferred_files:
                num_photos = self.num_photos - len(transferred_files)
                if num_photos <= 0:
                    report_bad_assumption('Transferred more files than were detected in iPhoto! num_photos: %d' % num_photos)
                    return
                self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = self.num_photos = num_photos
            if self.num_photos and self.app.config[self.CONFIG_KEY_SHOW_STICKY]:
                self.show_sticky()
        else:
            self.app.config[self.CONFIG_KEY_LAST_IMPORT] = int(time.time())
            TRACE('IPHOTOIMPORT: iPhoto import succeeded! Saving import time.')
            report('iphoto-import', action='import completed')

    @handle_exceptions
    def show_sticky(self):
        TRACE('IPHOTOIMPORT: Showing notification prompting user to import iPhoto photos')
        import_cb = functools.partial(self.prompt_import, source='sticky')
        never_cb = functools.partial(self._never_import, source='sticky')
        sticky = PhotoGalleryStickyNotification(num_photos=self.num_photos, import_source='iPhoto', import_cb=import_cb, never_cb=never_cb)
        self.app.notification_controller.add_sticky(sticky)

    @handle_exceptions
    def import_space_usage_callback(self, space_usage, num_files_to_read):
        self.controller.cancel()
        del self.controller
        if space_usage == NOT_OUT_OF_SPACE:
            self.app.config[self.CONFIG_KEY_NUM_FILES_FOUND] = self.num_photos = num_files_to_read
            if num_files_to_read:
                TRACE('IPHOTOIMPORT: %d photos ready to import from iPhoto!', num_files_to_read)
                report('iphoto-import', action='show sticky')
                self.app.config[self.CONFIG_KEY_SHOW_STICKY] = True
                self.show_sticky()
            else:
                TRACE('IPHOTOIMPORT: No new files found in iPhoto')
                self.app.config[self.CONFIG_KEY_SHOW_STICKY] = False
        else:
            self.app.config[self.CONFIG_KEY_OUT_OF_SPACE_QUOTA] = self.app.quota
            self.app.config[self.CONFIG_KEY_DISABLED] = True
            self.app.config[self.CONFIG_KEY_SHOW_STICKY] = False
            if space_usage == MAYBE_OUT_OF_SPACE:
                TRACE('IPHOTOIMPORT: Cannot import, may run out of space')
                report('iphoto-import', error='maybe out of space')
            elif space_usage == OUT_OF_QUOTA:
                TRACE('IPHOTOIMPORT: Cannot import, will run out of quota')
                report('iphoto-import', error='out of quota')
            elif space_usage == OUT_OF_DISK_SPACE:
                TRACE('IPHOTOIMPORT: Cannot import, will run out of disk space')
                report('iphoto-import', error='out of disk space')


class StuffImporter(object):

    def __init__(self, app):
        self.photo_importer = PhotoGalleryImporter(app)

    @staticmethod
    def show_import_button(app):
        return (PhotoGalleryImporter.show_import_button(app), False)

    def prompt_import(self):
        self.photo_importer.prompt_import()
