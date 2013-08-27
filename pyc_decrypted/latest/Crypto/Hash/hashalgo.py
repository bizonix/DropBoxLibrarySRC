#Embedded file name: Crypto/Hash/hashalgo.py
from binascii import hexlify

class HashAlgo:
    digest_size = None
    block_size = None

    def __init__(self, hashFactory, data = None):
        if hasattr(hashFactory, 'new'):
            self._hash = hashFactory.new()
        else:
            self._hash = hashFactory()
        if data:
            self.update(data)

    def update(self, data):
        return self._hash.update(data)

    def digest(self):
        return self._hash.digest()

    def hexdigest(self):
        return self._hash.hexdigest()

    def copy(self):
        return self._hash.copy()

    def new(self, data = None):
        pass
