#Embedded file name: dbus/connection.py
__all__ = ('Connection', 'SignalMatch')
__docformat__ = 'reStructuredText'
import logging
try:
    import thread
except ImportError:
    import dummy_thread as thread

import weakref
from _dbus_bindings import Connection as _Connection, LOCAL_PATH, LOCAL_IFACE, validate_interface_name, validate_member_name, validate_bus_name, validate_object_path, validate_error_name, UTF8String
from dbus.exceptions import DBusException
from dbus.lowlevel import ErrorMessage, MethodCallMessage, SignalMessage, MethodReturnMessage, HANDLER_RESULT_NOT_YET_HANDLED
from dbus.proxies import ProxyObject
_logger = logging.getLogger('dbus.connection')

def _noop(*args, **kwargs):
    pass


class SignalMatch(object):
    __slots__ = ('_sender_name_owner', '_member', '_interface', '_sender', '_path', '_handler', '_args_match', '_rule', '_utf8_strings', '_byte_arrays', '_conn_weakref', '_destination_keyword', '_interface_keyword', '_message_keyword', '_member_keyword', '_sender_keyword', '_path_keyword', '_int_args_match')

    def __init__(self, conn, sender, object_path, dbus_interface, member, handler, utf8_strings = False, byte_arrays = False, sender_keyword = None, path_keyword = None, interface_keyword = None, member_keyword = None, message_keyword = None, destination_keyword = None, **kwargs):
        if member is not None:
            validate_member_name(member)
        if dbus_interface is not None:
            validate_interface_name(dbus_interface)
        if sender is not None:
            validate_bus_name(sender)
        if object_path is not None:
            validate_object_path(object_path)
        self._rule = None
        self._conn_weakref = weakref.ref(conn)
        self._sender = sender
        self._interface = dbus_interface
        self._member = member
        self._path = object_path
        self._handler = handler
        self._sender_name_owner = sender
        self._utf8_strings = utf8_strings
        self._byte_arrays = byte_arrays
        self._sender_keyword = sender_keyword
        self._path_keyword = path_keyword
        self._member_keyword = member_keyword
        self._interface_keyword = interface_keyword
        self._message_keyword = message_keyword
        self._destination_keyword = destination_keyword
        self._args_match = kwargs
        if not kwargs:
            self._int_args_match = None
        else:
            self._int_args_match = {}
            for kwarg in kwargs:
                if not kwarg.startswith('arg'):
                    raise TypeError('SignalMatch: unknown keyword argument %s' % kwarg)
                try:
                    index = int(kwarg[3:])
                except ValueError:
                    raise TypeError('SignalMatch: unknown keyword argument %s' % kwarg)

                if index < 0 or index > 63:
                    raise TypeError('SignalMatch: arg match index must be in range(64), not %d' % index)
                self._int_args_match[index] = kwargs[kwarg]

    def __hash__(self):
        return hash(id(self))

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    sender = property(lambda self: self._sender)

    def __str__(self):
        if self._rule is None:
            rule = ["type='signal'"]
            if self._sender is not None:
                rule.append("sender='%s'" % self._sender)
            if self._path is not None:
                rule.append("path='%s'" % self._path)
            if self._interface is not None:
                rule.append("interface='%s'" % self._interface)
            if self._member is not None:
                rule.append("member='%s'" % self._member)
            if self._int_args_match is not None:
                for index, value in self._int_args_match.iteritems():
                    rule.append("arg%d='%s'" % (index, value))

            self._rule = ','.join(rule)
        return self._rule

    def __repr__(self):
        return '<%s at %x "%s" on conn %r>' % (self.__class__,
         id(self),
         self._rule,
         self._conn_weakref())

    def set_sender_name_owner(self, new_name):
        self._sender_name_owner = new_name

    def matches_removal_spec(self, sender, object_path, dbus_interface, member, handler, **kwargs):
        if handler not in (None, self._handler):
            return False
        if sender != self._sender:
            return False
        if object_path != self._path:
            return False
        if dbus_interface != self._interface:
            return False
        if member != self._member:
            return False
        if kwargs != self._args_match:
            return False
        return True

    def maybe_handle_message(self, message):
        args = None
        if self._sender_name_owner not in (None, message.get_sender()):
            return False
        if self._int_args_match is not None:
            args = message.get_args_list(utf8_strings=True, byte_arrays=True)
            for index, value in self._int_args_match.iteritems():
                if index >= len(args) or not isinstance(args[index], UTF8String) or args[index] != value:
                    return False

        if self._member not in (None, message.get_member()):
            return False
        if self._interface not in (None, message.get_interface()):
            return False
        if self._path not in (None, message.get_path()):
            return False
        try:
            if args is None or not self._utf8_strings or not self._byte_arrays:
                args = message.get_args_list(utf8_strings=self._utf8_strings, byte_arrays=self._byte_arrays)
            kwargs = {}
            if self._sender_keyword is not None:
                kwargs[self._sender_keyword] = message.get_sender()
            if self._destination_keyword is not None:
                kwargs[self._destination_keyword] = message.get_destination()
            if self._path_keyword is not None:
                kwargs[self._path_keyword] = message.get_path()
            if self._member_keyword is not None:
                kwargs[self._member_keyword] = message.get_member()
            if self._interface_keyword is not None:
                kwargs[self._interface_keyword] = message.get_interface()
            if self._message_keyword is not None:
                kwargs[self._message_keyword] = message
            self._handler(*args, **kwargs)
        except:
            logging.basicConfig()
            _logger.error('Exception in handler for D-Bus signal:', exc_info=1)

        return True

    def remove(self):
        conn = self._conn_weakref()
        if conn is not None:
            conn.remove_signal_receiver(self, self._member, self._interface, self._sender, self._path, **self._args_match)


class Connection(_Connection):
    ProxyObjectClass = ProxyObject

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        if not hasattr(self, '_dbus_Connection_initialized'):
            self._dbus_Connection_initialized = 1
            self.__call_on_disconnection = []
            self._signal_recipients_by_object_path = {}
            self._signals_lock = thread.allocate_lock()
            self.add_message_filter(self.__class__._signal_func)

    def activate_name_owner(self, bus_name):
        return bus_name

    def get_object(self, bus_name = None, object_path = None, introspect = True, **kwargs):
        named_service = kwargs.pop('named_service', None)
        if named_service is not None:
            if bus_name is not None:
                raise TypeError('bus_name and named_service cannot both be specified')
            from warnings import warn
            warn('Passing the named_service parameter to get_object by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
            bus_name = named_service
        if kwargs:
            raise TypeError('get_object does not take these keyword arguments: %s' % ', '.join(kwargs.iterkeys()))
        return self.ProxyObjectClass(self, bus_name, object_path, introspect=introspect)

    def add_signal_receiver(self, handler_function, signal_name = None, dbus_interface = None, bus_name = None, path = None, **keywords):
        self._require_main_loop()
        named_service = keywords.pop('named_service', None)
        if named_service is not None:
            if bus_name is not None:
                raise TypeError('bus_name and named_service cannot both be specified')
            bus_name = named_service
            from warnings import warn
            warn('Passing the named_service parameter to add_signal_receiver by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
        match = SignalMatch(self, bus_name, path, dbus_interface, signal_name, handler_function, **keywords)
        self._signals_lock.acquire()
        try:
            by_interface = self._signal_recipients_by_object_path.setdefault(path, {})
            by_member = by_interface.setdefault(dbus_interface, {})
            matches = by_member.setdefault(signal_name, [])
            matches.append(match)
        finally:
            self._signals_lock.release()

        return match

    def _iter_easy_matches(self, path, dbus_interface, member):
        if path is not None:
            path_keys = (None, path)
        else:
            path_keys = (None,)
        if dbus_interface is not None:
            interface_keys = (None, dbus_interface)
        else:
            interface_keys = (None,)
        if member is not None:
            member_keys = (None, member)
        else:
            member_keys = (None,)
        for path in path_keys:
            by_interface = self._signal_recipients_by_object_path.get(path, None)
            if by_interface is None:
                continue
            for dbus_interface in interface_keys:
                by_member = by_interface.get(dbus_interface, None)
                if by_member is None:
                    continue
                for member in member_keys:
                    matches = by_member.get(member, None)
                    if matches is None:
                        continue
                    for m in matches:
                        yield m

    def remove_signal_receiver(self, handler_or_match, signal_name = None, dbus_interface = None, bus_name = None, path = None, **keywords):
        named_service = keywords.pop('named_service', None)
        if named_service is not None:
            if bus_name is not None:
                raise TypeError('bus_name and named_service cannot both be specified')
            bus_name = named_service
            from warnings import warn
            warn('Passing the named_service parameter to remove_signal_receiver by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
        new = []
        deletions = []
        self._signals_lock.acquire()
        try:
            by_interface = self._signal_recipients_by_object_path.get(path, None)
            if by_interface is None:
                return
            by_member = by_interface.get(dbus_interface, None)
            if by_member is None:
                return
            matches = by_member.get(signal_name, None)
            if matches is None:
                return
            for match in matches:
                if handler_or_match is match or match.matches_removal_spec(bus_name, path, dbus_interface, signal_name, handler_or_match, **keywords):
                    deletions.append(match)
                else:
                    new.append(match)

            if new:
                by_member[signal_name] = new
            else:
                del by_member[signal_name]
                if not by_member:
                    del by_interface[dbus_interface]
                    if not by_interface:
                        del self._signal_recipients_by_object_path[path]
        finally:
            self._signals_lock.release()

        for match in deletions:
            self._clean_up_signal_match(match)

    def _clean_up_signal_match(self, match):
        pass

    def _signal_func(self, message):
        if not isinstance(message, SignalMessage):
            return HANDLER_RESULT_NOT_YET_HANDLED
        dbus_interface = message.get_interface()
        path = message.get_path()
        signal_name = message.get_member()
        for match in self._iter_easy_matches(path, dbus_interface, signal_name):
            match.maybe_handle_message(message)

        if dbus_interface == LOCAL_IFACE and path == LOCAL_PATH and signal_name == 'Disconnected':
            for cb in self.__call_on_disconnection:
                try:
                    cb(self)
                except Exception as e:
                    logging.basicConfig()
                    _logger.error('Exception in handler for Disconnected signal:', exc_info=1)

        return HANDLER_RESULT_NOT_YET_HANDLED

    def call_async(self, bus_name, object_path, dbus_interface, method, signature, args, reply_handler, error_handler, timeout = -1.0, utf8_strings = False, byte_arrays = False, require_main_loop = True):
        if object_path == LOCAL_PATH:
            raise DBusException('Methods may not be called on the reserved path %s' % LOCAL_PATH)
        if dbus_interface == LOCAL_IFACE:
            raise DBusException('Methods may not be called on the reserved interface %s' % LOCAL_IFACE)
        get_args_opts = {'utf8_strings': utf8_strings,
         'byte_arrays': byte_arrays}
        message = MethodCallMessage(destination=bus_name, path=object_path, interface=dbus_interface, method=method)
        try:
            message.append(signature=signature, *args)
        except Exception as e:
            logging.basicConfig()
            _logger.error('Unable to set arguments %r according to signature %r: %s: %s', args, signature, e.__class__, e)
            raise

        if reply_handler is None and error_handler is None:
            self.send_message(message)
            return
        if reply_handler is None:
            reply_handler = _noop
        if error_handler is None:
            error_handler = _noop

        def msg_reply_handler(message):
            if isinstance(message, MethodReturnMessage):
                reply_handler(*message.get_args_list(**get_args_opts))
            elif isinstance(message, ErrorMessage):
                error_handler(DBusException(name=message.get_error_name(), *message.get_args_list()))
            else:
                error_handler(TypeError('Unexpected type for reply message: %r' % message))

        return self.send_message_with_reply(message, msg_reply_handler, timeout, require_main_loop=require_main_loop)

    def call_blocking(self, bus_name, object_path, dbus_interface, method, signature, args, timeout = -1.0, utf8_strings = False, byte_arrays = False):
        if object_path == LOCAL_PATH:
            raise DBusException('Methods may not be called on the reserved path %s' % LOCAL_PATH)
        if dbus_interface == LOCAL_IFACE:
            raise DBusException('Methods may not be called on the reserved interface %s' % LOCAL_IFACE)
        get_args_opts = {'utf8_strings': utf8_strings,
         'byte_arrays': byte_arrays}
        message = MethodCallMessage(destination=bus_name, path=object_path, interface=dbus_interface, method=method)
        try:
            message.append(signature=signature, *args)
        except Exception as e:
            logging.basicConfig()
            _logger.error('Unable to set arguments %r according to signature %r: %s: %s', args, signature, e.__class__, e)
            raise

        reply_message = self.send_message_with_reply_and_block(message, timeout)
        args_list = reply_message.get_args_list(**get_args_opts)
        if len(args_list) == 0:
            return None
        elif len(args_list) == 1:
            return args_list[0]
        else:
            return tuple(args_list)

    def call_on_disconnection(self, callable):
        self.__call_on_disconnection.append(callable)
