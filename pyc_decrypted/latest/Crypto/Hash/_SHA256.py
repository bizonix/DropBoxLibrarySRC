#Embedded file name: Crypto/Hash/_SHA256.py
import sys
import os
import imp
found = False
for p in sys.path:
    if not os.path.isdir(p):
        continue
    f = os.path.join(p, 'Crypto.Hash._SHA256.so')
    if not os.path.exists(f):
        continue
    try:
        m = imp.load_dynamic(__name__, f)
    except ImportError:
        del sys.modules[__name__]
        raise

    sys.modules[__name__] = m
    found = True
    break

if not found:
    del sys.modules[__name__]
    raise ImportError, 'No module named %s' % __name__