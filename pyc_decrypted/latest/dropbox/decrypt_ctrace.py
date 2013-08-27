#Embedded file name: dropbox/decrypt_ctrace.py
from __future__ import absolute_import
import os
import struct
xor_size = 4
rand_max = 2 ** (8 * xor_size) - 1
packing = '<I'

def myrand(rand_state):
    while True:
        rand_state = rand_state * 1103515245 & rand_max
        rand_state = rand_state + 12345 & rand_max
        yield rand_state


def decrypt_ctrace(full_path):
    rand = myrand(int(os.path.basename(full_path), 2 ** xor_size))
    with open(full_path, 'rb') as f:
        read = ''
        while True:
            while len(read) < xor_size:
                chunk = f.read(len(read) - xor_size)
                if not chunk:
                    return
                read += chunk

            unpacked = struct.unpack(packing, read[:xor_size])[0]
            xored = (unpacked ^ rand.next()) % rand_max
            packed = struct.pack(packing, xored)
            yield packed
            read = read[xor_size:]


if __name__ == '__main__':
    import sys
    assert os.path.exists(sys.argv[1]), "log doesn't exist?"
    for chunk in decrypt_ctrace(sys.argv[1]):
        sys.stdout.write(chunk)
