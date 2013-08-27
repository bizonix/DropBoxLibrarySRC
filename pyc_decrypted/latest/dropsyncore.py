#Embedded file name: dropsyncore.py
import select
import socket
import sys
import time
import os
from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, ENOTCONN, ESHUTDOWN, EINTR, EISCONN, errorcode
socket_map = {}

class ExitNow(Exception):
    pass


def read(obj):
    try:
        obj.handle_read_event()
    except ExitNow:
        raise
    except:
        obj.handle_error()


def write(obj):
    try:
        obj.handle_write_event()
    except ExitNow:
        raise
    except:
        obj.handle_error()


def _exception(obj):
    try:
        obj.handle_expt_event()
    except ExitNow:
        raise
    except:
        obj.handle_error()


def readwrite(obj, flags):
    try:
        if flags & (select.POLLIN | select.POLLPRI):
            obj.handle_read_event()
        if flags & select.POLLOUT:
            obj.handle_write_event()
        if flags & (select.POLLERR | select.POLLHUP | select.POLLNVAL):
            obj.handle_expt_event()
    except ExitNow:
        raise
    except:
        obj.handle_error()


def poll(timeout = 0.0, map = None):
    if map is None:
        map = socket_map
    if map:
        r = []
        w = []
        e = []
        for fd, obj in map.items():
            is_r = obj.readable()
            is_w = obj.writable()
            if is_r:
                r.append(fd)
            if is_w:
                w.append(fd)
            if is_r or is_w:
                e.append(fd)

        if [] == r == w == e:
            time.sleep(timeout)
        else:
            try:
                r, w, e = select.select(r, w, e, timeout)
            except select.error as err:
                if err[0] != EINTR:
                    raise
                else:
                    return

        for fd in r:
            obj = map.get(fd)
            if obj is None:
                continue
            read(obj)

        for fd in w:
            obj = map.get(fd)
            if obj is None:
                continue
            write(obj)

        for fd in e:
            obj = map.get(fd)
            if obj is None:
                continue
            _exception(obj)


def poll2(timeout = 0.0, map = None):
    if map is None:
        map = socket_map
    if timeout is not None:
        timeout = int(timeout * 1000)
    pollster = select.poll()
    if map:
        for fd, obj in map.items():
            flags = 0
            if obj.readable():
                flags |= select.POLLIN | select.POLLPRI
            if obj.writable():
                flags |= select.POLLOUT
            if flags:
                flags |= select.POLLERR | select.POLLHUP | select.POLLNVAL
                pollster.register(fd, flags)

        try:
            r = pollster.poll(timeout)
        except select.error as err:
            if err[0] != EINTR:
                raise
            r = []

        for fd, flags in r:
            obj = map.get(fd)
            if obj is None:
                continue
            readwrite(obj, flags)


poll3 = poll2

def loop(timeout = 30.0, use_poll = False, map = None, count = None):
    if map is None:
        map = socket_map
    if use_poll and hasattr(select, 'poll'):
        poll_fun = poll2
    else:
        poll_fun = poll
    if count is None:
        while map:
            poll_fun(timeout, map)

    else:
        while map and count > 0:
            poll_fun(timeout, map)
            count = count - 1


class dispatcher:
    debug = False
    connected = False
    accepting = False
    closing = False
    addr = None

    def __init__(self, sock = None, map = None):
        if map is None:
            self._map = socket_map
        else:
            self._map = map
        if sock:
            self.set_socket(sock, map)
            self.socket.setblocking(0)
            self.connected = True
            try:
                self.addr = sock.getpeername()
            except socket.error:
                pass

        else:
            self.socket = None

    def __repr__(self):
        status = [self.__class__.__module__ + '.' + self.__class__.__name__]
        if self.accepting and self.addr:
            status.append('listening')
        elif self.connected:
            status.append('connected')
        if self.addr is not None:
            try:
                status.append('%s:%d' % self.addr)
            except TypeError:
                status.append(repr(self.addr))

        return '<%s at %#x>' % (' '.join(status), id(self))

    def add_channel(self, map = None):
        if map is None:
            map = self._map
        map[self._fileno] = self

    def del_channel(self, map = None):
        fd = self._fileno
        if map is None:
            map = self._map
        if fd in map:
            del map[fd]
        self._fileno = None

    def create_socket(self, family, type):
        self.family_and_type = (family, type)
        self.socket = socket.socket(family, type)
        self.socket.setblocking(0)
        self._fileno = self.socket.fileno()
        self.add_channel()

    def set_socket(self, sock, map = None):
        self.socket = sock
        self._fileno = sock.fileno()
        self.add_channel(map)

    def set_reuse_addr(self):
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR) | 1)
        except socket.error:
            pass

    def readable(self):
        return True

    def writable(self):
        return True

    def listen(self, num):
        self.accepting = True
        return self.socket.listen(num)

    def bind(self, addr):
        self.addr = addr
        return self.socket.bind(addr)

    def connect(self, address):
        self.connected = False
        err = self.socket.connect_ex(address)
        if err in (EINPROGRESS, EALREADY, EWOULDBLOCK):
            return
        if err in (0, EISCONN):
            self.addr = address
            self.connected = True
            self.handle_connect()
        else:
            raise socket.error(err, errorcode[err])

    def accept(self):
        try:
            conn, addr = self.socket.accept()
            return (conn, addr)
        except socket.error as why:
            if why[0] == EWOULDBLOCK:
                pass
            else:
                raise

    def send(self, data):
        try:
            result = self.socket.send(data)
            return result
        except socket.error as why:
            if why[0] == EWOULDBLOCK:
                return 0
            raise
            return 0

    def recv(self, buffer_size):
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                self.handle_close()
                return ''
            return data
        except socket.error as why:
            if why[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN]:
                self.handle_close()
                return ''
            raise

    def close(self):
        self.del_channel()
        self.socket.close()

    def __getattr__(self, attr):
        return getattr(self.socket, attr)

    def log(self, message):
        sys.stderr.write('log: %s\n' % str(message))

    def log_info(self, message, type = 'info'):
        if __debug__ or type != 'info':
            print '%s: %s' % (type, message)

    def handle_read_event(self):
        if self.accepting:
            if not self.connected:
                self.connected = True
            self.handle_accept()
        elif not self.connected:
            self.handle_connect()
            self.connected = True
            self.handle_read()
        else:
            self.handle_read()

    def handle_write_event(self):
        if not self.connected:
            self.handle_connect()
            self.connected = True
        self.handle_write()

    def handle_expt_event(self):
        self.handle_expt()

    def handle_error(self):
        nil, t, v, tbinfo = compact_traceback()
        try:
            self_repr = repr(self)
        except:
            self_repr = '<__repr__(self) failed for object at %0x>' % id(self)

        self.log_info('uncaptured python exception, closing channel %s (%s:%s %s)' % (self_repr,
         t,
         v,
         tbinfo), 'error')
        self.close()

    def handle_expt(self):
        self.log_info('unhandled exception', 'warning')

    def handle_read(self):
        self.log_info('unhandled read event', 'warning')

    def handle_write(self):
        self.log_info('unhandled write event', 'warning')

    def handle_connect(self):
        self.log_info('unhandled connect event', 'warning')

    def handle_accept(self):
        self.log_info('unhandled accept event', 'warning')

    def handle_close(self):
        self.log_info('unhandled close event', 'warning')
        self.close()


class dispatcher_with_send(dispatcher):

    def __init__(self, sock = None, map = None):
        dispatcher.__init__(self, sock, map)
        self.out_buffer = ''

    def initiate_send(self):
        num_sent = 0
        num_sent = dispatcher.send(self, self.out_buffer[:512])
        self.out_buffer = self.out_buffer[num_sent:]

    def handle_write(self):
        self.initiate_send()

    def writable(self):
        return not self.connected or len(self.out_buffer)

    def send(self, data):
        if self.debug:
            self.log_info('sending %s' % repr(data))
        self.out_buffer = self.out_buffer + data
        self.initiate_send()


def compact_traceback():
    t, v, tb = sys.exc_info()
    tbinfo = []
    assert tb
    while tb:
        tbinfo.append((tb.tb_frame.f_code.co_filename, tb.tb_frame.f_code.co_name, str(tb.tb_lineno)))
        tb = tb.tb_next

    del tb
    file, function, line = tbinfo[-1]
    info = ' '.join([ '[%s|%s|%s]' % x for x in tbinfo ])
    return ((file, function, line),
     t,
     v,
     info)


def close_all(map = None):
    if map is None:
        map = socket_map
    for x in map.values():
        x.socket.close()

    map.clear()


if os.name == 'posix':
    import fcntl

    class file_wrapper:

        def __init__(self, fd):
            self.fd = fd

        def recv(self, *args):
            return os.read(self.fd, *args)

        def send(self, *args):
            return os.write(self.fd, *args)

        read = recv
        write = send

        def close(self):
            os.close(self.fd)

        def fileno(self):
            return self.fd


    class file_dispatcher(dispatcher):

        def __init__(self, fd, map = None):
            dispatcher.__init__(self, None, map)
            self.connected = True
            self.set_file(fd)
            flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
            flags = flags | os.O_NONBLOCK
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)

        def set_file(self, fd):
            self._fileno = fd
            self.socket = file_wrapper(fd)
            self.add_channel()
