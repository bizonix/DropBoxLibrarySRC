#Embedded file name: dropbox/sync_engine/p2p/api.py
from __future__ import absolute_import
import struct
import json
import zlib
from .faststr import AppendString
from collections import deque
from . import protocol
from dropbox.trace import TRACE, unhandled_exc_handler
P2PSAFETYTIMEOUT = 55.0

class WrongOrder(Exception):
    pass


def peerget(sync_engine, hval, namespaces, cb):
    if namespaces:
        namespaces = list(namespaces)
    p2p_state = sync_engine.p2p_state
    if not p2p_state or not p2p_state.p2p_loaded:
        TRACE('P2P Download requested before P2P Thread initialized. Skipping.')
        return
    if not p2p_state.p2p_enabled:
        TRACE('P2P disabled via preferences. Not P2P fetching.')
        return
    if not p2p_state.xsock:
        TRACE('No Socketpair! P2P disabled?')
        return
    try:
        return doPeerget(p2p_state, hval, namespaces, cb)
    except Exception as e:
        TRACE('SOCKETPAIR FOR P2P BROKEN! DISABLING P2P CLIENT! (server still active)')
        p2p_state.xsock = None
        unhandled_exc_handler()
        try:
            assert False, 'killed socketpair because: %s' % (e,)
        except:
            unhandled_exc_handler()

        return


def doPeerget(p2p_state, hval, namespaces, cb):
    if namespaces == None:
        try:
            raise Exception("Can't get from Namespace None!")
        except:
            unhandled_exc_handler()

        return
    protocol.cbdict[str(cb)] = cb
    TRACE('PEERGET requesting hval %s from namespaces %s' % (hval, namespaces))
    msg = json.dumps(('GET',
     hval,
     namespaces,
     str(cb)))
    out = struct.pack('!I', len(msg)) + msg
    p2p_state.xsock.send(out)
    data = p2p_state.xsock.recv(4)
    try:
        cmdlen = struct.unpack('!I', data)[0]
    except:
        raise Exception('expected string of length 4, got %s' % (data,))

    cbuf = AppendString()
    while len(cbuf) < cmdlen:
        data = p2p_state.xsock.recv(cmdlen - len(cbuf))
        if len(data) == 0:
            return
        cbuf += data

    try:
        cmd = json.loads(cbuf.getbuf())
    except:
        unhandled_exc_handler()
        TRACE('cbuflen %d, cmdlen %d' % (len(cbuf), cmdlen))
        return

    if cmd[0] == 'GETREPLY':
        if cmd[1] != hval:
            raise WrongOrder('INVALID GETREPLY %s, expected %s' % (cmd[1], hval))
        cbuf = protocol.hash_cache[hval]
        try:
            del protocol.hash_cache[hval]
        except:
            pass

        TRACE('P2P-Downloaded Hash: %s %d %d' % (hval, len(cbuf), cmdlen))
        try:
            pass
        except Exception:
            unhandled_exc_handler()

        return cbuf
    if cmd[0] == 'GETFAIL' or cmd[0] == 'HASFAIL':
        TRACE('Received %s %s' % (cmd[0], cmd[1]))
    else:
        TRACE('Unknown Reply: %s' % (cmd[0],))
    TRACE("Couldn't P2P-Download Hash %s" % (hval,))
