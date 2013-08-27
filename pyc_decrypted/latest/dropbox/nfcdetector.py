#Embedded file name: dropbox/nfcdetector.py
from __future__ import absolute_import
from unicodedata import normalize
try:
    from unicodedata import is_normalized
except ImportError:

    def is_normalized(mode, s):
        return normalize(mode, s) == s


def is_nfc(x):
    return is_normalized('NFC', x)


def is_nfd(x):
    return is_normalized('NFD', x)
