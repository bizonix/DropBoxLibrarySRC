#Embedded file name: dbus/_dbus.py
from __future__ import generators
__all__ = ('Bus', 'SystemBus', 'SessionBus', 'StarterBus')
__docformat__ = 'reStructuredText'
import os
import sys
import weakref
from traceback import print_exc
from dbus.exceptions import DBusException
from _dbus_bindings import BUS_DAEMON_NAME, BUS_DAEMON_PATH, BUS_DAEMON_IFACE, UTF8String, validate_member_name, validate_interface_name, validate_bus_name, validate_object_path, BUS_SESSION, BUS_SYSTEM, BUS_STARTER, DBUS_START_REPLY_SUCCESS, DBUS_START_REPLY_ALREADY_RUNNING
from dbus.bus import BusConnection
from dbus.lowlevel import SignalMessage
try:
    import thread
except ImportError:
    import dummy_thread as thread

class Bus(BusConnection):
    _shared_instances = {}

    def __new__(cls, bus_type = BusConnection.TYPE_SESSION, private = False, mainloop = None):
        if not private and bus_type in cls._shared_instances:
            return cls._shared_instances[bus_type]
        if bus_type == BUS_SESSION:
            subclass = SessionBus
        elif bus_type == BUS_SYSTEM:
            subclass = SystemBus
        elif bus_type == BUS_STARTER:
            subclass = StarterBus
        else:
            raise ValueError('invalid bus_type %s' % bus_type)
        bus = BusConnection.__new__(subclass, bus_type, mainloop=mainloop)
        bus._bus_type = bus_type
        if not private:
            cls._shared_instances[bus_type] = bus
        return bus

    def close(self):
        t = self._bus_type
        if self.__class__._shared_instances.get(t) is self:
            del self.__class__._shared_instances[t]
        super(Bus, self).close()

    def get_connection(self):
        return self

    _connection = property(get_connection, None, None, 'self._connection == self, for backwards\n                           compatibility with earlier dbus-python versions\n                           where Bus was not a subclass of Connection.')

    def get_session(private = False):
        return SessionBus(private=private)

    get_session = staticmethod(get_session)

    def get_system(private = False):
        return SystemBus(private=private)

    get_system = staticmethod(get_system)

    def get_starter(private = False):
        return StarterBus(private=private)

    get_starter = staticmethod(get_starter)

    def __repr__(self):
        if self._bus_type == BUS_SESSION:
            name = 'session'
        elif self._bus_type == BUS_SYSTEM:
            name = 'system'
        elif self._bus_type == BUS_STARTER:
            name = 'starter'
        else:
            name = 'unknown bus type'
        return '<%s.%s (%s) at %#x>' % (self.__class__.__module__,
         self.__class__.__name__,
         name,
         id(self))

    __str__ = __repr__


class SystemBus(Bus):

    def __new__(cls, private = False, mainloop = None):
        return Bus.__new__(cls, Bus.TYPE_SYSTEM, mainloop=mainloop, private=private)


class SessionBus(Bus):

    def __new__(cls, private = False, mainloop = None):
        return Bus.__new__(cls, Bus.TYPE_SESSION, private=private, mainloop=mainloop)


class StarterBus(Bus):

    def __new__(cls, private = False, mainloop = None):
        return Bus.__new__(cls, Bus.TYPE_STARTER, private=private, mainloop=mainloop)


if 'DBUS_PYTHON_NO_DEPRECATED' not in os.environ:

    class _DBusBindingsEmulation:

        def __str__(self):
            return '_DBusBindingsEmulation()'

        def __repr__(self):
            return '_DBusBindingsEmulation()'

        def __getattr__(self, attr):
            global dbus_bindings
            import dbus.dbus_bindings as m
            dbus_bindings = m
            return getattr(m, attr)


    dbus_bindings = _DBusBindingsEmulation()
