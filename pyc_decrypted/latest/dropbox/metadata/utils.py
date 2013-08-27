#Embedded file name: dropbox/metadata/utils.py
import base64
MAX_METADATA_LENGTH = 100000

class contains_all_dict(object):

    def __contains__(self, elem):
        return True


def safe_read(file_obj, length, offset = None):
    if length > MAX_METADATA_LENGTH:
        raise ValueError('Read too long: %d bytes' % length)
    data = file_obj.read(length)
    if len(data) < length:
        raise ValueError('Expected %d bytes; only %d bytes available' % (length, len(data)))
    if offset != None:
        return (data, offset + length)
    return data


def encode_value(val):
    toret = val
    if isinstance(val, unicode):
        toret = val.encode('utf-8')
    elif type(val) is not str:
        toret = str(val)
    return toret


def normalize_metadata(attrs, whitelist):
    full_dict = {}
    for plat, plat_dict in attrs.iteritems():
        toret = {}
        try:
            plat_whitelist = whitelist[plat]
        except KeyError:
            continue
        else:
            if plat_whitelist is None or isinstance(plat_whitelist, contains_all_dict):
                toret = attrs[plat]
            else:
                for tag in plat_whitelist:
                    try:
                        val = attrs[plat][tag]
                        if val is not None:
                            toret[tag] = val
                    except KeyError:
                        if 'base64encoded' in plat_whitelist[tag] and plat_whitelist[tag]['base64encoded']:
                            decoded_tag = base64.b64decode(tag)
                            try:
                                val = attrs[plat][decoded_tag]
                                if val is not None:
                                    toret[tag] = val
                            except KeyError:
                                pass

            if toret:
                full_dict[plat] = to_encoded_dict(toret)

    return full_dict


def to_utf8_str(val):
    try:
        val = unicode(val, encoding='utf-8')
    except ValueError:
        try:
            val = unicode(val, encoding='utf-16')
        except ValueError:
            val = unicode(val, encoding='iso8859-1', errors='replace')

    return val.encode('utf-8')


def merge_list_defaultdicts(dest, other):
    for k, v in other.iteritems():
        dest[k].extend(v)


DELIM = ','

def to_encoded_dict(in_dict):
    toret = {}

    def assign(key, val):
        if val:
            toret[key] = encode_value(val)

    for key, val_list in in_dict.iteritems():
        if type(val_list) == list:
            if len(val_list) == 1:
                assign(key, val_list[0])
            else:
                for i, v in enumerate(val_list):
                    assign('%s%s%d' % (key, DELIM, i), v)

        else:
            assign(key, val_list)

    return toret


def from_encoded_dict(in_dict):
    toret = {}
    for full_key, val in in_dict.iteritems():
        try:
            key, num = full_key.split(DELIM)
            if key not in toret:
                toret[key] = []
            toret[key].append(val)
        except ValueError:
            toret[full_key] = val

    return toret


def split_metadata_key(full_key):
    try:
        key, num = full_key.split(DELIM)
        return key
    except ValueError:
        pass

    return full_key
