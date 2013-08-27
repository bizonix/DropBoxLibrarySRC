#Embedded file name: Crypto/Random/Fortuna/FortunaAccumulator.py
__revision__ = '$Id$'
import sys
if sys.version_info[0] == 2 and sys.version_info[1] == 1:
    from Crypto.Util.py21compat import *
from Crypto.Util.py3compat import *
from binascii import b2a_hex
import time
import warnings
from Crypto.pct_warnings import ClockRewindWarning
import SHAd256
import FortunaGenerator

class FortunaPool(object):
    digest_size = SHAd256.digest_size

    def __init__(self):
        self.reset()

    def append(self, data):
        self._h.update(data)
        self.length += len(data)

    def digest(self):
        return self._h.digest()

    def hexdigest(self):
        if sys.version_info[0] == 2:
            return b2a_hex(self.digest())
        else:
            return b2a_hex(self.digest()).decode()

    def reset(self):
        self._h = SHAd256.new()
        self.length = 0


def which_pools(r):
    assert r >= 1
    retval = []
    mask = 0
    for i in range(32):
        if r & mask == 0:
            retval.append(i)
        else:
            break
        mask = mask << 1 | 1L

    return retval


class FortunaAccumulator(object):
    min_pool_size = 64
    reseed_interval = 0.1

    def __init__(self):
        self.reseed_count = 0
        self.generator = FortunaGenerator.AESGenerator()
        self.last_reseed = None
        self.pools = [ FortunaPool() for i in range(32) ]
        assert self.pools[0] is not self.pools[1]

    def random_data(self, bytes):
        current_time = time.time()
        if self.last_reseed is not None and self.last_reseed > current_time:
            warnings.warn('Clock rewind detected. Resetting last_reseed.', ClockRewindWarning)
            self.last_reseed = None
        if self.pools[0].length >= self.min_pool_size and (self.last_reseed is None or current_time > self.last_reseed + self.reseed_interval):
            self._reseed(current_time)
        return self.generator.pseudo_random_data(bytes)

    def _reseed(self, current_time = None):
        if current_time is None:
            current_time = time.time()
        seed = []
        self.reseed_count += 1
        self.last_reseed = current_time
        for i in which_pools(self.reseed_count):
            seed.append(self.pools[i].digest())
            self.pools[i].reset()

        seed = b('').join(seed)
        self.generator.reseed(seed)

    def add_random_event(self, source_number, pool_number, data):
        assert 1 <= len(data) <= 32
        assert 0 <= source_number <= 255
        assert 0 <= pool_number <= 31
        self.pools[pool_number].append(bchr(source_number))
        self.pools[pool_number].append(bchr(len(data)))
        self.pools[pool_number].append(data)
