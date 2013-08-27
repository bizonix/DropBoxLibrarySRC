#Embedded file name: dropbox/sync_engine_file_system/posix_indexing_attributes_mixin.py
from binascii import b2a_hex
import base64
import errno
import os
import stat
import struct
import time
from Crypto.Random import random, get_random_bytes
from dropbox.features import feature_enabled
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.xattrs_posix import ENOATTR_LIST, XATTR_CREATE, fgetxattr, flistxattr, fremovexattr, fsetxattr
from pylinux import fstatvfs, statvfs
from .constants import FILE_TYPE_DIRECTORY, FILE_TYPE_POSIX_BLOCK_DEVICE, FILE_TYPE_POSIX_CHARACTER_DEVICE, FILE_TYPE_POSIX_FIFO, FILE_TYPE_POSIX_SYMLINK, FILE_TYPE_POSIX_SOCKET, FILE_TYPE_REGULAR, FILE_TYPE_UNKNOWN
from .util import IndexingAttributes, convert_os_error_dec

class RaceDetected(Exception):
    pass


class MachineGuidUnavailable(Exception):
    pass


def bitwise_or(flags):
    ret = 0
    for flag in flags:
        ret |= flag

    return ret


def st_equal(st1, st2):
    if st1 is None and st2 is None:
        return True
    if st1 is None or st2 is None:
        return False
    st1 = list(st1)
    st2 = list(st2)
    st1[stat.ST_ATIME] = st2[stat.ST_ATIME] = 0
    return st1 == st2


class PosixIndexingAttributesMixin(object):

    @convert_os_error_dec
    def indexing_attributes(self, path, resolve_link = True, write_machine_guid = False):
        resolve_link_or_callback = resolve_link
        del resolve_link
        fd = None
        while True:
            assert fd is None
            try:
                fd, resolving_link, symlink_stat, symlink_statvfs, symlink_target = self.__stat_symlink_and_open_path(path, resolve_link_or_callback)
                if fd is None:
                    return self.__indexing_attributes_without_fd(path, resolving_link, symlink_stat, symlink_statvfs, symlink_target)
                return self.indexing_attributes_from_fd(fd=fd, symlink_stat=symlink_stat, symlink_statvfs=symlink_statvfs, symlink_target=symlink_target, write_machine_guid=write_machine_guid, path=path)
            except RaceDetected:
                TRACE('Path modified while statting it.  Retrying %r', unicode(path))
            finally:
                if fd is not None:
                    os.close(fd)
                    fd = None

    def indexing_attributes_from_fd(self, fd, symlink_stat = None, symlink_statvfs = None, symlink_target = None, write_machine_guid = False, path = None):
        assert path is not None, 'path missing'
        st = os.fstat(fd)
        st_vfs = fstatvfs(fd) if self.USE_STATVFS else None
        try:
            machine_guid = self.__machine_guid_from_fd(fd, st, st_vfs, symlink_stat, symlink_statvfs, symlink_target, write_machine_guid, path=path)
        except MachineGuidUnavailable:
            if write_machine_guid and feature_enabled('fileids'):
                TRACE('!! Cannot obtain local machine guid for path %r', unicode(path))
            machine_guid = None

        if write_machine_guid:
            st = os.fstat(fd)
        return self.__indexing_attributes_from_stat_result(st, st_vfs, machine_guid=machine_guid)

    def __volume_id_from_stat_result(self, st, st_vfs):
        if self.USE_STATVFS:
            return st_vfs.f_fsid & 4294967295L
        else:
            return st.st_dev

    def __indexing_attributes_from_stat_result(self, st, st_vfs, **kwargs):
        _mode = st.st_mode
        _type = FILE_TYPE_REGULAR if stat.S_ISREG(_mode) else (FILE_TYPE_DIRECTORY if stat.S_ISDIR(_mode) else (FILE_TYPE_POSIX_BLOCK_DEVICE if stat.S_ISBLK(_mode) else (FILE_TYPE_POSIX_CHARACTER_DEVICE if stat.S_ISCHR(_mode) else (FILE_TYPE_POSIX_SYMLINK if stat.S_ISLNK(_mode) else (FILE_TYPE_POSIX_SOCKET if stat.S_ISSOCK(_mode) else (FILE_TYPE_POSIX_FIFO if stat.S_ISFIFO(_mode) else FILE_TYPE_UNKNOWN))))))
        kw = {}
        kw['mtime'] = st.st_mtime
        kw['size'] = st.st_size
        kw['ctime'] = st.st_ctime
        kw['volume_id'] = self.__volume_id_from_stat_result(st, st_vfs)
        kw['file_id'] = st.st_ino
        kw['type'] = _type
        kw['posix_mode'] = _mode
        kw['posix_uid'] = st.st_uid
        kw['posix_gid'] = st.st_gid
        kw['posix_nlink'] = st.st_nlink
        kw.update(kwargs)
        return IndexingAttributes(**kw)

    def __machine_guid_from_fd(self, fd, st, st_vfs, symlink_stat, symlink_statvfs, symlink_target, write_machine_guid, path = None):
        assert path is not None, 'path missing'
        if not feature_enabled('fileids'):
            raise MachineGuidUnavailable
        if stat.S_ISLNK(st.st_mode):
            report_bad_assumption('os.open succeeded on a symlink? path=%r', unicode(path))
            raise AssertionError
        try:
            machine_guid_xattr = self.__read_and_check_machine_guid_xattr(fd, st, st_vfs, write_machine_guid, path=path)
        except OSError as e:
            if e.errno == errno.ENOTSUP:
                TRACE('xattrs not supported by the filesystem, or are disabled (path: %r)', unicode(path))
                raise MachineGuidUnavailable
            else:
                TRACE('!! reading xattr failed (path: %r)', unicode(path))
                unhandled_exc_handler()
                raise MachineGuidUnavailable

        if write_machine_guid:
            xattr_name = self.__compute_machine_guid_xattr_name(st, st_vfs)
            self.__prune_old_machine_guid_xattrs(fd, xattr_name, path=path)
        if machine_guid_xattr is None and write_machine_guid:
            try:
                machine_guid_xattr = self.__write_machine_guid_xattr(fd, st, st_vfs)
            except OSError as e:
                if e.errno == errno.EACCES:
                    TRACE('!! Access denied while creating local guid xattr %r on path %r', xattr_name, unicode(path))
                    raise MachineGuidUnavailable
                else:
                    unhandled_exc_handler()
                    raise MachineGuidUnavailable

        if machine_guid_xattr is None:
            raise MachineGuidUnavailable
        return self.__compute_machine_guid(machine_guid_xattr, symlink_stat, symlink_statvfs)

    def __read_and_check_machine_guid_xattr(self, fd, st, st_vfs, write_machine_guid, path = None):
        assert path is not None, 'path missing'
        xattr_name = self.__compute_machine_guid_xattr_name(st, st_vfs)
        machine_guid_xattr = None
        try:
            machine_guid_xattr = fgetxattr(fd, xattr_name)
        except OSError as e:
            if e.errno in ENOATTR_LIST:
                pass
            else:
                raise

        if machine_guid_xattr is not None and self.__machine_guid_xattr_is_corrupt(st, st_vfs, machine_guid_xattr):
            report_bad_assumption('local guid xattr %r is corrupt on path %r (value is X%r)', xattr_name, unicode(path), b2a_hex(machine_guid_xattr))
            machine_guid_xattr = None
            if write_machine_guid:
                TRACE('!! Removing corrupt local guid xattr %r on path %r', xattr_name, unicode(path))
                self.__remove_corrupt_machine_guid_xattr(fd, xattr_name)
        return machine_guid_xattr

    def __compute_machine_guid_xattr_name(self, st, st_vfs):
        assert self.MACHINE_GUID_XATTR_PREFIX.endswith(u'.')
        volume_id = self.__volume_id_from_stat_result(st, st_vfs)
        xattr_name = u'%s%x.%x' % (self.MACHINE_GUID_XATTR_PREFIX, volume_id, st.st_ino)
        return xattr_name

    def __machine_guid_xattr_is_corrupt(self, st, st_vfs, machine_guid_xattr):
        if machine_guid_xattr is None or len(machine_guid_xattr) < 24:
            return True
        tag, randdata, volume_id, inode = struct.unpack('!B7sQQ', machine_guid_xattr[:24])
        return (tag, volume_id, inode) != (0, self.__volume_id_from_stat_result(st, st_vfs), st.st_ino)

    def __prune_old_machine_guid_xattrs(self, fd, current_xattr_name, path = None):
        assert path is not None, 'path missing'
        try:
            xattr_names = flistxattr(fd)
        except OSError as e:
            unhandled_exc_handler()
            return

        for xattr_name in xattr_names:
            if xattr_name.startswith(self.MACHINE_GUID_XATTR_PREFIX) and xattr_name != current_xattr_name:
                TRACE('Pruning stale xattr %r from path %r', xattr_name, unicode(path))
                try:
                    fremovexattr(fd, xattr_name)
                except OSError as e:
                    if e.errno in ENOATTR_LIST:
                        pass
                    elif e.errno == errno.EACCES:
                        TRACE("!! can't remove stale xattr: access denied")
                    else:
                        unhandled_exc_handler()

    def __generate_machine_guid_xattr(self, st, st_vfs):
        randdata = get_random_bytes(7)
        volume_id = self.__volume_id_from_stat_result(st, st_vfs)
        return struct.pack('!B7sQQ', 0, randdata, volume_id, st.st_ino)

    def __compute_machine_guid(self, machine_guid_xattr, symlink_stat, symlink_statvfs):
        if len(machine_guid_xattr) < 24:
            raise ValueError('truncated machine_guid_xattr')
        tag, randdata, volume_id, inode = struct.unpack('!B7sQQ', machine_guid_xattr[:24])
        if symlink_stat:
            tag = 2
            volume_id = self.__volume_id_from_stat_result(symlink_stat, symlink_statvfs)
            inode = symlink_stat.st_ino
        else:
            tag = 1
        binary_machine_guid = struct.pack('!B7sQQ', tag, randdata, volume_id, inode)
        return unicode(base64.urlsafe_b64encode(binary_machine_guid)).rstrip(u'=')

    def __remove_corrupt_machine_guid_xattr(self, fd, xattr_name):
        try:
            fremovexattr(fd, xattr_name)
        except OSError as e:
            if e.errno in ENOATTR_LIST:
                TRACE('!! Corrupt local guid xattr already gone! (probably racing)')
                sleeptime = random.randrange(100, 501) / 1000.0
                TRACE('!! Sleeping %d ms before restarting to avoid colliding with other instances', sleeptime * 1000)
                raise RaceDetected
            elif e.errno == errno.EACCES:
                TRACE("!! Can't remove corrupt local guid xattr: access denied")
                raise
            else:
                unhandled_exc_handler()
                raise
        else:
            sleeptime = random.randrange(50, 201) / 1000.0
            TRACE('!! Sleeping %d ms before continuing to avoid colliding with other instances', sleeptime * 1000)
            time.sleep(sleeptime)

    def __write_machine_guid_xattr(self, fd, st, st_vfs):
        xattr_name = self.__compute_machine_guid_xattr_name(st, st_vfs)
        new_machine_guid_xattr = self.__generate_machine_guid_xattr(st, st_vfs)
        try:
            fsetxattr(fd, xattr_name, new_machine_guid_xattr, XATTR_CREATE)
        except OSError as e:
            if e.errno == errno.EEXIST:
                TRACE('!! new local guid xattr already created (race?)')
                raise RaceDetected
            else:
                raise
        else:
            os.fsync(fd)
            return new_machine_guid_xattr

    def __stat_symlink_and_open_path(self, path, resolve_link_or_callback):
        symlink_stat = None
        symlink_statvfs = None
        symlink_target = None
        if callable(resolve_link_or_callback):
            resolving_link = None
        else:
            resolving_link = bool(resolve_link_or_callback)
        flags = set((os.O_RDONLY, os.O_NOCTTY, os.O_NOFOLLOW))
        if self.HAS_O_NOATIME:
            flags.add(os.O_NOATIME)
        fd = None
        while fd is None:
            try:
                fd = os.open(unicode(path), bitwise_or(flags))
            except OSError as e:
                if e.errno == errno.EPERM and self.HAS_O_NOATIME and os.O_NOATIME in flags:
                    flags.remove(os.O_NOATIME)
                    continue
                elif e.errno == errno.ELOOP and os.O_NOFOLLOW in flags:
                    try:
                        symlink_target = os.readlink(unicode(path))
                    except OSError as e:
                        if e.errno == errno.EINVAL:
                            raise RaceDetected
                        else:
                            raise

                    symlink_stat = os.lstat(unicode(path))
                    if not stat.S_ISLNK(symlink_stat.st_mode):
                        raise RaceDetected
                    if self.USE_STATVFS:
                        symlink_statvfs = statvfs(os.path.dirname(unicode(path)))
                        symlink_stat2 = os.lstat(unicode(path))
                        if not st_equal(symlink_stat, symlink_stat2):
                            raise RaceDetected
                    if callable(resolve_link_or_callback):
                        resolving_link = resolve_link_or_callback(symlink_stat=symlink_stat, symlink_statvfs=symlink_statvfs, symlink_target=symlink_target)
                    else:
                        assert isinstance(resolve_link_or_callback, bool)
                        resolving_link = resolve_link_or_callback
                    if resolving_link:
                        flags.remove(os.O_NOFOLLOW)
                    else:
                        break
                elif e.errno == errno.EACCES:
                    break
                else:
                    raise

        return (fd,
         resolving_link,
         symlink_stat,
         symlink_statvfs,
         symlink_target)

    def __indexing_attributes_without_fd(self, path, resolving_link, symlink_stat, symlink_statvfs, symlink_target):
        assert isinstance(resolving_link, bool)
        if symlink_stat and not resolving_link:
            return self.__indexing_attributes_from_stat_result(symlink_stat, symlink_statvfs, posix_symlink_target=symlink_target, machine_guid=None)
        elif symlink_stat:
            st = os.stat(unicode(path))
            if self.USE_STATVFS:
                st_vfs = statvfs(unicode(path))
                st2 = os.stat(unicode(path))
                if not st_equal(st, st2):
                    raise RaceDetected
            else:
                st_vfs = None
            symlink_stat2 = os.lstat(unicode(path))
            try:
                symlink_target2 = os.readlink(unicode(path))
            except OSError as e:
                if e.errno == errno.EINVAL:
                    raise RaceDetected
                else:
                    raise

            if not st_equal(symlink_stat, symlink_stat2) or not st_equal(symlink_target, symlink_target2):
                raise RaceDetected
            return self.__indexing_attributes_from_stat_result(st, st_vfs, machine_guid=None)
        else:
            st = os.lstat(unicode(path))
            if stat.S_ISLNK(st.st_mode):
                raise RaceDetected
            if self.USE_STATVFS:
                st_vfs = statvfs(os.path.dirname(unicode(path)))
                st2 = os.lstat(unicode(path))
                if not st_equal(st, st2):
                    raise RaceDetected
            else:
                st_vfs = None
            return self.__indexing_attributes_from_stat_result(st, st_vfs, machine_guid=None)
