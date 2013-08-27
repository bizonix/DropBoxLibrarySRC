#Embedded file name: arch/linux/commandserver.py
from __future__ import absolute_import
import threading
import asyncore
import asynchat
import itertools
import os
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.functions import desanitize, sanitize

class IllegalArgumentException(Exception):

    def __init__(self, msg = None):
        Exception.__init__(self, msg)

    def __unicode__(self):
        return u'Illegal Argument' + (self.message is not None and u': ' + self.message or u'')


class CommandNotFoundError(Exception):
    pass


class ConnectionState(object):

    def __init__(self):
        self.on_disconnect_hooks = []

    def add_on_disconnect_hook(self, hook):
        self.on_disconnect_hooks.append(hook)

    def remove_on_disconnect_hook(self, hook):
        self.on_disconnect_hooks.remove(hook)

    def call_on_disconnect_hooks(self, cs):
        for hook in self.on_disconnect_hooks:
            hook(cs, self)


class CommandServerHandler(asynchat.async_chat):
    WAITING_FOR_COMMAND, GETTING_ARGUMENTS = range(2)
    numinstances = 0

    def __init__(self, cs, conn, addr, *n, **kw):
        asynchat.async_chat.__init__(self)
        self._map = kw['map'] if 'map' in kw else None
        self.set_socket(conn, self._map)
        self.socket.setblocking(0)
        self.connected = True
        self.set_terminator('\n')
        self.current_line_data = []
        self.state = self.__class__.WAITING_FOR_COMMAND
        self.command_name = None
        self.command_arguments = None
        self.errors = []
        self.connstate = ConnectionState()
        self.cs = cs
        self.closed = False
        CommandServerHandler.numinstances += 1

    def collect_incoming_data(self, data):
        self.current_line_data.append(data)

    def close(self):
        if self.closed:
            return
        asynchat.async_chat.close(self)
        CommandServerHandler.numinstances -= 1
        try:
            self.connstate.call_on_disconnect_hooks(self.cs)
        except:
            unhandled_exc_handler()

        TRACE('Closed connection to command server')
        self.closed = True

    def respond_notok(self):
        self.push('notok\n')
        for error in self.errors:
            self.push(sanitize(error).encode('utf8'))
            self.push('\n')

        self.push('done\n')

    def respond_ok(self, rets):
        topush = [None] * 4
        i = 0
        topush[i] = 'ok\n'
        i += 1
        toappend = u'\n'.join((u'\t'.join((sanitize(elt) for elt in itertools.chain((k,), v))) for k, v in rets.iteritems())).encode('utf8')
        if toappend:
            topush[i] = toappend
            i += 1
            topush[i] = '\n'
            i += 1
        topush[i] = 'done\n'
        i += 1
        for data in itertools.islice(topush, i):
            self.push(data)

    def handle_error(self):
        unhandled_exc_handler()
        try:
            self.close()
        except:
            unhandled_exc_handler()

    def found_terminator(self):
        line = ''.join(self.current_line_data).decode('utf8')
        if self.state == self.__class__.WAITING_FOR_COMMAND:
            self.errors[:] = []
            self.command_name = desanitize(line)
            self.command_arguments = {}
            self.state = self.__class__.GETTING_ARGUMENTS
            self.numargs = 0
        elif self.state == self.__class__.GETTING_ARGUMENTS:
            if self.numargs >= 20:
                self.close()
                return
            if line == u'done':
                if self.errors:
                    TRACE(u'errors on done: ' + unicode(self.errors))
                    self.respond_notok()
                else:
                    try:
                        result = self.cs.call_command(self.command_name, self.connstate, self.command_arguments)
                        self.respond_ok(result)
                    except IllegalArgumentException as e:
                        TRACE(self.command_name + ': ' + unicode(e))
                        self.errors.append(unicode(e))
                        self.respond_notok()
                    except CommandNotFoundError as e:
                        TRACE(u'no command for: ' + self.command_name)
                        self.errors.append(u'No command exists by that name')
                        self.respond_notok()
                    except Exception as e:
                        unhandled_exc_handler()
                        self.errors.append(u'Unknown Error')
                        self.respond_notok()

                self.state = self.__class__.WAITING_FOR_COMMAND
            else:
                argval = line.split(u'\t')
                lenargval = len(argval)
                self.command_arguments[desanitize(argval[0])] = [ desanitize(a) for a in argval[1:] ]
                self.numargs = self.numargs + 1
        else:
            assert False
        self.current_line_data[:] = []


class CommandServer(asyncore.dispatcher):

    def __init__(self, app, addr, *n, **kw):
        asyncore.dispatcher.__init__(self, *n, **kw)
        self.map = kw.get('map', asyncore.socket_map)
        self.bind(addr)
        self.listen(5)
        self.command_dict = {}
        self.command_dict_lock = threading.Lock()
        self.app = app
        TRACE(u'Command Server listening')

    def writable(self):
        return False

    def add_command(self, name, fn):
        with self.command_dict_lock:
            self.command_dict[name] = fn

    def remove_command(self, name):
        with self.command_dict_lock:
            del self.command_dict[name]

    def call_command(self, name, *n, **kw):
        with self.command_dict_lock:
            try:
                cmd = self.command_dict[name]
            except KeyError:
                raise CommandNotFoundError(name)

            return cmd(self, *n, **kw)

    def handle_error(self):
        unhandled_exc_handler()

    def handle_accept(self):
        conn, addr = self.accept()
        if CommandServerHandler.numinstances >= 10:
            TRACE(u'Declined connection to command server: ' + unicode(addr))
            conn.close()
        else:
            TRACE(u'Connection to command server: ' + unicode(addr))
            CommandServerHandler(self, conn, addr, map=self.map)
