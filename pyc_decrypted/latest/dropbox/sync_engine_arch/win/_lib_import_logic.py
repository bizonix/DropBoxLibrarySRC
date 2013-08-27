#Embedded file name: dropbox/sync_engine_arch/win/_lib_import_logic.py
from __future__ import with_statement
import copy
import errno
import os
import subprocess32 as subprocess
import sys
import time
from comtypes import IUnknown, COMMETHOD
from comtypes.client import CreateObject
from comtypes.GUID import GUID
from ctypes import byref, c_void_p, POINTER
from ctypes.wintypes import DWORD, HRESULT, LPWSTR, MAX_PATH
from win32com.shell import shellcon
from dropbox.debugging import easy_repr
from dropbox.fastwalk_bridge import fastwalk_strict
from dropbox.fileutils import safe_move
from dropbox.functions import convert_to_twos_complement, handle_exceptions
from dropbox.gui import message_sender, spawn_thread_with_name
from dropbox.sync_engine_file_system.constants import FILE_TYPE_REGULAR
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.win32.version import VISTA, WINDOWS_VERSION, WIN7, WINXP
from pynt.constants import E_FILE_NOT_FOUND, E_PATH_NOT_FOUND, ERROR_ACCESS_DENIED, ERROR_ALREADY_EXISTS, ERROR_SHARING_VIOLATION, FOLDERID_DocumentsLibrary, FOLDERID_PicturesLibrary, FOLDERID_VideosLibrary, FOLDERID_MusicLibrary, FOLDERID_Documents, FOLDERID_Music, FOLDERID_Pictures, FOLDERID_Videos, FOLDERID_PublicDocuments, FOLDERID_PublicPictures, FOLDERID_PublicVideos, FOLDERID_PublicMusic
from pynt.helpers.general import windows_error
from pynt.helpers.shell import shell_get_known_folder_path, shell_set_known_folder_path
from arch.win32.internal import get_user_folder_path
from arch.win32.util import is_junction_point, create_junction_point, paths_on_same_device, set_hidden, uses_com, get_drives
CONFIG_KEY_LIBRARIES_MOVED = 'libraries_moved'
CLSID_SHELL_LIBRARY = GUID('{d9b3211d-e57f-4426-aaef-30a806add397}')

class IShellItem(IUnknown):
    _iid_ = GUID('{43826d1e-e718-42ee-bc55-a1e261c37bfe}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None), (None,
      '',
      [],
      None,
      [],
      None), COMMETHOD([], HRESULT, 'GetDisplayName', (['in'], DWORD, 'sigdnName'), (['out'], POINTER(LPWSTR), 'ppszName'))]


class IShellItemArray(IUnknown):
    _iid_ = GUID('{b63ea76d-1f85-456f-a19c-48159efa858b}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'GetCount', (['out'], POINTER(DWORD), 'pdwNumItems')),
     COMMETHOD([], HRESULT, 'GetItemAt', (['in'], DWORD, 'dwIndex'), (['out'], POINTER(POINTER(IShellItem)), 'ppsi'))]


class IShellLibrary(IUnknown):
    _iid_ = GUID('{11a66efa-382e-451a-9234-1e0e12ef3085}')
    _idlflags_ = []
    _methods_ = [(None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'LoadLibraryFromKnownFolder', (['in'], POINTER(GUID), 'kfidLibrary'), (['in'], DWORD, 'grfMode')),
     COMMETHOD([], HRESULT, 'AddFolder', (['in'], POINTER(IShellItem), 'psiLocation')),
     COMMETHOD([], HRESULT, 'RemoveFolder', (['in'], POINTER(IShellItem), 'psiLocation')),
     COMMETHOD([], HRESULT, 'GetFolders', (['in'], DWORD, 'lff'), (['in'], POINTER(GUID), 'riid'), (['out'], POINTER(POINTER(IShellItemArray)), 'ppv')),
     (None,
      '',
      [],
      None,
      [],
      None),
     COMMETHOD([], HRESULT, 'GetDefaultSaveFolder', (['in'], DWORD, 'dsft'), (['in'], POINTER(GUID), 'riid'), (['out'], POINTER(POINTER(IShellItem)), 'ppv')),
     COMMETHOD([], HRESULT, 'SetDefaultSaveFolder', (['in'], DWORD, 'dsft'), (['in'], POINTER(c_void_p), 'psi'))]


LFF_ALLITEMS = 3
STGM_READWRITE = 2
DSFT_DETECT = 1
SIGDN_DESKTOPABSOLUTEPARSING = 2147647488L

class LibraryNames(object):
    Documents = 'documents'
    Pictures = 'pictures'
    Videos = 'videos'
    Music = 'music'
    Desktop = 'desktop'


class LibraryDef(object):
    __slots__ = ('lib_id', 'folder_id', 'public_folder_id', 'parent_folder')

    def __init__(self, lib_id, folder_id, public_folder_id, parent_folder = None):
        self.lib_id = lib_id
        self.folder_id = folder_id
        self.public_folder_id = public_folder_id
        self.parent_folder = parent_folder

    def __repr__(self):
        return easy_repr(self, *self.__slots__)


class LibraryInfo(object):
    __slots__ = ('name', 'display_name', 'size', 'num_files', 'has_other_dirs', 'error')

    def __init__(self, name, display_name, size, num_files, has_other_dirs):
        self.name = name
        self.display_name = display_name
        self.size = size
        self.num_files = num_files
        self.has_other_dirs = has_other_dirs
        self.error = None

    def __repr__(self):
        return easy_repr(self, *self.__slots__)


class ImportExceptionBase(Exception):
    pass


class ImportCanceledError(ImportExceptionBase):
    pass


class ImportTimedOutError(ImportExceptionBase):
    pass


class DropboxPathAlreadyExistsError(ImportExceptionBase):

    def __init__(self, path):
        self.path = path


class FileInUseError(ImportExceptionBase):
    pass


class ExceedsMaxPathError(Exception):
    pass


if WINDOWS_VERSION >= WIN7:
    LIBRARIES = {LibraryNames.Documents: LibraryDef(FOLDERID_DocumentsLibrary, FOLDERID_Documents, FOLDERID_PublicDocuments),
     LibraryNames.Pictures: LibraryDef(FOLDERID_PicturesLibrary, FOLDERID_Pictures, FOLDERID_PublicPictures),
     LibraryNames.Videos: LibraryDef(FOLDERID_VideosLibrary, FOLDERID_Videos, FOLDERID_PublicVideos),
     LibraryNames.Music: LibraryDef(FOLDERID_MusicLibrary, FOLDERID_Music, FOLDERID_PublicMusic)}
elif WINDOWS_VERSION == VISTA:
    LIBRARIES = {LibraryNames.Documents: LibraryDef(None, shellcon.CSIDL_PERSONAL, None),
     LibraryNames.Music: LibraryDef(None, shellcon.CSIDL_MYMUSIC, None),
     LibraryNames.Pictures: LibraryDef(None, shellcon.CSIDL_MYPICTURES, None)}
elif WINDOWS_VERSION == WINXP:
    LIBRARIES = {LibraryNames.Documents: LibraryDef(None, shellcon.CSIDL_PERSONAL, None),
     LibraryNames.Music: LibraryDef(None, shellcon.CSIDL_MYMUSIC, None, LibraryNames.Documents),
     LibraryNames.Pictures: LibraryDef(None, shellcon.CSIDL_MYPICTURES, None, LibraryNames.Documents)}
IMPORT_ALLOWED = 0
IMPORT_ALREADY_IMPORTED = 1
IMPORT_CONTAINS_DROPBOX = 2
IMPORT_NOT_ON_DROPBOX_DRIVE = 3
IMPORT_CONFLICT_IN_DROPBOX = 4
IMPORT_FAT32 = 5
IMPORT_NOT_ENOUGH_SPACE = 6
IMPORT_LIB_HAS_OTHER_DIRS = 7
IMPORT_EXCEPTION = 8

class LibraryImporter(object):

    def __init__(self, dropbox_app):
        self._app = dropbox_app
        self._library_dirs = None
        self._moved_dirs = {}
        self._moved_paths = {}
        self._max_path_length = 0
        self._longest_path = ''
        self._total_size = 0
        self._info = None
        self._error = None
        self._lib_errors = None
        self._timeout = None
        self._cancel = False
        self._start_time = None
        self._interrupted_scan_size = 0
        self._interrupted_num_files = 0

    def cancel(self):
        self._cancel = True

    def _check_cancel(self):
        if self._cancel:
            raise ImportCanceledError()

    def _check_timeout(self):
        if self._timeout and time.time() > self._timeout:
            raise ImportTimedOutError()

    def _log(self, events):
        self._app.event.report('win_library_importer', events)

    def _log_failure(self, reasons):
        self._app.event.report('win_library_importer_fail', reasons)

    def check_import_supported(self, dropbox_path, which_libs, create_symlink_on_import = False):
        if self._library_dirs is None:
            raise Exception('Must call gather_library_stats first')
        try:
            for lib_name in which_libs:
                if lib_name not in self._library_dirs:
                    TRACE('!! IMPORT: Trying to import a library %s that was not scanned', lib_name)
                    report_bad_assumption('Trying to import a library %s that was not scanned', lib_name)
                    return IMPORT_EXCEPTION
                default_save_dir, _ = self._library_dirs[lib_name]
                if os.path.commonprefix([default_save_dir, dropbox_path]) == dropbox_path:
                    return IMPORT_ALREADY_IMPORTED
                if os.path.commonprefix([default_save_dir, dropbox_path]) == default_save_dir:
                    self._log_failure({'dropbox_in_%s_library' % lib_name: True})
                    return IMPORT_CONTAINS_DROPBOX
                if not paths_on_same_device(default_save_dir, dropbox_path):
                    db_drive, _ = os.path.splitdrive(dropbox_path)
                    lib_drive, _ = os.path.splitdrive(default_save_dir)
                    self._log_failure({'%s_default_drive' % lib_name: lib_drive,
                     'dropbox_drive': db_drive})
                    return IMPORT_NOT_ON_DROPBOX_DRIVE
                long_name = os.path.join(dropbox_path, self._longest_path)
                if len(long_name) > MAX_PATH:
                    self._log_failure({'max_path_exceeded': len(long_name)})
                    raise ExceedsMaxPathError('Filename will exceed MAX_PATH')
                if create_symlink_on_import:
                    for _, drive_info, _, _ in get_drives():
                        if drive_info and drive_info[4] == 'FAT32':
                            return IMPORT_FAT32

                if lib_name in self._info and self._info[lib_name].has_other_dirs:
                    return IMPORT_LIB_HAS_OTHER_DIRS
                new_path = os.path.join(dropbox_path, os.path.basename(default_save_dir))
                if os.path.exists(new_path):
                    return IMPORT_CONFLICT_IN_DROPBOX

            if self._app.quota < self._app.in_use + max(self._total_size, self._interrupted_scan_size):
                return IMPORT_NOT_ENOUGH_SPACE
        except Exception:
            unhandled_exc_handler()
            return IMPORT_EXCEPTION

        return IMPORT_ALLOWED

    @message_sender(spawn_thread_with_name('IMPORTSCANHELPER'))
    @uses_com
    def background_scan_libraries(self, dropbox_path, which_libs, on_completion, timeout = None):
        self._start_time = time.time()
        if timeout is not None:
            self._timeout = self._start_time + timeout
        try:
            if WINDOWS_VERSION >= WIN7:
                self._gather_library_stats(dropbox_path, which_libs)
            else:
                self._gather_folder_stats(dropbox_path, which_libs)
            self._timeout = None
            if on_completion:
                on_completion(self._error)
        except Exception:
            unhandled_exc_handler()
            self._library_dirs = {}

    def _gather_folder_stats(self, dropbox_path, which_libs):
        dirs = {}
        for dir_name in which_libs:
            try:
                parent_folder = LIBRARIES[dir_name].parent_folder
                dir_path = os.path.normpath(shell_get_known_folder_path(LIBRARIES[dir_name].folder_id))
                parent_id = LIBRARIES[parent_folder].folder_id if parent_folder else shellcon.CSIDL_PROFILE
                expected_parent_path = os.path.normpath(shell_get_known_folder_path(parent_id))
                expected_dir_path = os.path.normpath(os.path.join(expected_parent_path, os.path.basename(dir_path)))
                if expected_dir_path == dir_path:
                    dirs[dir_name] = (dir_path, False)
                else:
                    self._log_failure({'nondefault_%s_dir' % dir_name: True})
            except Exception:
                unhandled_exc_handler()

        self._scan_libraries(dirs)
        self._library_dirs = dirs

    def _gather_library_stats(self, dropbox_path, which_libs):
        expected_user_path = get_user_folder_path(shellcon.CSIDL_PROFILE)
        if not expected_user_path:
            self._log_failure({'no_user_path': True})
            return
        library_dirs = {}
        library = CreateObject(CLSID_SHELL_LIBRARY, interface=IShellLibrary)
        for lib_name in which_libs:
            lib = LIBRARIES[lib_name]
            try:
                default_save_dir = None
                if lib.lib_id:
                    library.LoadLibraryFromKnownFolder(byref(lib.lib_id), STGM_READWRITE)
                    dir_item = library.GetDefaultSaveFolder(DSFT_DETECT, byref(IShellItem._iid_))
                    default_save_dir = os.path.normpath(dir_item.GetDisplayName(SIGDN_DESKTOPABSOLUTEPARSING))
                    if os.path.commonprefix([default_save_dir, dropbox_path]) == dropbox_path:
                        continue
                    if os.path.join(expected_user_path, os.path.basename(default_save_dir)) != default_save_dir:
                        self._log_failure({'nondefault_%s_dir' % lib_name: True})
                        continue
                private_lib_dir = shell_get_known_folder_path(lib.folder_id)
                if not default_save_dir:
                    default_save_dir = private_lib_dir
                elif default_save_dir.lower() != private_lib_dir.lower():
                    self._log_failure({'bad_%s_known_folder' % lib_name: True})
                    continue
                has_other_dirs = False
                if lib.lib_id:
                    dirs = library.GetFolders(LFF_ALLITEMS, byref(IShellItemArray._iid_))
                    if dirs.GetCount() > 2:
                        has_other_dirs = True
                library_dirs[lib_name] = (default_save_dir, has_other_dirs)
            except Exception:
                unhandled_exc_handler()

        self._scan_libraries(library_dirs)
        self._library_dirs = library_dirs

    def _scan_libraries(self, library_dirs):
        TRACE('IMPORT: Scanning %s', library_dirs.keys())
        try:
            if library_dirs:
                total_size = 0
                num_files = 0
                info = {}
                errors = {}
                for lib_name, (path, has_other_dirs) in library_dirs.iteritems():
                    try:
                        if lib_name in LIBRARIES and LIBRARIES[lib_name].parent_folder:
                            continue
                        display_name = os.path.basename(path)
                        size, num_files = self._get_size_find_longest_path(path)
                        total_size += size
                        info[lib_name] = LibraryInfo(lib_name, display_name, size, num_files, has_other_dirs)
                        self._log({'%s-library-size' % lib_name: size})
                    except Exception as e:
                        unhandled_exc_handler()
                        errors[lib_name] = e

                self._log({'total-library-size': total_size})
                self._total_size = total_size
                self._info = info
                self._lib_errors = errors
        except Exception as e:
            unhandled_exc_handler()
            self._error = e
            if self._interrupted_scan_size > 0:
                self._log({'%s-partial-library-size' % lib_name: self._interrupted_scan_size})

    def get_library_info(self):
        return (max(self._total_size, self._interrupted_scan_size), self._info, self._lib_errors)

    def _get_size_find_longest_path(self, path):
        try:
            total_size = 0
            num_files = 0
            walker = fastwalk_strict(path, on_explore_error=_on_error, no_atime=True)
            user_dir_len = len(path) - len(os.path.basename(path))
            for dirpath, ents in walker:
                self._check_cancel()
                self._check_timeout()
                for dirent in ents:
                    srcfilepath = dirent.fullpath
                    length = len(srcfilepath) - user_dir_len
                    if length > self._max_path_length:
                        self._max_path_length = length
                        self._longest_path = srcfilepath[user_dir_len:]
                    total_size += dirent.size
                    if dirent.type == 'regular':
                        num_files += 1

            return (total_size, num_files)
        finally:
            self._interrupted_scan_size = total_size
            self._interrupted_num_files = num_files

    @message_sender(spawn_thread_with_name('IMPORTMOVEHELPER'))
    @uses_com
    def move_libraries(self, dropbox_path, which_libs, on_completion, create_symlink = False):
        error = None
        new_path = ''
        TRACE('IMPORT: Attempting to move the following libraries %r', which_libs)
        try:
            if WINDOWS_VERSION == WINXP:
                for lib_name in self._library_dirs:
                    if LIBRARIES[lib_name].parent_folder in which_libs:
                        which_libs.append(lib_name)

            for lib_name in which_libs:
                self._check_cancel()
                path, _ = self._library_dirs[lib_name]
                folder_id = LIBRARIES[lib_name].folder_id
                parent_folder = LIBRARIES[lib_name].parent_folder
                did_move = False
                if parent_folder and parent_folder in which_libs:
                    parent_path = shell_get_known_folder_path(LIBRARIES[parent_folder].folder_id)
                    new_path = os.path.join(parent_path, os.path.basename(path))
                else:
                    new_path = os.path.join(dropbox_path, os.path.basename(path))
                    safe_move(path, new_path)
                    did_move = True
                self._moved_dirs[lib_name] = [new_path, path]
                shell_set_known_folder_path(folder_id, new_path)
                self._moved_paths[lib_name] = [new_path, path, parent_folder]
                if did_move and create_symlink:
                    create_hidden_symlink(path, new_path)

        except Exception as e:
            error = e
            if isinstance(e, WindowsError) and e.winerror in (ERROR_ACCESS_DENIED, ERROR_SHARING_VIOLATION):
                unhandled_exc_handler(False)
                error = FileInUseError()
                self._log_failure({'file_in_use': True})
            else:
                unhandled_exc_handler()
                self._log_failure({'unknown_move_error': True})
            if isinstance(e, WindowsError) and e.winerror == ERROR_ALREADY_EXISTS:
                error = DropboxPathAlreadyExistsError(new_path)
            if self._moved_dirs or self._moved_paths:
                _rollback_internal(self._moved_dirs, self._moved_paths)

        if not error:
            old_libs = self._app.config.get(CONFIG_KEY_LIBRARIES_MOVED, None)
            libs_moved = old_libs.update(self._moved_dirs) if old_libs else self._moved_dirs
            self._app.config[CONFIG_KEY_LIBRARIES_MOVED] = libs_moved
        self._log({'import_successful': error is None})
        on_completion(error, self._moved_dirs)


@handle_exceptions
def redirect_libraries_to(config, new_dropbox_path):
    libraries_moved = config.get(CONFIG_KEY_LIBRARIES_MOVED, None)
    if not libraries_moved:
        return
    TRACE('IMPORT: Redirecting known folder libraries for move_dropbox for the following libraries: %r', libraries_moved.keys())
    for lib_name, (cur_path, old_path) in first_item_itr(libraries_moved, LibraryNames.Documents):
        try:
            parent_folder = LIBRARIES[lib_name].parent_folder
            parent_path = libraries_moved[parent_folder][0] if parent_folder else new_dropbox_path
            new_path = os.path.join(parent_path, os.path.basename(cur_path))
            success = _set_known_folder_path(lib_name, cur_path, new_path)
            if not success:
                return
            libraries_moved[lib_name] = [new_path, old_path]
            if os.path.exists(old_path) and not parent_folder:
                if is_junction_point(old_path):
                    ret = subprocess.call('rmdir "%s"' % old_path.encode('mbcs'), shell=True)
                    if ret != 0:
                        raise windows_error(ret)
                    create_hidden_symlink(old_path, new_path)
                else:
                    TRACE('!! IMPORT: Old path %r exists but is not a junction point!', old_path)
                    report_bad_assumption('Old path exists but is not a junction point!')
        except Exception:
            unhandled_exc_handler()

    config[CONFIG_KEY_LIBRARIES_MOVED] = libraries_moved


def _set_known_folder_path(lib_name, cur_path, new_path):
    try:
        known_path = shell_get_known_folder_path(LIBRARIES[lib_name].folder_id)
        if known_path != cur_path:
            TRACE('!! IMPORT: Known folder path for %s is different from what we set it to (%r)', lib_name, cur_path)
            report_bad_assumption('!! IMPORT: Known folder path for imported library has been changed!')
            return False
    except Exception as e:
        if isinstance(e, WindowsError) and convert_to_twos_complement(e.winerror) in (E_FILE_NOT_FOUND, E_PATH_NOT_FOUND):
            TRACE('IMPORT: Known folder points to missing path, this is expected because we just moved it')
        else:
            unhandled_exc_handler()

    TRACE('IMPORT: Resetting known folder path: Changing target to %r', new_path)
    shell_set_known_folder_path(LIBRARIES[lib_name].folder_id, new_path)
    return True


def rollback(moved_dirs):
    if not moved_dirs:
        return True
    return _rollback_internal(moved_dirs, moved_paths=copy.copy(moved_dirs))


def first_item_itr(dict_, first_item):
    if first_item in dict_:
        yield (first_item, dict_[first_item])
    for item in dict_.items():
        if item[0] is not first_item:
            yield item


def _rollback_internal(moved_dirs, moved_paths, db_path = None):
    if not (moved_dirs or moved_paths):
        return True
    for lib_name, (src, dst) in first_item_itr(moved_dirs, LibraryNames.Documents):
        try:
            TRACE('Rollback: Moving %r back', src)
            if os.path.exists(dst):
                if is_junction_point(dst):
                    TRACE('Rollback: Removing junction point at target')
                    try:
                        ret = subprocess.call('rmdir "%s"' % dst.encode('mbcs'), shell=True)
                        if ret != 0:
                            raise windows_error(ret)
                    except Exception:
                        unhandled_exc_handler()

                elif not LIBRARIES[lib_name].parent_folder:
                    TRACE('!! Rollback: Old path exists but is not a junction point!')
                    report_bad_assumption('Old path exists but is not a junction point!')
            if not LIBRARIES[lib_name].parent_folder:
                safe_move(src, dst)
            del moved_dirs[lib_name]
            if (lib_name, [src, dst]) in moved_paths.items():
                success = _set_known_folder_path(lib_name, src, dst)
                if success:
                    del moved_paths[lib_name]
        except Exception:
            unhandled_exc_handler()

    if db_path:
        try:
            TRACE('Rollback: Removing dropbox folder at %r', db_path)
            os.rmdir(db_path)
        except Exception:
            unhandled_exc_handler()

    if moved_dirs or moved_paths:
        return False
    return True


def _on_error(path):
    a, exc_value, c = sys.exc_info()
    if not (isinstance(exc_value, OSError) and exc_value.errno in (errno.EPERM, errno.ENOENT)):
        TRACE("!! Couldn't explore a path!")


def _get_files_size(dirpath):
    size = 0
    walker = fastwalk_strict(dirpath, on_explore_error=_on_error, no_atime=True)
    for dirpath, ents in walker:
        for dirent in ents:
            if dirent.type == FILE_TYPE_REGULAR:
                size += dirent.size

    return size


def create_hidden_symlink(source, target):
    if WINDOWS_VERSION >= VISTA:
        ret = subprocess.call('mklink /J "%s" "%s"' % (source.encode('mbcs'), target.encode('mbcs')), shell=True)
        if ret != 0:
            raise windows_error(ret)
    else:
        os.mkdir(source)
        create_junction_point(source, target)
    set_hidden(source)
