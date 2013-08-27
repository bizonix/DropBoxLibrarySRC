#Embedded file name: dbus/dbus_bindings.py
from warnings import warn as _warn
_dbus_bindings_warning = DeprecationWarning('The dbus_bindings module is not public API and will go away soon.\n\nMost uses of dbus_bindings are applications catching the exception\ndbus.dbus_bindings.DBusException. You should use dbus.DBusException\ninstead (this is compatible with all dbus-python versions since 0.40.2).\n\nIf you need additional public API, please contact the maintainers via\n<dbus@lists.freedesktop.org>.\n')
_warn(_dbus_bindings_warning, DeprecationWarning, stacklevel=2)
from dbus.exceptions import DBusException

class ConnectionError(Exception):
    pass


from dbus.types import *
from _dbus_bindings import Message, SignalMessage as Signal, MethodCallMessage as MethodCall, MethodReturnMessage as MethodReturn, ErrorMessage as Error
from _dbus_bindings import Connection
from dbus import Bus
bus_request_name = Bus.request_name
bus_release_name = Bus.release_name
