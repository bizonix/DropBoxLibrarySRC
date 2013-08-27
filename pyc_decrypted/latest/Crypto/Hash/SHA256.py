#Embedded file name: Crypto/Hash/SHA256.py
_revision__ = '$Id$'
__all__ = ['new', 'digest_size', 'SHA256Hash']
from Crypto.Util.py3compat import *
from Crypto.Hash.hashalgo import HashAlgo
try:
    import hashlib
    hashFactory = hashlib.sha256
except ImportError:
    from Crypto.Hash import _SHA256
    hashFactory = _SHA256

class SHA256Hash(HashAlgo):
    oid = b('\x06\t`\x86H\x01e\x03\x04\x02\x01')
    digest_size = 32
    block_size = 64

    def __init__(self, data = None):
        HashAlgo.__init__(self, hashFactory, data)

    def new(self, data = None):
        return SHA256Hash(data)


def new(data = None):
    return SHA256Hash().new(data)


digest_size = SHA256Hash.digest_size
block_size = SHA256Hash.block_size
