#Embedded file name: dropbox/metadata/transforms.py
from __future__ import with_statement
import contextlib
import os
import sys
import tempfile
from functools import partial
from metadata import get_metadata_for_plat
from EXIF import erase_thumbnail_ref, ExifWriter, ExifError
EXIF_IMAGE_ORIENTATION = 'Image Orientation'
EXIF_WHITELIST = {'exif': {'Image Orientation': {},
          'Thumbnail Orientation': {},
          'Thumbnail JPEGInterchangeFormat': {},
          'EXIF ExifImageLength': {},
          'EXIF ExifImageWidth': {},
          'TIFFThumbnail': {},
          'JPEGThumbnail': {}}}
JPEG_EXTS = set(['.jpg',
 '.jpeg',
 '.jfif',
 '.jif',
 '.jpe'])

class MissingTagError(Exception):
    pass


class BadThumbnailError(Exception):
    pass


class ThumbnailSizeError(Exception):
    pass


class NoRotationNeededError(Exception):
    pass


class UnknownOrientationError(Exception):
    pass


def umkstemp(dir = None, **kw):
    if dir is not None:
        dir = dir.encode(sys.getfilesystemencoding())
    f, tmp = tempfile.mkstemp(dir=dir, **kw)
    return (f, tmp.decode(sys.getfilesystemencoding()))


@contextlib.contextmanager
def tempfilename(**kw):
    f, fn = umkstemp(**kw)
    os.close(f)
    try:
        yield fn
    finally:
        if os.path.exists(fn):
            os.remove(fn)


try:
    import jpegtran
    JTRANSFORMS = {'2': jpegtran.FLIP_VERTICAL,
     '3': jpegtran.ROT_180,
     '4': jpegtran.FLIP_HORIZONTAL,
     '5': jpegtran.TRANSVERSE,
     '6': jpegtran.ROT_90,
     '7': jpegtran.TRANSPOSE,
     '8': jpegtran.ROT_270}
    from jpegtran import MalformedJpegError, PerfectTransformError

    def try_rotate_image_file(infile, ext = None, exif_attrs = None, on_success = None, on_error = None, cache_dir = None):
        if ext is None:
            ext = os.path.splitext(infile)[1]
        if ext.lower() not in JPEG_EXTS:
            event_result = 'badextension'
        elif exif_attrs is not None and EXIF_IMAGE_ORIENTATION not in exif_attrs:
            event_result = 'missingtag'
        else:
            try:
                with tempfilename(dir=cache_dir, prefix='rotate_image') as dummy_path:
                    event_result = _try_rotate_image_file(infile, dummy_path, metadata=exif_attrs, cache_dir=cache_dir)
                    if on_success is not None:
                        on_success(dummy_path)
            except ExifError:
                event_result = 'exiferror'
            except MalformedJpegError:
                event_result = 'malformedjpeg'
            except NoRotationNeededError:
                event_result = 'unneeded'
            except PerfectTransformError:
                event_result = 'lossy'
            except UnknownOrientationError:
                event_result = 'unknown_orientation'
            except IOError:
                event_result = 'ioerror'
            except Exception:
                if on_error is not None:
                    on_error()
                event_result = 'unknown'

        return event_result


    def _try_rotate_image_file(infile, outfile = None, metadata = None, cache_dir = None):
        if outfile is None:
            outfile = infile
        if metadata is None:
            with open(infile, 'rb') as f:
                try:
                    metadata = get_metadata_for_plat('exif', f, EXIF_WHITELIST)['exif']
                except KeyError:
                    raise MissingTagError('could not find exif data')

        try:
            orientation = metadata['Image Orientation']
        except KeyError:
            raise MissingTagError('could not find Image Orientation tag')

        if orientation == '1':
            raise NoRotationNeededError('Already right side up')
        if orientation not in JTRANSFORMS:
            raise UnknownOrientationError('Unknown orientation: %r' % orientation)
        if 'TIFFThumbnail' in metadata:
            raise BadThumbnailError('cannot rotate TIFF thumbnail')
        thumb_data = None
        if 'JPEGThumbnail' in metadata:
            if 'Thumbnail JPEGInterchangeFormat' not in metadata:
                raise BadThumbnailError('makernote thumbnail')
            thumb_orientation = metadata.get('Thumbnail Orientation', orientation)
            thumb_data = metadata['JPEGThumbnail']
            thumb_offset = int(metadata['Thumbnail JPEGInterchangeFormat'])
        _transform(JTRANSFORMS[orientation], infile, outfile)
        result = 'success'
        rotated_data = None
        orphan_thumbnail = False
        if thumb_data:
            try:
                rotated_data = _rotate_thumbnail(thumb_data, thumb_orientation, cache_dir=cache_dir)
            except ThumbnailSizeError:
                orphan_thumbnail = True
                result = 'orphaned_size'
            except UnknownOrientationError:
                orphan_thumbnail = True
                result = 'orphaned_bad_orientation'

        writer = ExifWriter()
        writer.register_fix_orientation()
        if orientation in ('5', '6', '7', '8') and 'EXIF ExifImageWidth' in metadata and 'EXIF ExifImageLength' in metadata:
            writer.register_fix_exif_width(int(metadata['EXIF ExifImageLength']))
            writer.register_fix_exif_length(int(metadata['EXIF ExifImageWidth']))
        if rotated_data:
            writer.register_fix_thumbnail(rotated_data, thumb_offset, len(thumb_data))
            if 'Thumbnail Orientation' in metadata:
                writer.register_fix_thumb_orientation()
        with open(outfile, 'r+b') as f:
            writer.commit_changes(f)
            if orphan_thumbnail:
                erase_thumbnail_ref(f)
        return result


    def _rotate_thumbnail(data, orientation, orig_size = None, cache_dir = None):
        if orientation == '1':
            return data
        if orientation not in JTRANSFORMS:
            raise UnknownOrientationError('Unknown orientation: %r' % orientation)
        if orig_size is None:
            orig_size = len(data)

        def check_output_size(filename):
            size = os.stat(filename).st_size
            if size <= orig_size:
                with open(filename, 'rb') as fout:
                    return fout.read()

        with tempfilename(dir=cache_dir, prefix='rotate_thumbnail_in') as infile:
            with open(infile, 'wb') as fin:
                fin.write(data)
            _transform_lossy(JTRANSFORMS[orientation], infile, infile)
            toret = check_output_size(infile)
            if toret:
                return toret
            with tempfilename(dir=cache_dir, prefix='rotate_thumbnail_out') as outfile:
                for quality in [100,
                 90,
                 70,
                 40,
                 10]:
                    _compress_lossy(quality, infile, outfile)
                    toret = check_output_size(outfile)
                    if toret:
                        return toret

                raise ThumbnailSizeError('could not rotate thumbnail to fit in %r', str(orig_size))


    def _call_with_unicode_filenames(func, infile, outfile):
        if isinstance(infile, unicode):
            infile = infile.encode(sys.getfilesystemencoding())
        if isinstance(outfile, unicode):
            outfile = outfile.encode(sys.getfilesystemencoding())
        func(infile, outfile)


    def _transform_lossy(transform, infile, outfile):
        _call_with_unicode_filenames(partial(jpegtran.transform_lossy, transform), infile, outfile)


    def _transform(transform, infile, outfile):
        _call_with_unicode_filenames(partial(jpegtran.transform, transform), infile, outfile)


    def _compress_lossy(quality, infile, outfile):
        _call_with_unicode_filenames(partial(jpegtran.compress_lossy, quality), infile, outfile)


except ImportError:

    def try_rotate_image_file(*n, **kw):
        raise NotImplementedError()


    def _try_rotate_image_file(*n, **kw):
        raise NotImplementedError()


    def _rotate_thumbnail(*n, **kw):
        raise NotImplementedError()


    class PerfectTransformError(Exception):
        pass


    class MalformedJpegError(Exception):
        pass
