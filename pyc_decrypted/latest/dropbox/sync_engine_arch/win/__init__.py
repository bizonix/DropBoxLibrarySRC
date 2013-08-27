#Embedded file name: dropbox/sync_engine_arch/win/__init__.py
from __future__ import with_statement, absolute_import
import win32file
import arch as global_arch
from pynt.helpers.registry import HKEY_LOCAL_MACHINE as HKLM, KEY_READ, KEY_WOW64_64KEY, registry_key, read_registry_value
from arch.win32.constants import default_dropbox_folder_name, appdata_path
from dropbox.i18n import trans
from dropbox.nfcdetector import is_nfc
from dropbox.sync_engine_file_system.constants import IGNORE_CONTAINS_DOUBLE_BACKSLASH_CODE, IGNORE_ENDS_BACKSLASH_CODE, IGNORE_INVALID_NFC_CODE
from dropbox.sync_engine_arch.path import sanitize_filename
from dropbox.win32_util import find_media_type
from dropbox import fsutil
from dropbox.trace import report_bad_assumption, unhandled_exc_handler, TRACE
from ._file_system import WindowsFileSystem as FileSystem
from ._folder_tagger import FolderTagger
from ._fschange import shell_touch, shell_touch_tree, get_installpath
from ._path import check_filename_localpath, INVALID_FILENAME_CHARS_RE
from ._stuff_importer import StuffImporter
from ._lib_import_logic import rollback as _rollback, redirect_libraries_to as _redirect_libraries_to

class Arch(object):

    class JournalReindexer(object):

        def __init__(self, *n, **kw):
            pass

        def can_journal(self, *n, **kw):
            return False

        def start_reindex(self, *n, **kw):
            pass

        def reset(self, *n, **kw):
            pass

    class JournalFailure(Exception):
        pass

    StuffImporter = StuffImporter
    DEFAULT_DROPBOX_FOLDER_NAME = default_dropbox_folder_name

    def __init__(self):
        self.file_system = FileSystem()
        self.make_path = self.file_system.make_path
        self.check_filename = check_filename_localpath
        self.shell_touch = shell_touch
        self.folder_tagger = FolderTagger(get_installpath(self.make_path), self.file_system)
        self.hash_wait_time = 0
        self.APPDATA_PATH = self.make_path(appdata_path)
        self.sanitize_filename = sanitize_filename(INVALID_FILENAME_CHARS_RE)

    def hide_folder(self, path):
        return fsutil.hide_file(self.file_system, path)

    def clear_shell_state(self, dropbox_path, timeout = 2):
        shell_touch_tree(unicode(dropbox_path), timeout=timeout)

    def should_ignore(self, lp):
        u_local_path = unicode(lp)
        if u_local_path[-1] == u'\\':
            return IGNORE_ENDS_BACKSLASH_CODE
        if u_local_path.rfind(u'\\\\') > 0:
            return IGNORE_CONTAINS_DOUBLE_BACKSLASH_CODE
        if not is_nfc(u_local_path):
            report_bad_assumption('Non-NFC normalized path on windows!: %r' % (u_local_path,))
            return IGNORE_INVALID_NFC_CODE

    def path_makes_invalid_dropbox_parent(self, path):

        def is_in_program_files():
            path_to_check = path.join(self.DEFAULT_DROPBOX_FOLDER_NAME)
            try:
                with registry_key(HKLM, u'SOFTWARE\\Microsoft\\Windows\\CurrentVersion', KEY_READ) as hkey:
                    prog_files = self.make_path(read_registry_value(hkey, u'ProgramFilesDir'))
                with registry_key(HKLM, u'SOFTWARE\\Microsoft\\Windows\\CurrentVersion', KEY_READ | KEY_WOW64_64KEY) as hkey:
                    prog_files_64 = self.make_path(read_registry_value(hkey, u'ProgramFilesDir'))
                TRACE('Program files: %r', prog_files)
                TRACE('Program files 64: %r', prog_files_64)
                if any((p.is_parent_of(path_to_check) for p in [prog_files, prog_files_64])):
                    return True
            except Exception:
                unhandled_exc_handler()

            return False

        if is_in_program_files():
            return trans(u'This folder is in the Program Files folder.')
        upath = unicode(path)
        type_, typepath = find_media_type(upath)
        if type_ is None:
            return trans(u'This folder is on an unknown media type.')
        elif type_ == win32file.DRIVE_FIXED:
            if upath == typepath:
                return False
            attr = win32file.GetFileAttributesW(upath)
            if not attr & win32file.FILE_ATTRIBUTE_DIRECTORY:
                return trans(u'This is not a folder.')
            if attr & win32file.FILE_ATTRIBUTE_SYSTEM:
                return trans(u'This is a system folder.')
            if attr & win32file.FILE_ATTRIBUTE_OFFLINE:
                return trans(u'This folder is offline.')
            if attr & win32file.FILE_ATTRIBUTE_TEMPORARY:
                return trans(u'This folder is used for temporary files.')
            return False
        elif type_ == win32file.DRIVE_REMOVABLE:
            return trans(u'This folder is on removable media.')
        elif type_ == win32file.DRIVE_REMOTE:
            return trans(u'This folder is on network media.')
        elif type_ == win32file.DRIVE_CDROM:
            return trans(u'This folder is on an optical media (CD/DVD) drive.')
        elif type_ == win32file.DRIVE_RAMDISK:
            return trans(u'This folder is on a RAM disk.')
        else:
            return trans(u'This folder is on an unknown media type.')

    def rollback(self, moved_dirs):
        _rollback(moved_dirs)

    def redirect_libraries_to(self, config, new_dropbox_path):
        _redirect_libraries_to(config, new_dropbox_path)

    def is_shortcut_file(self, path, cache_path = None, file_attrs = None):
        return global_arch.win32.util.is_shortcut_file(path, cache_path, file_attrs)
