#Embedded file name: dropbox/livetracer.py
from __future__ import absolute_import
import sys
import os
import threading
import socket
import asyncore
import time
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.threadutils import StoppableThread

def make_traced_thread(c):

    class TracedThread(c):

        def __init__(self, *n, **kw):
            super(TracedThread, self).__init__(*n, **kw)
            self.tracers = []
            self.tracer_lock = threading.Lock()

        def settrace(self, frame, event, arg):
            with self.tracer_lock:
                if self.tracers and frame.f_code.co_filename.startswith(os.getcwd()):
                    for tracer in self.tracers:
                        tracer(frame.f_code.co_filename, frame.f_lineno)

                    for i in xrange(10000):
                        i += 10000
                        i -= 10000

            return self.settrace

        def add_tracer(self, tracer):
            with self.tracer_lock:
                self.tracers.append(tracer)

        def remove_tracer(self, tracer):
            with self.tracer_lock:
                self.tracers.remove(tracer)

        def run(self):
            sys.settrace(self.settrace)
            super(TracedThread, self).run()

    return TracedThread


class LiveTraceHandler(asyncore.dispatcher):
    WAITING_FOR_THREAD, WRITING = range(2)

    def __init__(self, *n, **kw):
        asyncore.dispatcher.__init__(self, *n, **kw)
        self.state = LiveTraceHandler.WAITING_FOR_THREAD
        self.buffer_list = []
        self.buffer_lock = threading.Lock()
        self.out_buffer = []
        self.thr = None
        TRACE('New LiveTrace Connection')

    @classmethod
    def register_thread_tracer(cls, thr, inst):
        thr.add_tracer(inst.settrace)

    @classmethod
    def deregister_thread_tracer(cls, thr, inst):
        thr.remove_tracer(inst.settrace)

    def settrace(self, filename, lineno):
        with self.buffer_lock:
            self.out_buffer.append('%s\t%s\n' % (filename, lineno))

    def readable(self):
        return self.state == LiveTraceHandler.WAITING_FOR_THREAD

    def writable(self):
        if self.state == LiveTraceHandler.WAITING_FOR_THREAD:
            return False
        with self.buffer_lock:
            return len(self.out_buffer) != 0

    def handle_write(self):
        with self.buffer_lock:
            while len(self.out_buffer) != 0:
                try:
                    sent = self.send(self.out_buffer[0])
                except:
                    self.handle_close()
                    return

                if sent == 0:
                    break
                self.out_buffer[0] = self.out_buffer[0][sent:]
                if len(self.out_buffer[0]) == 0:
                    del self.out_buffer[0]

    def handle_read(self):
        newbuf = self.recv(4096)
        pos = newbuf.find('\n')
        if pos != -1:
            line = ''.join(self.buffer_list + [newbuf[:pos]])
            lookinfor = None
            for thr in threading.enumerate():
                if thr.getName() == line:
                    lookinfor = thr

            if lookinfor is None:
                TRACE('No thread named %s, closing connection' % line)
                self.handle_close()
                return
            self.thr = lookinfor
            LiveTraceHandler.register_thread_tracer(self.thr, self)
            self.state = LiveTraceHandler.WRITING
        else:
            self.buffer_list.append(newbuf)

    def handle_close(self):
        TRACE('Live trace connection finished')
        if self.thr is not None:
            LiveTraceHandler.deregister_thread_tracer(self.thr, self)
        self.close()


class LiveTraceServer(asyncore.dispatcher):

    def __init__(self, address, *n, **kw):
        asyncore.dispatcher.__init__(self, *n, **kw)
        self.map = kw.get('map', asyncore.socket_map)
        self.bind(address)
        self.listen(5)
        TRACE('Live Trace Server Started')

    def writable(self):
        return False

    def handle_accept(self):
        conn, addr = self.accept()
        LiveTraceHandler(sock=conn, map=self.map)


class LiveTraceThread(StoppableThread):

    def __init__(self, trace_socket_parent_dir, *n, **kw):
        kw['name'] = 'LIVETRACE'
        super(LiveTraceThread, self).__init__(*n, **kw)
        self.trace_socket_parent_dir = trace_socket_parent_dir
        self.pipe = socket.socketpair()
        self.pipe[0].setblocking(0)
        self.pipe[1].setblocking(0)

    def set_wakeup_event(self):
        try:
            self.pipe[1].send('a')
        except:
            unhandled_exc_handler()

    def run(self):
        this_map = {}
        trace_socket_path = self.trace_socket_parent_dir + u'/trace_socket'
        if os.path.exists(trace_socket_path):
            os.remove(trace_socket_path)
        LiveTraceServer(trace_socket_path, sock=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM), map=this_map)
        a = asyncore.dispatcher(sock=self.pipe[0], map=this_map)

        def handle_read():
            raise asyncore.ExitNow

        def readable():
            return True

        def writable():
            return False

        a.handle_read = handle_read
        a.readable = readable
        a.writable = writable
        while not self.stopped():
            try:
                asyncore.loop(None, False, this_map)
            except asyncore.ExitNow:
                break

        TRACE('ARGH DYING')
