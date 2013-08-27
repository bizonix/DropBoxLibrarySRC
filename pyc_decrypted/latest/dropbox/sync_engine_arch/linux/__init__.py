#Embedded file name: dropbox/sync_engine_arch/linux/__init__.py
from __future__ import with_statement, absolute_import
import re
import sys
from dropbox.nfcdetector import is_nfc
from arch.linux.constants import default_dropbox_folder_name, appdata_path
from dropbox.fsutil import shell_touch_tree
from dropbox.sync_engine.exceptions import UnreconstructableError
from dropbox.sync_engine_arch.path import sanitize_filename_unix
from dropbox.sync_engine_file_system.constants import IGNORE_INVALID_NFC_CODE, IGNORE_CONTAINS_BACKSLASH_CODE
from ..posix_invalid_parent import posix_path_makes_invalid_dropbox_parent
from ._file_system import LinuxFileSystem as FileSystem
from ._folder_tagger import LinuxFolderTagger
_INVALID_UNIX_PATH_RE = re.compile(u'/(\\.|\\.\\.)(/|$)')

class Arch(object):
    DEFAULT_DROPBOX_FOLDER_NAME = default_dropbox_folder_name
    APPDATA_PATH = None

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

    class StuffImporter(object):

        def __init__(self, *n, **kw):
            pass

        @staticmethod
        def show_import_button(app):
            return (False, False)

    def __init__(self, linux_control_thread):
        self.file_system = FileSystem()
        self.make_path = self.file_system.make_path
        self.folder_tagger = LinuxFolderTagger(self.file_system, self.shell_touch)
        self.hash_wait_time = 0
        self.ct = linux_control_thread
        self.APPDATA_PATH = self.make_path(appdata_path)
        self.sanitize_filename = sanitize_filename_unix()

    def should_ignore(self, u):
        u = unicode(u)
        if not is_nfc(u):
            return IGNORE_INVALID_NFC_CODE
        if u.find(u'\\') >= 0:
            return IGNORE_CONTAINS_BACKSLASH_CODE

    def check_filename(self, lp, is_delete, is_dir):
        lpu = unicode(lp)
        if _INVALID_UNIX_PATH_RE.search(lpu) is not None:
            raise UnreconstructableError('path contained invalid filename: %r' % (lpu,))
        unicode(lp).encode(sys.getfilesystemencoding())
        return True

    def hide_folder(self, lp):
        if lp.basename[0] != u'.':
            raise Exception("Can't hide folder!")

    def shell_touch(self, lp):
        self.ct.shell_touch(path=unicode(lp))

    def clear_shell_state(self, folder, timeout = 2):
        shell_touch_tree(self.file_system, self.shell_touch, folder, timeout=timeout)

    def path_makes_invalid_dropbox_parent(self, path):
        return posix_path_makes_invalid_dropbox_parent(self.file_system, path)

    def rollback(*args, **kwargs):
        pass

    def redirect_libraries_to(*args, **kwargs):
        pass

    def is_shortcut_file(*args, **kwargs):
        return False
