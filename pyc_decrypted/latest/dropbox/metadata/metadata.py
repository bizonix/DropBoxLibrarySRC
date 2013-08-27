#Embedded file name: dropbox/metadata/metadata.py
from __future__ import with_statement
import base64
import contextlib
from collections import defaultdict
from asfreader import read_asf
from asfreader import decode_binary_data as decode_asf
from docxreader import read_docx
from EXIF import read_exif
from flacreader import read_flac
from id3reader import read_id3
from id3reader import decode_binary_data as decode_id3
from m4areader import read_mp4
from oggreader import read_ogg_flac, read_ogg_theora, read_ogg_vorbis
from pdfreader import read_pdf
from utils import normalize_metadata, contains_all_dict
WHITELIST = {'exif': {'EXIF DateTimeOriginal': {},
          'EXIF ExifImageLength': {},
          'EXIF ExifImageWidth': {},
          'Image Make': {},
          'Image Model': {},
          'Image Orientation': {},
          'GPS GPSAltitude': {},
          'GPS GPSAltitudeRef': {},
          'GPS GPSLatitude': {},
          'GPS GPSLatitudeRef': {},
          'GPS GPSLongitude': {},
          'GPS GPSLongitudeRef': {}},
 'id3': {'album': {},
         'artist': {},
         'comment': {},
         'genre': {},
         'title': {},
         'track': {},
         'year': {},
         'v1title': {},
         'v1performer': {},
         'v1album': {},
         'v1year': {},
         'v1comment': {},
         'v1genre': {},
         'TRCK': {},
         'TIT2': {},
         'TPE1': {},
         'TYER': {},
         'TCON': {},
         'COMM': {},
         'TCOM': {},
         'TCOP': {},
         'TOPE': {},
         'TENC': {},
         'WXXX': {}},
 'asf': {'artist': {},
         'caption': {},
         'copyright': {},
         'rating': {},
         'title': {},
         'track001': {}},
 'flac': {'album': {},
          'artist': {},
          'comment': {},
          'date': {},
          'genre': {},
          'title': {},
          'tracknumber': {}},
 'oga': {'album': {},
         'artist': {},
         'comment': {},
         'date': {},
         'genre': {},
         'title': {},
         'tracknumber': {}},
 'ogg': {'album': {},
         'artist': {},
         'comment': {},
         'date': {},
         'genre': {},
         'title': {},
         'tracknumber': {}},
 'm4a': {base64.b64encode('moov.udta.meta.ilst.\xa9alb'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9ART'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9cmt'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9day'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9gen'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9grp'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9lyr'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9nam'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9too'): {'base64encoded': True},
         base64.b64encode('moov.udta.meta.ilst.\xa9wrt'): {'base64encoded': True},
         'moov.udta.meta.ilst.aART': {},
         'moov.udta.meta.ilst.catg': {},
         'moov.udta.meta.ilst.covr': {},
         'moov.udta.meta.ilst.cpil': {},
         'moov.udta.meta.ilst.cprt': {},
         'moov.udta.meta.ilst.desc': {},
         'moov.udta.meta.ilst.disk': {},
         'moov.udta.meta.ilst.egid': {},
         'moov.udta.meta.ilst.gnre': {},
         'moov.udta.meta.ilst.keyw': {},
         'moov.udta.meta.ilst.pcst': {},
         'moov.udta.meta.ilst.purd': {},
         'moov.udta.meta.ilst.purl': {},
         'moov.udta.meta.ilst.rtng': {},
         'moov.udta.meta.ilst.tmpo': {},
         'moov.udta.meta.ilst.trkn': {},
         'moov.udta.meta.ilst.tven': {},
         'moov.udta.meta.ilst.tves': {},
         'moov.udta.meta.ilst.tvnn': {},
         'moov.udta.meta.ilst.tvsh': {},
         'moov.udta.meta.ilst.tvsn': {},
         'ftyp': {}},
 'ogv': {'album': {},
         'artist': {},
         'comment': {},
         'date': {},
         'fps': {},
         'genre': {},
         'height': {},
         'title': {},
         'tracknumber': {},
         'width': {}},
 'pdf': {'Author': {},
         'CreationDate': {},
         'Creator': {},
         'ModDate': {},
         'Producer': {},
         'Title': {}},
 'docx': {'application': {},
          'appversion': {},
          'category': {},
          'characters': {},
          'characterswithspaces': {},
          'company': {},
          'contenttype': {},
          'created': {},
          'creator': {},
          'description': {},
          'docsecurity': {},
          'identifier': {},
          'keywords': {},
          'language': {},
          'lastmodifiedby': {},
          'lastprinted': {},
          'lines': {},
          'modified': {},
          'notes': {},
          'pages': {},
          'paragraphs': {},
          'revision': {},
          'scalecrop': {},
          'shareddoc': {},
          'subject': {},
          'template': {},
          'title': {},
          'totaltime': {},
          'version': {},
          'words': {}}}

def metadata_extractor(reader_func):

    def metadata_func(f, whitelist = None):
        return normalize_metadata(reader_func(f), whitelist)

    return metadata_func


def metadata_extractor_whitelist(reader_func):

    def metadata_func(f, whitelist = None):
        return normalize_metadata(reader_func(f, whitelist), whitelist)

    return metadata_func


EXTRACTORS = dict((('asf', metadata_extractor(read_asf)),
 ('docx', metadata_extractor(read_docx)),
 ('flac', metadata_extractor(read_flac)),
 ('id3', metadata_extractor(read_id3)),
 ('oga', metadata_extractor(read_ogg_flac)),
 ('ogg', metadata_extractor(read_ogg_vorbis)),
 ('ogv', metadata_extractor(read_ogg_theora)),
 ('pdf', metadata_extractor(read_pdf)),
 ('exif', metadata_extractor_whitelist(read_exif)),
 ('m4a', metadata_extractor_whitelist(read_mp4))))

def metadata_plats():
    return EXTRACTORS.keys()


@contextlib.contextmanager
def reset_file_cursor(fileobj):
    old_pos = fileobj.tell()
    try:
        yield
    finally:
        fileobj.seek(old_pos, 0)


def get_metadata_for_plat(plat, file_obj, whitelist = WHITELIST):
    with reset_file_cursor(file_obj):
        file_obj.seek(0, 0)
        return _decode_all_attrs(EXTRACTORS[plat](file_obj, whitelist))


def get_whitelisted_metadata(file_obj, whitelist = WHITELIST, handlerfunc = None):
    dict_to_ret = {}
    with reset_file_cursor(file_obj):
        for plat, extractor in EXTRACTORS.iteritems():
            if plat not in whitelist:
                continue
            file_obj.seek(0, 0)
            try:
                data = extractor(file_obj, whitelist)
            except ValueError:
                pass
            except Exception:
                if handlerfunc:
                    handlerfunc()
            else:
                if data:
                    dict_to_ret.update(data)

    return dict_to_ret


def get_all_metadata(file_obj):
    whitelist = {}
    for plat in EXTRACTORS:
        whitelist[plat] = contains_all_dict()

    return get_whitelisted_metadata(file_obj, whitelist)


def get_encoded_metadata(file_obj):
    toret = {}
    for plat, plat_dict in get_all_metadata(file_obj).iteritems():
        new_plat = {}
        for k, v in plat_dict.iteritems():
            try:
                k.decode('ascii')
            except UnicodeDecodeError:
                new_plat[base64.b64encode(k)] = v
            else:
                new_plat[k] = v

        if new_plat:
            toret[plat] = new_plat

    return toret


DECODERS = {'asf': decode_asf,
 'id3': decode_id3}

def _decode_all_attrs(toret):
    for plat, plat_attrs in toret.iteritems():
        for k, v in plat_attrs.iteritems():
            try:
                v = DECODERS[plat](v)
            except KeyError:
                pass

            toret[plat][k] = v

    return toret


def get_decoded_metadata(file_obj, whitelist = WHITELIST):
    toret = get_whitelisted_metadata(file_obj, whitelist)
    return _decode_all_attrs(toret)
