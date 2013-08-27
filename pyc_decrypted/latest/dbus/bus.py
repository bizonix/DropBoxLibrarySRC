#Embedded file name: dbus/bus.py
__all__ = ('BusConnection',)
__docformat__ = 'reStructuredText'
import logging
import weakref
from _dbus_bindings import validate_interface_name, validate_member_name, validate_bus_name, validate_object_path, validate_error_name, BUS_SESSION, BUS_STARTER, BUS_SYSTEM, DBUS_START_REPLY_SUCCESS, DBUS_START_REPLY_ALREADY_RUNNING, BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, NAME_FLAG_ALLOW_REPLACEMENT, NAME_FLAG_DO_NOT_QUEUE, NAME_FLAG_REPLACE_EXISTING, RELEASE_NAME_REPLY_NON_EXISTENT, RELEASE_NAME_REPLY_NOT_OWNER, RELEASE_NAME_REPLY_RELEASED, REQUEST_NAME_REPLY_ALREADY_OWNER, REQUEST_NAME_REPLY_EXISTS, REQUEST_NAME_REPLY_IN_QUEUE, REQUEST_NAME_REPLY_PRIMARY_OWNER
from dbus.connection import Connection
from dbus.exceptions import DBusException
from dbus.lowlevel import HANDLER_RESULT_NOT_YET_HANDLED
_NAME_OWNER_CHANGE_MATCH = "type='signal',sender='%s',interface='%s',member='NameOwnerChanged',path='%s',arg0='%%s'" % (BUS_DAEMON_NAME, BUS_DAEMON_IFACE, BUS_DAEMON_PATH)
_NAME_HAS_NO_OWNER = 'org.freedesktop.DBus.Error.NameHasNoOwner'
_logger = logging.getLogger('dbus.bus')

class NameOwnerWatch(object):
    __slots__ = ('_match', '_pending_call')

    def __init__(self, bus_conn, bus_name, callback):
        validate_bus_name(bus_name)

        def signal_cb(owned, old_owner, new_owner):
            callback(new_owner)

        def error_cb(e):
            if e.get_dbus_name() == _NAME_HAS_NO_OWNER:
                callback('')
            else:
                logging.basicConfig()
                _logger.debug('GetNameOwner(%s) failed:', bus_name, exc_info=(e.__class__, e, None))

        self._match = bus_conn.add_signal_receiver(signal_cb, 'NameOwnerChanged', BUS_DAEMON_IFACE, BUS_DAEMON_NAME, BUS_DAEMON_PATH, arg0=bus_name)
        self._pending_call = bus_conn.call_async(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'GetNameOwner', 's', (bus_name,), callback, error_cb, utf8_strings=True)

    def cancel(self):
        if self._match is not None:
            self._match.remove()
        if self._pending_call is not None:
            self._pending_call.cancel()
        self._match = None
        self._pending_call = None


class BusConnection(Connection):
    TYPE_SESSION = BUS_SESSION
    TYPE_SYSTEM = BUS_SYSTEM
    TYPE_STARTER = BUS_STARTER
    START_REPLY_SUCCESS = DBUS_START_REPLY_SUCCESS
    START_REPLY_ALREADY_RUNNING = DBUS_START_REPLY_ALREADY_RUNNING

    def __new__(cls, address_or_type = TYPE_SESSION, mainloop = None):
        bus = cls._new_for_bus(address_or_type, mainloop=mainloop)
        bus._bus_names = weakref.WeakValueDictionary()
        bus._signal_sender_matches = {}
        return bus

    def add_signal_receiver(self, handler_function, signal_name = None, dbus_interface = None, bus_name = None, path = None, **keywords):
        named_service = keywords.pop('named_service', None)
        if named_service is not None:
            if bus_name is not None:
                raise TypeError('bus_name and named_service cannot both be specified')
            bus_name = named_service
            from warnings import warn
            warn('Passing the named_service parameter to add_signal_receiver by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
        match = super(BusConnection, self).add_signal_receiver(handler_function, signal_name, dbus_interface, bus_name, path, **keywords)
        if bus_name is not None and bus_name != BUS_DAEMON_NAME:
            if bus_name[:1] == ':':

                def callback(new_owner):
                    if new_owner == '':
                        match.remove()

            else:
                callback = match.set_sender_name_owner
            watch = self.watch_name_owner(bus_name, callback)
            self._signal_sender_matches[match] = watch
        self.add_match_string(str(match))
        return match

    def _clean_up_signal_match(self, match):
        self.remove_match_string_non_blocking(str(match))
        watch = self._signal_sender_matches.pop(match, None)
        if watch is not None:
            watch.cancel()

    def activate_name_owner(self, bus_name):
        if bus_name is not None and bus_name[:1] != ':' and bus_name != BUS_DAEMON_NAME:
            try:
                return self.get_name_owner(bus_name)
            except DBusException as e:
                if e.get_dbus_name() != _NAME_HAS_NO_OWNER:
                    raise
                self.start_service_by_name(bus_name)
                return self.get_name_owner(bus_name)

        else:
            return bus_name

    def get_object(self, bus_name, object_path, introspect = True, follow_name_owner_changes = False, **kwargs):
        if follow_name_owner_changes:
            self._require_main_loop()
        named_service = kwargs.pop('named_service', None)
        if named_service is not None:
            if bus_name is not None:
                raise TypeError('bus_name and named_service cannot both be specified')
            from warnings import warn
            warn('Passing the named_service parameter to get_object by name is deprecated: please use positional parameters', DeprecationWarning, stacklevel=2)
            bus_name = named_service
        if kwargs:
            raise TypeError('get_object does not take these keyword arguments: %s' % ', '.join(kwargs.iterkeys()))
        return self.ProxyObjectClass(self, bus_name, object_path, introspect=introspect, follow_name_owner_changes=follow_name_owner_changes)

    def get_unix_user(self, bus_name):
        validate_bus_name(bus_name)
        return self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'GetConnectionUnixUser', 's', (bus_name,))

    def start_service_by_name(self, bus_name, flags = 0):
        validate_bus_name(bus_name)
        return (True, self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'StartServiceByName', 'su', (bus_name, flags)))

    def request_name(self, name, flags = 0):
        validate_bus_name(name, allow_unique=False)
        return self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'RequestName', 'su', (name, flags))

    def release_name(self, name):
        validate_bus_name(name, allow_unique=False)
        return self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'ReleaseName', 's', (name,))

    def list_names(self):
        return self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'ListNames', '', (), utf8_strings=True)

    def list_activatable_names(self):
        return self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'ListActivatableNames', '', (), utf8_strings=True)

    def get_name_owner(self, bus_name):
        validate_bus_name(bus_name, allow_unique=False)
        return self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'GetNameOwner', 's', (bus_name,), utf8_strings=True)

    def watch_name_owner(self, bus_name, callback):
        return NameOwnerWatch(self, bus_name, callback)

    def name_has_owner(self, bus_name):
        return bool(self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'NameHasOwner', 's', (bus_name,)))

    def add_match_string(self, rule):
        self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'AddMatch', 's', (rule,))

    def add_match_string_non_blocking(self, rule):
        self.call_async(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'AddMatch', 's', (rule,), None, None)

    def remove_match_string(self, rule):
        self.call_blocking(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'RemoveMatch', 's', (rule,))

    def remove_match_string_non_blocking(self, rule):
        self.call_async(BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, 'RemoveMatch', 's', (rule,), None, None)
