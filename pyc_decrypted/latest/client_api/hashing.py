#Embedded file name: client_api/hashing.py
import base64
import string
from binascii import b2a_base64
from hashlib import sha256
DROPBOX_HASH_LENGTH = 43
DROPBOX_MAX_BLOCK_SIZE = 4194304
_to_websafe = string.maketrans('+/', '-_')
_from_websafe = string.maketrans('-_~', '+/=')

def digest_to_base64(digest):
    return b2a_base64(digest)[:-2].translate(_to_websafe)


def base64_to_digest(b64_digest):
    return base64.decodestring(b64_digest.translate(_from_websafe) + '=')


def is_valid_blocklist(blocklist):
    try:
        return blocklist == '' or all((len(_hash) == DROPBOX_HASH_LENGTH for _hash in blocklist.split(',')))
    except (TypeError, AttributeError):
        return False


class DropboxHasher(object):
    __slots__ = ('d', 'total')

    def __init__(self):
        self.d = sha256()
        self.total = 0

    def update(self, data):
        self.d.update(data)
        self.total += len(data)

    def digest(self, data = None):
        if data:
            self.update(data)
        assert self.total <= DROPBOX_MAX_BLOCK_SIZE
        return b2a_base64(self.d.digest())[:-2].translate(_to_websafe)


class BetterDropboxHasher(object):

    def __init__(self):
        self.blocklist = []
        self.db_hash = sha256()
        self.db_hash_left = DROPBOX_MAX_BLOCK_SIZE

    def update(self, buf):
        offset = 0
        size = len(buf)
        while offset < size:
            db_left = min(self.db_hash_left, size - offset)
            self.db_hash.update(buffer(buf, offset, offset + db_left))
            self.db_hash_left -= db_left
            if not self.db_hash_left:
                self.blocklist.append(digest_to_base64(self.db_hash.digest()))
                self.db_hash_left = DROPBOX_MAX_BLOCK_SIZE
                self.db_hash = sha256()
            offset += db_left

    def digest(self):
        if self.db_hash_left < DROPBOX_MAX_BLOCK_SIZE:
            self.blocklist.append(digest_to_base64(self.db_hash.digest()))
        return ','.join(self.blocklist)


def dropbox_hash(contents):
    return DropboxHasher().digest(contents)
