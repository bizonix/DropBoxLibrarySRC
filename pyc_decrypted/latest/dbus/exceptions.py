#Embedded file name: dbus/exceptions.py
__all__ = ('DBusException', 'MissingErrorHandlerException', 'MissingReplyHandlerException', 'ValidationException', 'IntrospectionParserException', 'UnknownMethodException', 'NameExistsException')

class DBusException(Exception):
    include_traceback = False

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        if name is not None or getattr(self, '_dbus_error_name', None) is None:
            self._dbus_error_name = name
        if kwargs:
            raise TypeError('DBusException does not take keyword arguments: %s' % ', '.join(kwargs.keys()))
        Exception.__init__(self, *args)

    def __str__(self):
        s = Exception.__str__(self)
        if self._dbus_error_name is not None:
            return '%s: %s' % (self._dbus_error_name, s)
        else:
            return s

    def get_dbus_message(self):
        s = Exception.__str__(self)
        return s.decode('utf-8', 'replace')

    def get_dbus_name(self):
        return self._dbus_error_name


class MissingErrorHandlerException(DBusException):
    include_traceback = True

    def __init__(self):
        DBusException.__init__(self, 'error_handler not defined: if you define a reply_handler you must also define an error_handler')


class MissingReplyHandlerException(DBusException):
    include_traceback = True

    def __init__(self):
        DBusException.__init__(self, 'reply_handler not defined: if you define an error_handler you must also define a reply_handler')


class ValidationException(DBusException):
    include_traceback = True

    def __init__(self, msg = ''):
        DBusException.__init__(self, 'Error validating string: %s' % msg)


class IntrospectionParserException(DBusException):
    include_traceback = True

    def __init__(self, msg = ''):
        DBusException.__init__(self, 'Error parsing introspect data: %s' % msg)


class UnknownMethodException(DBusException):
    include_traceback = True
    _dbus_error_name = 'org.freedesktop.DBus.Error.UnknownMethod'

    def __init__(self, method):
        DBusException.__init__(self, 'Unknown method: %s' % method)


class NameExistsException(DBusException):
    include_traceback = True

    def __init__(self, name):
        DBusException.__init__(self, 'Bus name already exists: %s' % name)
