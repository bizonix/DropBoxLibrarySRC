#Embedded file name: dropbox/camera/util.py
import os
from contextlib import contextmanager
from datetime import datetime
from .filetypes import image_or_video, nonphoto_image
from dropbox.debugging import easy_repr
from dropbox.fastwalk_bridge import fastwalk_with_exception_handling
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.sync_engine_file_system.constants import FILE_TYPE_REGULAR

class OnDiskFile(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('id', '_name', '_size', '_time', '_path')

    def __init__(self, id, name, size, mtime, path):
        self.id = id
        self._name = name
        self._size = size
        self._time = mtime
        self._path = path

    def __repr__(self):
        return easy_repr(self, *self.__slots__)

    @contextmanager
    def open(self, fs, *n, **kw):
        with fs.open(self._path, 'r') as fobj:
            yield fobj.read

    def name(self):
        return self._name

    def size(self):
        return self._size

    def time(self):
        return self._time


def is_apple_device(device):
    if not device.model:
        return False
    return any((name in device.model for name in ('iPhone', 'iPad')))


_NOKIA_IMAGES_PATH = os.path.join(u'Images', u'Camera')
_NOKIA_VIDEOS_PATH = os.path.join(u'Videos')

def find_dcim(srcpath):
    paths = []
    dcim_path = os.path.join(srcpath, u'DCIM')
    nokia_images = os.path.join(srcpath, _NOKIA_IMAGES_PATH)
    nokia_videos = os.path.join(srcpath, _NOKIA_VIDEOS_PATH)
    if os.path.isdir(nokia_images) and os.path.isdir(nokia_videos):
        TRACE('This is a suspected Symbian device')
        paths += [_NOKIA_IMAGES_PATH, _NOKIA_VIDEOS_PATH]
    if os.path.exists(dcim_path) and os.path.isdir(dcim_path):
        paths.append(u'DCIM')
        for path in [os.path.join(u'PRIVATE', u'AVCHD', u'BDMV', u'STREAM'),
         u'SD_VIDEO',
         u'VIDEO',
         u'MP_ROOT']:
            full_path = os.path.join(srcpath, path)
            if os.path.exists(full_path) and os.path.isdir(full_path):
                paths.append(path)

    if paths:
        return paths


def get_images(root, paths, blacklist_nonphotos = False, is_path_hidden = None, is_filename_hidden = None):
    if is_path_hidden is None:
        is_path_hidden = lambda x: None
    if is_filename_hidden is None:
        is_filename_hidden = lambda x: None
    if paths is None:
        paths = [u'']
    for path in paths:
        srcpath = os.path.join(root, path)
        TRACE('Getting all images in %s', srcpath)
        walker = fastwalk_with_exception_handling(srcpath, no_atime=True)
        for dirpath, ents in walker:
            skip = False
            while True:
                dirname = os.path.basename(dirpath)
                try:
                    hidden = is_path_hidden(dirpath)
                except Exception:
                    unhandled_exc_handler()
                    hidden = False

                if hidden or len(dirname) > 0 and dirname[0] == '.' or os.path.exists(os.path.join(dirpath, '.nomedia')):
                    try:
                        TRACE('Directory %r is hidden.  Skipping to next dir', dirpath)
                        dirpath, ents = walker.send(True)
                    except StopIteration:
                        skip = True
                        break
                    except Exception:
                        unhandled_exc_handler()
                        skip = True
                        break

                else:
                    break

            if skip:
                continue
            TRACE('Searching directory %r for images', dirpath)
            for dirent in ents:
                if dirent.type != FILE_TYPE_REGULAR:
                    continue
                try:
                    srcfilepath = os.path.join(dirpath, dirent.name)
                    try:
                        hidden = is_path_hidden(srcfilepath) or is_filename_hidden(dirent.name)
                    except Exception:
                        unhandled_exc_handler()
                        hidden = False

                    if hidden:
                        TRACE('Skipping hidden file %s', srcfilepath)
                        continue
                    if not image_or_video(dirent.name) or blacklist_nonphotos and nonphoto_image(dirent.name):
                        TRACE('Skipping %s, not photo or video', srcfilepath)
                        continue
                    try:
                        st_mtime = os.stat(srcfilepath).st_mtime
                        if st_mtime < 0:
                            raise Exception('st_mtime for file(%r) is negative (%r), the m_time will be invalid' % (srcfilepath, st_mtime))
                        mtime = datetime.fromtimestamp(st_mtime)
                    except Exception:
                        TRACE('!! Unable to get the mtime on this file: %r', srcfilepath)
                        unhandled_exc_handler()
                        mtime = None

                    fobj = OnDiskFile(id=srcfilepath, name=srcfilepath[len(root):], size=os.path.getsize(srcfilepath), mtime=mtime, path=srcfilepath)
                    TRACE('Got %r', fobj)
                    yield fobj
                except Exception:
                    unhandled_exc_handler()
                    continue
