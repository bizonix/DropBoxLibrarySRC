#Embedded file name: Crypto/Cipher/blockalgo.py
import sys
if sys.version_info[0] == 2 and sys.version_info[1] == 1:
    from Crypto.Util.py21compat import *
from Crypto.Util.py3compat import *
MODE_ECB = 1
MODE_CBC = 2
MODE_CFB = 3
MODE_PGP = 4
MODE_OFB = 5
MODE_CTR = 6
MODE_OPENPGP = 7

def _getParameter(name, index, args, kwargs, default = None):
    param = kwargs.get(name)
    if len(args) > index:
        if param:
            raise ValueError("Parameter '%s' is specified twice" % name)
        param = args[index]
    return param or default


class BlockAlgo:

    def __init__(self, factory, key, *args, **kwargs):
        self.mode = _getParameter('mode', 0, args, kwargs, default=MODE_ECB)
        self.block_size = factory.block_size
        if self.mode != MODE_OPENPGP:
            self._cipher = factory.new(key, *args, **kwargs)
            self.IV = self._cipher.IV
        else:
            self._done_first_block = False
            self._done_last_block = False
            self.IV = _getParameter('iv', 1, args, kwargs)
            if not self.IV:
                raise ValueError('MODE_OPENPGP requires an IV')
            IV_cipher = factory.new(key, MODE_CFB, b('\x00') * self.block_size, segment_size=self.block_size * 8)
            if len(self.IV) == self.block_size:
                self._encrypted_IV = IV_cipher.encrypt(self.IV + self.IV[-2:] + b('\x00') * (self.block_size - 2))[:self.block_size + 2]
            elif len(self.IV) == self.block_size + 2:
                self._encrypted_IV = self.IV
                self.IV = IV_cipher.decrypt(self.IV + b('\x00') * (self.block_size - 2))[:self.block_size + 2]
                if self.IV[-2:] != self.IV[-4:-2]:
                    raise ValueError('Failed integrity check for OPENPGP IV')
                self.IV = self.IV[:-2]
            else:
                raise ValueError('Length of IV must be %d or %d bytes for MODE_OPENPGP' % (self.block_size, self.block_size + 2))
            self._cipher = factory.new(key, MODE_CFB, self._encrypted_IV[-self.block_size:], segment_size=self.block_size * 8)

    def encrypt(self, plaintext):
        if self.mode == MODE_OPENPGP:
            padding_length = (self.block_size - len(plaintext) % self.block_size) % self.block_size
            if padding_length > 0:
                if self._done_last_block:
                    raise ValueError('Only the last chunk is allowed to have length not multiple of %d bytes', self.block_size)
                self._done_last_block = True
                padded = plaintext + b('\x00') * padding_length
                res = self._cipher.encrypt(padded)[:len(plaintext)]
            else:
                res = self._cipher.encrypt(plaintext)
            if not self._done_first_block:
                res = self._encrypted_IV + res
                self._done_first_block = True
            return res
        return self._cipher.encrypt(plaintext)

    def decrypt(self, ciphertext):
        if self.mode == MODE_OPENPGP:
            padding_length = (self.block_size - len(ciphertext) % self.block_size) % self.block_size
            if padding_length > 0:
                if self._done_last_block:
                    raise ValueError('Only the last chunk is allowed to have length not multiple of %d bytes', self.block_size)
                self._done_last_block = True
                padded = ciphertext + b('\x00') * padding_length
                res = self._cipher.decrypt(padded)[:len(ciphertext)]
            else:
                res = self._cipher.decrypt(ciphertext)
            return res
        return self._cipher.decrypt(ciphertext)
