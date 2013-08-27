#Embedded file name: dropbox/sync_engine_arch/win/_folder_tagger.py
from __future__ import with_statement, absolute_import
import win32con
from dropbox.i18n import trans
from dropbox.win32.version import VISTA, WINDOWS_VERSION
import arch
from dropbox import fsutil
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError, create_file_not_found_error
from ._fschange import shell_touch
from ._path import GetFileAttributesW, SetFileAttributesW
from build_number import BUILD_KEY

class FolderTagger(object):

    def __init__(self, installpath, fs):
        self.fs = fs
        self.installpath = installpath
        self.desktop_ini_template = '[.ShellClassInfo]\nIconFile=%(path)s\n%(index)s\nInfoTip=%(infotip)s\n'
        self._cached_desktop_ini = {}
        self.desktop_ini_attr = win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM
        self.folder_attr = win32con.FILE_ATTRIBUTE_READONLY
        self.ns_file_attr = win32con.FILE_ATTRIBUTE_HIDDEN
        self.icon_tags = {'dropbox': ('%s.exe' % BUILD_KEY, 1001),
         'public': ('%s.exe' % BUILD_KEY, 1101),
         'photos': ('%s.exe' % BUILD_KEY, 1201),
         'shared': ('%s.exe' % BUILD_KEY, 1301),
         'sandbox': ('%s.exe' % BUILD_KEY, 1401),
         'camerauploads': ('%s.exe' % BUILD_KEY, 1501)}

    def get_folder_ns(self, path):
        try:
            with fsutil.DotDropboxFile(self.fs, path, 'r') as f:
                try:
                    val = long(f.read().strip())
                    TRACE('TEST get_folder_ns: %d', val)
                    return val
                except Exception:
                    unhandled_exc_handler()
                    return

        except FileNotFoundError:
            return
        except Exception:
            unhandled_exc_handler()
            return

    def tag_folder(self, target_path, tag, to_ns = None):
        if not fsutil.is_directory(self.fs, target_path):
            raise create_file_not_found_error(filename=target_path)
        target_pathu = unicode(target_path)
        desktop_ini_path = target_path.join(u'desktop.ini')
        try:
            if to_ns is not None:
                if self.get_folder_ns(target_path) != to_ns:
                    with fsutil.DotDropboxFile(self.fs, target_path, 'w') as f:
                        fn = self.fs.make_path(f.name)
                        TRACE('Adding namespace file: %r', fn)
                        f.write('%s\n' % to_ns)
                        if GetFileAttributesW(unicode(fn)) & self.ns_file_attr != self.ns_file_attr:
                            SetFileAttributesW(unicode(fn), self.ns_file_attr)
            try:
                text = self._cached_desktop_ini[tag]
            except KeyError:
                icon_file, icon_index = self.icon_tags[tag]
                if WINDOWS_VERSION >= VISTA:
                    icon_index += 1000
                text = self.desktop_ini_template % dict(path=unicode(self.installpath.join(icon_file)), index=icon_index and 'IconIndex=-%s' % icon_index or '', infotip=trans(arch.util.FOLDER_INFOTIP))
                text = text.encode('mbcs')
                self._cached_desktop_ini[tag] = text

            roll_over_existing = True
            try:
                with self.fs.open(desktop_ini_path, 'r') as f:
                    existing_text = f.read()
                    if existing_text == text:
                        attr = GetFileAttributesW(desktop_ini_path)
                        roll_over_existing = attr & self.desktop_ini_attr != self.desktop_ini_attr
            except FileNotFoundError:
                pass
            except Exception:
                unhandled_exc_handler()

            if roll_over_existing:
                try:
                    self.fs.remove(desktop_ini_path)
                except FileNotFoundError:
                    pass
                except Exception:
                    unhandled_exc_handler()

                try:
                    with self.fs.open(desktop_ini_path, 'w') as f:
                        f.write(text)
                    SetFileAttributesW(desktop_ini_path, self.desktop_ini_attr)
                except Exception:
                    unhandled_exc_handler()

            try:
                attr = GetFileAttributesW(target_pathu)
                if attr & self.folder_attr != self.folder_attr:
                    SetFileAttributesW(target_pathu, self.folder_attr)
                    roll_over_existing = True
            except Exception:
                unhandled_exc_handler()

            if roll_over_existing:
                try:
                    shell_touch(target_path)
                except Exception:
                    unhandled_exc_handler()

        except Exception:
            unhandled_exc_handler()

    def untag_folder(self, path, preserve_nsfile = False):
        if not preserve_nsfile:
            with fsutil.DotDropboxFile(self.fs, path, 'w', open_file=False) as f:
                try:
                    fn = self.fs.make_path(f.name)
                    SetFileAttributesW(unicode(fn), 0)
                    TRACE('Removing namespace file: %r', fn)
                    self.fs.remove(fn)
                except FileNotFoundError:
                    pass
                except Exception:
                    unhandled_exc_handler()

        desktop_ini_path = path.join(u'desktop.ini')
        try:
            SetFileAttributesW(desktop_ini_path, 0)
            self.fs.remove(desktop_ini_path)
            SetFileAttributesW(path, 0)
            shell_touch(path)
        except FileNotFoundError:
            pass
        except OSError:
            pass
        except Exception:
            unhandled_exc_handler()
