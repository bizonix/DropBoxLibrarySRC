#Embedded file name: dropbox/metadata/vorbis.py
from collections import defaultdict
import struct
from .utils import safe_read

def readVorbisComment(file_obj):
    toret = defaultdict(list)
    try:
        vendor_length = struct.unpack('<I', safe_read(file_obj, 4))[0]
        safe_read(file_obj, vendor_length)
        user_comment_list_length = struct.unpack('<I', safe_read(file_obj, 4))[0]
        for i in range(user_comment_list_length):
            length = struct.unpack('<I', safe_read(file_obj, 4))[0]
            comment = ''.join(struct.unpack('<%dc' % length, safe_read(file_obj, length)))
            k, v = comment.split('=')
            toret[k.lower()].append(v)

        return toret
    except Exception:
        return {}


def decodeBlockPicture(file_obj):
    try:
        pic_type, mime_length = struct.unpack('>II', safe_read(file_obj, 8))
        mime = ''.join(struct.unpack('>%dc' % mime_length, safe_read(file_obj, mime_length)))
        desc_length = struct.unpack('>I', safe_read(file_obj, 4))[0]
        description = unicode(''.join(struct.unpack('>%dc' % desc_length, safe_read(file_obj, desc_length))), 'utf-8')
        width, height, depth, colors, data_len = struct.unpack('>IIIII', safe_read(file_obj, 20))
        data = safe_read(file_obj, data_len)
        return {'type': pic_type,
         'mime': mime,
         'description': description,
         'width': width,
         'height': height,
         'depth': depth,
         'colors': colors,
         'data': data}
    except Exception:
        return {}


def readBlockPicture(file_obj):
    try:
        buf = ''
        buf += safe_read(file_obj, 8)
        pic_type, mime_length = struct.unpack('>II', buf[-8:])
        buf += safe_read(file_obj, mime_length)
        buf += safe_read(file_obj, 4)
        desc_length = struct.unpack('>I', buf[-4:])[0]
        buf += safe_read(file_obj, desc_length)
        buf += safe_read(file_obj, 20)
        width, height, depth, colors, data_len = struct.unpack('>IIIII', buf[-20:])
        buf += safe_read(file_obj, data_len)
        return {'metadata_block_picture': [buf]}
    except Exception:
        return {}
