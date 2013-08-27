#Embedded file name: dropbox/client/photoimporter.py
from __future__ import absolute_import
import collections
import datetime
import errno
import itertools
import json
import operator
import pprint
import re
import struct
import threading
import time
from contextlib import contextmanager
from hashlib import md5
import arch
import dropbox.fsutil as fsutil
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, BetterDropboxHasher
from dropbox.attrs import attr_dict_from_whitelist, Attributes, get_attr_data, unfreeze_attr_dict
from dropbox.build_common import get_build_number
from dropbox.camera import PhotoImportCanceled, PhotoImportDisconnected, PhotoImportSelectiveSync, PhotoImportDeviceLocked, PhotoImportExceptionBase, PhotoImportLowDropboxSpace, PhotoImportNoConnectionError, PhotoImportAlbumCreationError
from dropbox.camera.util import is_apple_device
from dropbox.callbacks import Observable, ObservableIterator
from dropbox.debugging import easy_repr
from dropbox.dbexceptions import LowDiskSpaceError
from dropbox.functions import batch, handle_exceptions, safe_str, split_extension
from dropbox.i18n import trans
from dropbox.lock_ordering import NonRecursiveLock
from dropbox.metadata.metadata import get_metadata_for_plat
from dropbox.metadata.transforms import try_rotate_image_file
from dropbox.native_event import AutoResetEvent
from dropbox.path import ServerPath
from dropbox.timehelper import tz_offset_string
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption, reraise_exc_handler
IMPORT_FREE_SPACE_BUFFER = 50 * 1024 * 1024
CU_HASH_8_BYTES = 8 * 1024
NUM_READ_RETRIES = 10
XATTR_EXIF_MANUFACTURER = 'exif_manufacturer'
XATTR_EXIF_MODEL = 'exif_model'
XATTR_EXIF_DATETIME = 'exif_datetime'
XATTR_DEVICE_MANUFACTURER = 'device_manufacturer'
XATTR_DEVICE_MODEL = 'device_model'
XATTR_DEVICE_NAME = 'device_name'
XATTR_DEVICE_UID = 'device_uid'
XATTR_DEVICE_SERIALNUM = 'device_serialnum'
XATTR_CLIENT_IMPORT_TIME = 'client_import_time'
XATTR_CLIENT_PLATFORM = 'client_platform'
XATTR_CLIENT_BUILDSTRING = 'client_buildstring'
XATTR_CLIENT_USERID = 'client_userid'
XATTR_CLIENT_TIMEOFFSET = 'client_timeoffset'
XATTR_FILE_DATETIME = 'file_datetime'
XATTR_FILE_MTIME = 'file_mtime'
XATTR_FILE_HASHFULL = 'file_hashfull'
XATTR_FILE_NAMEORIG = 'file_nameorig'
CAMERA_XATTRS = [XATTR_EXIF_MANUFACTURER,
 XATTR_EXIF_MODEL,
 XATTR_EXIF_DATETIME,
 XATTR_DEVICE_MANUFACTURER,
 XATTR_DEVICE_MODEL,
 XATTR_DEVICE_NAME,
 XATTR_DEVICE_UID,
 XATTR_DEVICE_SERIALNUM,
 XATTR_CLIENT_IMPORT_TIME,
 XATTR_CLIENT_PLATFORM,
 XATTR_CLIENT_BUILDSTRING,
 XATTR_CLIENT_USERID,
 XATTR_CLIENT_TIMEOFFSET,
 XATTR_FILE_DATETIME,
 XATTR_FILE_MTIME,
 XATTR_FILE_HASHFULL]
CAMERA_XATTRS_PLAT = 'dropbox_camera_upload'
XATTR_COLLECTION_GIDS = 'collection_gids'
COLLECTION_XATTRS_PLAT = 'dropbox_collection_gid'
PHOTOIMPORT_EXCEPTIONS_RERAISE = (PhotoImportExceptionBase, LowDiskSpaceError)
EXIF_IMAGE_ORIENTATION = 'Image Orientation'
EXIF_IMAGE_MAKE = 'Image Make'
EXIF_IMAGE_MODEL = 'Image Model'
EXIF_LENGTH = 'EXIF ExifImageLength'
EXIF_WIDTH = 'EXIF ExifImageWidth'
EXIF_THUMBNAIL = 'Thumbnail Compression'
EXIF_THUMBNAIL_OFFSET = 'Thumbnail JPEGInterchangeFormat'
EXIF_THUMBNAIL_ORIENTATION = 'Thumbnail Orientation'
EXIF_JPEG_THUMBNAIL = 'JPEGThumbnail'
EXIF_TIFF_THUMBNAIL = 'TIFFThumbnail'
EXIF_DATETIME = 'EXIF DateTimeOriginal'
EXIF_CUSTOMRENDERED = 'EXIF CustomRendered'
PHOTO_EXIF_WHITELIST = {'exif': {EXIF_IMAGE_ORIENTATION: {},
          EXIF_IMAGE_MAKE: {},
          EXIF_IMAGE_MODEL: {},
          EXIF_LENGTH: {},
          EXIF_WIDTH: {},
          EXIF_THUMBNAIL: {},
          EXIF_THUMBNAIL_OFFSET: {},
          EXIF_THUMBNAIL_ORIENTATION: {},
          EXIF_JPEG_THUMBNAIL: {},
          EXIF_TIFF_THUMBNAIL: {},
          EXIF_DATETIME: {},
          EXIF_CUSTOMRENDERED: {}}}
EXIF_TO_CAMERA_ATTR = {EXIF_IMAGE_MAKE: XATTR_EXIF_MANUFACTURER,
 EXIF_IMAGE_MODEL: XATTR_EXIF_MODEL,
 EXIF_DATETIME: XATTR_EXIF_DATETIME}
DEFAULT_UPLOAD_LOCATION = u'/Camera Uploads'
EXIF_DATETIME_STRPTIME_FMTS = ['%Y:%m:%d %H:%M:%S', '%Y:%m:%d:%H:%M:%S', '%Y:%m:%d %I:%M:%S %p']

def parse_exif_datetime(data, strptime_fn):
    normalized_data = data.replace('/', ':').replace('-', ':').replace('.', '')
    for i, pattern in enumerate(EXIF_DATETIME_STRPTIME_FMTS):
        try:
            return strptime_fn(normalized_data, pattern)
        except ValueError:
            if i == len(EXIF_DATETIME_STRPTIME_FMTS) - 1:
                raise
            continue


def _nexus_datetime_from_path(taken_at, path):
    try:
        match = re.search('img_(\\d{8}_\\d{6})(_\\d+)?\\.jpg', path.lower())
        if match:
            fname_datetime = datetime.datetime.strptime(match.group(1), '%Y%m%d_%H%M%S')
            delta = fname_datetime - taken_at
            if abs(delta) > datetime.timedelta(seconds=60):
                taken_at = fname_datetime
    except ValueError:
        pass
    except Exception:
        unhandled_exc_handler()

    return taken_at.strftime('%Y:%m:%d %H:%M:%S')


def _motorola_datetime_from_path(taken_at, path):
    try:
        match = re.search('(\\d{4}).(\\d{2}).(\\d{2}).(\\d{2}).(\\d{2}).(\\d{2})(_\\d+)?\\.jpg', path.lower())
        if match:
            fname_datetime = datetime.datetime(*map(int, match.group(1, 2, 3, 4, 5, 6)))
            delta = fname_datetime - taken_at
            if abs(delta) > datetime.timedelta(seconds=60):
                taken_at = fname_datetime
    except ValueError:
        pass
    except Exception:
        unhandled_exc_handler()

    return taken_at.strftime('%Y:%m:%d %H:%M:%S')


def update_device_specific_deets(details):
    exif_data = details.exif
    if EXIF_DATETIME in exif_data:
        try:
            taken_at = parse_exif_datetime(exif_data[EXIF_DATETIME], datetime.datetime.strptime)
            if (exif_data.get('Image Make', '').lower(), exif_data.get('Image Model', '').lower()) in (('lge', 'nexus 4'), ('samsung', 'galaxy nexus')):
                exif_data[EXIF_DATETIME] = _nexus_datetime_from_path(taken_at, details.f_name)
            elif exif_data.get('Image Make', '').lower() == 'motorola':
                exif_data[EXIF_DATETIME] = _motorola_datetime_from_path(taken_at, details.f_name)
        except ValueError:
            TRACE('Unable to parse %r into datetime.', exif_data[EXIF_DATETIME])
        except Exception:
            unhandled_exc_handler()


class PhotoDetails(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('blocklist', 'size', 'mtime', 'path', 'cu_hash_8', 'cu_hash_full', 'exif', 'f_obj', 'f_name', 'f_basename', 'f_ext', 'f_time', 'photo_name', 'photo_time', 'member_of_albums', 'rotation_result')

    def __init__(self, f_obj):
        self.mtime = time.time()
        self.f_obj = f_obj
        self.f_time = f_obj.time()
        self.size = f_obj.size()
        self.f_name = f_obj.name()
        self.f_basename, self.f_ext = split_extension(self.f_name)
        self.member_of_albums = None

    def __repr__(self):
        return easy_repr(self, 'f_obj', 'f_time', 'size', 'f_name')


OUT_OF_QUOTA = 'out of quota'
OUT_OF_DISK_SPACE = 'out of disk space'
NOT_OUT_OF_SPACE = 'not out of space'
MAYBE_OUT_OF_SPACE = 'maybe out of space'

class PhotoImporter(threading.Thread):
    STARTING, SCANNING, TRANSFERRING, DONE = range(4)
    N = 0
    lock = NonRecursiveLock()

    def __init__(self, device, uploader, app):
        with PhotoImporter.lock:
            thread_name = 'CAMERAIMPORTER-%d' % PhotoImporter.N
            PhotoImporter.N += 1
            self.importer_id = PhotoImporter.N
        super(PhotoImporter, self).__init__(name=thread_name)
        self.device = device
        self.uploader = uploader
        self.photodb = self.uploader.photodb
        self.app = app
        self.fs = self.app.sync_engine.fs
        self.state = Observable(self.STARTING, handle_exc=unhandled_exc_handler)
        self.total_bytes = Observable(0, handle_exc=unhandled_exc_handler)
        self.cur_bytes = Observable(0, handle_exc=unhandled_exc_handler)
        self.transferred_files = Observable([], handle_exc=unhandled_exc_handler)
        self.error = Observable(None, handle_exc=unhandled_exc_handler)
        self.found_files = Observable(0, handle_exc=unhandled_exc_handler)
        self.remaining_files = set([])
        self.skipped_files = []
        self._cancel = False
        self._disconnected = False
        self._event = AutoResetEvent()
        self.has_imported = False
        self.cu_hashes_full = set()
        self._show_finding_progress = False
        self._dest_path_verified = False
        self._files_to_read = None

    def _prep_for_file_read(self):
        pass

    def cancel(self):
        self._cancel = True
        self._event.set()
        return False

    def disconnected(self):
        self._disconnected = True
        self._event.set()
        return False

    def device_ready(self):
        self._event.set()

    def check_cancel(self, timeout = 0):
        self._event.wait(timeout=timeout)
        if self._cancel:
            raise PhotoImportCanceled()
        if self._disconnected:
            raise PhotoImportDisconnected()

    def _get_dest_path_sp(self):
        return ServerPath.from_ns_rel(self.app.sync_engine.main_root_ns, self.uploader.location or DEFAULT_UPLOAD_LOCATION)

    def run(self):
        try:
            if self.app.quota < self.app.in_use:
                raise PhotoImportLowDropboxSpace()
            self.state.set(self.STARTING)
            if not self.app.sync_engine.check_if_initial_list_is_done():
                ev = threading.Event()
                if not self.app.sync_engine.check_if_initial_list_is_done(ev.set):
                    ev.wait()
            status = self.app.sync_engine.status
            while not status.try_set_status_label('importing', True, fail_if_set=['moving']):
                TRACE('Currently moving Dropbox folder, import thread is sleeping. Status: %r', status.get_status())
                self.check_cancel(1)

            wait_for_list_results_thunk = self.uploader.demand_freshness()
            try:
                while not self.device.ready:
                    if not self._show_finding_progress and self.device.percent != 100 and self.device.percent < 40:
                        self._show_finding_progress = True
                        self.total_bytes.set(100)
                    if self._show_finding_progress:
                        self.cur_bytes.set(self.device.percent)
                    TRACE('Device is still connecting.')
                    self.check_cancel(1)

                self._prep_for_file_read()
                sync_engine = self.app.sync_engine
                self.dest_path_sp = self._get_dest_path_sp()
                self.dest_path = sync_engine.server_to_local(self.dest_path_sp)
                self.cache_path = sync_engine.verify_cache_path()
                self.sel_sync = sync_engine._ignore_set_should_ignore(self.dest_path_sp)
                self.import_time = time.time()
                self.device_attr_dict = self._create_device_attr_dict(self.device)
                with self.device.files() as files:

                    def update_found_files(num_found):
                        self.found_files.set(num_found)
                        if num_found % 50 == 0:
                            self.check_cancel()

                    files_observed = ObservableIterator(files, handle_exc=reraise_exc_handler)
                    files_observed.register(update_found_files)
                    if wait_for_list_results_thunk:
                        wait_for_list_results_thunk()
                        wait_for_list_results_thunk = None
                    self._files_to_read = self._filter_device_files((PhotoDetails(f) for f in files_observed))
                    if not self._files_to_read:
                        return
                    available_quota, available_disk_space = self.get_available_space()
                    import_space_usage = self.get_import_space_usage(self._files_to_read, available_quota, available_disk_space, num_imported=self.photodb.num_imported())
                    self.import_normally = self.can_import_normally(import_space_usage)
                    if not self.import_normally:
                        self.get_available_space(trace=True)
                    self._transfer_files()
            finally:
                status.set_status_label('importing', False)
                TRACE("Setting status label 'importing' to false!")

        except Exception as e:
            TRACE('!! Photo import raised exception %r', e)
            if not isinstance(e, PHOTOIMPORT_EXCEPTIONS_RERAISE):
                unhandled_exc_handler()
            if arch.photouploader.is_disconnected_error(e):
                TRACE('Exception seems to be the result of a device disconnection. Not bubbling import error.')
            else:
                self.error.set(e)
        else:
            self.error.set(None)
        finally:
            self.state.set(self.DONE)
            self.device.release()

    @staticmethod
    def _filter_seen_photos(device_files, seen_photos):
        if not seen_photos:
            return (list(device_files), [], [])
        TRACE('%d photos have been imported from this device before. Pruning.', len(seen_photos))
        entries_seen = []
        new_files = []
        for details in device_files:
            photo = (details.f_name, details.f_time)
            if details.f_time is not None and photo in seen_photos:
                seen_photos.remove(photo)
                entries_seen.append(details)
            else:
                new_files.append(details)

        return (new_files, list(seen_photos), entries_seen)

    @contextmanager
    def _handle_photo_exceptions(self):
        try:
            yield
        except PHOTOIMPORT_EXCEPTIONS_RERAISE:
            raise
        except (IOError, OSError) as e:
            if e.errno == errno.ENOSPC:
                raise LowDiskSpaceError(0, 0)
            self.device.handle_disconnect_exceptions(e)
            unhandled_exc_handler()
        except Exception as e:
            self.device.handle_disconnect_exceptions(e)
            unhandled_exc_handler()

    @staticmethod
    def update_photo_name_and_time(details, default = None):
        try:
            st_time = parse_exif_datetime(details.exif.get(EXIF_DATETIME, ''), time.strptime)
            details.photo_name = time.strftime(u'%Y-%m-%d %H.%M.%S', st_time)
            details.photo_time = time.mktime(st_time)
        except Exception:
            TRACE('Failed to rename photo by EXIF time, falling back to default!')
            st_time = details.f_time.timetuple() if details.f_time else time.localtime(default)
            details.photo_name = time.strftime(u'%Y-%m-%d %H.%M.%S', st_time)
            details.photo_time = time.mktime(st_time)

    def update_photo_details(self, details):
        with self.fs.open(details.path, 'r') as tmp:
            details.exif = get_metadata_for_plat('exif', tmp, PHOTO_EXIF_WHITELIST).get('exif', {})
        update_device_specific_deets(details)
        self.update_photo_name_and_time(details, default=self.import_time)
        if 'HDR' in details.exif.get(EXIF_CUSTOMRENDERED, ''):
            details.photo_name += u' HDR'

    def _filter_device_files(self, device_files):
        TRACE('Looking for previously imported files from this device.')
        files, entries_to_remove, self.skipped_files = self._filter_seen_photos(device_files, self.photodb.get_seen_photos(self.device.uid))
        if (files or self.skipped_files) and entries_to_remove:
            TRACE('Pruning %d entries from the database.', len(entries_to_remove))
            self.photodb.del_seen_photos(self.device.uid, entries_to_remove)
        TRACE('Found and processing %r new files from device! (%r seen photos skipped, %r seen photos removed)', len(files), len(self.skipped_files), len(entries_to_remove))
        found_nothing = not files and not self.skipped_files
        if arch.constants.platform == 'win' and is_apple_device(self.device) and found_nothing:
            raise PhotoImportDeviceLocked()
        if self.device.locked and found_nothing:
            raise PhotoImportDeviceLocked()
        TRACE('%r potentially new files will be read from device!', len(files))
        return files

    def _transfer_files(self):
        files = self._files_to_read
        self.total_bytes.set(sum((deet.size for deet in files)))
        self.has_imported = self._has_imported_before()
        self.remaining_files = set(files)
        self.state.set(self.SCANNING)
        cache = self.cache_path.join(datetime.date.today().strftime('camera-import-%Y-%m-%d'), str(self.importer_id))
        retries = [0]
        pending_files = collections.deque()
        by_timestamp = []
        self.pending_size_in_cache = 0

        def progress(n):
            self.cur_bytes.set(self.cur_bytes.get() + n)

        self.app.safe_makedirs(unicode(cache))
        try:
            for i, details in enumerate(files):
                with self._handle_photo_exceptions():
                    self.check_cancel()
                    self.app.sync_engine.verify_disk_space(cache, details.size)
                    bytes_read = self._read_and_hash(details, cache, retries, self.check_cancel, progress)
                    if bytes_read == 0:
                        TRACE('Skipping 0 byte file %r', details)
                        self.skipped_files.append(details)
                        self.remaining_files.remove(details)
                        continue
                    self.update_photo_details(details)
                    if self._handle_existing_hashes(details, files, i):
                        continue
                    if self.sel_sync:
                        raise PhotoImportSelectiveSync(self.dest_path_sp)
                    if self._end_photo_group(pending_files, details):
                        self._maybe_write_photos(pending_files, by_timestamp)
                        pending_files.clear()
                    pending_files.append(details)

            if pending_files:
                with self._handle_photo_exceptions():
                    self._maybe_write_photos(pending_files, by_timestamp)
                    pending_files.clear()
        except (LowDiskSpaceError, PhotoImportLowDropboxSpace, PhotoImportSelectiveSync):
            raise
        except Exception:
            self.complete_maybe_import(by_timestamp)
            raise
        else:
            self.complete_maybe_import(by_timestamp)
        finally:
            try:
                fsutil.rmtree(self.fs, cache, ignore_errors=True)
            except Exception:
                unhandled_exc_handler()

    def _end_photo_group(self, pending_files, curr_deets):
        return pending_files and pending_files[0].photo_name != curr_deets.photo_name

    def complete_maybe_import(self, by_timestamp):
        if not self.import_normally:
            for by_basename in by_timestamp:
                with self._handle_photo_exceptions():
                    self.check_space(sum((deet.size for f_basename, deet_list in by_basename for deet in deet_list)))
                    self._rename_photos(by_basename)

    def _read_and_hash(self, details, dest_dir, retries, check_cancel, progress_cb):
        dest = None
        bytes_read = 0
        assert struct.calcsize('I') == 4
        mask = 2 ** (8 * struct.calcsize('I')) - 1
        try:
            with details.f_obj.open(self.fs, dest_dir) as read:
                cu_hash_full = md5()
                cu_hash_8 = md5()
                cu_hash_8_left = CU_HASH_8_BYTES
                fail_fast = getattr(details.f_obj, 'fail_fast', False)
                needs_write = getattr(details.f_obj, 'needs_write', True)
                cu_hash_8.update(struct.pack('>I', details.size & mask))
                while True:
                    check_cancel()
                    try:
                        buf = read(DROPBOX_MAX_BLOCK_SIZE)
                    except Exception:
                        retries[0] += 1
                        if retries[0] >= NUM_READ_RETRIES or fail_fast:
                            raise
                        check_cancel(1)
                        try:
                            buf = read(DROPBOX_MAX_BLOCK_SIZE)
                        except Exception:
                            raise
                        else:
                            retries[0] = 0

                    else:
                        retries[0] = 0

                    if not buf:
                        break
                    l_buf = len(buf)
                    progress_cb(l_buf)
                    bytes_read += l_buf
                    if needs_write:
                        if dest is None:
                            dest = fsutil.mkstemp(self.fs, suffix=details.f_ext, dir=dest_dir)
                            details.path = self.fs.make_path(dest.name)
                        dest.write(buf)
                    size = len(buf)
                    cu_hash_full.update(buf)
                    if cu_hash_8_left:
                        m_8 = min(cu_hash_8_left, size)
                        cu_hash_8.update(buffer(buf, 0, m_8))
                        cu_hash_8_left -= m_8

                if not needs_write:
                    details.path = self.fs.make_path(details.f_obj.path)
        finally:
            if dest:
                dest.close()

        details.cu_hash_8 = cu_hash_8.hexdigest()
        details.cu_hash_full = cu_hash_full.hexdigest()
        if bytes_read != details.size:
            report_bad_assumption("Bytes read don't match details")
        return bytes_read

    def get_import_space_usage(self, *args, **kwargs):
        return self.import_space_usage(*args, **kwargs)

    @staticmethod
    def import_space_usage(files, available_quota, available_disk, num_imported):
        max_import_size = sum((f.size for f in files))
        min_import_size = sum((f.size for f in sorted(files, key=operator.attrgetter('size'))[:-num_imported])) if num_imported else max_import_size
        TRACE('Determining if importing normally: max import size: %r, num imported: %r, min import size: %r', max_import_size, num_imported, min_import_size)
        if available_quota >= max_import_size and available_disk >= max_import_size:
            return NOT_OUT_OF_SPACE
        if available_quota < min_import_size:
            return OUT_OF_QUOTA
        if available_disk < min_import_size:
            return OUT_OF_DISK_SPACE
        return MAYBE_OUT_OF_SPACE

    def can_import_normally(self, import_space_usage):
        if import_space_usage == NOT_OUT_OF_SPACE:
            TRACE('Definitely not going over quota.  Importing normally.')
            return True
        if import_space_usage == OUT_OF_QUOTA:
            raise PhotoImportLowDropboxSpace()
        elif import_space_usage == OUT_OF_DISK_SPACE:
            raise LowDiskSpaceError(0, 0)
        elif import_space_usage == MAYBE_OUT_OF_SPACE:
            TRACE("!! May go over quota, can't import normally.  Importing into the cache temporarily!")
            return False

    def get_available_space(self, pending_size_in_cache = 0, trace = False):
        quota = self.app.quota
        unearned = self.uploader.cu_quota_unearned
        in_use = self.app.in_use
        pending_size = self.photodb.get_pending_size() + pending_size_in_cache
        if pending_size < 0:
            report_bad_assumption('In get_available_space, pending size is negative! photodb.pending: %r, pending_in_cache: %r', self.photodb.get_pending_size(), pending_size_in_cache)
        quota_remaining = quota + unearned - in_use - pending_size - IMPORT_FREE_SPACE_BUFFER
        free_disk_space = self.fs.get_disk_free_space(self.app.config['dropbox_path'])
        disk_space_remaining = free_disk_space - IMPORT_FREE_SPACE_BUFFER
        if trace:
            pending = self.photodb.pending()
            TRACE('quota(%s) + unearned(%s) - in_use(%s) - pending(%s (%s)) - buffer(%s) = %s', quota, unearned, in_use, pending_size, len(pending), IMPORT_FREE_SPACE_BUFFER, quota_remaining)
            TRACE('free disk space(%s) - buffer(%s) = %s', free_disk_space, IMPORT_FREE_SPACE_BUFFER, disk_space_remaining)
            TRACE('Pending = %s', pprint.pformat(pending))
        return (quota_remaining, disk_space_remaining)

    def check_space(self, size, pending_size_in_cache = 0):
        avail_quota, avail_disk = self.get_available_space(pending_size_in_cache)
        if avail_quota < size:
            self.get_available_space(pending_size_in_cache, trace=True)
            raise PhotoImportLowDropboxSpace()
        if avail_disk < size:
            self.get_available_space(pending_size_in_cache, trace=True)
            raise LowDiskSpaceError(0, 0)

    def generate_path_from_deets(self, details, n):
        fn = u'%s%s%s' % (details.photo_name, u'-%d' % n if n else u'', details.f_ext.lower())
        return self.dest_path.join(fn)

    def _handle_dup(self, details):
        self.skipped_files.append(details)
        self.remaining_files.remove(details)
        fsutil.safe_remove(self.fs, details.path)
        if details.f_time:
            self.uploader.add_seen_photos(self.device.uid, ((details.f_name, details.f_time),))

    def _handle_existing_hashes(self, details, files, cur_index):
        is_dup = False
        if details.cu_hash_full in self.cu_hashes_full or self.uploader.exists(details.cu_hash_full):
            is_dup = True
            TRACE('Photo %r, cu_hash_full %r exists in our photo database already!  Not importing', details.f_name, details.cu_hash_full)
            self._handle_dup(details)
        else:
            self.cu_hashes_full.add(details.cu_hash_full)
            self._rotate_and_hash(details)
        return is_dup

    def _maybe_write_photos(self, files, by_timestamp):
        try:
            self.check_cancel()
            size = sum((deets.size for deets in files))
            self.check_space(size, self.pending_size_in_cache)
            details_by_f_basename = collections.defaultdict(list)
            for details in files:
                details_by_f_basename[details.f_basename].append(details)

            by_basename = sorted(details_by_f_basename.iteritems())
            if self.import_normally:
                self._rename_photos(by_basename)
            else:
                by_timestamp.append(by_basename)
                self.pending_size_in_cache += size
        except PHOTOIMPORT_EXCEPTIONS_RERAISE:
            raise
        except Exception:
            unhandled_exc_handler()

    def _rename_photos(self, ordered_by_f_basename):
        self._verify_dest_path(ordered_by_f_basename)
        suffix = 0 if len(ordered_by_f_basename) == 1 else 1
        to_add_seen = []
        for f_name, details_list in ordered_by_f_basename:
            self.state.set(self.TRANSFERRING)
            self.check_cancel()
            for n in itertools.count(suffix):
                paths = [ self.generate_path_from_deets(details, n) for details in details_list ]
                if any((fsutil.is_exists(self.fs, path) for path in paths)):
                    continue
                else:
                    break
            else:
                raise Exception('Too many files with the same name')

            suffix = n + 1
            for path, details in itertools.izip(paths, details_list):
                details.photo_time += n * 0.001
                try:
                    self._write_photo_to_path(details, path)
                except Exception:
                    unhandled_exc_handler()
                    continue

                if not self.uploader.exists(details.cu_hash_full):
                    self.uploader.add_photo(details)
                self.transferred_files.append(details)
                self.remaining_files.remove(details)
                if details.f_time:
                    to_add_seen.append((details.f_name, details.f_time))
                TRACE('Downloaded image to %r, blocklist %r', path, details.blocklist)

        if to_add_seen:
            self.uploader.add_seen_photos(self.device.uid, to_add_seen)

    def _has_imported_before(self):
        return self.photodb.has_imported()

    def _verify_dest_path(self, file_deets_pairs = None, force = False):
        if self._dest_path_verified and not force:
            return
        dirs_created = []
        fsutil.makedirs(self.fs, self.dest_path, dirs_created)
        if dirs_created:
            try:
                self.app.sync_engine._retag_special_folders()
            except Exception:
                unhandled_exc_handler()

        else:
            self.has_imported = self.has_imported or self._has_imported_before()
            if not self.has_imported:
                reason = trans(u'Old')
                self.app.sync_engine._resolve_conflict(self.dest_path, self.dest_path.basename, reason)
                fsutil.makedirs(self.fs, self.dest_path)
        self.has_imported = True
        self._dest_path_verified = True

    def _rotate_and_hash(self, details):
        exif_attrs = details.exif

        def on_success(path):
            if self.uploader.rotation_type == self.uploader.ROTATION_TYPE_V1:
                path = self.fs.make_path(path)
                old_path = details.path
                new_temp = details.path.append(u'.rot')
                self.fs.rename(path, new_temp)
                details.path = new_temp
                fsutil.safe_remove(self.fs, old_path)

        event_result = try_rotate_image_file(unicode(details.path), ext=details.f_ext, exif_attrs=exif_attrs, on_error=unhandled_exc_handler, on_success=on_success, cache_dir=unicode(self.cache_path))
        TRACE('Rotation event result: %r rotation type: %r', event_result, self.uploader.rotation_type)
        details.rotation_result = event_result
        dbhash = BetterDropboxHasher()
        with self.fs.open(details.path, sequential=True) as f:
            while True:
                s = f.read(DROPBOX_MAX_BLOCK_SIZE)
                if s == '':
                    break
                dbhash.update(s)

        details.blocklist = dbhash.digest()

    def _write_photo_to_path(self, details, newpath):
        self.fs.rename(details.path, newpath)
        details.path = newpath
        try:
            self._write_attrs(details)
        except Exception:
            unhandled_exc_handler()

        exif_attrs = details.exif
        try:
            self.report_camera_event('photo-rotate', self.device, result=details.rotation_result, length=exif_attrs.get(EXIF_LENGTH, ''), width=exif_attrs.get(EXIF_WIDTH, ''), orientation=exif_attrs.get(EXIF_IMAGE_ORIENTATION, ''), thumbnail=EXIF_THUMBNAIL in exif_attrs, rotation_type=self.uploader.rotation_type)
        except Exception:
            unhandled_exc_handler()

        try:
            self.fs.set_file_mtime(details.path, details.photo_time)
        except Exception:
            unhandled_exc_handler()

    def _write_attrs(self, details):
        camera_import_attrs = self._create_import_attrs(details)
        self.app.sync_engine.attr_handler.write_attributes(camera_import_attrs, None, details.path)

    def _create_device_attr_dict(self, device):
        attr_dict = {}
        for xattr in CAMERA_XATTRS:
            if xattr.startswith('device'):
                try:
                    device_attr_name = xattr.split('_')[1]
                except Exception:
                    TRACE('!!Camera xattr name %r not formatted properly!  Expected device_[propertyname]', xattr)
                    unhandled_exc_handler()
                else:
                    device_attr = getattr(self.device, device_attr_name, None)
                    if device_attr:
                        if not isinstance(device_attr, str):
                            device_attr = device_attr.encode('utf8')
                        attr_dict[xattr] = device_attr

        plat_string = arch.util.get_platform_info()
        plat_string = plat_string[0] + ' ' + plat_string[3]
        import_attr_dict = {XATTR_CLIENT_IMPORT_TIME: str(int(self.import_time * 1000)),
         XATTR_CLIENT_TIMEOFFSET: tz_offset_string(datetime.datetime.now()),
         XATTR_CLIENT_PLATFORM: plat_string,
         XATTR_CLIENT_BUILDSTRING: get_build_number(),
         XATTR_CLIENT_USERID: str(self.app.uid)}
        attr_dict.update(import_attr_dict)
        TRACE('Readable general import attrs: %r', attr_dict)
        return attr_dict

    def _get_additional_import_attrs(self, *args, **kwargs):
        return (None, None)

    def _create_import_attrs(self, details):
        old_attrs = self.app.sync_engine.attr_handler.read_attributes(details.path)
        old_attrs_dict = unfreeze_attr_dict(old_attrs.attr_dict)
        attr_dict = self._create_file_attr_dict(details)
        TRACE('Readable camera upload file attrs: %r, file: %r', attr_dict, details.path)
        attr_dict.update(self.device_attr_dict)
        attr_dict = attr_dict_from_whitelist(attr_dict, CAMERA_XATTRS_PLAT)
        formatted = old_attrs_dict
        formatted.update(dict([(CAMERA_XATTRS_PLAT, attr_dict)]))
        additional_plats, additional_attrs = self._get_additional_import_attrs(details, old_attrs_dict)
        if additional_attrs:
            formatted.update(additional_attrs)
        new_data_plats = set(old_attrs.data_plats)
        new_data_plats.add(CAMERA_XATTRS_PLAT)
        if additional_plats:
            new_data_plats.add(additional_plats)
        attrs = Attributes(attr_dict=formatted, data_plats=new_data_plats)
        TRACE('Encoded attrs: %r', attrs)
        return attrs

    def _create_file_attr_dict(self, details):
        ret = {}
        for exif_attr_name, attr in details.exif.items():
            if exif_attr_name in EXIF_TO_CAMERA_ATTR:
                ret[EXIF_TO_CAMERA_ATTR[exif_attr_name]] = attr

        manufacturer = ret.get(XATTR_EXIF_MANUFACTURER, None)
        model = ret.get(XATTR_EXIF_MODEL, None)
        if manufacturer and model:
            manufacturer = manufacturer.split()[0]
            if model.startswith(manufacturer):
                model = model[len(manufacturer):].strip()
            ret[XATTR_EXIF_MANUFACTURER] = manufacturer
            ret[XATTR_EXIF_MODEL] = model
        if details.photo_time:
            try:
                photo_time = datetime.datetime.fromtimestamp(details.photo_time)
                _datetime = photo_time.strftime('%Y:%m:%d %H:%M:%S')
                if photo_time.microsecond:
                    _datetime += '.%.3d' % (photo_time.microsecond / 1000)
            except Exception:
                unhandled_exc_handler()
            else:
                ret[XATTR_FILE_DATETIME] = _datetime

        ret[XATTR_FILE_HASHFULL] = details.cu_hash_full
        try:
            basename = self.app.sync_engine.arch.make_path(unicode(details.f_name)).basename
        except Exception:
            basename = unicode(details.f_name)

        ret[XATTR_FILE_NAMEORIG] = safe_str(basename)
        return ret


def get_albums_by_photo_dict(albums_list):
    by_photo_id = collections.defaultdict(list)
    for album in albums_list:
        for photo_id in album.photos_list:
            by_photo_id[photo_id].append(album)

    return by_photo_id


class PhotoGalleryImporter(PhotoImporter):
    ALBUM_BATCH_SIZE = 250

    def __init__(self, *args, **kwargs):
        self.check_space_callback = kwargs.pop('check_space_callback')
        self.import_albums = kwargs.pop('import_albums')
        self.create_event_subdirs = kwargs.pop('create_subdirs')
        super(PhotoGalleryImporter, self).__init__(*args, **kwargs)
        self.albums_by_photo = {}
        self.event_dirname_by_id = {}

    def _get_additional_import_attrs(self, details, old_attrs):
        if details.member_of_albums:
            existing_albums = []
            try:
                try:
                    attr = old_attrs[COLLECTION_XATTRS_PLAT][XATTR_COLLECTION_GIDS]
                except KeyError:
                    pass
                else:
                    existing_albums = json.loads(get_attr_data(attr))

            except Exception:
                unhandled_exc_handler()

            albums = [ album.server_collection_gid for album in details.member_of_albums ]
            albums += existing_albums
            attr_dict = dict([(XATTR_COLLECTION_GIDS, json.dumps(albums))])
            TRACE('IPHOTOIMPORT: Album membership file attrs: %r', attr_dict)
            attr_dict = attr_dict_from_whitelist(attr_dict, COLLECTION_XATTRS_PLAT)
            return (COLLECTION_XATTRS_PLAT, dict([(COLLECTION_XATTRS_PLAT, attr_dict)]))
        return (None, None)

    def _get_dest_path_sp(self):
        default_location = '/' + trans(u'Photos from iPhoto')
        return ServerPath.from_ns_rel(self.app.sync_engine.main_root_ns, default_location)

    def _has_imported_before(self):
        return self.photodb.get_device_last_import(self.device.uid) is not None

    def update_photo_details(self, details):
        super(PhotoGalleryImporter, self).update_photo_details(details)
        details.member_of_albums = self.albums_by_photo.get(details.f_obj.id)

    @staticmethod
    def update_photo_name_and_time(details, default = None):
        try:
            st_time = details.f_obj.iphoto_time()
            if st_time is None:
                st_time = parse_exif_datetime(details.exif.get(EXIF_DATETIME, ''), time.strptime)
            details.photo_name = time.strftime(u'%Y-%m-%d %H.%M.%S', st_time)
            details.photo_time = time.mktime(st_time)
        except Exception:
            TRACE('Failed to rename photo by EXIF or iPhoto time, falling back to default!')
            st_time = details.f_time.timetuple() if details.f_time else time.localtime(default)
            details.photo_name = time.strftime(u'%Y-%m-%d %H.%M.%S', st_time)
            details.photo_time = time.mktime(st_time)

    def _prep_for_file_read(self):
        if self.create_event_subdirs:
            self.events = self.device.events()
            TRACE('IPHOTOIMPORT: Got %d events', len(self.events))
        if self.import_albums:
            albums = self.device.albums()
            server_gids = []
            if albums:
                albums_list = albums.values()
                server_id_by_iphoto_id = self.photodb.get_iphoto_album_server_cgid_mapping()
                if server_id_by_iphoto_id:
                    TRACE('IPHOTOIMPORT: Got saved iPhoto album to server gid mapping! %d collections previously created on server!', len(server_id_by_iphoto_id))
                else:
                    TRACE('IPHOTOIMPORT: Creating %d collections on the server!', len(albums))
                    for album_batch in batch(albums_list, self.ALBUM_BATCH_SIZE):
                        try:
                            ret = self.app.conn.create_collections([ album.name for album in album_batch ])
                        except Exception as e:
                            unhandled_exc_handler()
                            if self.app.conn.is_transient_error(e):
                                raise PhotoImportNoConnectionError()
                            else:
                                raise PhotoImportAlbumCreationError()
                        else:
                            server_gids.extend(ret['collection_gids'])
                            self.check_cancel()

                    for album, server_gid in zip(albums_list, server_gids):
                        server_id_by_iphoto_id[album.uid] = server_gid

                    self.photodb.save_iphoto_album_server_cgid_mapping(server_id_by_iphoto_id)
                for iphoto_album_uid, server_gid in server_id_by_iphoto_id.iteritems():
                    albums[iphoto_album_uid].server_collection_gid = server_gid

                albums_list = [ album for album in albums.itervalues() if album.server_collection_gid is not None ]
                self.albums_by_photo = get_albums_by_photo_dict(albums_list)
            else:
                self.albums_by_photo = {}

    def get_import_space_usage(self, *args, **kwargs):
        import_space_usage = self.import_space_usage(*args, **kwargs)
        if self.check_space_callback:
            if import_space_usage != NOT_OUT_OF_SPACE:
                self.get_available_space(trace=True)
            self.check_space_callback(import_space_usage, len(self._files_to_read))
            self.check_cancel()
        return import_space_usage

    def _handle_existing_hashes(self, details, files, cur_index):
        other_path = None
        is_dup = False
        if details.cu_hash_full in self.cu_hashes_full:
            is_dup = True
            TRACE('Photo %r, cu_hash_full %r was already imported in this session!  Not importing', details.f_name, details.cu_hash_full)
        else:
            self._rotate_and_hash(details)
            other_path = self.app.sync_engine.find_blocklist_in_dir(details.blocklist, self.dest_path_sp)
            if other_path:
                other_path = self.app.sync_engine.server_to_local(other_path.server_path)
                is_dup = True
                TRACE('Photo %r, blocklist %r exists in the camera uploads folder at %s already!  Not importing', details.f_name, details.blocklist, other_path)
        if is_dup:
            self._handle_dup(details)
            if details.member_of_albums:
                TRACE('Duplicate photo was in iPhoto albums! Adding existing photo to albums')
                if details.cu_hash_full in self.cu_hashes_full:
                    for other_deets in reversed(files[:cur_index]):
                        if other_deets.cu_hash_full == other_deets.cu_hash_full and other_deets not in self.skipped_files:
                            TRACE('Found existing file in this import with same hash at %s', other_deets.path)
                            if other_deets.member_of_albums is None:
                                other_deets.member_of_albums = []
                            other_deets.member_of_albums.extend(details.member_of_albums)
                            if other_deets.path.dirname == self.dest_path and fsutil.is_exists(other_deets.path):
                                other_path = other_deets.path
                            break

                if other_path:
                    TRACE('Found existing file in folder with same blocklist: %s', other_path)
                    details.path = other_path
                    self._write_attrs(details)
        else:
            self.cu_hashes_full.add(details.cu_hash_full)
        return is_dup

    @handle_exceptions
    def run(self):
        if self.create_event_subdirs:
            try:
                self.event_dirname_by_id = self.photodb.get_iphoto_event_dirname_by_id()
                self.event_dirname_by_id = dict(((event_id, self.fs.make_path(dirname)) for event_id, dirname in self.event_dirname_by_id.iteritems()))
            except Exception:
                unhandled_exc_handler()
                self.event_dirname_by_id = {}

        super(PhotoGalleryImporter, self).run()
        if self.check_space_callback:
            if not self._files_to_read:
                self.check_space_callback(NOT_OUT_OF_SPACE, 0)
        else:
            self.photodb.clear_iphoto_album_server_cgid_mapping()

    def _end_photo_group(self, pending_files, curr_deets):
        if self.create_event_subdirs:
            return pending_files and (pending_files[0].photo_name != curr_deets.photo_name or pending_files[0].f_obj.event_id() != curr_deets.f_obj.event_id())
        else:
            return pending_files and pending_files[0].photo_name != curr_deets.photo_name

    def _verify_dest_path(self, file_deets_pairs, force = False):
        super(PhotoGalleryImporter, self)._verify_dest_path(force=force)
        if self.create_event_subdirs:
            deetslist = file_deets_pairs[0][1]
            event_id = deetslist[0].f_obj.event_id()
            dirs_created = []
            event_dir = self.event_dirname_by_id.get(event_id)
            if event_dir:
                TRACE('IPHOTOIMPORT: Found existing event folder %r', unicode(event_dir))
                if not fsutil.is_exists(self.fs, event_dir):
                    fsutil.makedirs(self.fs, event_dir, dirs_created)
            else:
                try:
                    event_dir = self.events[event_id].name
                except KeyError:
                    unhandled_exc_handler()
                    event_dir = trans(u'Untitled event')
                else:
                    TRACE('IPHOTOIMPORT: Creating folder for event %r', event_dir)
                    event_dir = normalize_event_name(event_dir)

                for suffix in itertools.count():
                    event_dirname = event_dir if suffix == 0 else '%s (%d)' % (event_dir, suffix)
                    event_dir_path = self.dest_path.join(event_dirname)
                    fsutil.makedirs(self.fs, event_dir_path, dirs_created)
                    if dirs_created:
                        break

                TRACE('IPHOTOIMPORT: Creating folder for event %r at path %r', event_id, unicode(event_dir_path))
                self.photodb.save_iphoto_event_dirname_by_id(event_id, unicode(event_dir_path))
                self.event_dirname_by_id[event_id] = event_dir_path

    def generate_path_from_deets(self, details, n):
        fn = u'%s%s%s' % (details.photo_name, u'-%d' % n if n else u'', details.f_ext.lower())
        if self.create_event_subdirs:
            dirpath = self.event_dirname_by_id[details.f_obj.event_id()]
        else:
            dirpath = self.dest_path
        return dirpath.join(fn)


STRIPPED_CHAR_PLACEHOLDER = '-'

def normalize_event_name(name):
    normalized_name = re.sub('[\\\\/:*?"<>|]+', STRIPPED_CHAR_PLACEHOLDER, name)
    normalized_name = re.sub('^\\.+', STRIPPED_CHAR_PLACEHOLDER, normalized_name)
    if not normalized_name or normalized_name != name and not normalized_name.strip(STRIPPED_CHAR_PLACEHOLDER):
        normalized_name = trans(u'Untitled event')
    return normalized_name
