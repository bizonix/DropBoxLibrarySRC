#Embedded file name: dropbox/sync_engine_arch/linux/_folder_tagger.py
from __future__ import with_statement, absolute_import
import cPickle as pickle
from dropbox import fsutil
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.safebuiltinunpickler import SafeBuiltInUnpickler
from dropbox.sync_engine_file_system.exceptions import FileNotFoundError

class LinuxFolderTagger(object):

    def __init__(self, fs, shell_touch):
        self.fs = fs
        self.shell_touch = shell_touch

    def get_folder_ns(self, path):
        try:
            with fsutil.DotDropboxFile(self.fs, path, 'r') as f:
                try:
                    return SafeBuiltInUnpickler.load(f)[u'ns']
                except pickle.UnpicklingError:
                    unhandled_exc_handler()
                    return

        except (KeyError, FileNotFoundError):
            return
        except Exception as e:
            if not isinstance(e, OSError) and not isinstance(e, IOError):
                unhandled_exc_handler()
            return

    def tag_folder(self, path, tag, to_ns = None):
        with fsutil.DotDropboxFile(self.fs, path, 'w') as f:
            to_write = {u'tag': tag}
            if to_ns:
                to_write[u'ns'] = to_ns
            pickle.dump(to_write, f)
        self.shell_touch(path)

    def untag_folder(self, path, preserve_nsfile = False):
        with fsutil.DotDropboxFile(self.fs, path, 'r+') as f:
            try:
                read_tag = SafeBuiltInUnpickler.load(f)
            except pickle.UnpicklingError:
                unhandled_exc_handler()
                read_tag = {}

            try:
                del read_tag[u'tag']
            except KeyError:
                pass

            if not preserve_nsfile:
                try:
                    del read_tag[u'ns']
                except KeyError:
                    pass

            if not read_tag:
                fn = self.fs.make_path(f.name)
                try:
                    TRACE('Removing namespace file: %r', fn)
                    self.fs.remove(fn)
                except FileNotFoundError:
                    pass
                except Exception:
                    unhandled_exc_handler()
                else:
                    return

            f.seek(0)
            pickle.dump(read_tag, f)
        self.shell_touch(path)
