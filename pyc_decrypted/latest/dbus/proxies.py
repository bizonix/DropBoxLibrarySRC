#Embedded file name: dbus/proxies.py
import sys
import logging
try:
    from threading import RLock
except ImportError:
    from dummy_threading import RLock

import _dbus_bindings
from dbus._expat_introspect_parser import process_introspection_data
from dbus.exceptions import MissingReplyHandlerException, MissingErrorHandlerException, IntrospectionParserException, DBusException
__docformat__ = 'restructuredtext'
_logger = logging.getLogger('dbus.proxies')
from _dbus_bindings import LOCAL_PATH, BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, INTROSPECTABLE_IFACE

class _DeferredMethod():

    def __init__(self, proxy_method, append, block):
        self._proxy_method = proxy_method
        self._method_name = proxy_method._method_name
        self._append = append
        self._block = block

    def __call__(self, *args, **keywords):
        if keywords.has_key('reply_handler') or keywords.get('ignore_reply', False):
            self._append(self._proxy_method, args, keywords)
            return None
        else:
            self._block()
            return self._proxy_method(*args, **keywords)

    def call_async(self, *args, **keywords):
        self._append(self._proxy_method, args, keywords)


class _ProxyMethod():

    def __init__(self, proxy, connection, bus_name, object_path, method_name, iface):
        if object_path == LOCAL_PATH:
            raise DBusException('Methods may not be called on the reserved path %s' % LOCAL_PATH)
        self._proxy = proxy
        self._connection = connection
        self._named_service = bus_name
        self._object_path = object_path
        _dbus_bindings.validate_member_name(method_name)
        self._method_name = method_name
        if iface is not None:
            _dbus_bindings.validate_interface_name(iface)
        self._dbus_interface = iface

    def __call__(self, *args, **keywords):
        reply_handler = keywords.pop('reply_handler', None)
        error_handler = keywords.pop('error_handler', None)
        ignore_reply = keywords.pop('ignore_reply', False)
        signature = keywords.pop('signature', None)
        if reply_handler is not None or error_handler is not None:
            if reply_handler is None:
                raise MissingReplyHandlerException()
            elif error_handler is None:
                raise MissingErrorHandlerException()
            elif ignore_reply:
                raise TypeError('ignore_reply and reply_handler cannot be used together')
        dbus_interface = keywords.pop('dbus_interface', self._dbus_interface)
        if signature is None:
            if dbus_interface is None:
                key = self._method_name
            else:
                key = dbus_interface + '.' + self._method_name
            signature = self._proxy._introspect_method_map.get(key, None)
        if ignore_reply or reply_handler is not None:
            self._connection.call_async(self._named_service, self._object_path, dbus_interface, self._method_name, signature, args, reply_handler, error_handler, **keywords)
        else:
            return self._connection.call_blocking(self._named_service, self._object_path, dbus_interface, self._method_name, signature, args, **keywords)

    def call_async(self, *args, **keywords):
        reply_handler = keywords.pop('reply_handler', None)
        error_handler = keywords.pop('error_handler', None)
        signature = keywords.pop('signature', None)
        dbus_interface = keywords.pop('dbus_interface', self._dbus_interface)
        if signature is None:
            if dbus_interface:
                key = dbus_interface + '.' + self._method_name
            else:
                key = self._method_name
            signature = self._proxy._introspect_method_map.get(key, None)
        self._connection.call_async(self._named_service, self._object_path, dbus_interface, self._method_name, signature, args, reply_handler, error_handler, **keywords)


class ProxyObject(object):
    ProxyMethodClass = _ProxyMethod
    DeferredMethodClass = _DeferredMethod
    INTROSPECT_STATE_DONT_INTROSPECT = 0
    INTROSPECT_STATE_INTROSPECT_IN_PROGRESS = 1
    INTROSPECT_STATE_INTROSPECT_DONE = 2

    def __init__(self, conn = None, bus_name = None, object_path = None, introspect = True, follow_name_owner_changes = False, **kwargs):
        bus = kwargs.pop('bus', None)
        if bus is not None:
            if conn is not None:
                raise TypeError('conn and bus cannot both be specified')
            conn = bus
            from warnings import warn
            warn('Passing the bus parameter to ProxyObject by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
        named_service = kwargs.pop('named_service', None)
        if named_service is not None:
            if bus_name is not None:
                raise TypeError('bus_name and named_service cannot both be specified')
            bus_name = named_service
            from warnings import warn
            warn('Passing the named_service parameter to ProxyObject by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
        if kwargs:
            raise TypeError('ProxyObject.__init__ does not take these keyword arguments: %s' % ', '.join(kwargs.iterkeys()))
        if follow_name_owner_changes:
            conn._require_main_loop()
        self._bus = conn
        if bus_name is not None:
            _dbus_bindings.validate_bus_name(bus_name)
        self._named_service = self._requested_bus_name = bus_name
        _dbus_bindings.validate_object_path(object_path)
        self.__dbus_object_path__ = object_path
        if not follow_name_owner_changes:
            self._named_service = conn.activate_name_owner(bus_name)
        self._pending_introspect = None
        self._pending_introspect_queue = []
        self._introspect_method_map = {}
        self._introspect_lock = RLock()
        if not introspect or self.__dbus_object_path__ == LOCAL_PATH:
            self._introspect_state = self.INTROSPECT_STATE_DONT_INTROSPECT
        else:
            self._introspect_state = self.INTROSPECT_STATE_INTROSPECT_IN_PROGRESS
            self._pending_introspect = self._Introspect()

    bus_name = property(lambda self: self._named_service, None, None, 'The bus name to which this proxy is bound. (Read-only,\n            may change.)\n\n            If the proxy was instantiated using a unique name, this property\n            is that unique name.\n\n            If the proxy was instantiated with a well-known name and with\n            ``follow_name_owner_changes`` set false (the default), this\n            property is the unique name of the connection that owned that\n            well-known name when the proxy was instantiated, which might\n            not actually own the requested well-known name any more.\n\n            If the proxy was instantiated with a well-known name and with\n            ``follow_name_owner_changes`` set true, this property is that\n            well-known name.\n            ')
    requested_bus_name = property(lambda self: self._requested_bus_name, None, None, 'The bus name which was requested when this proxy was\n            instantiated.\n            ')
    object_path = property(lambda self: self.__dbus_object_path__, None, None, 'The object-path of this proxy.')

    def connect_to_signal(self, signal_name, handler_function, dbus_interface = None, **keywords):
        return self._bus.add_signal_receiver(handler_function, signal_name=signal_name, dbus_interface=dbus_interface, bus_name=self._named_service, path=self.__dbus_object_path__, **keywords)

    def _Introspect(self):
        return self._bus.call_async(self._named_service, self.__dbus_object_path__, INTROSPECTABLE_IFACE, 'Introspect', '', (), self._introspect_reply_handler, self._introspect_error_handler, utf8_strings=True, require_main_loop=False)

    def _introspect_execute_queue(self):
        for proxy_method, args, keywords in self._pending_introspect_queue:
            proxy_method(*args, **keywords)

        self._pending_introspect_queue = []

    def _introspect_reply_handler(self, data):
        self._introspect_lock.acquire()
        try:
            try:
                self._introspect_method_map = process_introspection_data(data)
            except IntrospectionParserException as e:
                self._introspect_error_handler(e)
                return

            self._introspect_state = self.INTROSPECT_STATE_INTROSPECT_DONE
            self._pending_introspect = None
            self._introspect_execute_queue()
        finally:
            self._introspect_lock.release()

    def _introspect_error_handler(self, error):
        logging.basicConfig()
        _logger.error('Introspect error on %s:%s: %s.%s: %s', self._named_service, self.__dbus_object_path__, error.__class__.__module__, error.__class__.__name__, error)
        self._introspect_lock.acquire()
        try:
            _logger.debug('Executing introspect queue due to error')
            self._introspect_state = self.INTROSPECT_STATE_DONT_INTROSPECT
            self._pending_introspect = None
            self._introspect_execute_queue()
        finally:
            self._introspect_lock.release()

    def _introspect_block(self):
        self._introspect_lock.acquire()
        try:
            if self._pending_introspect is not None:
                self._pending_introspect.block()
        finally:
            self._introspect_lock.release()

    def _introspect_add_to_queue(self, callback, args, kwargs):
        self._introspect_lock.acquire()
        try:
            if self._introspect_state == self.INTROSPECT_STATE_INTROSPECT_IN_PROGRESS:
                self._pending_introspect_queue.append((callback, args, kwargs))
            else:
                callback(*args, **kwargs)
        finally:
            self._introspect_lock.release()

    def __getattr__(self, member):
        if member.startswith('__') and member.endswith('__'):
            raise AttributeError(member)
        else:
            return self.get_dbus_method(member)

    def get_dbus_method(self, member, dbus_interface = None):
        ret = self.ProxyMethodClass(self, self._bus, self._named_service, self.__dbus_object_path__, member, dbus_interface)
        if self._introspect_state == self.INTROSPECT_STATE_INTROSPECT_IN_PROGRESS:
            ret = self.DeferredMethodClass(ret, self._introspect_add_to_queue, self._introspect_block)
        return ret

    def __repr__(self):
        return '<ProxyObject wrapping %s %s %s at %#x>' % (self._bus,
         self._named_service,
         self.__dbus_object_path__,
         id(self))

    __str__ = __repr__


class Interface(object):

    def __init__(self, object, dbus_interface):
        if isinstance(object, Interface):
            self._obj = object.proxy_object
        else:
            self._obj = object
        self._dbus_interface = dbus_interface

    object_path = property(lambda self: self._obj.object_path, None, None, 'The D-Bus object path of the underlying object')
    __dbus_object_path__ = object_path
    bus_name = property(lambda self: self._obj.bus_name, None, None, 'The bus name to which the underlying proxy object is bound')
    requested_bus_name = property(lambda self: self._obj.requested_bus_name, None, None, 'The bus name which was requested when the underlying object was created')
    proxy_object = property(lambda self: self._obj, None, None, 'The underlying proxy object')
    dbus_interface = property(lambda self: self._dbus_interface, None, None, 'The D-Bus interface represented')

    def connect_to_signal(self, signal_name, handler_function, dbus_interface = None, **keywords):
        if not dbus_interface:
            dbus_interface = self._dbus_interface
        return self._obj.connect_to_signal(signal_name, handler_function, dbus_interface, **keywords)

    def __getattr__(self, member):
        if member.startswith('__') and member.endswith('__'):
            raise AttributeError(member)
        else:
            return self._obj.get_dbus_method(member, self._dbus_interface)

    def get_dbus_method(self, member, dbus_interface = None):
        if dbus_interface is None:
            dbus_interface = self._dbus_interface
        return self._obj.get_dbus_method(member, dbus_interface)

    def __repr__(self):
        return '<Interface %r implementing %r at %#x>' % (self._obj, self._dbus_interface, id(self))

    __str__ = __repr__
