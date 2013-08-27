#Embedded file name: dropbox/dropbox_helper_installer.py
from __future__ import absolute_import
import POW
import hashlib
import struct
from hashlib import sha256

class NoSignature(Exception):
    pass


class BadSignature(Exception):
    pass


MAGIC = 14401537
VERSION = 3
PUBLICKEY = '\n-----BEGIN RSA PUBLIC KEY-----\nMIIBCAKCAQEAs24msupO4460ViJDTX4qbdqcosjkDKyjW8ZseZ8fm54hXUPwZz7V\nLinFS3M6mjjKnAH81dNb3u3KnKadQ/8eHQXIjvmVPGSGHhCc7PRon30wQZYH/azQ\na+ld27xKdzxiB1zK9f2/uzV5sgs7QUhJdcqIpMXMWAyH7MbsU8g+YEXu/Mz0yZv6\nrAHkupNWoddd7+AjEAeKvlKjOM805+pwedjN3FKnAWSWIIzJJZk76loXoboub/RB\nPmN83HNJdmFmDda0AY8qWtgS+DX/xEaipbCvda33ZHt/pIhfwl0Wq8RPN7cdS6DE\nW4qbB0qxBdOF/Wt5JJmGEIXiKHH/udTuIwIBBQ==\n-----END RSA PUBLIC KEY-----\n'
DIGESTTYPE = POW.SHA256_DIGEST

def encode_str(b):
    return b + struct.pack('!L', len(b))


def gen_signature(f, keys):
    sha_digest = sha256()
    data = f.read(4096)
    while data:
        sha_digest.update(data)
        data = f.read(4096)

    digest_output = sha_digest.digest()
    out = ''
    for key in keys:
        out += encode_str(key.sign(digest_output, DIGESTTYPE))

    out += struct.pack('!LLL', len(keys), VERSION, MAGIC)
    return out


class HeaderReader(object):

    def __init__(self, f):
        self.f = f
        f.seek(0, 2)
        self.cur = f.tell()

    def read_int(self):
        self.f.seek(self.cur - 4, 0)
        self.cur -= 4
        return struct.unpack('!L', self.f.read(4))[0]

    def read_string(self):
        len = self.read_int()
        self.f.seek(self.cur - len, 0)
        self.cur -= len
        return self.f.read(len)


def read_header_info(f):
    r = HeaderReader(f)
    if r.read_int() != MAGIC:
        raise NoSignature()
    v = r.read_int()
    if v > VERSION or v < 3:
        raise BadSignature()
    num_sigs = r.read_int()
    sigs = []
    for i in xrange(num_sigs):
        sigs.append(r.read_string())

    end = r.cur
    f.seek(0)
    sha_digest = sha256()
    return dict(version=v, digest=sha_digest, sigs=sigs, end=end)


def verify_signature(info):
    pub_key = POW.pemRead(POW.RSA_PUBLIC_KEY, PUBLICKEY)
    d = info['digest'].digest()
    signed = False
    for sig in info['sigs']:
        try:
            pub_key.verify(sig, d, POW.SHA256_DIGEST)
            signed = True
            break
        except Exception as e:
            error = e

    if signed:
        return True
    raise error
