#Embedded file name: dbus/mainloop/glib.py
__all__ = ('DBusGMainLoop', 'threads_init')
from _dbus_glib_bindings import DBusGMainLoop, gthreads_init
_dbus_gthreads_initialized = False

def threads_init():
    global _dbus_gthreads_initialized
    if not _dbus_gthreads_initialized:
        gthreads_init()
        _dbus_gthreads_initialized = True
