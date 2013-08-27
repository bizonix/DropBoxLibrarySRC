#Embedded file name: dropbox/metadata/m4areader.py
from __future__ import with_statement
import struct
import base64
from collections import defaultdict
from utils import safe_read
FLAGS = CONTAINER, IGNORE, XTAGITEM, FTYP_HEADER, METADATA = [ 2 ** _ for _ in xrange(5) ]
CALLBACK = XTAGITEM
FLAGS.append(CALLBACK)
TAGTYPES = (('ftyp', FTYP_HEADER),
 ('moov', CONTAINER),
 ('mdat', IGNORE),
 ('udta', CONTAINER),
 ('meta', METADATA),
 ('ilst', CONTAINER),
 ('stbl', IGNORE),
 ('free', IGNORE),
 ('trak', CONTAINER),
 ('----', XTAGITEM),
 ('mdia', CONTAINER),
 ('minf', CONTAINER))
RATING_TYPES = {0: 'None',
 2: 'Clean',
 4: 'Explicit'}
MEDIA_TYPES = {0: 'Movie',
 1: 'Normal',
 2: 'Audio Book',
 6: 'Music Video',
 9: 'Movie',
 10: 'TV Show',
 11: 'Booklet',
 14: 'Ringtone'}
GENRE_TYPES = {1: 'Blues',
 2: 'Classic Rock',
 3: 'Country',
 4: 'Dance',
 5: 'Disco',
 6: 'Funk',
 7: 'Grunge',
 8: 'Hip-Hop',
 9: 'Jazz',
 10: 'Metal',
 11: 'New Age',
 12: 'Oldies',
 13: 'Other',
 14: 'Pop',
 15: 'R&B',
 16: 'Rap',
 17: 'Reggae',
 18: 'Rock',
 19: 'Techno',
 20: 'Industrial',
 21: 'Alternative',
 22: 'Ska',
 23: 'Death Metal',
 24: 'Pranks',
 25: 'Soundtrack',
 26: 'Euro-Techno',
 27: 'Ambient',
 28: 'Trip-Hop',
 29: 'Vocal',
 30: 'Jazz+Funk',
 31: 'Fusion',
 32: 'Trance',
 33: 'Classical',
 34: 'Instrumental',
 35: 'Acid',
 36: 'House',
 37: 'Game',
 38: 'Sound Clip',
 39: 'Gospel',
 40: 'Noise',
 41: 'AlternRock',
 42: 'Bass',
 43: 'Soul',
 44: 'Punk',
 45: 'Space',
 46: 'Meditative',
 47: 'Instrumental Pop',
 48: 'Instrumental Rock',
 49: 'Ethnic',
 50: 'Gothic',
 51: 'Darkwave',
 52: 'Techno-Industrial',
 53: 'Electronic',
 54: 'Pop-Folk',
 55: 'Eurodance',
 56: 'Dream',
 57: 'Southern Rock',
 58: 'Comedy',
 59: 'Cult',
 60: 'Gangsta',
 61: 'Top 40',
 62: 'Christian Rap',
 63: 'Pop/Funk',
 64: 'Jungle',
 65: 'Native American',
 66: 'Cabaret',
 67: 'New Wave',
 68: 'Psychadelic',
 69: 'Rave',
 70: 'Showtunes',
 71: 'Trailer',
 72: 'Lo-Fi',
 73: 'Tribal',
 74: 'Acid Punk',
 75: 'Acid Jazz',
 76: 'Polka',
 77: 'Retro',
 78: 'Musical',
 79: 'Rock & Roll',
 80: 'Hard Rock',
 81: 'Folk',
 82: 'Folk/Rock',
 83: 'National Folk',
 84: 'Swing',
 85: 'Fast Fusion',
 86: 'Bebob',
 87: 'Latin',
 88: 'Revival',
 89: 'Celtic',
 90: 'Bluegrass',
 91: 'Avantgarde',
 92: 'Gothic Rock',
 93: 'Progressive Rock',
 94: 'Psychedelic Rock',
 95: 'Symphonic Rock',
 96: 'Slow Rock',
 97: 'Big Band',
 98: 'Chorus',
 99: 'Easy Listening',
 100: 'Acoustic',
 101: 'Humour',
 102: 'Speech',
 103: 'Chanson',
 104: 'Opera',
 105: 'Chamber Music',
 106: 'Sonata',
 107: 'Symphony',
 108: 'Booty Bass',
 109: 'Primus',
 110: 'Porn Groove',
 111: 'Satire',
 112: 'Slow Jam',
 113: 'Club',
 114: 'Tango',
 115: 'Samba',
 116: 'Folklore',
 117: 'Ballad',
 118: 'Power Ballad',
 119: 'Rhythmic Soul',
 120: 'Freestyle',
 121: 'Duet',
 122: 'Punk Rock',
 123: 'Drum Solo',
 124: 'A Capella',
 125: 'Euro-House',
 126: 'Dance Hall'}
FIELD_TYPES = {'text': 0,
 'int': 1,
 'genre': 2,
 'ratio': 3,
 'packed': 4,
 'packedratio': 5,
 'packedint': 6,
 'packedshort': 7,
 'packedbool': 8,
 'art': 9,
 'rating': 10,
 'mediatype': 11,
 'quicktime_text': 12}
DATA_TYPES = {'moov.udta.meta.ilst.\xa9alb': 'text',
 'moov.udta.meta.ilst.\xa9ART': 'text',
 'moov.udta.meta.ilst.\xa9cmt': 'text',
 'moov.udta.meta.ilst.\xa9day': 'text',
 'moov.udta.meta.ilst.\xa9enc': 'text',
 'moov.udta.meta.ilst.\xa9gen': 'text',
 'moov.udta.meta.ilst.\xa9grp': 'text',
 'moov.udta.meta.ilst.\xa9lyr': 'text',
 'moov.udta.meta.ilst.\xa9nam': 'text',
 'moov.udta.meta.ilst.\xa9too': 'text',
 'moov.udta.meta.ilst.\xa9wrt': 'text',
 'moov.udta.meta.ilst.aART': 'packed',
 'moov.udta.meta.ilst.apID': 'packed',
 'moov.udta.meta.ilst.catg': 'packed',
 'moov.udta.meta.ilst.cnID': 'packedint',
 'moov.udta.meta.ilst.covr': 'art',
 'moov.udta.meta.ilst.cpil': 'packedbool',
 'moov.udta.meta.ilst.cprt': 'packed',
 'moov.udta.meta.ilst.desc': 'packed',
 'moov.udta.meta.ilst.disk': 'packedratio',
 'moov.udta.meta.ilst.gnre': 'genre',
 'moov.udta.meta.ilst.grup': 'text',
 'moov.udta.meta.ilst.hdvd': 'packedbool',
 'moov.udta.meta.ilst.ldes': 'packed',
 'moov.udta.meta.ilst.keyw': 'packed',
 'moov.udta.meta.ilst.pcst': 'packedbool',
 'moov.udta.meta.ilst.pgap': 'packedbool',
 'moov.udta.meta.ilst.purd': 'packed',
 'moov.udta.meta.ilst.rtng': 'rating',
 'moov.udta.meta.ilst.soaa': 'packed',
 'moov.udta.meta.ilst.soal': 'packed',
 'moov.udta.meta.ilst.soar': 'packed',
 'moov.udta.meta.ilst.soco': 'packed',
 'moov.udta.meta.ilst.sonm': 'packed',
 'moov.udta.meta.ilst.sosn': 'packed',
 'moov.udta.meta.ilst.stik': 'mediatype',
 'moov.udta.meta.ilst.tmpo': 'packedshort',
 'moov.udta.meta.ilst.trkn': 'ratio',
 'moov.udta.meta.ilst.tven': 'packed',
 'moov.udta.meta.ilst.tves': 'packedint',
 'moov.udta.meta.ilst.tvnn': 'packed',
 'moov.udta.meta.ilst.tvsh': 'packed',
 'moov.udta.meta.ilst.tvsn': 'packedint',
 'moov.udta.meta.ilst.xid ': 'packed',
 'ftyp': 'text',
 'com.apple.quicktime.camera.framereadouttimeinmicroseconds': 'int',
 'moov.udta.\xa9arg': 'quicktime_text',
 'moov.udta.\xa9ark': 'quicktime_text',
 'moov.udta.\xa9cok': 'quicktime_text',
 'moov.udta.\xa9com': 'quicktime_text',
 'moov.udta.\xa9cpy': 'quicktime_text',
 'moov.udta.\xa9day': 'quicktime_text',
 'moov.udta.\xa9dir': 'quicktime_text',
 'moov.udta.\xa9fmt': 'quicktime_text',
 'moov.udta.\xa9inf': 'quicktime_text',
 'moov.udta.\xa9isr': 'quicktime_text',
 'moov.udta.\xa9lab': 'quicktime_text',
 'moov.udta.\xa9lal': 'quicktime_text',
 'moov.udta.\xa9mak': 'quicktime_text',
 'moov.udta.\xa9mal': 'quicktime_text',
 'moov.udta.\xa9mod': 'quicktime_text',
 'moov.udta.\xa9nak': 'quicktime_text',
 'moov.udta.\xa9nam': 'quicktime_text',
 'moov.udta.\xa9pdk': 'quicktime_text',
 'moov.udta.\xa9phg': 'quicktime_text',
 'moov.udta.\xa9prd': 'quicktime_text',
 'moov.udta.\xa9prf': 'quicktime_text',
 'moov.udta.\xa9prk': 'quicktime_text',
 'moov.udta.\xa9prl': 'quicktime_text',
 'moov.udta.\xa9req': 'quicktime_text',
 'moov.udta.\xa9snk': 'quicktime_text',
 'moov.udta.\xa9snm': 'quicktime_text',
 'moov.udta.\xa9src': 'quicktime_text',
 'moov.udta.\xa9swf': 'quicktime_text',
 'moov.udta.\xa9swk': 'quicktime_text',
 'moov.udta.\xa9swr': 'quicktime_text',
 'moov.udta.\xa9wrt': 'quicktime_text',
 'moov.udta.\xa9xyz': 'quicktime_text'}
flagged = {}
for flag in FLAGS:
    flagged[flag] = frozenset((_[0] for _ in TAGTYPES if _[1] & flag))

def _xtra(s):
    offset = 0
    result = {}
    while offset < len(s):
        atomsize = struct.unpack('!i', s[offset:offset + 4])[0]
        atomtype = s[offset + 4:offset + 8]
        if atomtype == 'data':
            result[atomtype] = s[offset + 16:offset + atomsize]
        else:
            result[atomtype] = s[offset + 12:offset + atomsize]
        offset += atomsize

    return result


class InvalidFormatError(Exception):
    pass


def _read_next_size(fp):
    sizedat = fp.read(4)
    if len(sizedat) != 4:
        raise InvalidFormatError('Invalid atom size: %r' % (sizedat,))
    atomsize = struct.unpack('!i', sizedat)[0]
    if atomsize < 8:
        raise InvalidFormatError('Invalid atom size: %r' % (atomsize,))
    return atomsize


def _read_next_type(fp):
    atomtype = fp.read(4)
    if len(atomtype) != 4:
        raise InvalidFormatError('Invalid atom: %r' % (atomtype,))
    return atomtype


def _analyse(fp, offset0, offset1, whitelist, atomname = '', uid_list = None):
    if uid_list == None:
        uid_list = []
    keycounts = defaultdict(int)
    offset = offset0
    while offset < offset1:
        fp.seek(offset)
        atomsize = _read_next_size(fp)
        atomtype = _read_next_type(fp)
        try:
            newatomname = atomname + atomtype
            newuid = uid_list + [keycounts[atomtype]]
            keycounts[atomtype] += 1
            if atomtype in flagged[CONTAINER] or atomtype in flagged[METADATA] or newatomname not in whitelist:
                data = ''
            elif atomtype not in flagged[IGNORE]:
                fp.seek(offset + 8)
                if atomtype in flagged[XTAGITEM]:
                    data = _xtra(safe_read(fp, atomsize - 8))
                elif atomtype in flagged[FTYP_HEADER]:
                    data = safe_read(fp, atomsize - 8)[:4]
                else:
                    data = safe_read(fp, atomsize - 8)
            if data:
                data = decode_data_by_atomname(newatomname, data)
            if atomtype not in flagged[IGNORE]:
                yield (generate_full_atom_name(newatomname, newuid),
                 newatomname,
                 atomsize,
                 data)
            if atomtype in flagged[METADATA]:
                for reply in _parse_meta_tag(fp, offset + 8, offset + atomsize, whitelist, newatomname + '.', newuid):
                    yield reply

            if atomtype in flagged[CONTAINER]:
                for reply in _analyse(fp, offset + 8, offset + atomsize, whitelist, newatomname + '.', newuid):
                    yield reply

        except InvalidFormatError:
            pass

        offset += atomsize


def _parse_meta_hdlr(fp, offset0):
    fp.seek(offset0)
    try:
        atomsize = _read_next_size(fp)
    except InvalidFormatError:
        sizedat = fp.read(4)
        if len(sizedat) != 4:
            raise InvalidFormatError('Invalid atom size: %r' % (sizedat,))
        atomsize = struct.unpack('!i', sizedat)[0]
        offset0 += 4

    atomtype = _read_next_type(fp)
    if atomtype != 'hdlr':
        raise InvalidFormatError('Expected hdlr tag for meta, got %r' % atomtype)
    flags = struct.unpack('!ii', fp.read(8))
    if flags != (0, 0):
        raise InvalidFormatError('Expected 8 null bytes in hdlr parser, got %r' % repr(flags))
    handler_type = fp.read(4)
    vendor, empty, empty = struct.unpack('!4s4s4s', fp.read(12))
    name = fp.read(atomsize - 32)
    ret = (handler_type,
     vendor,
     name,
     offset0 + atomsize)
    return ret


def _parse_meta_keys(fp):
    flags = struct.unpack('!i', fp.read(4))
    if flags != (0,):
        raise InvalidFormatError('Expected 4 null bytes in keys parser, got %r' % repr(flags))
    toret = []
    keycount = struct.unpack('!i', fp.read(4))[0]
    for i in range(keycount):
        key_size = struct.unpack('!i', fp.read(4))[0]
        namespace = fp.read(4)
        key_value = fp.read(key_size - 8)
        toret.append(key_value)

    return toret


def _parse_item_atom(fp, offset, offset1):
    toret = []
    while offset < offset1:
        fp.seek(offset)
        atomsize = _read_next_size(fp)
        atomtype = _read_next_type(fp)
        if atomtype == 'data':
            typelocale = fp.read(8)
            toret.append(fp.read(atomsize - 16))
        offset += atomsize

    return toret


def _parse_meta_ilst(fp, offset, offset1):
    toret = {}
    while offset < offset1:
        fp.seek(offset)
        atomsize = _read_next_size(fp)
        atomtype = _read_next_type(fp)
        toret[struct.unpack('!i', atomtype)[0]] = _parse_item_atom(fp, offset + 8, offset + atomsize)
        offset += atomsize

    return toret


HANDLER_TYPE = 0
HANDLER_VENDOR = 1
HANDLER_NAME = 2
HANDLER_END_OFFSET = 3

def _parse_meta_tag(fp, offset0, offset1, whitelist, atomname = '', uid_list = None):
    hdlr = _parse_meta_hdlr(fp, offset0)
    if hdlr[HANDLER_TYPE] == 'mdta':
        keys = None
        ilst = None
        offset = hdlr[HANDLER_END_OFFSET]
        while offset < offset1:
            fp.seek(offset)
            atomsize = _read_next_size(fp)
            atomtype = _read_next_type(fp)
            if atomtype == 'keys':
                keys = _parse_meta_keys(fp)
            elif atomtype == 'ilst':
                ilst = _parse_meta_ilst(fp, offset + 8, offset + atomsize)
            offset += atomsize

        if keys and ilst:
            for k, v in ilst.iteritems():
                atomname = keys[k - 1]
                data = decode_data_by_atomname(atomname, v[0])
                yield (atomname,
                 atomname,
                 len(data),
                 data)

    elif hdlr[HANDLER_TYPE] == 'mdir':
        for reply in _analyse(fp, hdlr[HANDLER_END_OFFSET], offset1, whitelist, atomname, uid_list):
            yield reply

    else:
        raise InvalidFormatError('Cannot find handler for this metadata tag')


def generate_full_atom_name(atomname, uid):
    return '%s,%s' % (atomname, '.'.join((str(_) for _ in uid)))


def mp4_atoms(fp, whitelist):
    if fp.read(8)[4:] not in ('ftyp', 'moov', '  jp'):
        raise InvalidFormatError()
    fp.seek(0, 2)
    for atom in _analyse(fp, 0, fp.tell(), whitelist):
        yield atom


def parseDataAtom(dat, offset = 0, strictlength = True):
    if len(dat) < offset + 8:
        raise InvalidFormatError('Binary packed field < 8 in length')
    length = struct.unpack('!I', dat[offset:4 + offset])[0]
    checkLength = len(dat) == offset + length if strictlength else len(dat) >= offset + length
    if not (checkLength and dat[offset + 4:offset + 8] == 'data' and length > 16):
        raise InvalidFormatError('Length of binary packed field does not match')
    atomversion, flag1, flag2, flag3 = struct.unpack('!bbbb', dat[offset + 8:offset + 12])
    return (dat[offset + 16:offset + length], offset + length)


def parseArt(data):
    arts = []
    offset = 0
    while offset < len(data):
        try:
            cur, offset = parseDataAtom(data, offset, strictlength=False)
            arts.append(cur)
        except InvalidFormatError:
            break

    return arts


def decode_data_by_atomname(atomname, data, offset = 0):
    if atomname in DATA_TYPES:
        return _decode_binary_data(FIELD_TYPES[DATA_TYPES[atomname]], data, offset)
    return data


def _decode_binary_data(field_type, data, offset = 0):

    def ratio(dat):
        if dat[2] != 0:
            return '%d/%d' % (dat[1], dat[2])
        return '%d' % dat[1]

    if field_type == FIELD_TYPES['text']:
        if len(data) > offset + 8 and data[offset + 4:offset + 8] == 'data':
            field_type = FIELD_TYPES['packed']
        else:
            return data[offset:]
    if field_type == FIELD_TYPES['quicktime_text']:
        return data[offset + 4:]
    if field_type == FIELD_TYPES['int']:
        return '%d' % struct.unpack('!i', data[offset:])[0]
    if field_type == FIELD_TYPES['ratio']:
        data = struct.unpack('!HHHH', parseDataAtom(data, offset)[0])
        return ratio(data)
    if field_type == FIELD_TYPES['packed']:
        return parseDataAtom(data, offset)[0]
    if field_type == FIELD_TYPES['packedratio']:
        data = struct.unpack('!HHH', parseDataAtom(data, offset)[0])
        return ratio(data)
    if field_type == FIELD_TYPES['packedint']:
        return '%d' % struct.unpack('!I', parseDataAtom(data, offset)[0])[0]
    if field_type == FIELD_TYPES['packedshort']:
        return '%d' % struct.unpack('!H', parseDataAtom(data, offset)[0])[0]
    if field_type == FIELD_TYPES['packedbool']:
        return bool(struct.unpack('!c', parseDataAtom(data, offset)[0])[0])
    if field_type == FIELD_TYPES['genre']:
        try:
            flag = struct.unpack('!H', parseDataAtom(data, offset)[0])[0]
            return GENRE_TYPES[flag]
        except Exception:
            return data

    if field_type == FIELD_TYPES['rating']:
        return RATING_TYPES[struct.unpack('!B', parseDataAtom(data, offset)[0])[0]]
    if field_type == FIELD_TYPES['mediatype']:
        return MEDIA_TYPES[struct.unpack('!B', parseDataAtom(data, offset)[0])[0]]
    if field_type == FIELD_TYPES['art']:
        return data[offset:]
    raise InvalidFormatError('Cannot determine type of this tag')


def decode_binary_data(packeddata):
    if len(packeddata) < 4:
        raise InvalidFormatError('Field type not in data')
    field_type = struct.unpack('!I', packeddata[:4])[0]
    return _decode_binary_data(field_type, packeddata, offset=4)


def mp4_metadata(file_obj, whitelist):
    try:
        toret = {}
        for atomtype, raw_type, atomsize, val in mp4_atoms(file_obj, whitelist):
            go = False
            if raw_type not in whitelist:
                tag = base64.b64encode(raw_type)
                try:
                    _idict = whitelist[tag]
                except:
                    pass
                else:
                    go = _idict.get('base64encoded', False)
                    tag = base64.b64encode(atomtype)

            else:
                tag = atomtype
                go = True
            if go:
                try:
                    if isinstance(val, unicode):
                        val = val.encode('utf-8')
                    elif type(val) is not str:
                        val = str(val)
                except Exception as e:
                    raise ValueError(str(e))
                else:
                    toret[tag] = val

        return toret
    except InvalidFormatError as e:
        raise ValueError(str(e))


def read_mp4(file_obj, whitelist):
    try:
        whitelist = whitelist['m4a']
    except KeyError:
        return {'m4a': {}}

    try:
        toret = defaultdict(list)
        for atomtype, raw_type, atomsize, val in mp4_atoms(file_obj, whitelist):
            if 'moov.udta.meta.ilst.covr' == raw_type:
                for data in parseArt(val):
                    toret[raw_type].append(data)

            else:
                try:
                    if val:
                        toret[raw_type].append(val)
                except ValueError:
                    continue

        return {'m4a': dict(toret)}
    except InvalidFormatError as e:
        raise ValueError(str(e))
