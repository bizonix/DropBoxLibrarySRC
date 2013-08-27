#Embedded file name: arch/linux/interfacerequestserver.py
from __future__ import absolute_import
import Queue
import asyncore
import threading
from dropbox.callbacks import Handler
from dropbox.functions import sanitize
from dropbox.trace import TRACE, unhandled_exc_handler

class InterfaceRequestServerHandler(asyncore.dispatcher):

    def __init__(self, conn, addr, *n, **kw):
        asyncore.dispatcher.__init__(self, conn, *n, **kw)
        self.close_callback = None
        self.output_queue = Queue.Queue()
        self._pending_message = None

    def writable(self):
        return self._pending_message is not None or not self.output_queue.empty()

    def readable(self):
        return True

    def handle_expt(self):
        pass

    def handle_read(self):
        self.recv(4096)

    def handle_close(self):
        self.close()

    def handle_error(self):
        unhandled_exc_handler()
        self.close()

    def handle_write(self):
        try:
            if self._pending_message is None:
                self._pending_message = self.output_queue.get_nowait()
        except Queue.Empty:
            pass

        try:
            if self._pending_message is not None:
                sent = self.send(self._pending_message)
                if sent < len(self._pending_message):
                    self._pending_message = self._pending_message[sent:]
                else:
                    self._pending_message = None
        except EnvironmentError as e:
            TRACE(u'killing interface socket: ' + unicode(e))
            self.close()
        except Exception:
            unhandled_exc_handler()
            self.close()

    def close(self):
        TRACE('closed connection to interface request server')
        asyncore.dispatcher.close(self)
        if self.close_callback is not None:
            cb = self.close_callback
            self.close_callback = None
            cb()


class InterfaceRequestServer(asyncore.dispatcher):

    def __init__(self, app, addr, *n, **kw):
        self.app = app
        asyncore.dispatcher.__init__(self, *n, **kw)
        self.map = kw.get('map', asyncore.socket_map)
        self.bind(addr)
        self.listen(5)
        self.ifaces_list_lock = threading.Lock()
        self.ifaces_list = []
        TRACE(u'Interface server listening')

    def writable(self):
        return False

    def handle_error(self):
        unhandled_exc_handler()

    def ifaces_request(self, command_name, args):
        if self.app.mbox.is_secondary:
            return self.app.mbox.notify_primary(command_name, args)
        if not self._anyonelistening():
            return False
        lines = []
        lines.append(sanitize(command_name))
        for k, vals in args.iteritems():
            lines.append(u'\t'.join([sanitize(k)] + [ sanitize(val) for val in vals ]))

        lines.append(u'done')
        rawmsg = u''.join((u'%s\n' % line for line in lines)).encode('utf-8')
        self._push_rawmsg_to_ifaces(rawmsg)
        return True

    def _push_rawmsg_to_ifaces(self, data):
        with self.ifaces_list_lock:
            for iface_conn in self.ifaces_list:
                iface_conn.output_queue.put(data)

    def _anyonelistening(self):
        with self.ifaces_list_lock:
            return len(self.ifaces_list) > 0

    def _handle_iface_conn_closed(self, iface_conn):
        with self.ifaces_list_lock:
            self.ifaces_list.remove(iface_conn)

    def handle_accept(self):
        conn, addr = self.accept()
        with self.ifaces_list_lock:
            if len(self.ifaces_list) >= 10:
                TRACE(u'Declined connection to interface server: ' + unicode(addr))
                conn.close()
            else:
                TRACE(u'Connection to interface server: ' + unicode(addr))
                iface_conn = InterfaceRequestServerHandler(conn, addr, map=self.map)
                iface_conn.close_callback = lambda : self._handle_iface_conn_closed(iface_conn)
                self.ifaces_list.append(iface_conn)
