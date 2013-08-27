#Embedded file name: dropbox/sync_engine/reconstruct.py
from __future__ import absolute_import
import errno
import hashlib
import itertools
import pprint
import sys
import time
import urllib
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, dropbox_hash
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.dbexceptions import LowDiskSpaceError
from dropbox.features import feature_enabled
from dropbox.functions import frozendict, is_watched_filename, loop_delete, RECONSTRUCT_TEMP_FILE_PREFIX
from dropbox.i18n import trans, format_number, ungettext
from dropbox.threadutils import StoppableThread
from dropbox.attrs import attr_dict_from_whitelist, get_attr_data, unfreeze_attr_dict
from dropbox.bubble import BubbleKind, Bubble
import dropbox.fsutil as fsutil
from dropbox.file_cache import RECONSTRUCT_PERMISSION_DENIED_CODE, RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE, RECONSTRUCT_READ_ONLY_FS_CODE, RECONSTRUCT_LOW_DISK_SPACE_CODE, RECONSTRUCT_NO_HASHES_CODE, RECONSTRUCT_PREDICTABLE_CODE, RECONSTRUCT_UNRECONSTRUCTABLE_CODE, RECONSTRUCT_BAD_LOCAL_DETAILS_CODE, RECONSTRUCT_BUSY_CODE, RECONSTRUCT_NO_PARENT_FOLDER_CODE, RECONSTRUCT_SHORTCUT_CODE, RECONSTRUCT_UNKNOWN_CODE
from dropbox.server_path import server_path_basename
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR, FILE_TYPE_POSIX_SYMLINK
from dropbox.sync_engine_file_system.exceptions import InvalidPathError, FileSystemError, FileNotFoundError, NotADirectoryError, DirectoryNotEmptyError, PermissionDeniedError, FileExistsError
from dropbox.metadata.metadata import metadata_plats
from .exceptions import BadLocalDetailsError, BusyFileError, CustomPermissionError, NoLocalDetailsError, NoParentFolderError, PredictableError, ReconstructCodeError, ShortcutFileError, UnreconstructableError
from .sync_engine_util import add_sig_and_check, SyncEngineStoppedError, AttributeMergeError, BlockContentsError
ONE_AM_TOMORROW = 25 * 60 * 60

def match_stat(local_details, st):
    if local_details is None and st is None:
        return True
    if local_details is None or st is None:
        return False
    this = (bool(local_details.dir),
     local_details.mtime,
     local_details.size,
     local_details.machine_guid)
    other = (st.type == FILE_TYPE_DIRECTORY,
     long(st.mtime),
     st.size if not st.type == FILE_TYPE_DIRECTORY else 0,
     st.machine_guid)
    return this == other


def makedirs_with_ignore(sync_engine, local_path):
    lpl = local_path.lower()
    if not sync_engine.dropbox_folder.lower().is_parent_of(lpl):
        raise Exception("Won't create non subpath of dropbox root!")
    parent_path = local_path.dirname
    if not sync_engine.is_directory(parent_path):
        makedirs_with_ignore(sync_engine, parent_path)
    if sync_engine.target_ns(sync_engine.local_to_server(local_path)):
        raise Exception("Won't create shared folder root if it doesn't already exist")
    try:
        sync_engine.fs.mkdir(local_path)
    except FileExistsError:
        exc_info = sys.exc_info()
        try:
            path_type = sync_engine.fs.indexing_attributes(local_path, resolve_link=False).type
            if path_type == FILE_TYPE_POSIX_SYMLINK:
                sync_engine.fs.remove(local_path)
                sync_engine.fs.mkdir(local_path)
            else:
                if path_type == FILE_TYPE_DIRECTORY:
                    return
                raise exc_info[0], exc_info[1], exc_info[2]
        except Exception:
            TRACE("Couldn't stat to check if file was a symlink, here's why:")
            unhandled_exc_handler()
            raise exc_info[0], exc_info[1], exc_info[2]
        finally:
            del exc_info


def check_busy_file_error(e):
    if hasattr(e, 'winerror') and e.winerror == 32:
        exc_info = sys.exc_info()
        raise BusyFileError, None, exc_info[2]


def create_local_copy(sync_engine, local_path, server_path):
    reason = sync_engine.get_conflict_reason(server_path)
    try:
        new_filename = sync_engine._resolve_conflict(local_path, local_path.basename, reason)
    except EnvironmentError as e:
        if e.errno in _UNRECONSTRUCTABLE_UNIX_ERRNOS or hasattr(e, 'winerror') and (e.winerror in _UNRECONSTRUCTABLE_WINDOWS_ERRNOS or e.winerror == 3):
            raise UnreconstructableError(str(e))
        elif e.errno in _DOES_NOT_EXIST_ERRNO:
            TRACE('Old path no longer exists! %r: %r, %r', local_path, sync_engine.is_exists(local_path), e)
        else:
            check_busy_file_error(e)
            unhandled_exc_handler()
            if hasattr(e, 'filename') and e.filename is not None:
                dst = e.filename
            else:
                dst = local_path.dirname.join(u'UNKNOWN')
            TRACE('Was trying to move %r (exists: %r) to %r (parent isdir? %r)', local_path, sync_engine.is_exists(local_path), dst, sync_engine.is_directory(local_path.dirname))
            raise PredictableError(str(e))
    except UnreconstructableError:
        raise
    except OverflowError as e:
        raise PredictableError('Too many conflicted copies! %r' % (local_path,))
    else:
        TRACE('Local copy: renamed %r to %r', local_path, new_filename)

    if sync_engine.is_exists(local_path):
        raise Exception("Couldn't actually move the previous file! %r", local_path)


class ReconstructResult(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ['ctime',
     'mtime',
     'data_plats',
     'attrs',
     'machine_guid']

    def __init__(self, *n, **kw):
        for key, val in kw.iteritems():
            setattr(self, key, val)

    def __repr__(self):
        return ''.join(['ReconstructResult(', ','.join([ '%s=%r' % (k, getattr(self, k)) for k in self.__slots__ if hasattr(self, k) ]), ')'])


_UNRECONSTRUCTABLE_WINDOWS_ERRNOS = (206,
 123,
 87,
 267)
_UNRECONSTRUCTABLE_UNIX_ERRNOS = (errno.EINVAL, errno.ENAMETOOLONG, errno.EILSEQ)
_DOES_NOT_EXIST_ERRNO = (errno.ENOTDIR, errno.ENOENT)

def _delete_dir_and_unwatched(local_path, sync_engine):
    fs = sync_engine.fs

    def simple_remove(the_path):
        try:
            fs.remove(the_path)
        except PermissionDeniedError:
            TRACE('Unable to delete %r: Permission denied', the_path)
            return False
        except (FileNotFoundError, NotADirectoryError):
            return False

        return True

    def my_remove(dirent):
        fullpath = local_path.join(dirent.name)
        try:
            ent_type = dirent.type
        except AttributeError:
            ent_type = sync_engine.fs.indexing_attributes(fullpath, resolve_link=False)

        if not is_watched_filename(dirent.name, ent_type == FILE_TYPE_DIRECTORY) or ent_type not in (FILE_TYPE_REGULAR, FILE_TYPE_DIRECTORY) or sync_engine.arch.is_shortcut_file(unicode(fullpath)):
            return simple_remove(fullpath)

    try:
        if fs.supports_extension('win32'):
            fsutil.clear_fs_bits(fs, local_path)
        try:
            fs.rmdir(local_path)
        except DirectoryNotEmptyError:
            with fs.opendir(local_path) as dir_handle:
                try:
                    loop_delete(dir_handle, my_remove)
                except Exception:
                    unhandled_exc_handler()

            fs.rmdir(local_path)

    except NotADirectoryError:
        simple_remove(local_path)
    except FileNotFoundError:
        return
    except Exception as e:
        exc_info = sys.exc_info()
        try:
            try:

                def safe_stat(path):
                    try:
                        return fs.indexing_attributes(path)
                    except Exception:
                        unhandled_exc_handler(False)
                        return None

                with fs.opendir(local_path) as dir_handle:
                    dict_to_print = dict(((dirent.name, safe_stat(local_path.join(dirent.name))) for dirent in itertools.islice(dir_handle, 100)))
                    num_entries = len(dict_to_print) + sum((1 for x in dir_handle))
                TRACE('Directory contents of %r (%s files total): %s', local_path, num_entries, pprint.pformat(dict_to_print, indent=4, width=100))
            except Exception:
                unhandled_exc_handler()

            check_busy_file_error(e)
            raise exc_info[0], exc_info[1], exc_info[2]
        finally:
            del exc_info


def _one_file(sync_engine, details, hash_sigs_to_prune, get_contents):
    cache_path = sync_engine.verify_cache_path()
    server_path, blocklist, size, mtime, dir, attrs = (details.server_path,
     details.blocklist,
     details.size,
     details.mtime,
     details.dir,
     details.attrs)
    temp_fn = cache_path.join(u'~%s.tmp' % hashlib.md5(blocklist + unicode(server_path).encode('utf8')).hexdigest()[:8])
    target_fn = sync_engine.server_to_local(server_path)
    try:
        st = sync_engine.fs.indexing_attributes(temp_fn)
    except FileNotFoundError:
        pass
    except Exception:
        unhandled_exc_handler()
    else:
        already_reconstructed = False
        if st.size == size:
            try:
                with sync_engine.fs.open(temp_fn) as f:
                    if blocklist:
                        for _hash in blocklist.split(','):
                            if not sync_engine.running:
                                raise SyncEngineStoppedError
                            s = f.read(DROPBOX_MAX_BLOCK_SIZE)
                            if s == '':
                                already_reconstructed = True
                                break
                            if dropbox_hash(s) != _hash:
                                break
                            add_sig_and_check(hash_sigs_to_prune, sync_engine.sigstore, _hash, s)

                    else:
                        already_reconstructed = True
            except Exception:
                unhandled_exc_handler()
                TRACE('Error while checking previously reconstructed file; reconstructing again.')

        if not already_reconstructed:
            try:
                sync_engine.fs.remove(temp_fn)
            except FileNotFoundError:
                pass
            except Exception:
                unhandled_exc_handler()

        else:
            TRACE('Found old %r at temp file %r', target_fn, temp_fn)
            return (temp_fn, st.mtime, st.size)

    try:
        sync_engine.verify_disk_space(cache_path, size)
        with sync_engine.fs.open(temp_fn, 'w') as f:
            TRACE('Beginning restoration of %r (contents %r)', server_path, blocklist)
            if blocklist:
                pos = 0
                for i, _hash in enumerate(blocklist.split(',')):
                    if not sync_engine.running:
                        raise SyncEngineStoppedError
                    TRACE(u'Yanking %s@%s (%s)' % (server_path, pos, _hash))
                    s = get_contents(_hash)
                    try:
                        f.write(s)
                    except IOError as e:
                        TRACE("Couldn't write to %r@%r", temp_fn, pos)
                        if e.errno == errno.ENOSPC:
                            sync_engine.status.set_status_label('low_disk_space', True)
                            raise LowDiskSpaceError(0, 0)
                        raise
                    else:
                        TRACE('Restored contents of %r@%d from %r', server_path, pos, _hash)
                        pos += len(s)

            f.datasync()
        st = sync_engine.fs.indexing_attributes(temp_fn)
        TRACE('Reconstructed %r into temp file %r successfully', target_fn, temp_fn)
        return (temp_fn, st.mtime, st.size)
    except:
        exc = sys.exc_info()
        try:
            try:
                sync_engine.fs.remove(temp_fn)
            except FileNotFoundError:
                pass
            except Exception:
                unhandled_exc_handler()

            raise exc[0], exc[1], exc[2]
        finally:
            del exc


def handle_attrs_conflict(sync_engine, details, conflicted_details = -1):
    if conflicted_details == -1:
        conflicted_details = sync_engine.is_conflicted(details.server_path)
    if not conflicted_details:
        return (True, details.attrs)
    if details.blocklist == conflicted_details.blocklist:
        try:
            return (True, sync_engine.attr_handler.merge_for_conflict(conflicted_details.attrs, details.attrs))
        except AttributeMergeError:
            return (False, details.attrs)

    else:
        return (False, details.attrs)


def do_just_attrs(sync_engine, details, target_fn):
    just_attrs = not details.dir and details.size >= 0 and details.blocklist == getattr(details, 'parent_blocklist', None)
    if just_attrs:
        if sync_engine.fs.is_normal_file(target_fn):
            just_attrs, attrs = handle_attrs_conflict(sync_engine, details)
        else:
            just_attrs = False
    if just_attrs:
        return (just_attrs, attrs)


def _actually_reconstruct(sync_engine, all_details, hash_sigs_to_prune):

    def get_contents(_hash):
        s = sync_engine.contents(_hash, _already_have_sync_engine_lock=True)
        add_sig_and_check(hash_sigs_to_prune, sync_engine.sigstore, _hash, s)
        return s

    low_disk_space = False
    mtime_size_map = {}
    for details in all_details:
        if not sync_engine.running:
            break
        if sync_engine._eager_should_not_reconstruct(details):
            continue
        target_fn = sync_engine.server_to_local(details.server_path)
        just_attrs = do_just_attrs(sync_engine, details, target_fn)
        if just_attrs or details.size < 0 or details.dir:
            continue
        if low_disk_space:
            continue
        try:
            mtime_size_map[details] = _one_file(sync_engine, details, hash_sigs_to_prune, get_contents)
        except LowDiskSpaceError:
            unhandled_exc_handler()
            low_disk_space = True
        except Exception as e:
            unhandled_exc_handler(not isinstance(e, BlockContentsError))

    return mtime_size_map


def mute_attr_set(attrs):
    try:
        mute_attr = attrs.attr_dict.get('dropbox_mute', {}).get('mute', None)
        if mute_attr is None:
            return False
        return bool(get_attr_data(mute_attr, None))
    except Exception:
        unhandled_exc_handler()

    return False


def _reconstruct(sync_engine, details, hash_sigs_to_prune, get_contents, ctx, mtime_size_map):
    server_path, blocklist, size, mtime, dir, attrs = (details.server_path,
     details.blocklist,
     details.size,
     details.mtime,
     details.dir,
     details.attrs)
    should_mute = mute_attr_set(attrs)
    should_bubble = getattr(details, 'host_id', None) != sync_engine.host_int and not should_mute
    if sync_engine.is_dirty(server_path):
        raise PredictableError('file is dirty')
    if sync_engine.is_uploading(server_path):
        raise PredictableError('file is uploading')
    if not sync_engine.is_reconstructable(server_path):
        raise PredictableError('file is no longer queued for reconstruction')
    my_fs_move = sync_engine.safe_move
    try:
        old_fn = target_fn = sync_engine.server_to_local(server_path)
    except InvalidPathError as e:
        raise UnreconstructableError(e.message)

    if server_path.ns != sync_engine.main_root_ns and (server_path.dirname.is_root and old_fn.basename == u'.dropbox' or unicode(server_path).startswith(u'%d:/.dropbox/' % server_path.ns)):
        raise UnreconstructableError("Can't create a .dropbox folder from the server where a .dropbox shared folder should be")
    target_fn_parent = target_fn.dirname
    conflicted_details = sync_engine.is_conflicted(details.server_path)
    just_attrs_tuple = do_just_attrs(sync_engine, details, target_fn)
    if just_attrs_tuple is not None:
        just_attrs, attrs = just_attrs_tuple
    else:
        just_attrs = False
    if not just_attrs and not dir and size >= 0:
        try:
            mtime_size_entry = mtime_size_map[details]
        except KeyError:
            mtime_size_entry = _one_file(sync_engine, details, hash_sigs_to_prune, get_contents)

    else:
        mtime_size_entry = None

    def feasibility_checks():
        if size >= 0:
            sync_engine.verify_disk_space(target_fn_parent, size)
        else:
            sync_engine.verify_disk_space(target_fn_parent)
        if not sync_engine.arch.check_filename(target_fn, size < 0, dir):
            return False
        try:
            st_parent = sync_engine.fs.indexing_attributes(target_fn_parent)
        except FileSystemError as e:
            if e.errno not in _DOES_NOT_EXIST_ERRNO:
                if hasattr(e, 'winerror'):
                    if e.winerror in _UNRECONSTRUCTABLE_WINDOWS_ERRNOS:
                        raise UnreconstructableError(str(e))
                    else:
                        raise
                elif e.errno in _UNRECONSTRUCTABLE_UNIX_ERRNOS:
                    raise UnreconstructableError(str(e))
                else:
                    raise
        else:
            if st_parent.type == FILE_TYPE_DIRECTORY:
                if not sync_engine.verify_file_perms(target_fn_parent, 'write', st=st_parent):
                    raise CustomPermissionError('bad perms on %r' % target_fn_parent)
            else:
                raise PredictableError("parent %r isn't a directory..." % target_fn_parent)

        return True

    if not feasibility_checks():
        assert size < 0, 'Can only have false feasibility checks when this is a delete'
        return ReconstructResult(ctime=-1, mtime=-1, machine_guid=None, data_plats=(), attrs=())
    can_go = sync_engine._reconstruct_can_go(server_path, details)
    if not can_go:
        raise PredictableError('File is pending or has changed')
    target_fn2, local_details = can_go
    old_fn2 = target_fn2
    if target_fn2 != target_fn:
        target_fn = target_fn2
        old_fn = old_fn2
        target_fn_parent = target_fn.dirname
        if not feasibility_checks():
            assert size < 0, 'Can only have false feasibility checks when this is a delete'
            return ReconstructResult(ctime=-1, mtime=-1, machine_guid=None, data_plats=(), attrs=())
    if local_details:
        if just_attrs and local_details.blocklist != blocklist:
            raise Exception('Blocklist is not the same as local file blocklist')
        attr_blocklist = sync_engine.attr_handler.get_downloadable_blocklist(old_fn, attrs)
        if attr_blocklist or details.size < 0:
            try:
                st = sync_engine.fs.indexing_attributes(old_fn)
            except (FileNotFoundError, NotADirectoryError):
                st = None
            except FileSystemError as e:
                if hasattr(e, 'winerror'):
                    if e.winerror in _UNRECONSTRUCTABLE_WINDOWS_ERRNOS:
                        raise UnreconstructableError(str(e))
                    else:
                        raise
                elif e.errno in _UNRECONSTRUCTABLE_UNIX_ERRNOS:
                    raise UnreconstructableError(str(e))
                else:
                    raise

            if st and not match_stat(local_details, st):
                raise BadLocalDetailsError(local_path=old_fn, server_path=server_path, l_mtime=local_details.mtime, l_size=local_details.size, l_isdir=bool(local_details.dir), l_machine_guid=local_details.machine_guid, st_mtime=st.mtime, st_size=st.size, st_isdir=st.type == FILE_TYPE_DIRECTORY, st_machine_guid=st.machine_guid)
            local_attrs = local_details.attrs
            hashes_to_save = sync_engine.attr_handler.get_downloadable_blocklist(old_fn, local_attrs)
            if details.size >= 0:
                hashes_to_save &= attr_blocklist
            if hashes_to_save:
                for hash_ in hashes_to_save:
                    try:
                        sync_engine.deleted_file_cache.add_data(hash_, get_contents(hash_))
                    except BlockContentsError:
                        raise
                    except:
                        unhandled_exc_handler()

                can_go = sync_engine._reconstruct_can_go(server_path, details)
                if not can_go:
                    raise PredictableError('File is pending or has changed')
                target_fn2, local_details = can_go
                if target_fn2 != target_fn:
                    target_fn = target_fn2
                    old_fn = old_fn2
                    target_fn_parent = target_fn.dirname
                    if not feasibility_checks():
                        assert size < 0, 'Can only have false feasibility checks when this is a delete'
                        return ReconstructResult(ctime=-1, mtime=-1, machine_guid=None, data_plats=(), attrs=())
    if conflicted_details and not just_attrs:
        was_a_directory = sync_engine.is_directory(old_fn)
        assert details.sjid != -1
        create_local_copy(sync_engine, old_fn, server_path)
        if was_a_directory:
            sync_engine._queue_reindex(target_fn)
        local_details = None
        st = None
    else:
        try:
            st = sync_engine.fs.indexing_attributes(old_fn)
        except (FileNotFoundError, NotADirectoryError):
            st = None
        except FileSystemError as e:
            if hasattr(e, 'winerror'):
                if e.winerror in _UNRECONSTRUCTABLE_WINDOWS_ERRNOS:
                    raise UnreconstructableError(str(e))
                else:
                    raise
            elif e.errno in _UNRECONSTRUCTABLE_UNIX_ERRNOS:
                raise UnreconstructableError(str(e))
            else:
                raise

    deleted_fn = None
    deleted_move = None
    if st is not None and st.type != FILE_TYPE_DIRECTORY:
        if is_watched_filename(old_fn.basename, False):
            if not local_details:
                cached_fn, _, _ = mtime_size_entry
                if sync_engine.arch.is_shortcut_file(unicode(old_fn), unicode(cached_fn), attrs):
                    raise ShortcutFileError()
                raise NoLocalDetailsError(old_fn, server_path, st.mtime, st.size)
            elif not match_stat(local_details, st):
                raise BadLocalDetailsError(local_path=old_fn, server_path=server_path, l_mtime=local_details.mtime, l_size=local_details.size, l_isdir=bool(local_details.dir), l_machine_guid=local_details.machine_guid, st_mtime=st.mtime, st_size=st.size, st_isdir=st.type == FILE_TYPE_DIRECTORY, st_machine_guid=st.machine_guid)
        if not dir and not just_attrs:
            deleted_fn = sync_engine.deleted_file_cache.get_filename(server_path, st.mtime, st.size, local_details.blocklist)
            deleted_move = (deleted_fn,
             old_fn,
             server_path,
             local_details.size,
             local_details.blocklist)
    switched_files = [False]
    unwritten_plats = [None]

    def copy_file_from_temp():

        def move_to_deleted(fn):
            TRACE('Going to move active file (%r) to backup file (%r)', fn, deleted_move[0])
            try:
                try:
                    sync_engine.fs.remove(deleted_move[0])
                    TRACE('Deleted file %r already exists in cache?', deleted_move[0])
                except FileNotFoundError:
                    pass
                except Exception:
                    unhandled_exc_handler()

                my_fs_move(fn, deleted_move[0])
            except Exception:
                unhandled_exc_handler()
                sync_engine.fs.remove(fn)
            else:
                sync_engine.deleted_file_cache.add_entry(*deleted_move)

        try:
            temp_fn, temp_fn_mtime, temp_fn_size = mtime_size_entry
            st = sync_engine.fs.indexing_attributes(temp_fn)
            if st.size != temp_fn_size or long(round(st.mtime * 1000)) != long(round(temp_fn_mtime * 1000)):
                raise Exception('Bad temp file!')
            successfully_completed_exchangedata = False
            if deleted_move:
                try:
                    sync_engine.fs.exchangedata(temp_fn, old_fn, temp_prefix=RECONSTRUCT_TEMP_FILE_PREFIX)
                except Exception as e:
                    if not (isinstance(e, OSError) and e.errno in (errno.EOPNOTSUPP, errno.EACCES)):
                        unhandled_exc_handler()
                else:
                    successfully_completed_exchangedata = True
                    try:
                        move_to_deleted(temp_fn)
                    except Exception:
                        unhandled_exc_handler()

            if not successfully_completed_exchangedata:
                if deleted_move:
                    try:
                        move_to_deleted(old_fn)
                    except Exception:
                        unhandled_exc_handler()

                try:
                    sync_engine.fs.rename(temp_fn, target_fn)
                except FileSystemError as e:
                    if e.errno == errno.EXDEV:
                        fsutil.copyfile(sync_engine.fs, temp_fn, target_fn)
                        try:
                            sync_engine.fs.remove(temp_fn)
                        except Exception:
                            unhandled_exc_handler()

                    else:
                        raise

        except FileSystemError as e:
            check_busy_file_error(e)
            TRACE('Was trying to move %r (exists: %r) to %r (exists: %r) (parent isdir? %r)', temp_fn, sync_engine.is_exists(temp_fn), target_fn, sync_engine.is_exists(target_fn), sync_engine.is_directory(target_fn_parent))
            raise
        else:
            switched_files[0] = True

        unwritten_plats[0] = sync_engine.attr_handler.write_attributes(attrs, get_contents, target_fn, is_dir=False)
        try:
            fsutil.inherit_properly_from_parent_directory(sync_engine.arch.file_system, target_fn)
        except FileNotFoundError:
            raise
        except Exception:
            unhandled_exc_handler()

    if size >= 0:
        new_ctime = 0
        new_machine_guid = None
        try:
            if just_attrs:
                TRACE("Doing 'just_attrs' reconstruct: %r", details)
                try:
                    unwritten_plats[0] = sync_engine.attr_handler.write_attributes(attrs, get_contents, target_fn, is_dir=False)
                except UnreconstructableError:
                    switched_files[0] = True
                    raise

            else:
                if not sync_engine.is_directory(target_fn_parent):
                    if sync_engine.get_reconstruct_create_tries(server_path) > 3:
                        makedirs_with_ignore(sync_engine, target_fn_parent)
                    else:
                        raise NoParentFolderError()
                if st is None:
                    if dir:
                        try:
                            sync_engine.fs.mkdir(target_fn)
                        except FileExistsError:
                            exc_info = sys.exc_info()
                            try:
                                reraise = True
                                try:
                                    if sync_engine.fs.indexing_attributes(target_fn, resolve_link=False).type not in (FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR):
                                        sync_engine.fs.remove(target_fn)
                                        reraise = False
                                except Exception:
                                    unhandled_exc_handler()

                                if reraise:
                                    raise exc_info[0], exc_info[1], exc_info[2]
                                else:
                                    sync_engine.fs.mkdir(target_fn)
                            finally:
                                del exc_info

                        unwritten_plats[0] = sync_engine.attr_handler.write_attributes(attrs, get_contents, target_fn, is_dir=True)
                        try:
                            sync_engine.tag_folder_if_special(server_path, target_fn)
                        except:
                            e = sys.exc_info()
                            try:
                                try:
                                    sync_engine.fs.rmdir(target_fn)
                                except FileNotFoundError:
                                    pass
                                except Exception:
                                    unhandled_exc_handler()

                                raise e[0], e[1], e[2]
                            finally:
                                del e

                    else:
                        copy_file_from_temp()
                elif dir:
                    if st.type != FILE_TYPE_DIRECTORY:
                        try:
                            sync_engine.fs.remove(old_fn)
                        except (FileNotFoundError, NotADirectoryError):
                            pass
                        else:
                            sync_engine.fs.mkdir(target_fn)

                    try:
                        sync_engine.tag_folder_if_special(server_path, target_fn, resolve_conflict=True)
                    except:
                        e = sys.exc_info()
                        try:
                            try:
                                sync_engine.fs.rmdir(target_fn)
                            except FileNotFoundError:
                                pass
                            except Exception:
                                unhandled_exc_handler()

                            raise e[0], e[1], e[2]
                        finally:
                            del e

                    unwritten_plats[0] = sync_engine.attr_handler.write_attributes(attrs, get_contents, target_fn, is_dir=True)
                else:
                    if st.type == FILE_TYPE_DIRECTORY:
                        _delete_dir_and_unwatched(old_fn, sync_engine)
                    copy_file_from_temp()
            try:
                sync_engine.fs.set_file_mtime(target_fn, mtime)
            except FileNotFoundError:
                raise
            except Exception:
                unhandled_exc_handler()
                new_mtime = None
            else:
                new_mtime = mtime

            try:
                a = sync_engine.fs.indexing_attributes(target_fn, write_machine_guid=True)
            except FileNotFoundError:
                raise
            except Exception:
                unhandled_exc_handler()
            else:
                read_mtime = long(a.mtime)
                if not new_mtime:
                    new_mtime = read_mtime
                else:
                    difference = long(new_mtime) - read_mtime
                    if difference:
                        if not abs(difference) == 3600:
                            if abs(difference) != 1:
                                report_bad_assumption("Mtime wasn't set correctly!! %r vs %r" % (new_mtime, read_mtime))
                            new_mtime = read_mtime
                new_ctime = long(a.ctime)
                new_machine_guid = a.machine_guid
                sync_engine._ignore_change(target_fn, new_mtime, size, bool(dir), new_ctime, new_machine_guid)

            data_plats = unwritten_plats[0][1]
            whitelist = sync_engine.get_attrs_whitelist()
            derived_metadata = sync_engine.get_metadata(target_fn, whitelist) if not dir else frozendict()
            if derived_metadata:
                attr_dict = unfreeze_attr_dict(attrs.attr_dict)
                derived_metadata = dict(((k, attr_dict_from_whitelist(derived_metadata[k], k, whitelist)) for k, val in derived_metadata.iteritems()))
                for metadata_plat, metadata_dict in derived_metadata.iteritems():
                    try:
                        other_dict = attr_dict[metadata_plat]
                    except KeyError:
                        other_dict = attr_dict[metadata_plat] = {}

                    for attr_key, attr_value in metadata_dict.iteritems():
                        try:
                            other_value = other_dict[attr_key]
                        except KeyError:
                            other_dict[attr_key] = attr_value
                        else:
                            if attr_value != other_value:
                                report_bad_assumption('Mismatched derived attrs? %r.%r %r vs %r', metadata_plat, attr_key, other_value, attr_value)

                attrs = attrs.copy(attr_dict=attr_dict)
                data_plats = set(data_plats) | set(metadata_plats())
        except Exception as e:
            try:
                toraise = e

                def debug_parent_status():
                    try:
                        to_explore = target_fn
                        statuses = {}
                        while True:
                            try:
                                st_ = sync_engine.fs.indexing_attributes(to_explore)
                            except Exception as e_:
                                st_ = e_

                            statuses[to_explore] = st_
                            if to_explore.is_root:
                                break
                            to_explore = to_explore.dirname

                        TRACE('!! Error while creating file: %r, here are the statuses of everything:\n%s', target_fn, pprint.pformat(sorted(statuses.iteritems(), key=lambda (p, st): p)))
                    except Exception:
                        unhandled_exc_handler()

                debug_parent_status()
                if isinstance(e, FileSystemError):
                    if hasattr(e, 'winerror'):
                        if e.winerror in _UNRECONSTRUCTABLE_WINDOWS_ERRNOS:
                            toraise = UnreconstructableError(str(e))
                    elif e.errno in _UNRECONSTRUCTABLE_UNIX_ERRNOS:
                        toraise = UnreconstructableError(str(e))
                elif isinstance(e, IOError) and e.errno in _UNRECONSTRUCTABLE_UNIX_ERRNOS:
                    toraise = UnreconstructableError(str(e))
                if toraise is e:
                    raise
                else:
                    raise toraise
            finally:
                if switched_files[0]:
                    TRACE('Cleaning up %r %r %r %r', target_fn, st, deleted_fn, old_fn)
                    try:
                        sync_engine.fs.remove(target_fn)
                    except FileNotFoundError as e:
                        pass
                    except Exception:
                        unhandled_exc_handler()

                    if not isinstance(toraise, UnreconstructableError) and st:
                        if st.type == FILE_TYPE_DIRECTORY:
                            try:
                                sync_engine.fs.mkdir(old_fn)
                            except Exception:
                                unhandled_exc_handler()

                        elif deleted_move:
                            TRACE('Moving back %r, %r', deleted_move[0], old_fn)
                            try:
                                my_fs_move(deleted_move[0], old_fn)
                            except Exception:
                                unhandled_exc_handler()

        else:
            if not dir:
                if should_bubble:
                    ctx.rft.add_updated_file(server_path, 'added' if st is None else 'updated')
                elif should_mute:
                    TRACE('Not bubbling for file %r due to mute attribute.', server_path)
                else:
                    TRACE('Not bubbling for file %r, same host_id.', server_path)
            if new_machine_guid is None and feature_enabled('fileids'):
                TRACE('!! No machine_guid while reconstructing %r', target_fn)
            return ReconstructResult(ctime=new_ctime, mtime=new_mtime, machine_guid=new_machine_guid, data_plats=data_plats, attrs=attrs)

    else:
        if st is not None:
            if st.type != FILE_TYPE_DIRECTORY:
                if deleted_move:
                    TRACE('Going to move active file (%r) to backup file (%r)', old_fn, deleted_move[0])
                    try:
                        try:
                            sync_engine.fs.remove(deleted_move[0])
                            TRACE('Deleted file %r already exists in cache?', deleted_move[0])
                        except FileNotFoundError:
                            pass
                        except Exception:
                            unhandled_exc_handler()

                        my_fs_move(old_fn, deleted_move[0])
                    except Exception:
                        unhandled_exc_handler(False)
                        try:
                            sync_engine.fs.remove(old_fn)
                        except FileNotFoundError:
                            pass
                        except FileSystemError as e:
                            check_busy_file_error(e)
                            raise

                    else:
                        sync_engine.deleted_file_cache.add_entry(*deleted_move)
                        if should_bubble:
                            ctx.rft.add_updated_file(server_path, 'deleted')
                        else:
                            TRACE('Not bubbling for file delete %r, same host_id', server_path)
            else:
                TRACE('Deleting directory %r', old_fn)
                _delete_dir_and_unwatched(old_fn, sync_engine)
            sync_engine._ignore_change(target_fn, -1, -1, False)
        return ReconstructResult(ctime=-1, mtime=-1, machine_guid=None, data_plats=(), attrs=())


def reconstruct_error_from_exception(fs, e):
    if isinstance(e, FileSystemError) or isinstance(e, EnvironmentError):
        if hasattr(e, 'winerror'):
            if e.winerror == 5:
                return RECONSTRUCT_PERMISSION_DENIED_CODE
            if e.winerror == 145:
                return RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE
        else:
            if e.errno in (errno.EPERM, errno.EACCES):
                return RECONSTRUCT_PERMISSION_DENIED_CODE
            if e.errno == errno.EROFS:
                return RECONSTRUCT_READ_ONLY_FS_CODE
            if e.errno == errno.ENOTEMPTY:
                return RECONSTRUCT_DIRECTORY_NOT_EMPTY_CODE
    else:
        if isinstance(e, LowDiskSpaceError):
            return RECONSTRUCT_LOW_DISK_SPACE_CODE
        if isinstance(e, CustomPermissionError):
            return RECONSTRUCT_PERMISSION_DENIED_CODE
        if isinstance(e, BlockContentsError):
            return RECONSTRUCT_NO_HASHES_CODE
        if isinstance(e, PredictableError):
            return RECONSTRUCT_PREDICTABLE_CODE
        if isinstance(e, UnreconstructableError):
            return RECONSTRUCT_UNRECONSTRUCTABLE_CODE
        if isinstance(e, BadLocalDetailsError):
            return RECONSTRUCT_BAD_LOCAL_DETAILS_CODE
        if isinstance(e, BusyFileError):
            return RECONSTRUCT_BUSY_CODE
        if isinstance(e, NoParentFolderError):
            return RECONSTRUCT_NO_PARENT_FOLDER_CODE
        if isinstance(e, ShortcutFileError):
            return RECONSTRUCT_SHORTCUT_CODE
        if isinstance(e, ReconstructCodeError):
            return e.code
    return RECONSTRUCT_UNKNOWN_CODE


class ReconstructedFilesTracker(object):

    def __init__(self):
        self.num_files = {}
        self.last_path = None

    def add_updated_file(self, path, action):
        assert action in ('updated', 'added', 'deleted')
        self.last_path = path
        self.num_files[action] = self.num_files.get(action, 0) + 1

    def get_update_results(self):
        return (self.num_files.get('updated', 0),
         self.num_files.get('added', 0),
         self.num_files.get('deleted', 0),
         self.last_path)


class ReconstructThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'RECONSTRUCT'
        super(ReconstructThread, self).__init__(*n, **kw)
        self.rft = ReconstructedFilesTracker()
        self.se = sync_engine

    def set_wakeup_event(self):
        self.se.reconstruct_event.set()

    def run(self):
        initted = False
        while not self.stopped():
            try:
                if not self.se.check_if_running(self.se.reconstruct_event.set):
                    self.se.set_thread_is_running(False)
                    initted = False
                    TRACE('SyncEngine has stopped, waiting...')
                    self.se.reconstruct_event.wait()
                    continue
                self.se.set_thread_is_running(True)
                if not initted:
                    self.se.deleted_file_cache.prune(always=True)
                    if not self.se.check_if_initial_hash_is_done(self.se.reconstruct_event.set):
                        TRACE('Waiting for hash reindex event...')
                        self.se.reconstruct_event.wait()
                        continue
                    TRACE('Reconstruct thread starting.')
                    initted = True
                self._reconstruct_once()
                if not self.stopped() and self.se.running:
                    ready_time = self.se.reconstruct_ready_time()
                    if ready_time is not None:
                        timeout = ready_time - time.time()
                        if self.se.status.is_true('low_disk_space'):
                            TRACE('Low disk space! Sleeping for 30 seconds')
                            timeout = max(timeout, 30)
                        if timeout > 0:
                            TRACE('Reconstruct sleeping for %r seconds', timeout)
                            self.se.reconstruct_event.wait(timeout)
                    else:
                        t = time.localtime(time.time())
                        timeout = ONE_AM_TOMORROW - ((t[3] * 60 + t[4]) * 60 + t[5])
                        TRACE('Reconstruct sleeping until 1AM (%d seconds)', timeout)
                        self.se.reconstruct_event.wait(timeout)
            except:
                unhandled_exc_handler()
                time.sleep(30)

        TRACE('Stopping...')

    def _reconstruct_once(self):
        self.se.perform_reconstruct(self)
        if not self.se.get_reconstruct_count():
            self.se.deleted_file_cache.prune()
            num_files_updated, num_files_added, num_files_deleted, last_file_changed = self.rft.get_update_results()
            self.rft = ReconstructedFilesTracker()
            if last_file_changed:
                msg = caption = bubble_context = bubble_kind = msg_passive = None
                if num_files_updated > 0 and num_files_added == 0 and num_files_deleted == 0:
                    bubble_context = self.se.bubble_context.make_sp_context_ref(last_file_changed, False)
                    if num_files_updated == 1:
                        fn = server_path_basename(last_file_changed)
                        msg_args = {'filename': fn}
                        msg_passive = trans(u'"%(filename)s" was updated to the latest version.') % msg_args
                        msg = trans(u'"%(filename)s" was updated to the latest version (click to view).') % msg_args
                        caption = trans(u'%(filename)s updated') % msg_args
                        bubble_kind = BubbleKind.SINGLE_FILE_UPDATED
                    else:
                        msg = ungettext(u'%s file was updated to the latest version.', u'%s files were updated to the latest version.', num_files_updated) % (format_number(num_files_updated, frac_precision=0),)
                        caption = ungettext(u'%s file updated', u'%s files updated', num_files_updated) % (format_number(num_files_updated, frac_precision=0),)
                        bubble_kind = BubbleKind.MULTIPLE_FILES_UPDATED
                elif num_files_added > 0 and num_files_updated == 0 and num_files_deleted == 0:
                    bubble_context = self.se.bubble_context.make_sp_context_ref(last_file_changed, False)
                    if num_files_added == 1:
                        fn = server_path_basename(last_file_changed)
                        msg_args = {'filename': fn}
                        msg_passive = trans(u'"%(filename)s" was added to your Dropbox folder.') % msg_args
                        msg = trans(u'"%(filename)s" was added to your Dropbox folder (click to view).') % msg_args
                        caption = trans(u'%(filename)s added') % msg_args
                        bubble_kind = BubbleKind.SINGLE_FILE_ADDED
                    else:
                        msg = ungettext(u'%s file was added to your Dropbox folder.', u'%s files were added to your Dropbox folder.', num_files_added) % (format_number(num_files_added, frac_precision=0),)
                        caption = ungettext(u'%s file added', u'%s files added', num_files_added) % (format_number(num_files_added, frac_precision=0),)
                        bubble_kind = BubbleKind.MULTIPLE_FILES_ADDED
                elif num_files_deleted > 0 and num_files_updated == 0 and num_files_added == 0:
                    if num_files_deleted == 1:
                        fn = server_path_basename(last_file_changed)
                        ns, rel = last_file_changed.ns_rel()
                        url = 'c/undelete%s?ns_id=%d' % (urllib.quote(rel.encode('utf8')), ns)
                        msg_args = {'filename': fn}
                        msg_passive = trans(u'"%(filename)s" was removed from your Dropbox folder.') % msg_args
                        msg = trans(u'"%(filename)s" was removed from your Dropbox folder (click to view).') % msg_args
                        caption = trans(u'%(filename)s deleted') % msg_args
                        bubble_context = self.se.bubble_context.make_func_context_ref(self.se.desktop_login.login_and_redirect, url)
                        bubble_kind = BubbleKind.SINGLE_FILE_DELETED
                    else:
                        msg = ungettext(u'%s file was removed from your Dropbox folder.', u'%s files were removed from your Dropbox folder.', num_files_deleted) % (format_number(num_files_deleted, frac_precision=0),)
                        caption = ungettext(u'%s file deleted', u'%s files deleted', num_files_deleted) % (format_number(num_files_deleted, frac_precision=0),)
                        bubble_kind = BubbleKind.MULTIPLE_FILES_DELETED
                elif num_files_deleted != 0 or num_files_updated != 0 or num_files_added != 0:
                    num_changed = num_files_updated + num_files_deleted + num_files_added
                    bubble_context = self.se.bubble_context.make_sp_context_ref(last_file_changed, False)
                    msg = ungettext(u'%s file was changed in your Dropbox folder.', u'%s files were changed in your Dropbox folder.', num_changed) % (format_number(num_changed, frac_precision=0),)
                    caption = trans(u'Dropbox folder synced')
                    bubble_kind = BubbleKind.DROPBOX_FOLDER_SYNCED
                if msg is not None and caption is not None:
                    self.se.ui_kit.show_bubble(Bubble(bubble_kind, msg, caption, self.se.bubble_context, bubble_context, msg_passive=msg_passive))
