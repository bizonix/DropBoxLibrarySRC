#Embedded file name: dropbox/metadata/flacreader.py
from __future__ import absolute_import
from __future__ import with_statement
from collections import defaultdict
import struct
from .utils import safe_read as _read
from .utils import merge_list_defaultdicts
from .vorbis import readVorbisComment, readBlockPicture
HEADERS = {'VORBIS_COMMENT': 4,
 'BLOCK_PICTURE': 6}

def _readMetadataHeader(file_obj, offset):
    header = {}
    data, offset = _read(file_obj, 4, offset)
    flags, i1, i2, i3 = struct.unpack('>BBBB', data)
    header['done'] = flags >> 7
    header['type'] = flags & 127
    header['length'] = (i1 << 16) + (i2 << 8) + i3
    return (header, offset)


def readMetadataBlock(file_obj, offset):
    toret = defaultdict(list)
    header, offset = _readMetadataHeader(file_obj, offset)
    if header['type'] == HEADERS['VORBIS_COMMENT']:
        toret = readVorbisComment(file_obj)
    elif header['type'] == HEADERS['BLOCK_PICTURE']:
        toret = readBlockPicture(file_obj)
    else:
        file_obj.seek(header['length'] + offset)
    return (toret, header['done'], header['length'] + offset)


def read_flac(file_obj):
    header, offset = _read(file_obj, 4, 0)
    if header != 'fLaC':
        raise ValueError('Not a valid flac file')
    toret, done, offset = readMetadataBlock(file_obj, offset)
    while not done:
        block, done, offset = readMetadataBlock(file_obj, offset)
        merge_list_defaultdicts(toret, block)

    return {'flac': dict(toret)}


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as f:
        for k, v in read_flac(f).iteritems():
            print k, v
