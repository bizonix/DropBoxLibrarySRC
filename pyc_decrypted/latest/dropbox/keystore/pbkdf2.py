#Embedded file name: dropbox/keystore/pbkdf2.py
import sys
import hmac
from struct import pack
import hashlib

def pbkdf2(password, salt, itercount, keylen, hashfn = hashlib.sha1):
    try:
        digest_size = hashfn().digest_size
    except TypeError:
        digest_size = hashfn.digest_size

    l = keylen / digest_size
    if keylen % digest_size != 0:
        l += 1
    h = hmac.new(password, None, hashfn)
    T = ''
    for i in range(1, l + 1):
        T += pbkdf2_F(h, salt, itercount, i)

    return T[0:keylen]


def xorstr(a, b):
    if len(a) != len(b):
        raise ValueError('xorstr(): lengths differ')
    return ''.join((chr(ord(x) ^ ord(y)) for x, y in zip(a, b)))


def prf(h, data):
    hm = h.copy()
    hm.update(data)
    return hm.digest()


def pbkdf2_F(h, salt, itercount, blocknum):
    U = prf(h, salt + pack('>i', blocknum))
    T = U
    for i in range(2, itercount + 1):
        U = prf(h, U)
        T = xorstr(T, U)

    return T
