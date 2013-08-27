#Embedded file name: dropbox/fsutil.py
from __future__ import with_statement, absolute_import
import contextlib
import errno
import os
import stat
import struct
import sys
import tempfile
import threading
from Crypto.Random import get_random_bytes
from dropbox.functions import loop_delete
from dropbox.platform import platform
from dropbox.trace import TRACE, unhandled_exc_handler, trace_stack
from dropbox.read_write_lock import RWLock
from dropbox.path import ServerPath
from dropbox.fastwalk import fastwalk as fastwalk_fs, fastwalk_with_exception_handling as fastwalk_with_exception_handling_fs, is_file_not_found_exception as _is_file_not_found_exception
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_REGULAR, FILE_TYPE_POSIX_SYMLINK
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError, DirectoryModifiedError, FileSystemError, NotADirectoryError, AttrsModifiedError, FileExistsError, PermissionDeniedError
is_file_not_found_exception = _is_file_not_found_exception

def is_permission_denied_exception(e):
    return isinstance(e, EnvironmentError) and e.errno == errno.EACCES


class Error(EnvironmentError):
    pass


try:
    WindowsError
except NameError:
    WindowsError = None

def copyfileobj(fsrc, fdst, length = 16384):
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)


def local_case_filenames(fs, local_path):
    basename = local_path.basename
    names = []
    if basename:
        lower = basename.lower()
        dirname = local_path.dirname
        try:
            for entry in listdir(fs, dirname):
                if entry.lower() == lower:
                    names.append(dirname.join(entry))

        except FileSystemError:
            return []

    return names


def _samefile(fs, src, dst):
    st1 = fs.indexing_attributes(src)
    try:
        st2 = fs.indexing_attributes(dst)
    except FileNotFoundError:
        return False

    return (st1.volume_id, st1.file_id) == (st2.volume_id, st2.file_id)


def copyfile(fs, src, dst):
    if _samefile(fs, src, dst):
        raise Exception('`%s` and `%s` are the same file' % (src, dst))
    fsrc = None
    fdst = None
    try:
        fsrc = fs.open(src, 'r')
        fdst = fs.open(dst, 'w')
        copyfileobj(fsrc, fdst)
    finally:
        if fdst:
            fdst.close()
        if fsrc:
            fsrc.close()


def copymode(src, dst):
    if hasattr(os, 'chmod'):
        st = os.stat(src)
        mode = stat.S_IMODE(st.st_mode)
        os.chmod(dst, mode)


def copystat(fs, src, dst):
    ia = fs.indexing_attributes(src)
    fs.set_file_mtime(dst, ia.mtime)
    if fs.supports_extension('posix'):
        fs.posix_chmod(dst, stat.S_IMODE(ia.posix_mode))


def copy(src, dst):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst)
    copymode(src, dst)


def copy2(fs, src, dst):
    if is_directory(fs, dst):
        dst = dst.join(src.basename)
    copyfile(fs, src, dst)
    copystat(fs, src, dst)


def copytree(src, dst, symlinks = False):
    names = os.listdir(src)
    os.makedirs(dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks)
            else:
                copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        except Error as err:
            errors.extend(err.args[0])

    try:
        copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            pass
        else:
            errors.extend((src, dst, str(why)))

    if errors:
        raise Error(errors)


def listdir(fs, path):
    return [ dirent.name for dirent in listdir_full(fs, path) ]


def listdir_full(fs, path):
    with fs.opendir(path) as _dir:
        return [ dirent for dirent in _dir ]


def rmtree(fs, path, ignore_errors = False, onerror = None):
    if ignore_errors:

        def onerror(*args):
            pass

    elif onerror is None:

        def onerror(*args):
            raise

    def _remove(dirent):
        if dirent.type == FILE_TYPE_DIRECTORY:
            return rmtree(fs, path.join(dirent.name), ignore_errors=ignore_errors, onerror=onerror)
        try:
            fs.remove(path.join(dirent.name))
            return True
        except Exception:
            onerror(fs.remove, path.join(dirent.name), sys.exc_info())
            return False

    try:
        opened_dir = fs.opendir(path)
    except Exception:
        onerror(fs.opendir, path, sys.exc_info())
        return False

    with opened_dir as _dir:
        loop_delete(_dir, _remove, dirmodifiederror=DirectoryModifiedError)
    try:
        fs.rmdir(path)
        return True
    except Exception:
        onerror(fs.rmdir, path, sys.exc_info())
        return False


def move(fs, src, dst):
    try:
        fs.rename(src, dst)
    except FileSystemError:
        copy2(fs, src, dst)
        fs.remove(src)


def destinsrc(src, dst):
    return dst.is_parent_of(src) or dst == src


def is_exists(fs, fs_path, resolve_link = True):
    try:
        fs.indexing_attributes(fs_path, resolve_link=True)
    except (FileNotFoundError, PermissionDeniedError):
        return False
    except Exception:
        unhandled_exc_handler(False)
        return False

    return True


def is_file_type(fs, fs_path, fs_node_type, resolve_link = True):
    try:
        return fs.indexing_attributes(fs_path, resolve_link=resolve_link).type == fs_node_type
    except (FileNotFoundError, NotADirectoryError, PermissionDeniedError):
        return False
    except Exception:
        unhandled_exc_handler(False)
        return False


def create_tester(fs_node_type, resolve_link = True):

    def func(fs, fs_path):
        return is_file_type(fs, fs_path, fs_node_type, resolve_link=resolve_link)

    return func


is_directory = create_tester(FILE_TYPE_DIRECTORY)
is_regular = create_tester(FILE_TYPE_REGULAR)
is_symlink = create_tester(FILE_TYPE_POSIX_SYMLINK, resolve_link=False)

def getsize(fs, fs_path):
    return fs.indexing_attributes(fs_path).size


def getmtime(fs, fs_path):
    return fs.indexing_attributes(fs_path).mtime


def makedirs(fs, fs_path, dirs_created = None):
    if fs_path.is_root and is_exists(fs, fs_path):
        return
    try:
        fs.mkdir(fs_path)
    except FileNotFoundError:
        if fs_path == fs_path.dirname:
            raise
    except FileExistsError:
        return
    else:
        if dirs_created is not None:
            dirs_created.append(fs_path)
        return

    makedirs(fs, fs_path.dirname)
    fs.mkdir(fs_path)
    if dirs_created is not None:
        dirs_created.append(fs_path)


def make_random_dir(fs, parent):
    while True:
        fname = get_random_bytes(8).encode('hex').decode('utf8')
        newp = parent.join(fname)
        try:
            fs.mkdir(newp)
        except FileExistsError:
            pass
        else:
            return newp


@contextlib.contextmanager
def tempfilename(fs, *n, **kw):
    f = mkstemp(fs, *n, **kw)
    try:
        f.close()
        yield fs.make_path(f.name)
    finally:
        safe_remove(fs, f.name)


def _get_child_handle_from_attr_handle(fs, handle, key_func, open_func):
    handle.reset()
    while True:
        try:
            key = key_func(handle)
        except AttrsModifiedError:
            handle.reset()
            continue

        if key is None:
            break
        child_handle = open_func(handle, key)
        try:
            yield child_handle
        finally:
            child_handle.close()


def get_plat_attr_handles_from_handle(fs, attr_handle):

    def attr_func(handle):
        return handle.readplat()

    def open_func(handle, key):
        return handle.open(key)

    for h in _get_child_handle_from_attr_handle(fs, attr_handle, attr_func, open_func):
        yield h


def get_attr_handles_from_plat_attr_handle(fs, plat_attrs_handle, mode = 'r'):

    def attr_func(handle):
        return handle.readattr()

    def open_func(handle, key):
        return handle.open(key, mode)

    for h in _get_child_handle_from_attr_handle(fs, plat_attrs_handle, attr_func, open_func):
        yield h


_perm2mode = {'exec': 73,
 'write': 146,
 'read': 292}

def posix_verify_file_perms(fs, local_file, perm, st = None):
    if st is None:
        st = fs.indexing_attributes(local_file)
    try:
        posix_mode = st.posix_mode
        posix_uid = st.posix_uid
        posix_gid = st.posix_gid
    except AttributeError:
        raise Exception('This function is only valid on posix file systems')

    uid = os.geteuid() if hasattr(os, 'geteuid') else -1
    if uid == 0:
        if perm == 'exec':
            return posix_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) != 0
        return True
    if posix_uid == uid:
        check = stat.S_IRWXU
    elif hasattr(os, 'getgroups') and posix_gid in os.getgroups():
        check = stat.S_IRWXG
    else:
        check = stat.S_IRWXO
    return posix_mode & (check & _perm2mode[perm]) != 0


def shell_touch_tree(fs, shell_touch, path, timeout = 2):

    def clear_shell_state_fn():
        for dirpath, ents in fastwalk_fs(fs, path, no_atime=True):
            for dirent in ents:
                try:
                    shell_touch(unicode(dirpath.join(dirent.name)))
                except Exception:
                    unhandled_exc_handler()

    _thread = threading.Thread(target=clear_shell_state_fn, name='CLEAR_SHELL')
    _thread.start()
    _thread.join(timeout)


def touch(fs, path):
    fs.open(path, 'a').close()


def safe_move(fs, src, dst):
    try:
        fs.rename(src, dst)
    except FileSystemError as e:
        if e.errno == errno.EXDEV:
            copy2(fs, src, dst)
            fs.remove(src)
        else:
            raise


def reparent_path(old_parent, new_parent, path):
    assert old_parent == path or old_parent.is_parent_of(path), 'Bad arguments, old_parent is not parent of path: %r vs %r' % (old_parent, path)
    to_append = []
    while path != old_parent:
        to_append.append(path.basename)
        path = path.dirname

    return new_parent.join(*reversed(to_append))


def win32_is_junction_point(fs, path, dirent = None):
    try:
        file_attributes = dirent.win32_file_attributes
    except AttributeError:
        ia = fs.indexing_attributes(path)
        try:
            file_attributes = ia.win32_file_attributes
        except AttributeError:
            return False

    FILE_ATTRIBUTE_REPARSE_POINT = 1024
    return file_attributes & FILE_ATTRIBUTE_REPARSE_POINT


def remove_all_attrs_on_handle(ah):
    for plat_name in ah:
        with ah.open(plat_name) as plat_handle:
            for attr_name in list(plat_handle):
                ah.remove(plat_name, attr_name)


def copyxattr(fs, src, dest):
    with fs.open_attributes(src) as sah:
        with fs.open_attributes(dest) as dah:
            remove_all_attrs_on_handle(dah)
            for plat_name in sah:
                sp, dp = None, None
                try:
                    sp = sah.open(plat_name)
                    dp = dah.open(plat_name)
                except Exception as e:
                    if not is_file_not_found_exception(e):
                        unhandled_exc_handler()
                        raise
                    continue
                else:
                    for attr_name in sp:
                        copyfileobj(sp.open(attr_name), dp.open(attr_name, 'w'))

                finally:
                    if sp is not None:
                        sp.close()
                    if dp is not None:
                        dp.close()

            sp, dp = None, None
            try:
                sp = sah.open_preserved()
                dp = dah.open_preserved('w')
            except Exception as e:
                if not is_file_not_found_exception(e):
                    unhandled_exc_handler()
                    raise
            else:
                copyfileobj(sp, dp)
            finally:
                if sp is not None:
                    sp.close()
                if dp is not None:
                    dp.close()


def clear_fs_bits(fs, path):
    if fs.supports_extension('win32'):
        fs.win32_set_file_attributes(path, 0)


def hide_file(fs, path):
    if fs.supports_extension('win32'):
        from pynt.headers.WinNT import FILE_ATTRIBUTE_HIDDEN, FILE_ATTRIBUTE_SYSTEM
        attrs = fs.win32_get_file_attributes(path)
        fs.win32_set_file_attributes(path, attrs | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)


def inherit_properly_from_parent_directory(fs, path):
    try:
        if fs.supports_extension('win32'):
            from pynt.headers.windows import DACL_SECURITY_INFORMATION
            psecurity = fs.win32_get_file_security(path.dirname, DACL_SECURITY_INFORMATION)
            fs.win32_set_file_security(path, DACL_SECURITY_INFORMATION, psecurity)
    except Exception:
        unhandled_exc_handler()

    try:
        if fs.supports_extension('win32'):
            fs.win32_inherit_not_content_indexing(path)
    except Exception:
        unhandled_exc_handler()


def safe_rmdir(fs, path):
    try:
        clear_fs_bits(fs, path)
    except Exception:
        unhandled_exc_handler(False)

    try:
        fs.rmdir(path)
    except FileNotFoundError:
        pass
    except Exception:
        unhandled_exc_handler(False)


def safe_remove(fs, path):
    try:
        fs.remove(path)
        return
    except FileNotFoundError:
        return
    except Exception:
        unhandled_exc_handler()
        trace_stack()

    try:
        with fs.open(path, 'r+') as f:
            f.seek(0)
            f.truncate()
            f.sync()
    except FileNotFoundError:
        pass
    except Exception:
        unhandled_exc_handler()
        trace_stack()


def expanduser(fs, raw_path):
    return fs.make_path(os.path.expanduser(raw_path))


def join_path_string(fs, path1, path2):
    return unicode(fs.make_path(path1).join(path2))


def make_normalized_path(fs, path):
    return fs.make_path(os.path.normpath(os.path.abspath(path)))


_dot_dropbox_file_lock = RWLock()

@contextlib.contextmanager
def DotDropboxFile(fs, path, mode, open_file = True):

    class FakeFile:

        def __init__(self, name):
            self.name = unicode(name)

    class WithName(object):

        def __init__(self, f, name):
            object.__setattr__(self, 'name', unicode(name))
            object.__setattr__(self, 'f', f)

        def __getattr__(self, name):
            return getattr(self.f, name)

        def __setattr__(self, name, value):
            if name == 'name':
                raise AttributeError('Name is read-only yo!')
            return setattr(self.f, name, value)

    writing = mode[0] in ('w', 'a') or mode[:2] == 'r+'
    dropbox_path = path.join(u'.dropbox')
    f = None
    try:
        if writing:
            _dot_dropbox_file_lock.acquire_write()
            if open_file and platform == 'win':
                assert mode[0] == 'w', 'Calling DotDropboxFile for writing with something other than w'
                try:
                    fs.remove(dropbox_path)
                except FileNotFoundError:
                    pass

        else:
            _dot_dropbox_file_lock.acquire_read()
        if open_file:
            f = WithName(fs.open(dropbox_path, mode), dropbox_path)
        else:
            f = FakeFile(dropbox_path)
        yield f
    finally:
        try:
            if f and open_file:
                f.close()
        finally:
            if writing:
                _dot_dropbox_file_lock.release_write()
            else:
                _dot_dropbox_file_lock.release_read()


def posix_is_normal_file(fs, path):
    try:
        st = fs.indexing_attributes(path, resolve_link=False)
    except FileNotFoundError:
        return False
    except Exception as e:
        if not isinstance(e, OSError):
            unhandled_exc_handler()
        return False

    return st.type == FILE_TYPE_REGULAR and st.posix_nlink == 1


def same_file_object(fs, a, b):
    aia = fs.indexing_attributes(a)
    bia = fs.indexing_attributes(b)
    return (aia.volume_id, aia.file_id) == (bia.volume_id, bia.file_id)


def on_same_device(fs, a, b):
    aia = fs.indexing_attributes(a)
    bia = fs.indexing_attributes(b)
    return aia.volume_id == bia.volume_id


def mkstemp(fs, dir = None, *n, **kw):
    if not fs.supports_extension('fdopen'):
        raise Exception('FS does not support fdopen!')
    if dir:
        kw['dir'] = unicode(dir)
    fd, path = tempfile.mkstemp(*n, **kw)
    f = fs.fdopen(fd, 'r+')
    f.name = path
    return f


def get_attr(fs, path, plat, key, offset = None, size = None):
    with fs.open_attributes(path) as attribute_handle:
        with attribute_handle.open(plat) as platform_handle:
            with platform_handle.open(key) as f:
                if offset is not None:
                    f.seek(offset)
                if size is None:
                    return f.read()
                return f.read(size)


def set_attr(fs, path, plat, key, data):
    with fs.open_attributes(path) as attribute_handle:
        with attribute_handle.open(plat) as platform_handle:
            with platform_handle.open(key, 'w') as f:
                f.write(data)


def get_directory_usage(fs, path):
    try:
        usage = 0
        for dirpath, ents in fastwalk_with_exception_handling_fs(fs, path, no_atime=True, follow_symlinks=False):
            for dirent in ents:
                try:
                    usage += dirent.size
                except AttributeError:
                    usage += fs.indexing_attributes(dirpath.join(dirent.name)).size

        return usage
    except Exception:
        unhandled_exc_handler()
        return 0


def get_directory_count(fs, path, count_dirs = False):
    count = 1
    try:
        for dirpath, ents in fastwalk_with_exception_handling_fs(fs, path, no_atime=True, follow_symlinks=False):
            for dirent in ents:
                if count_dirs or dirent.type != FILE_TYPE_DIRECTORY:
                    count += 1

        return count
    except Exception:
        unhandled_exc_handler()
        return count


def create_unique_file_name(fs, dest_path, basename):
    if not is_exists(fs, dest_path):
        makedirs(fs, dest_path)
    new_file_name = file_path = unicode(dest_path.join(basename))
    count = 2
    file_path_without_extension, file_extension = fs.splitext(file_path)
    while is_exists(fs, new_file_name):
        new_file_name = u'%s(%d)%s' % (file_path_without_extension, count, file_extension)
        count += 1

    return fs.make_path(new_file_name)


def supports_preserved_attrs(fs, path):
    try:
        with tempfilename(fs, dir=unicode(path)) as fn:
            with fs.open_attributes(fn) as f:
                f.open_preserved('w').close()
    except Exception as e:
        if is_file_not_found_exception(e):
            TRACE("Directory %s doesn't support extended attributes", path)
        else:
            unhandled_exc_handler()
        return False

    return True


def root_relative_to_local_path(app, path):
    relative_path_sp = ServerPath.from_ns_rel(app.sync_engine.main_root_ns, path)
    full_path = app.sync_engine.server_to_local(relative_path_sp)
    return full_path
