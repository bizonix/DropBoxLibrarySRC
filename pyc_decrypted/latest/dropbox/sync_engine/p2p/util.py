#Embedded file name: dropbox/sync_engine/p2p/util.py
import random
import socket
from dropbox.trace import TRACE, unhandled_exc_handler

def _socketpair():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for _i in ('SO_REUSEADDR', 'SO_REUSEPORT'):
        try:
            s.setsockopt(socket.SOL_SOCKET, getattr(socket, _i), 1)
        except AttributeError:
            pass
        except Exception:
            unhandled_exc_handler()

    targetPort = 19872
    success = False
    attempts = 0
    while attempts < 10:
        try:
            s.bind(('127.0.0.1', targetPort))
            s.listen(2)
            success = True
        except Exception:
            unhandled_exc_handler()
        else:
            break

        targetPort += random.choice(range(10, 200))
        attempts += 1

    if not success:
        TRACE('failed to get a port for the socketpair')
        return (None, None)
    TRACE('managed to get a port for the socketpair')
    try:
        s.setblocking(1)
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.setblocking(1)
        c.connect(('127.0.0.1', targetPort))
        nc, addr = s.accept()
        s.close()
        return (nc, c)
    except Exception:
        unhandled_exc_handler()
        return (None, None)


try:
    socketpair = socket.socketpair
except AttributeError:
    socketpair = _socketpair
