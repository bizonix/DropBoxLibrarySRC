#Embedded file name: arch/mac/directory_reader_helper.py
import errno
import os
from dropbox.fileevents import FileEvents
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.sync_engine_arch import make_arch
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR
from dropbox.symlink_util import should_recurse

class RescanMixin(object):

    def rescan(self, path, recurse = False, no_trace = False):
        NOTHING = (set(), set(), set())
        if self.recurse == FileEvents.RECURSE_NONE or path not in self.path_map:
            return NOTHING
        fs = make_arch().file_system
        if not self.isdir:
            if self.dir is None:
                return NOTHING
            if path != self.dir:
                return NOTHING
            files = self.path_map[self.dir][1]
            fn = self.path
            updated = set()
            deleted = set()
            ctime_changed = set()
            try:
                st = fs.indexing_attributes(fs.make_path(fn))
            except OSError as e:
                if e.errno == errno.ENOENT:
                    deleted.add(fn)
                    if fn in files:
                        del files[fn]
                else:
                    unhandled_exc_handler()
            else:
                if fn not in files:
                    updated.add(fn)
                    files[fn] = (long(st.mtime),
                     long(st.ctime),
                     st.size,
                     st.machine_guid)
                else:
                    mtime, ctime, size, machine_guid = files[fn]
                    if (mtime, size, machine_guid) != (long(st.mtime), st.size, st.machine_guid):
                        updated.add(fn)
                        files[fn] = (long(st.mtime),
                         long(st.ctime),
                         st.size,
                         st.machine_guid)
                    elif ctime != long(st.ctime):
                        ctime_changed.add(fn)
                        files[fn] = (long(st.mtime),
                         long(st.ctime),
                         st.size,
                         st.machine_guid)

            return (updated, deleted, ctime_changed)
        dirs, files = self.path_map[path][:2]
        old_set = set(dirs.keys())
        old_set.update(files.keys())
        try:
            new_set = os.listdir(path)
        except OSError as e:
            if e.errno == errno.ENOENT or e.errno == errno.EACCES:
                TRACE('Error listing path %r' % path.encode('utf-8'))
                new_set = []
            else:
                raise

        deleted = old_set.difference(new_set)
        for k in deleted:
            if k in dirs:
                self.del_subdir(os.path.join(path, k))
                del dirs[k]
            elif k in files:
                del files[k]

        updated = set()
        ctime_changed = set()
        for fn in new_set:
            full_path = os.path.join(path, fn)
            try:
                st = fs.indexing_attributes(fs.make_path(full_path))
            except OSError as e:
                if e.errno == errno.ENOENT:
                    TRACE('%r in listdir() but now gone?' % full_path.encode('utf-8'))
                    deleted.add(fn)
                    if fn in dirs:
                        self.del_subdir(full_path)
                        del dirs[fn]
                    elif fn in files:
                        del files[fn]
                else:
                    unhandled_exc_handler()
                continue

            if st.type == FILE_TYPE_DIRECTORY:
                if fn in dirs and long(st.ctime) != dirs[fn][1]:
                    ctime_changed.add(fn)
                    dirs[fn] = (dirs[fn][0], long(st.ctime), dirs[fn][2])
                if recurse or fn in dirs and (long(st.mtime) != dirs[fn][0] or st.machine_guid != dirs[fn][2]):
                    if self.recurse == FileEvents.RECURSE_ALL:
                        child_updated, child_deleted, child_ctime = self.rescan(full_path, recurse)
                        updated.update((os.path.join(fn, x) for x in child_updated))
                        deleted.update((os.path.join(fn, x) for x in child_deleted))
                        ctime_changed.update((os.path.join(fn, x) for x in child_ctime))
                    if fn in dirs:
                        dirs[fn] = (long(st.mtime), long(st.ctime), st.machine_guid)
                if fn not in dirs and should_recurse(full_path, rel=self.path, case_insensitive=self.case_insensitive):
                    if self.recurse == FileEvents.RECURSE_ALL:
                        self.add_subdir(full_path, no_trace=no_trace)
                    updated.add(fn)
                    dirs[fn] = (long(st.mtime), long(st.ctime), st.machine_guid)
                    if fn in files:
                        del files[fn]
            elif st.type == FILE_TYPE_REGULAR:
                if fn in dirs:
                    self.del_subdir(full_path)
                    del dirs[fn]
                if fn not in files:
                    updated.add(fn)
                    files[fn] = (long(st.mtime),
                     st.ctime,
                     st.size,
                     st.machine_guid)
                else:
                    mtime, ctime, size, machine_guid = files[fn]
                    if (mtime, size, machine_guid) != (long(st.mtime), st.size, st.machine_guid):
                        updated.add(fn)
                        files[fn] = (long(st.mtime),
                         st.ctime,
                         st.size,
                         st.machine_guid)
                    elif ctime != long(st.ctime):
                        ctime_changed.add(fn)
                        files[fn] = (long(st.mtime),
                         st.ctime,
                         st.size,
                         st.machine_guid)

        return (updated, deleted, ctime_changed)
