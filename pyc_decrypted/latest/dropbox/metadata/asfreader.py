#Embedded file name: dropbox/metadata/asfreader.py
from __future__ import absolute_import
from __future__ import with_statement
import binascii
import struct
MAIN_HEADER_BYTES = 30
HEADER_BYTES = 24
FIELD_TYPES = {'string': struct.pack('!B', 1),
 'binary': struct.pack('!B', 2)}

def parse_guid(string, binary = False):
    endian = '>'
    if not binary:
        endian = '<'
        string = binascii.a2b_hex(string)
    return struct.unpack(endian + 'IHH8s', string)


HEADERS = {'ASF_Header_Object': parse_guid('75B22630668E11CFA6D900AA0062CE6C'),
 'ASF_Content_Description_Object': parse_guid('75B22633668E11CFA6D900AA0062CE6C'),
 'ASF_Stream_Properties_Object': parse_guid('B7DC0791A9B711CF8EE600C00C205365'),
 'ASF_Audio_Media': parse_guid('F8699E405B4D11CFA8FD00805F5C442B'),
 'ASF_Video_Media': parse_guid('BC19EFC05B4D11CFA8FD00805F5C442B')}

def read_asf(file_obj):
    raw_header = file_obj.read(MAIN_HEADER_BYTES)
    if len(raw_header) < MAIN_HEADER_BYTES:
        raise ValueError('Not enough header bytes for asf')
    guid, size, total_headers, r1, r2 = struct.unpack('<16sQIBB', raw_header)
    if parse_guid(guid, binary=True) != HEADERS['ASF_Header_Object']:
        raise ValueError('Corrupt header')
    toret = {}
    for i in range(total_headers):
        ret = _read_header(file_obj)
        toret.update(ret)

    return {'asf': toret}


def _read_header(file_obj):
    header_data = file_obj.read(24)
    if len(header_data) < 24:
        raise ValueError('Incomplete or corrupt header')
    guid, size = struct.unpack('<16sQ', header_data)
    guid = parse_guid(guid, binary=True)
    end_header = file_obj.tell() + size - 24
    toret = {}
    try:
        if guid == HEADERS['ASF_Content_Description_Object']:
            header_content = file_obj.read(size - 24)
            boundaries = list(struct.unpack('<5H', header_content[:10]))
            for i in range(1, 5):
                boundaries[i] += boundaries[i - 1]

            toret = {}
            keys = ['title',
             'artist',
             'copyright',
             'caption',
             'rating']
            left = 0
            for i in range(5):
                right = boundaries[i]
                if left == right:
                    continue
                toret[keys[i]] = header_content[10 + left:10 + right].replace('\x00', '').strip()
                left = right

        elif guid == HEADERS['ASF_Stream_Properties_Object']:
            stream_header = file_obj.read(16)
            stream_guid = parse_guid(stream_header, binary=True)
            file_obj.seek(32, 1)
            header_content = file_obj.read(2)
            flags = struct.unpack('<H', header_content)[0]
            stream_number = flags & 127
            file_obj.seek(4, 1)
            key = 'track%03d' % stream_number
            if stream_guid == HEADERS['ASF_Audio_Media']:
                toret = {key: FIELD_TYPES['binary'] + stream_header + file_obj.read(16)}
            elif stream_guid == HEADERS['ASF_Video_Media']:
                toret = {key: FIELD_TYPES['binary'] + stream_header + file_obj.read(8)}
    except IndexError:
        pass
    finally:
        file_obj.seek(end_header, 0)
        return toret


def decode_binary_data(data):
    if data[0] == FIELD_TYPES['binary']:
        stream_guid = parse_guid(data[1:17], binary=True)
        if stream_guid == HEADERS['ASF_Video_Media']:
            width, height = struct.unpack('<II', data[17:25])
            return {'width': width,
             'height': height}
        if stream_guid == HEADERS['ASF_Audio_Media']:
            codec, channels, sample_rate, bitrate, block, sample_bits = struct.unpack('<HHIIHH', data[17:33])
            return {'codec': codec,
             'channels': channels,
             'sample_rate': sample_rate,
             'bitrate': bitrate,
             'block': block,
             'sample_bits': sample_bits}
        raise ValueError('unrecognized stream type')
    else:
        return data


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as f:
        for k, v in read_asf(f).iteritems():
            print k, decode_binary_data(v)
