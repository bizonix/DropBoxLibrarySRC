#Embedded file name: dropbox/metadata/oggreader.py
from __future__ import absolute_import
from __future__ import with_statement
import cStringIO
import struct
from .utils import safe_read as _read
from .vorbis import readVorbisComment
from .flacreader import readMetadataBlock
CONTINUATION = 1
BOS = 2
EOS = 4

def peek_ogg_page(file_obj):
    start = file_obj.tell()
    toret = ''
    next_page = start
    try:
        data = _read(file_obj, 5)
        capture, version = struct.unpack('<4sB', data)
        if capture != 'OggS' or version != 0:
            raise ValueError('Not a valid ogg container')
        file_obj.seek(21, 1)
        data = _read(file_obj, 1)
        segments = struct.unpack('<B', data)[0]
        data = _read(file_obj, segments)
        segment_lengths = struct.unpack('<%dB' % segments, data)
        toret = _read(file_obj, 7)
        next_page = start + 27 + segments + sum((int(x) for x in segment_lengths))
    except Exception as e:
        raise e
    else:
        file_obj.seek(start)
        return (toret, next_page)


def read_ogg_page(file_obj):
    data = _read(file_obj, 27)
    capture, version, header_type, granule, serial, sequence, checksum, segments = struct.unpack('<4sBBQIIIB', data)
    if capture != 'OggS' or version != 0:
        raise ValueError('Not a valid ogg container')
    data = _read(file_obj, segments)
    segment_lengths = struct.unpack('<%dB' % segments, data)
    cur_packet_length = 0
    packet_lengths = []
    for segment in segment_lengths:
        cur_packet_length += segment
        if segment < 255:
            packet_lengths.append(cur_packet_length)
            cur_packet_length = 0

    if cur_packet_length > 0:
        packet_lengths.append(cur_packet_length)
        complete = False
    else:
        complete = True
    packets = []
    for packet_length in packet_lengths:
        data = _read(file_obj, packet_length)
        packets.append(data)

    return (packets, serial, complete)


def read_next_matching_packets(file_obj, serial):
    packets = ['']
    while True:
        new_packets, new_serial, new_complete = read_ogg_page(file_obj)
        if new_serial == serial:
            packets[-1] += new_packets[0]
            packets.extend(new_packets[1:])
            if new_complete or len(new_packets) > 1:
                break

    return packets


def find_capture_pattern(file_obj, pattern):
    capture, next_page = peek_ogg_page(file_obj)
    while not capture.startswith(pattern):
        file_obj.seek(next_page)
        capture, next_page = peek_ogg_page(file_obj)


def read_ogg_flac(file_obj):
    find_capture_pattern(file_obj, '\x7fFLAC')
    packets, serial, complete = read_ogg_page(file_obj)
    version1, version2, headers, signature = struct.unpack('>BBH4s', packets[0][5:13])
    if version1 != 1 or version2 != 0 or signature != 'fLaC':
        raise ValueError('malformed FLAC header')
    packets = read_next_matching_packets(file_obj, serial)
    fake_file = cStringIO.StringIO(packets[0])
    ret, done, offset = readMetadataBlock(fake_file, 0)
    return {'oga': dict(ret)}


def read_ogg_vorbis(file_obj):
    find_capture_pattern(file_obj, '\x01vorbis')
    packets, serial, complete = read_ogg_page(file_obj)
    packets = read_next_matching_packets(file_obj, serial)
    if not packets[0].startswith('\x03vorbis'):
        raise ValueError('Vorbis comment header not found')
    fake_file = cStringIO.StringIO(packets[0][7:])
    ret = readVorbisComment(fake_file)
    return {'ogg': dict(ret)}


def read_ogg_theora(file_obj):
    find_capture_pattern(file_obj, '\x80theora')
    packets, serial, complete = read_ogg_page(file_obj)
    vmaj, vmin, vrev, fmbw, fmbh, picw, pich, picx, picy, frn, frd, parn, pard, cs, nombr, flagss = struct.unpack('>BBBHH3s3sBBII3s3sB3s2s', packets[0][7:])
    if vmaj != 3 or vmin != 2:
        raise ValueError('Wrong version number')
    picw = (ord(picw[0]) << 16) + (ord(picw[1]) << 8) + (ord(picw[2]) << 0)
    pich = (ord(pich[0]) << 16) + (ord(pich[1]) << 8) + (ord(pich[2]) << 0)
    packets = read_next_matching_packets(file_obj, serial)
    if not packets[0].startswith('\x81theora'):
        raise ValueError('Theora comment header not found')
    fake_file = cStringIO.StringIO(packets[0][7:])
    ret = readVorbisComment(fake_file)
    ret['width'].append(str(picw))
    ret['height'].append(str(pich))
    ret['fps'].append('%d/%d' % (frn, frd))
    return {'ogv': dict(ret)}


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as f:
        try:
            for k, v in read_ogg_flac(f).iteritems():
                print k, v

        except Exception:
            pass

    with open(sys.argv[1], 'rb') as f:
        try:
            for k, v in read_ogg_vorbis(f).iteritems():
                print k, v

        except Exception:
            pass

    with open(sys.argv[1], 'rb') as f:
        try:
            for k, v in read_ogg_theora(f).iteritems():
                print k, v

        except Exception:
            pass
