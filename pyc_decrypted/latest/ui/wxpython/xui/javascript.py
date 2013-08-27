#Embedded file name: ui/wxpython/xui/javascript.py
import types
from contextlib import contextmanager
from weakref import WeakValueDictionary
import pycef
import wx
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.common.xui import dict_get_property, list_get_property, serialize_exception, get_exposed_properties, XUIException, XUIInvalidObjectError, XUIJavaScriptError

def parse_exception(exception):
    assert isinstance(exception, pycef.CefV8Exception)
    return XUIJavaScriptError(exception.GetMessage())


def create_exception(value):
    return serialize_exception(value)


class XUIHandler(pycef.CefV8Handler):

    def __init__(self, target):
        self._target = target
        pycef.CefV8Handler.__init__(self)

    @event_handler
    def Execute(self, name, obj, arguments):
        try:

            def arg_gen():
                for argument in arguments:
                    yield _from_js_value(argument)

            result = self._target(*arg_gen())
            retval = _to_js_value(result)
            return (True, retval)
        except XUIException:
            unhandled_exc_handler()
            return False
        except Exception as e:
            unhandled_exc_handler()
            return (True, pycef.CefV8Value.CreateNull(), str(e))


class XUIAccessor(pycef.CefV8Accessor):

    def __init__(self, target):
        self._target = target
        pycef.CefV8Accessor.__init__(self)

    @event_handler
    def Get(self, name, this_object):
        success = False
        result = None
        exception = None
        try:
            if isinstance(self._target, (types.ListType, types.TupleType)):
                _property = list_get_property(self._target, name)
            elif isinstance(self._target, types.DictType):
                _property = dict_get_property(self._target, name)
            else:
                _property = getattr(self._target, name)
            result = _to_js_value(_property)
            success = True
        except Exception as exc:
            exception = create_exception(exc)

        if exception:
            return (success, result, exception)
        else:
            return (success, result)

    @event_handler
    def Set(self, name, this_object, value):
        return (False, None)


@contextmanager
def _xui_ensure_valid(ctx, objects):
    if not ctx.IsValid():
        raise XUIInvalidObjectError('Context is no longer valid!')
    if objects and not all((obj.IsValid() for obj in objects)):
        raise XUIInvalidObjectError('A required object is no longer valid!')
    if not ctx.Enter():
        raise XUIException('Failed to enter context!')
    try:
        yield
    finally:
        if not ctx.Exit():
            TRACE('!! Failed to exit context!')


class XUICefObject(object):
    __slots__ = ('_xui_ctx', '_xui_cef_obj', '_xui_ensure_valid')

    def __init__(self, ctx, cef_obj):
        self._xui_ctx = ctx
        self._xui_cef_obj = cef_obj

    def _xui_get_property(self, key):
        return self._xui_cef_obj.GetValue(key)

    def _xui_get_property_by_index(self, i):
        return self._xui_cef_obj.GetValueByIndex(i)

    @assert_message_queue
    def __getattribute__(self, name):
        if name.startswith('_xui') or name.startswith('__') or name.startswith('_%s_' % self.__class__.__name__):
            return object.__getattribute__(self, name)
        with _xui_ensure_valid(self._xui_ctx, (self._xui_cef_obj,)):
            value = self._xui_get_property(name)
            if value is not None:
                return _from_js_value(value, this_object=self._xui_cef_obj)
            return object.__getattribute__(self, name)

    @assert_message_queue
    def __getitem__(self, key):
        with _xui_ensure_valid(self._xui_ctx, (self._xui_cef_obj,)):
            if isinstance(key, types.IntType):
                value = self._xui_get_property_by_index(key)
            elif isinstance(key, types.StringTypes):
                value = self._xui_get_property(key)
            else:
                raise XUIException('Unsupported indexing type?')
            return _from_js_value(value, this_object=self._xui_cef_obj)

    @assert_message_queue
    def __iter__(self):
        raise NotImplementedError()

    @assert_message_queue
    def __len__(self):
        with _xui_ensure_valid(self._xui_ctx, (self._xui_cef_obj,)):
            length = self._xui_get_property('length')
            return _from_js_value(length)

    def __str__(self):
        return '<xuijsobject[cef] %r>' % (self._xui_cef_obj,)


class XUICefFunction(object):
    __slots__ = ('_xui_ctx', '_xui_cef_func', '_xui_this_obj')

    def __init__(self, ctx, func, this_obj = None):
        self._xui_ctx = ctx
        self._xui_cef_func = func
        self._xui_this_obj = this_obj

    @message_sender(wx.CallAfter, block=True)
    def __call__(self, *args):
        with _xui_ensure_valid(self._xui_ctx, (self._xui_cef_func,)):

            def arg_gen():
                for argument in args:
                    yield _to_js_value(argument)

            serialized = pycef.CefV8ValueList(list(arg_gen()))
            returned = self._xui_cef_func.ExecuteFunction(self._xui_this_obj, serialized)
            if returned is None and self._xui_cef_func.HasException():
                exception = self._xui_cef_func.GetException()
                try:
                    raise parse_exception(exception)
                finally:
                    self._xui_cef_func.ClearException()

            elif returned is None:
                raise XUIException('We called ExecuteFunction incorrectly!')
            else:
                return _from_js_value(returned)


_registry = WeakValueDictionary()

def _from_js_value(value, this_object = None):
    global _registry
    if value.IsString():
        return value.GetStringValue()
    if value.IsInt():
        return value.GetIntValue()
    if value.IsUInt():
        return value.GetUIntValue()
    if value.IsDouble():
        return value.GetDoubleValue()
    if value.IsUndefined() or value.IsNull():
        return None
    if value.IsBool():
        return value.GetBoolValue()
    if value.IsArray() and value.IsUserCreated():
        result = []
        for i in range(value.GetArrayLength()):
            result.append(_from_js_value(value.GetValueByIndex(i)))

        return tuple(result)
    if value.IsFunction():
        if value.IsUserCreated():
            key = value.GetUserData()
            return _registry[key]._target
        ctx = pycef.CefV8Context.GetEnteredContext()
        assert ctx
        return XUICefFunction(ctx, value, this_object)
    if value.IsObject():
        if value.IsUserCreated():
            key = value.GetUserData()
            return _registry[key]._target
        ctx = pycef.CefV8Context.GetEnteredContext()
        assert ctx
        return XUICefObject(ctx, value)
    raise XUIException('Unsupported V8 Value Type in %r' % (value,))


def _to_js_value(value):
    result = None
    if value is None:
        result = pycef.CefV8Value.CreateNull()
    elif isinstance(value, (types.StringType, types.UnicodeType)):
        result = pycef.CefV8Value.CreateString(unicode(value))
    elif isinstance(value, types.BooleanType):
        result = pycef.CefV8Value.CreateBool(value)
    elif isinstance(value, types.IntType):
        result = pycef.CefV8Value.CreateInt(value)
    elif isinstance(value, types.FloatType):
        result = pycef.CefV8Value.CreateDouble(value)
    elif isinstance(value, types.TupleType):
        result = pycef.CefV8Value.CreateArray(len(value))
        for index, item in enumerate(value):
            result.SetValueByIndex(index, _to_js_value(item))

    elif isinstance(value, types.ListType):
        raise XUIException('Mutable lists are not supported.')
    elif isinstance(value, (types.FunctionType, types.LambdaType, types.MethodType)):
        key = id(value)
        handler = _registry.get(key)
        if handler is None:
            handler = XUIHandler(value)
            _registry[key] = handler
        assert handler._target is value
        result = pycef.CefV8Value.CreateFunction(value.__name__, handler)
        if not result.SetUserData(key):
            raise XUIException('Failed to tag function!')
    elif isinstance(value, object):
        key = id(value)
        accessor = _registry.get(key)
        if accessor is None:
            accessor = XUIAccessor(value)
            _registry[key] = accessor
        assert accessor._target is value
        result = pycef.CefV8Value.CreateObject(accessor)
        if isinstance(value, types.DictType):
            property_list = list(value.iterkeys())
        else:
            property_list = get_exposed_properties(value)
        for property_name in property_list:
            result.RegisterValue(str(property_name), pycef.V8_ACCESS_CONTROL_ALL_CAN_READ, pycef.V8_PROPERTY_ATTRIBUTE_READONLY)

        if not result.SetUserData(key):
            raise XUIException('Failed to tag object!')
    else:
        raise XUIException('Unsupported Python Value Type: %r (%r)' % (type(value), value))
    if result is None:
        raise XUIException('Failed to create V8 Value for Python Value: %r' % (value,))
    return result


@assert_message_queue
def inject_object(context, name, obj):
    with _xui_ensure_valid(context, ()):
        _obj = _to_js_value(obj)
        gbl_obj = context.GetGlobal()
        gbl_obj.SetValue(name, _obj, pycef.V8_PROPERTY_ATTRIBUTE_READONLY | pycef.V8_PROPERTY_ATTRIBUTE_DONTDELETE)
