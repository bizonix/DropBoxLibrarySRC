#Embedded file name: Crypto/Random/__init__.py
__revision__ = '$Id$'
__all__ = ['new']
from Crypto.Random import OSRNG
from Crypto.Random import _UserFriendlyRNG

def new(*args, **kwargs):
    return _UserFriendlyRNG.new(*args, **kwargs)


def atfork():
    _UserFriendlyRNG.reinit()


def get_random_bytes(n):
    return _UserFriendlyRNG.get_random_bytes(n)
