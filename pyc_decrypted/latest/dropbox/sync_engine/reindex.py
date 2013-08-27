#Embedded file name: dropbox/sync_engine/reindex.py
import errno
import functools
import json
import operator
import threading
import time
import unicodedata
from Queue import Empty
from collections import Counter
from dropbox.directoryevent import DirectoryEvent
from dropbox.event import report
from dropbox.fastwalk import fastwalk_with_exception_handling
from dropbox.low_functions import identity
from dropbox.native_threading import NativeCondition
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_POSIX_SYMLINK
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, assert_, report_bad_assumption, unhandled_exc_handler
from dropbox.usertuple import UserTuple
from .sync_engine_util import SyncEngineStoppedError
from .hashing import _get_attributes

class ReindexDetails(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('dir', 'size', 'mtime', 'ctime', 'fj_id', 'attrs', 'filename', 'machine_guid')

    def __init__(self, *args, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def __repr__(self):
        return ''.join(['ReindexDetails(', ','.join([ '%s=%r' % (k, getattr(self, k)) for k in self.__slots__ if hasattr(self, k) ]), ')'])


def _startup(self):
    TRACE('Waiting for valid directory watch..')
    self.se.wait_for_directory_watch()
    self.se.status.set_status_labels(starting=False, reindexing=True)
    TRACE('Doing initial reindex...')
    gandalf_enabled = False
    reindex_stats = {}
    try:
        self.se.perf_tracker.info('freshly_linked', self.se.freshly_linked)
        self.se.perf_tracker.event('reindex_start')
        reindex(self.se, self.se.dropbox_folder, self.se.dropbox_folder, self.dirty_files, should_cancel=self.should_stop, attempt_journal=gandalf_enabled, stats=reindex_stats)
    except SyncEngineStoppedError:
        pass
    except Exception:
        unhandled_exc_handler()
    finally:
        TRACE('Gathered reindex stats: %s', reindex_stats)
        self.se.perf_tracker.update(**reindex_stats)
        self.se.perf_tracker.event('reindex_end')
        report('reindex_startup', **self.se.perf_tracker.report)
        self.se.status.set_status_label('reindexing', False)
        self.se.signal_initial_reindex_done()


def _reindex_thread(self):
    initted = False
    while not self.stopped():
        try:
            if not self.se.check_if_running(self.set_wakeup_event):
                initted = False
                self.se.set_thread_is_running(False)
                TRACE('SyncEngine has stopped, waiting...')
                to_reindex = self.se.reindex_queue.get()
                if to_reindex is not None:
                    self.se.reindex_queue.put(to_reindex)
                continue
            self.se.set_thread_is_running(True)
            if not initted:
                TRACE('Reindex thread starting')
                _startup(self)
                initted = True
            to_reindex = self.se.reindex_queue.get()
            if to_reindex is None:
                continue
            TRACE('Reindex request for %r', to_reindex)
            the_root = self.se.dropbox_folder
            if (to_reindex if self.se.case_sensitive else to_reindex.lower()) == (the_root if self.se.case_sensitive else the_root.lower()):
                TRACE('Received reindex event')
                self.se.status.set_status_label('reindexing', True)
                try:
                    reindex(self.se, the_root, the_root, self.dirty_files, should_cancel=self.should_stop)
                    TRACE('Finished initial reindex')
                finally:
                    self.se.status.set_status_label('reindexing', False)

            else:
                reindex(self.se, the_root, to_reindex, self.dirty_files, should_cancel=self.should_stop)
        except SyncEngineStoppedError:
            pass
        except Exception:
            unhandled_exc_handler()


class ReindexThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'REINDEX'
        super(ReindexThread, self).__init__(*n, **kw)
        self.se = sync_engine

    def set_wakeup_event(self):
        self.se.reindex_queue.put(None)

    def should_stop(self):
        if not self.se.running:
            raise SyncEngineStoppedError

    def dirty_files(self, *n, **kw):
        kw['recurse'] = 0
        return self.se._dirty_files_no_start_lock(*n, **kw)

    def run(self):
        _reindex_thread(self)
        TRACE('Stopping...')


def reindex(sync_engine, *n, **kw):
    with sync_engine.start_stop_lock:
        return reindex_no_start_lock(sync_engine, *n, **kw)


def reindex_no_start_lock(sync_engine, top_level, root, dirty_files, should_cancel = None, ctime_update = True, attempt_journal = False, stats = None):
    assert_(sync_engine.start_stop_lock.locked)
    if not sync_engine.running:
        raise SyncEngineStoppedError()
    local_directory_event = DirectoryEvent
    local_mod_attr_only = DirectoryEvent.TYPE_ATTR_ONLY
    count, adds, deletes, edits, new_file_size = (0, 0, 0, 0, 0)
    pending_files = []
    ctime_update_list = []
    attrs_whitelist = sync_engine.cache.get_attrs_whitelist()
    ideal_cache = {}
    for ent in reindex_low_manager(sync_engine, top_level, root, attempt_journal, should_cancel=should_cancel):
        dirty_type = ent[0]
        if dirty_type not in ('edit_attr', 'edit_machine_guid'):
            if dirty_type == 'add':
                TRACE('New file: %r', ent[1])
                adds += 1
                if hasattr(ent[1], 'size'):
                    new_file_size += ent[1].size()
            elif dirty_type == 'delete':
                TRACE('Deleted file: %r', ent[1])
                deletes += 1
            try:
                if sync_engine.ideal_tracker is not None:
                    sync_engine.ideal_tracker.handle_reindex_file(ent[1], ideal_cache=ideal_cache)
            except Exception:
                unhandled_exc_handler()

            pending_files.append(local_directory_event(ent[1]))
        else:
            edits += 1
            deet, ctime = ent[2:4]
            if ctime_update and not deet.ctime:
                try:
                    attrs = _get_attributes(sync_engine, ent[1], None, attrs_whitelist)
                    ia = sync_engine.fs.indexing_attributes(ent[1])
                    if attrs == deet.attrs and long(ia.mtime) == long(deet.mtime) and ia.size == deet.size and ia.machine_guid == deet.machine_guid:
                        ctime = long(ctime)
                        ctime_update_list.append(UserTuple(ctime, deet.fj_id, ctime))
                        if len(ctime_update_list) >= 500:
                            sync_engine.update_ctime_on_files(ctime_update_list)
                            ctime_update_list = []
                        continue
                except Exception:
                    unhandled_exc_handler()

            pending_files.append(local_directory_event(ent[1], local_mod_attr_only))
        if len(pending_files) >= sync_engine.max_upload_count:
            count += len(pending_files)
            dirty_files(pending_files)
            pending_files = []

    if pending_files:
        count += len(pending_files)
        dirty_files(pending_files)
    if ctime_update_list:
        sync_engine.update_ctime_on_files(ctime_update_list)
        ctime_update_list = []
    if stats is not None:
        stats['changed_things'] = count
        if adds > 0:
            stats['adds'] = adds
        if new_file_size > 0:
            stats['added_size'] = new_file_size
        if deletes > 0:
            stats['deletes'] = deletes
        if edits > 0:
            stats['edits'] = edits
    return count


def is_sibling_of_parent(a, b):
    return len(a) < len(b) and a[:-1] == b[:len(a) - 1]


def reindex_cmp(a, b):

    def split_and_normalize(s):
        return [ unicode(x).encode('utf8') for x in s.split() ]

    a = split_and_normalize(a)
    b = split_and_normalize(b)
    if is_sibling_of_parent(a, b):
        return -1
    if is_sibling_of_parent(b, a):
        return 1
    return cmp(a, b)


class MemoizedIndexingAttributes(object):

    def __init__(self, fs, fullpath):
        self.fs = fs
        self.fullpath = fullpath
        self.indexing_attributes = None

    def __call__(self, resolve_link = True):
        if resolve_link and not callable(resolve_link):
            if self.indexing_attributes:
                return self.indexing_attributes
            self.indexing_attributes = self.fs.indexing_attributes(self.fullpath)
            return self.indexing_attributes
        else:
            return self.fs.indexing_attributes(self.fullpath, resolve_link=resolve_link)


class FallBackDirectoryEntry(object):

    def __init__(self, ent, indexing_attributed_thunk):
        self.__ent = ent
        self.__iat = indexing_attributed_thunk

    def __getattr__(self, name):
        try:
            return getattr(self.__ent, name)
        except AttributeError:
            return getattr(self.__iat(), name)


def check_for_edits(fs, fj_deet, dir_deet, rpath, local_case_sensitive):
    fullpath = rpath.lower() if not local_case_sensitive else rpath
    ia = MemoizedIndexingAttributes(fs, fullpath)
    try:
        try:
            _type = dir_deet.type
        except AttributeError:
            _type = ia(resolve_link=False).type

        if _type == FILE_TYPE_POSIX_SYMLINK:
            file_metadata = ia()
        else:
            file_metadata = FallBackDirectoryEntry(dir_deet, ia)
        if file_metadata.type == FILE_TYPE_DIRECTORY:
            if not fj_deet.dir:
                TRACE('Checking on dirty directory %r', fullpath)
                return ('edit', rpath)
        else:
            mtime = long(file_metadata.mtime)
            size = file_metadata.size
            if fj_deet.dir or size != fj_deet.size or mtime != long(fj_deet.mtime):
                if long(mtime) == long(fj_deet.mtime) and fj_deet.size and size == 0:
                    report_bad_assumption('We have a zero byte file with the mtime the same.')
                TRACE('Checking on dirty file %r: (size, is_dir, mtime,) %r vs %r', fullpath, (size, False, mtime), (fj_deet.size, fj_deet.dir, fj_deet.mtime))
                return ('edit', rpath)
        ctime = file_metadata.ctime
        cmp_ctime = long(file_metadata.ctime)
        if fj_deet.ctime == 0 or long(fj_deet.ctime) != cmp_ctime:
            TRACE('Checking on ctime change (current: %r vs old: %r) %r', cmp_ctime, fj_deet.ctime, fullpath)
            return ('edit_attr',
             rpath,
             fj_deet,
             ctime)
        if fj_deet.machine_guid != file_metadata.machine_guid:
            return ('edit_machine_guid', rpath)
        return None
    except Exception as e:
        unhandled_exc_handler(not (hasattr(e, 'errno') and e.errno in (errno.ENOENT, errno.ELOOP)))
        TRACE('Error while checking file: %r', fullpath)
        return ('edit', rpath)


def reindex_low_manager(sync_engine, top_level, root, attempt_journal, should_cancel = None, stats = None):
    if attempt_journal:
        journal_reindexer = None
        try:
            journal_reindexer = sync_engine.arch.JournalReindexer(sync_engine, top_level, stats, root)
            if journal_reindexer.can_journal(root):
                changed_dirs = dict(((sync_engine.fs.make_path(p), v) for p, v in journal_reindexer.start_reindex().iteritems()))
                if changed_dirs:
                    return reindex_low_changed(sync_engine, top_level, root, should_cancel=should_cancel, changed_dirs=changed_dirs, stats=stats)
            else:
                TRACE("Platform doesn't support journaling")
        except sync_engine.arch.JournalFailure as e:
            TRACE('Journal error: %r', e)
        except Exception:
            if journal_reindexer is None:
                sync_engine.remove_config_key('reindex_cursor')
            else:
                journal_reindexer.reset()
            if stats:
                stats['failed_reason'] = 'Unknown failure'
            unhandled_exc_handler()
            TRACE('Journaling failed. Falling back on regular reindex')

    return reindex_low(sync_engine, top_level, root, should_cancel=should_cancel, stats=stats)


def reindex_low(sync_engine, top_level, root, should_cancel = None, stats = None):
    start_reindex = time.time()
    edits = edit_attrs = adds = deletes = 0
    local_case_sensitive = sync_engine.case_sensitive
    fj_entries = sync_engine.get_all_local_details_under_relative_root_iterator(root)
    if local_case_sensitive:

        def local_path_recover((key_path, deet)):
            return key_path

    else:

        def local_path_recover((key_path, deet)):
            return key_path.dirname.join_nfc_components(deet.filename)

    if local_case_sensitive:
        local_normalize = identity
    else:
        local_normalize = operator.methodcaller('lower')
    sort_entries = functools.partial(sorted, key=lambda dirent: local_normalize(unicodedata.normalize('NFC', dirent.name)).encode('utf8'))
    try:
        sync_engine.fs.indexing_attributes(root)
    except FileNotFoundError:
        dir_entries = iter([])
    else:
        walker = fastwalk_with_exception_handling(sync_engine.fs, root, no_atime=True, dont_follow_up_to=top_level, case_insensitive=not local_case_sensitive, preprocess_entries_func=sort_entries)
        dir_count = [0]

        def skip_local_cache(walker):
            already_checked = False
            local_cache_path_l = sync_engine.cache_path_l
            for dirpath, ents in walker:
                dir_count[0] += 1
                should_cancel and should_cancel()
                if not already_checked and (dirpath if local_case_sensitive else dirpath.lower()) == local_cache_path_l:
                    already_checked = True
                    try:
                        dirpath, ents = walker.send(True)
                    except StopIteration:
                        break
                    except Exception:
                        unhandled_exc_handler()
                        continue

                for dirent in ents:
                    rpath = fullpath = dirpath.join(dirent.name)
                    if not local_case_sensitive:
                        fullpath = rpath.lower()
                    yield (fullpath, dirent, rpath)

        dir_entries = skip_local_cache(walker)

    def safe_next(iter_):
        try:
            return iter_.next()
        except StopIteration:
            return None

    fj_entry = safe_next(fj_entries)
    dir_entry = safe_next(dir_entries)
    while True:
        try:
            if not fj_entry and not dir_entry:
                break
            elif not fj_entry:
                yield ('add', dir_entry[2])
                adds += 1
                dir_entry = safe_next(dir_entries)
            elif not dir_entry:
                yield ('delete', local_path_recover(fj_entry))
                deletes += 1
                fj_entry = safe_next(fj_entries)
            else:
                compare = reindex_cmp(fj_entry[0], dir_entry[0])
                if compare > 0:
                    yield ('add', dir_entry[2])
                    adds += 1
                    dir_entry = safe_next(dir_entries)
                elif compare < 0:
                    yield ('delete', local_path_recover(fj_entry))
                    deletes += 1
                    fj_entry = safe_next(fj_entries)
                else:
                    ret = check_for_edits(sync_engine.fs, fj_entry[1], dir_entry[1], dir_entry[2], local_case_sensitive)
                    if ret:
                        yield ret
                        edits += 1
                    fj_entry = safe_next(fj_entries)
                    dir_entry = safe_next(dir_entries)
        except Exception:
            unhandled_exc_handler(trace_locals=False)

    took = time.time() - start_reindex
    sync_engine.perf_tracker.event('reindex_low_done')
    if stats:
        stats['directory_count'] = dir_count[0]
        stats['regular_reindex_time'] = took
        reindex_info = {}
        reindex_info['last_reindex'] = time.time()
        reindex_info['num_dirs'] = dir_count[0]
        sync_engine.set_config_key('reindex_info', json.dumps(reindex_info))
    TRACE('reindex() took %f seconds. Statistics: edit: %d edit_attr: %d add: %d delete: %d ', took, edits, edit_attrs, adds, deletes)


def reindex_low_changed(sync_engine, top_level, root, should_cancel = None, changed_dirs = None, stats = None):
    start_reindex = time.time()
    local_case_sensitive = sync_engine.case_sensitive
    visited_dirs = set()

    def reindex_regular(path):
        if path not in visited_dirs:
            visited_dirs.add(path)
            for dir_ in changed_dirs:
                if dir_.startswith(path):
                    visited_dirs.add(dir_)

            for dir_info in reindex_low(sync_engine, top_level, path, should_cancel=should_cancel):
                yield dir_info

    for dirpath, should_recurse in sorted(changed_dirs.iteritems()):
        if dirpath in visited_dirs:
            continue
        if should_recurse:
            for item in reindex_regular(dirpath):
                yield item

            continue
        should_cancel and should_cancel()
        try:
            directory = sync_engine.fs.opendir(dirpath)
            TRACE('Directory %s', dirpath)
            fj_set = dict(sync_engine.get_immediate_local_details_under_relative_root(root, dirpath))
            if local_case_sensitive:
                local_fj_set_pop = fj_set.pop
            else:

                def local_fj_set_pop(path):
                    return fj_set.pop(path.lower())

            with directory:
                for dirent in directory:
                    try:
                        fullpath = dirpath.join(dirent.name)
                        try:
                            deet = local_fj_set_pop(fullpath)
                        except KeyError:
                            TRACE('Checking on new path %r', fullpath)
                            yield ('add', fullpath)
                            ia = MemoizedIndexingAttributes(sync_engine.fs, fullpath)
                            is_symlink = dirent.type == FILE_TYPE_POSIX_SYMLINK
                            if ia().type == FILE_TYPE_DIRECTORY if is_symlink else dirent.type == FILE_TYPE_DIRECTORY:
                                TRACE('New directory %r', fullpath)
                                for dir_info in reindex_regular(fullpath):
                                    yield dir_info

                        else:
                            ent_status = check_for_edits(sync_engine.fs, deet, dirent, fullpath, local_case_sensitive)
                            if ent_status is not None:
                                yield ent_status

                    except Exception:
                        unhandled_exc_handler(trace_locals=False)

        except OSError as e:
            if e.errno != errno.ENOENT:
                unhandled_exc_handler()
        except Exception as e:
            unhandled_exc_handler()
        else:
            if local_case_sensitive:
                for lp, deet in fj_set.iteritems():
                    yield ('delete', lp)
                    if deet.dir:
                        for item in reindex_regular(lp):
                            yield item

            else:
                for lp, deet in fj_set.iteritems():
                    yield ('delete', lp.dirname.join_nfc_components(deet.filename))
                    if deet.dir:
                        for item in reindex_regular(lp):
                            yield item

    took = time.time() - start_reindex
    if stats:
        stats['journal_reindex_time'] = took
    TRACE('reindex() took %f seconds' % took)


class ReindexQueue(object):

    def __init__(self):
        self._cond = NativeCondition()
        self._counts = Counter()

    def put(self, path):
        with self._cond:
            self._counts[path] += 1
            count = self._counts[path]
            self._cond.notify()
        if path is not None:
            if count == 101:
                report_bad_assumption('Asked to reindex the same path more than 100x. path: %s', path, full_stack=True)
            elif count == 11:
                report_bad_assumption('Asked to reindex the same path more than 10x. path: %s', path, full_stack=True)

    def get(self, block = True):
        with self._cond:
            while not self._counts:
                if block:
                    self._cond.wait()
                else:
                    raise Empty

            path, count = self._counts.popitem()
            return path

    def get_nowait(self):
        return self.get(block=False)

    def clear(self):
        with self._cond:
            self._counts.clear()
