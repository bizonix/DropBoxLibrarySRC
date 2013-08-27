#Embedded file name: dropbox/sync_engine/sync_memory_caches.py
from __future__ import with_statement
import re
import sys
import threading
import time
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.server_path import NsRelativePathMemory, NsRelativePathFast
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError
from dropbox.languages import NEW_TEXT_DOCUMENT_NAMES, NEW_FOLDER_NAMES
_is_win = sys.platform.startswith('win')
NEW_FILE_RE = re.compile(u'^(%s)( \\(\\d+\\))?\\.txt$' % '|'.join([ re.escape(name) for name in NEW_TEXT_DOCUMENT_NAMES ]))
NEW_FOLDER_RE = re.compile(u'^(%s)( \\(\\d+\\))?$' % '|'.join([ re.escape(name) for name in NEW_FOLDER_NAMES ]))

class PathCache(object):

    def shouldnt_touch(self, local_path):
        if not _is_win:
            return False
        fn = local_path.basename
        if NEW_FOLDER_RE.match(fn) or NEW_FILE_RE.match(fn):
            try:
                if time.time() - self.fs.indexing_attributes(local_path).mtime < 60:
                    return True
            except FileNotFoundError:
                pass
            except Exception:
                unhandled_exc_handler()

        return False

    def __init__(self, arch, server_local_mapper = None):
        self.fs = arch.file_system
        self.pending_count = {}
        self.lock = threading.Lock()
        self.shell_touch = arch.shell_touch
        self.set_server_local_mapper(server_local_mapper)

    def clear(self):
        with self.lock:
            self.pending_count = {}

    def __nonzero__(self):
        return bool(self.pending_count)

    def set_server_local_mapper(self, slm):
        self.slm = slm

    def mark_changed(self, root_relative = None, lower = True, local_path = None):
        if self.slm is None:
            raise Exception('Must set server local mapper before calling this!')
        no_touch = False
        with self.lock:
            if not local_path:
                local_path = self.slm.convert_root_relative(root_relative)
            else:
                root_relative = self.slm.convert_local(local_path, ctor=NsRelativePathMemory)
            root_was_syncing = bool(self.pending_count)
            curpath = root_relative.lower() if lower else root_relative
            while not curpath.is_root:
                count = self.pending_count.get(curpath, 0) + 1
                if count == 1:
                    if self.shouldnt_touch(local_path) or no_touch:
                        no_touch = True
                    else:
                        try:
                            self.shell_touch(local_path)
                        except Exception:
                            unhandled_exc_handler()

                self.pending_count[curpath] = count
                curpath = curpath.dirname
                local_path = local_path.dirname

            if not self.shouldnt_touch(local_path) and not no_touch and root_was_syncing != bool(self.pending_count):
                try:
                    self.shell_touch(local_path)
                except Exception:
                    unhandled_exc_handler()

    def mark_active(self, root_relative = None, lower = True, local_path = None):
        if self.slm is None:
            raise Exception('Must set server local mapper before calling this!')
        no_touch = False
        with self.lock:
            if not local_path:
                local_path = self.slm.convert_root_relative(root_relative)
            else:
                root_relative = self.slm.convert_local(local_path, ctor=NsRelativePathMemory)
            assert root_relative is not None, 'Must pass in root_relative!'
            assert local_path is not None, 'Must pass in local_path'
            root_was_syncing = bool(self.pending_count)
            curpath = root_relative.lower() if lower else root_relative
            while not curpath.is_root:
                current_count = self.pending_count.get(curpath, 0)
                if current_count <= 1:
                    try:
                        del self.pending_count[curpath]
                    except KeyError:
                        report_bad_assumption("Pending count didn't exist for %r, something is inconsistent" % curpath)

                    if self.shouldnt_touch(local_path) or no_touch:
                        no_touch = True
                    else:
                        try:
                            self.shell_touch(local_path)
                        except Exception:
                            unhandled_exc_handler()

                else:
                    self.pending_count[curpath] = current_count - 1
                curpath = curpath.dirname
                local_path = local_path.dirname

            if not self.shouldnt_touch(local_path) and not no_touch and root_was_syncing != bool(self.pending_count):
                try:
                    self.shell_touch(local_path)
                except Exception:
                    unhandled_exc_handler()

    def mark_error(self, is_failing, root_relative = None, lower = True, local_path = None):
        pass

    def is_changed(self, root_relative = None, lower = True, local_path = None):
        with self.lock:
            if local_path:
                root_relative = self.slm.convert_local(local_path, ctor=NsRelativePathFast)
            if root_relative.is_root and self.pending_count:
                return True
            return self.pending_count.get(root_relative.lower() if lower else root_relative)


class WriteIgnoreMap(object):
    ENTRY_LIFETIME = 300

    def __init__(self):
        self.d = {}
        self.lock = threading.Lock()

    def remove(self, fn, lower = True):
        with self.lock:
            try:
                del self.d[fn.lower() if lower else fn]
            except KeyError:
                pass

    def ignore(self, fn, mtime, size, is_dir, ctime = None, machine_guid = None):
        with self.lock:
            TRACE('Ignoring %r->%r,%r,%r,%r,%r' % (fn,
             mtime,
             size,
             is_dir,
             ctime,
             machine_guid))
            self.d[fn.lower()] = (mtime,
             size,
             False if size < 0 else is_dir,
             time.time(),
             ctime,
             machine_guid)

    def prune_old_entries(self):
        with self.lock:
            count = 0
            for key, val in self.d.items():
                if time.time() - val[3] > WriteIgnoreMap.ENTRY_LIFETIME:
                    count += 1
                    del self.d[key]

            if count > 0:
                TRACE('Pruned %d writes-to-ignore entries' % count)

    def should_ignore(self, fn, mtime, size, is_dir, ctime = None, machine_guid = None):
        with self.lock:
            key = fn.lower()
            try:
                ignored_mtime, ignored_size, ignored_is_dir, ignored_time, ignored_ctime, ignored_machine_guid = self.d[key]
            except KeyError:
                return False

            if time.time() - ignored_time > WriteIgnoreMap.ENTRY_LIFETIME:
                ignored_mtime = ignored_size = ignored_is_dir = ignored_machine_guid = None
            if size < 0:
                is_dir = False
            ret = (ignored_mtime,
             ignored_size if not ignored_is_dir else 0,
             ignored_is_dir,
             ignored_ctime if ignored_ctime and ctime else None,
             ignored_machine_guid) == (mtime,
             size if not is_dir else 0,
             is_dir,
             ctime if ignored_ctime and ctime else None,
             machine_guid)
            if not ret:
                TRACE('WRITES_TO_IGNORE: statted (%r, %r, %r, %r, %r), had (%r, %r, %r, %r, %r) for %r' % (mtime,
                 size,
                 is_dir,
                 ctime,
                 machine_guid,
                 ignored_mtime,
                 ignored_size,
                 ignored_is_dir,
                 ignored_ctime,
                 ignored_machine_guid,
                 fn))
                del self.d[key]
            return ret

    def clear(self, warn = False):
        with self.lock:
            if len(self.d):
                if warn:
                    TRACE('Deleting %s writes-to-ignore entries (first 25: %r)' % (len(self.d), self.d.items()[:25]))
                    try:
                        assert len([ x for x in self.d.values() if x[0] > -1 ]) == 0, '%s writes-to-ignore entries not processed' % len(self.d)
                    except:
                        unhandled_exc_handler()

            self.d.clear()
