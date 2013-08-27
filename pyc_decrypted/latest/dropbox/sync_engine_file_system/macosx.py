#Embedded file name: dropbox/sync_engine_file_system/macosx.py
from __future__ import with_statement, absolute_import
import errno
import os
import sys
from unicodedata import normalize
from Foundation import NSAutoreleasePool, NSString
from pymac.helpers import pythonfile
from dropbox import fsutil
from dropbox.nfcdetector import is_nfd
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from .exceptions import FileNotFoundError, FileSystemError, PermissionDeniedError
from .hfsplus_compare import hfsplus_casefold
from .local_path import AbstractPosixPath
from .posix import PosixFileSystem
from .util import FileSystemDirectory, convert_os_error_dec
from .xattr_util import path_supports_xattrs, XAttrAttributesHandle

class MacOSXPath(AbstractPosixPath):
    SEPARATOR = u'/'

    @classmethod
    def _join_validate(cls, comp):
        res = super(MacOSXPath, cls)._join_validate(comp)
        if res:
            return res

    def to_dropbox_ns_relative(self, parent_local_path):
        toret = super(MacOSXPath, self).to_dropbox_ns_relative(parent_local_path)
        if not is_nfd(toret):
            raise Exception('Cannot convert Non-NFD Mac path to Dropbox: %r %r' % (parent_local_path, toret))
        return normalize('NFC', toret)

    def join_nfc_components(self, *descendants):
        return self.join(*(normalize('NFD', x) for x in descendants))


class FileSystem(PosixFileSystem):
    MACHINE_GUID_XATTR_PREFIX = u'com.dropbox.local-id.'
    USE_STATVFS = False
    HAS_O_NOATIME = False

    def __init__(self):
        if not sys.platform.startswith('darwin'):
            raise Exception('This only works on a mac os x system')
        super(FileSystem, self).__init__(MacOSXPath.from_path_string)

    def opendir(self, _path, **_kw):
        return FileSystemDirectory(unicode(_path), **_kw)

    def open_attributes(self, _path):
        return XAttrAttributesHandle(_path, 'mac', 'com.dropbox.attributes')

    def exchangedata(self, src, dest, temp_prefix = ''):
        srcu = unicode(src)
        destu = unicode(dest)
        try:
            pythonfile.exchangedata(srcu, destu)
        except OSError as e:
            if e.errno == errno.EXDEV:
                real_dest_path = self.make_path(os.path.realpath(destu))
                real_dest_dir = real_dest_path.dirname
                with fsutil.tempfilename(self, dir=real_dest_dir, prefix=temp_prefix) as temp_src_file:
                    fsutil.safe_move(self, src, temp_src_file)
                    pythonfile.exchangedata(destu, unicode(temp_src_file))
                    fsutil.safe_move(self, temp_src_file, src)
            elif e.errno == errno.ENOTSUP:
                raise OSError(errno.EOPNOTSUPP, 'Exchangedata not supported')
            else:
                raise

    def supports_extension(self, ext):
        return super(FileSystem, self).supports_extension(ext) or ext == 'exchangedata'

    def supported_attributes(self, path = None):
        if path is None:
            return ()
        elif path_supports_xattrs(path):
            return ('mac',)
        else:
            return ()

    def indexing_attributes(self, path, resolve_link = True, write_machine_guid = False):
        try:
            return super(FileSystem, self).indexing_attributes(path, resolve_link=resolve_link, write_machine_guid=write_machine_guid)
        except FileSystemError as exc:
            if exc.errno == errno.ENAMETOOLONG:
                TRACE('!! indexing_attributes got ENAMETOOLONG on path %r', path)
                self.__handle_enametoolong(path)
                TRACE('!! indexing_attributes raising ENAMETOOLONG for path %r', path)
            raise

    def __handle_enametoolong(self, path):
        orig_path = path
        while not path.is_root:
            basename = path.basename
            path = path.dirname
            basename_norm = self.__normalize_path(basename)
            basename_normcase = hfsplus_casefold(basename_norm)
            if len(basename.encode('utf-16be')) > 510 or len(basename_norm.encode('utf-16be')) > 510:
                TRACE('[ENAMETOOLONG workaround] Name is actually too long: %r', basename)
                return
            try:
                with self.opendir(path) as dir_:
                    dirlist = set((ent.name for ent in dir_))
                break
            except PermissionDeniedError:
                TRACE('!! [ENAMETOOLONG workaround] Failed - Not allowed to list ancestor directory: %r', path)
                return
            except FileSystemError as e:
                if e.errno == errno.ENAMETOOLONG:
                    continue
                TRACE('!! [ENAMETOOLONG workaround] Other error occurred.')
                unhandled_exc_handler()
                return

        else:
            report_bad_assumption('ENAMETOOLONG on the filesystem root?! %r', path, full_stack=True)
            return

        if basename in dirlist:
            TRACE('[ENAMETOOLONG workaround] Found the child %r in directory %r.', basename, path)
            return
        if basename != basename_norm and basename_norm in dirlist:
            report_bad_assumption('ENAMETOOLONG workaround needed basename normalization to succeed')
            TRACE('[ENAMETOOLONG workaround] Found the child %r (normalized: %r) in directory %r.', basename, basename_norm, path)
            return
        dirlist_norm = set(self.__normalize_path_batch(dirlist))
        if basename_norm in dirlist_norm:
            report_bad_assumption('ENAMETOOLONG workaround needed directory content normalization to succeed')
            TRACE('[ENAMETOOLONG workaround] Found the child %r (normalized: %r) in directory %r', basename, basename_norm, path)
            return
        dirlist_normcase = set((hfsplus_casefold(name) for name in dirlist_norm))
        if basename_normcase in dirlist_normcase:
            TRACE('[ENAMETOOLONG workaround] Found the child %r (case-folded: %r) in directory %r ', basename, basename_normcase, path)
            report_bad_assumption('ENAMETOOLONG workaround needed case-folding to succeed')
            return
        report_bad_assumption('ENOENT inferred using ENAMETOOLONG workaround (not our bug; just for stats)')
        TRACE('[ENAMETOOLONG workaround] Inferring ENOENT for path %r (basename %r not found in parent dir %r)', orig_path, basename, path)
        raise FileNotFoundError(errno.ENOENT, 'ENOENT inferred using ENAMETOOLONG workaround', unicode(orig_path).encode('utf-8'))

    def __normalize_path(self, path):
        return self.__normalize_path_batch([path])[0]

    def __normalize_path_batch(self, paths):
        pool = NSAutoreleasePool.alloc().init()
        try:
            results = []
            for path in paths:
                assert isinstance(path, unicode)
                s = NSString.alloc().initWithString_(path).autorelease()
                ret = s.fileSystemRepresentation()
                results.append(ret.decode('UTF-8'))

            return results
        finally:
            del pool
