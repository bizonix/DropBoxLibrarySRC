#Embedded file name: dropbox/fastwalk.py
from __future__ import with_statement
from __future__ import absolute_import
import collections
import sys
import errno
import itertools
import functools
import operator
from dropbox.functions import run_iterable_in_c
from dropbox.low_functions import identity
from dropbox.trace import TRACE, unhandled_exc_handler, assert_
from dropbox.usertuple import UserTuple
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_UNKNOWN, FILE_TYPE_POSIX_SYMLINK
from dropbox.sync_engine_file_system.exceptions import DirectoryModifiedError, FileSystemError

def is_file_not_found_exception(e):
    return isinstance(e, EnvironmentError) and e.errno == errno.ENOENT


def _iterate_up_to(rel, path, case_insensitive = True):
    if rel.lower() == path.lower() if case_insensitive else rel == path:
        return
    while True:
        path = path.dirname
        yield path
        if path.lower() == rel.lower() if case_insensitive else path == rel:
            break


class _fastwalk_helper_common(object):

    def __init__(self, fs, the_queue, on_explore_error, low_helper, ctx, dir_path, dir_obj):
        self.fs = fs
        self.queue = the_queue
        self.orig_len = len(self.queue)
        self.on_explore_error = on_explore_error
        self.low_helper = low_helper
        self.ctx = ctx
        self.dir_path = dir_path
        self.dir_obj = dir_obj
        self._next = self.lowiter().next
        self.close = self.dir_obj.close

    def __iter__(self):
        return self

    def next(self):
        return self._next()

    def __enter__(self):
        return self

    def __exit__(self, *n, **kw):
        self.close()

    def reset(self):
        run_iterable_in_c(itertools.starmap(self.queue.pop, itertools.repeat((), len(self.queue) - self.orig_len)))
        self.dir_obj.reset()
        self._next = self.lowiter().next

    def readdir(self):
        try:
            return self.next()
        except StopIteration:
            return None

    def lowiter(self):
        try:
            for dirent in self.low_helper(self.ctx, self.dir_obj):
                yield dirent

        except DirectoryModifiedError:

            def _raise():
                raise DirectoryModifiedError

            self._next = _raise
            _raise()
        except Exception:
            self.on_explore_error and self.on_explore_error(self.dir_path)


def _filter_subs_based_on_unicode(parent, dir_obj, on_nonunicode_error):
    for dirent in dir_obj:
        if type(dirent.name) is not unicode:
            if on_nonunicode_error is not None:
                on_nonunicode_error(parent, dirent)
            continue
        yield dirent


def _fastwalk_helper_dont_follow(fs, on_nonunicode_error, local_queue_extend, parent, subs, preprocess_entries_func = None):
    subs = _filter_subs_based_on_unicode(parent, subs, on_nonunicode_error)
    if preprocess_entries_func:
        subs = preprocess_entries_func(subs)
    current_queue = []
    for dirent in subs:
        yield dirent
        full_path = None
        try:
            _type = dirent.type
        except AttributeError:
            full_path = parent.join(dirent.name)
            try:
                _type = fs.indexing_attributes(full_path).type
            except Exception:
                _type = FILE_TYPE_UNKNOWN

        if _type == FILE_TYPE_DIRECTORY:
            current_queue.append(parent.join(dirent.name))

    local_queue_extend(reversed(current_queue))


def _fastwalk_helper_follow(fs, on_nonunicode_error, local_queue_extend, elt, subs, preprocess_entries_func = None):
    parent, pstat, parent_elt = elt
    subs = _filter_subs_based_on_unicode(parent, subs, on_nonunicode_error)
    if preprocess_entries_func:
        subs = preprocess_entries_func(subs)
    current_queue = []
    for dirent in subs:
        yield dirent
        _full_path = [None]

        def full_path():
            if _full_path[0]:
                return _full_path[0]
            _full_path[0] = parent.join(dirent.name)
            return _full_path[0]

        _ia = [None, None]

        def indexing_attributes(resolve_link = True):
            idx = 0 if resolve_link else 1
            if _ia[idx]:
                return _ia[idx]
            _ia[idx] = fs.indexing_attributes(full_path(), resolve_link=resolve_link)
            return _ia[idx]

        try:
            _type = dirent.type
        except AttributeError:
            try:
                _type = indexing_attributes(resolve_link=False).type
            except Exception:
                _type = FILE_TYPE_UNKNOWN

        if _type == FILE_TYPE_DIRECTORY:
            try:
                file_id = dirent.file_id
            except AttributeError:
                try:
                    st = indexing_attributes()
                except Exception as e:
                    if not is_file_not_found_exception(e):
                        unhandled_exc_handler()
                    continue

                file_id = st.file_id

            new_pstat = (pstat[0], file_id)
        elif _type == FILE_TYPE_POSIX_SYMLINK:
            try:
                st = indexing_attributes()
            except Exception as e:
                if not (isinstance(e, EnvironmentError) and e.errno == errno.ELOOP) and not is_file_not_found_exception(e):
                    unhandled_exc_handler()
                continue
            else:
                if st.type != FILE_TYPE_DIRECTORY:
                    continue
                new_pstat = (st.volume_id, st.file_id)

        else:
            continue
        pelt = elt
        no = False
        while pelt:
            if new_pstat == pelt[1]:
                no = True
                break
            pelt = pelt[2]

        if not no:
            current_queue.append(UserTuple(full_path(), new_pstat, elt))

    local_queue_extend(reversed(current_queue))


def fastwalk_strict(fs, dir_path, on_explore_error = None, on_nonunicode_error = None, no_atime = False, follow_symlinks = True, dont_follow_up_to = None, case_insensitive = None, preprocess_entries_func = None):
    if follow_symlinks:
        if case_insensitive is None:
            case_insensitive = True
            try:
                case_insensitive = fs.is_case_insensitive_directory(dir_path)
            except FileSystemError:
                unhandled_exc_handler(False)
            except Exception:
                unhandled_exc_handler()

        last = None
        try:
            if dont_follow_up_to:
                for path in reversed(list(_iterate_up_to(dont_follow_up_to, dir_path, case_insensitive=case_insensitive))):
                    pstat = fs.indexing_attributes(path)
                    last = UserTuple(path, (pstat.volume_id, pstat.file_id), last)

            pstat = fs.indexing_attributes(dir_path)
        except Exception:
            if on_explore_error is not None:
                on_explore_error(dir_path)
                return
            raise

        initial = UserTuple(dir_path, (pstat.volume_id, pstat.file_id), last)
        low_helper = functools.partial(_fastwalk_helper_follow, preprocess_entries_func=preprocess_entries_func)
        get_dir = operator.itemgetter(0)
    else:
        assert_(lambda : dont_follow_up_to is None, 'dont_follow_up_to cannot be set if ' + 'follow_symlinks is false: %r', dont_follow_up_to)
        low_helper = functools.partial(_fastwalk_helper_dont_follow, preprocess_entries_func=preprocess_entries_func)
        initial = dir_path
        get_dir = identity
    queue = collections.deque((initial,))
    local_queue_pop = queue.pop
    helper = functools.partial(_fastwalk_helper_common, fs, queue, on_explore_error, functools.partial(low_helper, fs, on_nonunicode_error, queue.extend))
    while queue:
        ctx = local_queue_pop()
        dir_to_explore = get_dir(ctx)
        try:
            dir_obj = fs.opendir(dir_to_explore, no_atime=no_atime)
        except Exception:
            if on_explore_error is not None:
                on_explore_error(dir_to_explore)
                continue
            else:
                raise

        files = helper(ctx, dir_to_explore, dir_obj)
        try:
            yield (dir_to_explore, files)
        finally:
            try:
                files.close()
            except Exception:
                unhandled_exc_handler()


def _old_fastwalk_helper(fs, dirents):
    try:
        for dirent in dirents:
            yield dirent

    except DirectoryModifiedError:
        pass


def fastwalk(fs, *n, **kw):
    for dir, dirents in fastwalk_strict(fs, *n, **kw):
        dirents = _old_fastwalk_helper(fs, dirents)
        if not (yield (dir, dirents)):
            run_iterable_in_c(dirents)


def fastwalk_with_exception_handling(fs, dir, **kw):

    def on_explore_error(path):
        a, exc_value, c = sys.exc_info()
        if not (hasattr(exc_value, 'errno') and exc_value.errno in (errno.EPERM, errno.ENOENT)):
            report = True
        else:
            report = False
        unhandled_exc_handler(report)

    def on_nonunicode_error(parent, dirent):
        TRACE('!! Non filesystem-encoding path in Dropbox: %r %r', parent, dirent)

    return fastwalk(fs, dir, on_explore_error=on_explore_error, on_nonunicode_error=on_nonunicode_error, **kw)
