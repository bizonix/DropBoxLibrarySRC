#Embedded file name: dropbox/sync_engine_arch/macosx/_folder_tagger.py
from __future__ import with_statement
import contextlib
import MacOS
import Carbon.Icons
from Carbon.Icn import ReadIconFromFSRef
from Carbon.Files import fsRdWrPerm
from Carbon.Res import FSCreateResFile, FSOpenResFile, Handle, GetResource, Get1Resource, UseResFile, Resource, SetResLoad, CloseResFile
from pymac.helpers.finder import FinderInfoEditor
from dropbox.mac.version import LEOPARD, MAC_VERSION
import dropbox.fsutil as fsutil
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError, NotADirectoryError
from dropbox.trace import TRACE, unhandled_exc_handler
ICON_TAGS = {'dropbox': 'DropboxFolderIcon.icns',
 'public': 'public.icns',
 'photos': 'photos.icns',
 'shared': 'shared.icns',
 'sandbox': 'sandbox.icns',
 'camerauploads': 'camerauploads.icns'}
if MAC_VERSION >= LEOPARD:
    for k in ICON_TAGS.keys():
        ICON_TAGS[k] = ICON_TAGS[k].split('.icns')[0] + '_leopard.icns'

class FolderTagger(FinderInfoEditor):

    def __init__(self, icon_folder, fs):
        super(type(self), self).__init__()
        self._tags_to_icon_data = {}
        self.fs = fs
        self.icon_folder = icon_folder

    def get_folder_ns(self, path):
        try:
            with fsutil.DotDropboxFile(self.fs, path, 'r') as f:
                try:
                    return long(f.read().strip())
                except Exception:
                    unhandled_exc_handler()
                    return

        except FileNotFoundError:
            return
        except Exception:
            unhandled_exc_handler()
            return

    def tag_folder(self, target_path, tag, to_ns = None):
        self.fs.opendir(target_path).close()
        target_pathu = unicode(target_path)
        if to_ns is not None:
            if self.get_folder_ns(target_path) != to_ns:
                with fsutil.DotDropboxFile(self.fs, target_path, 'w') as f:
                    fn = self.fs.make_path(f.name)
                    TRACE('Adding namespace file: %r', fn)
                    f.write('%s\n' % to_ns)
                    self.set_invisible(unicode(fn))
        iconr_path = target_path.join(u'Icon\r')
        iconr_pathu = unicode(iconr_path)
        if not fsutil.is_exists(self.fs, iconr_path):
            FSCreateResFile(target_pathu, u'Icon\r')
        self.set_invisible(iconr_pathu)
        try:
            rf = FSOpenResFile(iconr_pathu, fsRdWrPerm)
        except Exception:
            try:
                self.fs.remove(iconr_path)
            except FileNotFoundError:
                pass

            FSCreateResFile(target_pathu, u'Icon\r')
            self.set_invisible(iconr_pathu)
            rf = FSOpenResFile(iconr_pathu, fsRdWrPerm)

        try:
            try:
                icon_data = self._tags_to_icon_data[tag]
            except KeyError:
                target_icon = ReadIconFromFSRef(unicode(self.icon_folder.join(ICON_TAGS[tag])))
                target_icon.AutoDispose(1)
                icon_data = target_icon.data
                self._tags_to_icon_data[tag] = icon_data

            UseResFile(rf)
            try:
                existing_icon = Get1Resource(Carbon.Icons.kIconFamilyType, Carbon.Icons.kCustomIconResource)
            except MacOS.Error as e:
                if e.args[0] == -192:
                    pass
                else:
                    unhandled_exc_handler()
            except Exception:
                unhandled_exc_handler()
            else:
                if icon_data == existing_icon.data:
                    if not self.has_custom_icon(target_pathu):
                        self.set_custom_icon(target_pathu)
                    return
                existing_icon.RemoveResource()
                existing_icon.AutoDispose(1)
                del existing_icon

            TRACE('TAG FOLDER: %r, %r, %r', target_path, tag, to_ns)
            toadd = Handle(icon_data)
            UseResFile(rf)
            toadd.AddResource(Carbon.Icons.kIconFamilyType, Carbon.Icons.kCustomIconResource, '\\p')
            toadd.AutoDispose(0)
        finally:
            CloseResFile(rf)

        self.set_custom_icon(target_pathu)

    def untag_folder(self, target_path, preserve_nsfile = False):
        TRACE('UNTAG FOLDER: %r %r', target_path, preserve_nsfile)
        if not preserve_nsfile:
            with fsutil.DotDropboxFile(self.fs, target_path, 'w', open_file=False) as f:
                fn = self.fs.make_path(f.name)
                TRACE('Removing namespace file: %r', fn)
                try:
                    self.fs.remove(fn)
                except (FileNotFoundError, NotADirectoryError):
                    TRACE('Namespace file was already gone!')
                except Exception:
                    unhandled_exc_handler()

        iconr_path = target_path.join(u'Icon\r')
        TRACE('Removing Icon\\r file: %r', iconr_path)
        try:
            self.fs.remove(iconr_path)
        except (FileNotFoundError, NotADirectoryError):
            TRACE('Icon\\r file was already gone!')
        except Exception:
            unhandled_exc_handler()

        try:
            self.set_custom_icon(unicode(target_path))
        except Exception:
            unhandled_exc_handler()
