#Embedded file name: dropbox/sync_engine_arch/macosx/__init__.py
from __future__ import with_statement
from __future__ import absolute_import
import re
import arch as global_arch
from arch.mac.constants import default_dropbox_folder_name, appdata_path
from dropbox.db_thread import db_thread
from dropbox.fsutil import is_regular
from dropbox.functions import RECONSTRUCT_TEMP_FILE_PREFIX
from dropbox.mac.internal import binaries_ready, BINARIES_READY_TIMEOUT, find_finder_pid, get_icons_folder
from dropbox.nfcdetector import is_nfd
from dropbox.sync_engine.exceptions import UnreconstructableError
from dropbox.sync_engine_arch.path import sanitize_filename_unix
from dropbox.sync_engine_file_system.constants import IGNORE_CONTAINS_BACKSLASH_CODE, IGNORE_INVALID_NFD_CODE, IGNORE_UNWATCHED_CODE, IGNORE_ALIAS_FILE_CODE
from dropbox.trace import TRACE, unhandled_exc_handler
from ..posix_invalid_parent import posix_path_makes_invalid_dropbox_parent
from ._file_system import MacOSXFileSystem as FileSystem
from ._folder_tagger import FolderTagger
from ._fschange import FsChangeThread
from ._journal_reindex import JournalReindexer, JournalFailure
from ._stuff_importer import StuffImporter
_INVALID_UNIX_PATH_RE = re.compile(u'/(\\.|\\.\\.)(/|$)')

class Arch(object):
    DEFAULT_DROPBOX_FOLDER_NAME = default_dropbox_folder_name
    JournalReindexer = JournalReindexer
    JournalFailure = JournalFailure
    StuffImporter = StuffImporter

    def __init__(self):
        self.file_system = FileSystem()
        self.make_path = self.file_system.make_path
        self.last_finder_pid = None
        self.finder_bundle_version = ()
        self.fschange = None
        self.folder_tagger = FolderTagger(self.make_path(get_icons_folder()), self.file_system)
        self.hash_wait_time = 0
        self.APPDATA_PATH = self.make_path(appdata_path)
        self.sanitize_filename = sanitize_filename_unix()

    def enable_fs_change_notifications(self, dropbox_app):
        if not self.fschange:
            try:
                TRACE('Waiting for binaries to check out')
                ret = binaries_ready.wait(timeout=BINARIES_READY_TIMEOUT)
                if ret is None:
                    TRACE('Timeout waiting for user authorization. Going ahead anyway.')
                TRACE('Ok, good to go')
                self.fschange = db_thread(FsChangeThread)(dropbox_app, self.file_system)
            except Exception:
                unhandled_exc_handler()
            else:
                self.fschange.start()

    def request_finder_bundle_version(self):
        if self.fschange:
            self.fschange.request_finder_bundle_version()

    def set_finder_bundle_version(self, version):
        try:
            if version:
                self.finder_bundle_version = tuple((int(x) for x in version.split(u'.')))
            else:
                self.finder_bundle_version = ()
        except Exception:
            unhandled_exc_handler()
            self.finder_bundle_version = ()

    def shell_touch(self, *n, **kw):
        if self.fschange:
            return self.fschange.shell_touch(*n, **kw)

    def clear_shell_state(self, *n, **kw):
        if self.fschange:
            return self.fschange.clear_shell_state(*n, **kw)

    def should_ignore(self, lp):
        u_local_path = unicode(lp)
        if u_local_path.endswith(u'/..namedfork/rsrc') and is_regular(self.file_system, lp.dirname.dirname):
            return IGNORE_UNWATCHED_CODE
        if unicode(lp.basename).startswith(RECONSTRUCT_TEMP_FILE_PREFIX):
            return IGNORE_UNWATCHED_CODE
        if u_local_path.find(u'\\') >= 0:
            return IGNORE_CONTAINS_BACKSLASH_CODE
        if not is_nfd(u_local_path):
            return IGNORE_INVALID_NFD_CODE
        if self.is_shortcut_file(u_local_path):
            return IGNORE_ALIAS_FILE_CODE

    def check_filename(self, lp, is_delete, is_dir):
        lpu = unicode(lp)
        if _INVALID_UNIX_PATH_RE.search(lpu) is not None:
            raise UnreconstructableError('path contained invalid filename: %r' % (lpu,))
        return True

    def hide_folder(self, lp):
        if lp.basename[0] != u'.':
            raise Exception("Can't hide folder!")

    def init_shell_touch(self):
        new_finder_pid = find_finder_pid()
        if self.last_finder_pid is not None and self.last_finder_pid != new_finder_pid:
            TRACE('queueing finder shell touch')
            self.clear_shell_state()
        self.last_finder_pid = new_finder_pid

    def path_makes_invalid_dropbox_parent(self, path):
        return posix_path_makes_invalid_dropbox_parent(self.file_system, path)

    def rollback(*args, **kwargs):
        pass

    def redirect_libraries_to(*args, **kwargs):
        pass

    def is_shortcut_file(self, path, cache_path = None, file_attrs = None):
        return global_arch.mac.util.is_shortcut_file(path, cache_path, file_attrs)
