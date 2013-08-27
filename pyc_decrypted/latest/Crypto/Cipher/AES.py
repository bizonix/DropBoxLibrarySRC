#Embedded file name: Crypto/Cipher/AES.py
__revision__ = '$Id$'
from Crypto.Cipher import blockalgo
from Crypto.Cipher import _AES

class AESCipher(blockalgo.BlockAlgo):

    def __init__(self, key, *args, **kwargs):
        blockalgo.BlockAlgo.__init__(self, _AES, key, *args, **kwargs)


def new(key, *args, **kwargs):
    return AESCipher(key, *args, **kwargs)


MODE_ECB = 1
MODE_CBC = 2
MODE_CFB = 3
MODE_PGP = 4
MODE_OFB = 5
MODE_CTR = 6
MODE_OPENPGP = 7
block_size = 16
key_size = (16, 24, 32)
