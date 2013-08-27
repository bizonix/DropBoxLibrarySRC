#Embedded file name: arch/linux/control_thread.py
from __future__ import absolute_import
import os
import threading
import socket
import asyncore
import errno
import time
from dropbox.globals import dropbox_globals
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.threadutils import StoppableThread
from .commandserver import CommandServer
from .interfacerequestserver import InterfaceRequestServer
from .constants import appdata_path

class ControlThread(StoppableThread):

    class KillServerHandler(asyncore.dispatcher):

        def __init__(self, cs, irs, *n, **kw):
            asyncore.dispatcher.__init__(self, *n, **kw)
            self.irs = irs
            self.cs = cs

        def readable(self):
            return True

        def writable(self):
            return False

        def handle_read(self):
            gotb = False
            gota = False
            while True:
                try:
                    rs = self.recv(32)
                except socket.error as e:
                    if e[0] == errno.EAGAIN:
                        break
                    else:
                        raise

                gota = gota or 'a' in rs
                gotb = gotb or 'b' in rs
                del rs

            if gota:
                raise asyncore.ExitNow
            if gotb:
                TRACE('stop listening...')
                self.cs.close()
                self.irs.close()

    def __init__(self, app):
        super(ControlThread, self).__init__(name='CONTROL')
        self.map = {}
        self.waiting_to_wake = False
        self.waiting_to_wake_lock = threading.Lock()
        self.pipe = socket.socketpair()
        self.pipe[0].setblocking(0)
        self.pipe[1].setblocking(0)
        self.initted = False
        self.app = app

    def kill_servers(self):
        if not self.initted:
            return
        try:
            self.pipe[1].send('b')
        except:
            unhandled_exc_handler()

    def set_wakeup_event(self):
        with self.waiting_to_wake_lock:
            if not self.waiting_to_wake:
                try:
                    self.pipe[1].send('a')
                except:
                    unhandled_exc_handler()
                else:
                    self.waiting_to_wake = True

    def ifaces_request(self, *n, **kw):
        if not self.isAlive() or not self.initted:
            return
        ret = self.irs.ifaces_request(*n, **kw)
        self.set_wakeup_event()
        return ret

    def shell_touch(self, path):
        self.ifaces_request(u'shell_touch', {u'path': [path]})

    def __build_servers(self):
        command_socket_path = os.path.join(appdata_path, u'command_socket')
        iface_socket_path = os.path.join(appdata_path, u'iface_socket')
        for path in (command_socket_path, iface_socket_path):
            printed_exception = False
            while True:
                try:
                    os.remove(path)
                except OSError as e:
                    if e.errno == errno.ENOENT:
                        break
                    elif not printed_exception:
                        unhandled_exc_handler()
                        printed_exception = True
                else:
                    break

                time.sleep(5)

        self.cs = CommandServer(self.app, command_socket_path, sock=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM), map=self.map)
        from .dropboxcommands import add_commands
        add_commands(self.cs.add_command)
        self.irs = InterfaceRequestServer(self.app, iface_socket_path, sock=socket.socket(socket.AF_UNIX, socket.SOCK_STREAM), map=self.map)
        self.ksh = ControlThread.KillServerHandler(self.cs, self.irs, sock=self.pipe[0], map=self.map)
        os.chmod(command_socket_path, 384)
        os.chmod(iface_socket_path, 384)

    def run(self):
        try:
            self.__build_servers()
        except Exception:
            unhandled_exc_handler()
            return

        self.initted = True
        while not self.stopped():
            try:
                asyncore.loop(None, False, self.map)
            except asyncore.ExitNow:
                with self.waiting_to_wake_lock:
                    self.waiting_to_wake = False
            except:
                unhandled_exc_handler()

        TRACE('Stopping...')
