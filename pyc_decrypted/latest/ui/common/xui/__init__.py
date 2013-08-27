#Embedded file name: ui/common/xui/__init__.py
import os
import tempfile
import urllib
from itertools import chain
from functools import partial, wraps
import build_number
from dropbox.functions import handle_exceptions_ex
from dropbox.i18n import trans as _trans, ungettext as _ungettext
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
_PROPERTY_LIST_KEY = '__xui_properties__'

@handle_exceptions_ex(return_value=())
def get_exposed_properties(obj):
    properties = list(chain.from_iterable((getattr(cls, _PROPERTY_LIST_KEY, ()) for cls in obj.__class__.__mro__)))
    if not properties:
        properties = list(chain.from_iterable((getattr(cls, '__slots__', ()) for cls in obj.__class__.__mro__)))
    return properties


def serialize_exception(value):
    if isinstance(value, Exception):
        return '%s: %s' % (value.__class__.__name__, unicode(value))
    else:
        return unicode(value)


def list_get_property(obj, propertyName):
    if propertyName == 'length':
        return len(obj)
    if propertyName.isdigit():
        return obj[int(propertyName)]
    raise Exception('Unsupported list property!')


def dict_get_property(obj, name):
    return obj[name]


class MetaXUIController(type):
    _registry = {}

    def __init__(cls, name, bases, cls_dict):
        if name == 'XUIController':
            return
        _attrs = ('__xui_resource__', '__xui_properties__')
        for attr in _attrs:
            assert attr in cls_dict, "Classes deriving from MetaXUIController must have a '%s' class attribute" % (attr,)

        MetaXUIController._registry[cls.__xui_resource__] = cls
        super(MetaXUIController, cls).__init__(name, bases, cls_dict)


class XUIException(Exception):
    pass


class XUINotReadyError(Exception):
    pass


class XUIInvalidObjectError(XUIException):
    pass


class XUIJavaScriptError(Exception):
    pass


class XUIController(object):
    _OBJECT_NAME = 'controller'
    __metaclass__ = MetaXUIController
    __xui_properties__ = ('trans', 'ungettext', 'attach_view', 'TRACE')

    def __init__(self):
        self._value_host = None
        self._value_view = None

    @classmethod
    def _get_view_data(cls):
        import _views
        resource_data = getattr(_views, cls.__xui_resource__ + '_view_data')
        return resource_data

    def attach_view(self, view):
        TRACE('XUIController %r is now attached to view: %r', self, view)
        self._value_view = view

    def trans(self, msgid):
        try:
            return _trans(unicode(msgid))
        except Exception:
            unhandled_exc_handler()
            return None

    def ungettext(self, singular, plural, n):
        try:
            return _ungettext(unicode(singular), unicode(plural), n)
        except Exception:
            unhandled_exc_handler()
            return None

    def TRACE(self, string, *n):
        try:
            return TRACE(unicode(string), *n)
        except Exception:
            unhandled_exc_handler()
            return None

    @property
    def _view(self):
        if self._value_view is None:
            raise XUINotReadyError('View is not yet available')
        return self._value_view

    @property
    def _host(self):
        return self._value_host

    @_host.setter
    def _host(self, value):
        TRACE('XUIController %r is now attached to host: %r', self, value)
        self._value_host = value


class XUIHost(object):

    def __init__(self, controller):
        self._failed = False
        self.controller = controller
        controller._host = self

    def _get_failed(self):
        return self._failed

    def _set_failed(self, has_failed = True, fatal = False):
        has_failed = bool(has_failed)
        if hasattr(build_number, 'frozen') and build_number.stable_build() or fatal:
            TRACE('!! Host %r has failed!', self)
            self._failed = has_failed
        elif has_failed:
            TRACE('!! Host %r has failed! This would have brought down the host.', self)

    failed = property(_get_failed, _set_failed)
