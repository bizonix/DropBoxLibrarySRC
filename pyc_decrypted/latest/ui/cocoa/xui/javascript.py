#Embedded file name: ui/cocoa/xui/javascript.py
import threading
import types
from ctypes import cast, POINTER, byref, create_string_buffer
from pymac.dlls.JavaScriptCore import JavaScriptCore, JSClassDefinition, JSContextRef, JSGlobalContextRef, JSObjectCallAsFunctionCallback, JSObjectCallAsConstructorCallback, JSObjectConvertToTypeCallback, JSObjectDeletePropertyCallback, JSObjectFinalizeCallback, JSObjectGetPropertyCallback, JSObjectGetPropertyNamesCallback, JSObjectHasInstanceCallback, JSObjectHasPropertyCallback, JSObjectInitializeCallback, JSObjectSetPropertyCallback, JSObjectRef, JSValueRef, kJSClassAttributeNone, kJSTypeString
from PyObjCTools import AppHelper
from dropbox.debugging import easy_repr
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.gui import assert_message_queue, event_handler, message_sender
from ui.common.xui import dict_get_property, list_get_property, serialize_exception, get_exposed_properties, XUIException, XUIInvalidObjectError, XUIJavaScriptError
_STRING_BUFFER_SIZE = 2048
_object_class = None
_object_definition = None
_object_registry = {}
_object_registry_lock = None
_context_registry = {}
_context_set = set()

class RegistryEntry(object):
    __slots__ = ('obj', 'js_obj')

    def __init__(self, obj, js_obj):
        self.obj = obj
        self.js_obj = js_obj

    def __repr__(self):
        return easy_repr(self, *self.__slots__)


@assert_message_queue
def _initialize_object_registry():
    global _object_registry_lock
    global _object_definition
    global _object_class
    if _object_registry_lock is not None:
        return
    _object_registry_lock = threading.RLock()
    _object_definition = JSClassDefinition()
    _object_definition.version = 0
    _object_definition.attributes = kJSClassAttributeNone
    _object_definition.className = 'XUIPythonObject'
    _object_definition.staticValues = None
    _object_definition.staticFunctions = None
    _object_definition.initialize = cast(None, JSObjectInitializeCallback)
    _object_definition.hasProperty = cast(None, JSObjectHasPropertyCallback)
    _object_definition.setProperty = cast(None, JSObjectSetPropertyCallback)
    _object_definition.deleteProperty = cast(None, JSObjectDeletePropertyCallback)
    _object_definition.callAsConstructor = cast(None, JSObjectCallAsConstructorCallback)
    _object_definition.hasInstance = cast(None, JSObjectHasInstanceCallback)

    def _to_string(ctx, pyobj):
        unicode_value = unicode(pyobj).encode('utf-8')
        string_value = JavaScriptCore.JSStringCreateWithUTF8CString(unicode_value)
        try:
            return JavaScriptCore.JSValueMakeString(ctx, string_value)
        finally:
            JavaScriptCore.JSStringRelease(string_value)

    @event_handler
    def _convert_to_type(ctx, obj, jstype, exception):
        global _object_registry
        if jstype != kJSTypeString:
            return
        identifier = int(JavaScriptCore.JSObjectGetPrivate(obj))
        with _object_registry_lock:
            entry = _object_registry.get(identifier)
            if entry is None:
                exception[0] = create_exception(ctx, 'No such Python object.')
                return
            return _to_string(ctx, entry.obj)

    _object_definition.convertToType = JSObjectConvertToTypeCallback(_convert_to_type)

    @event_handler
    def _get_property(ctx, obj, propertyName, exception):
        ctx = cast(ctx, JSContextRef)
        identifier = int(JavaScriptCore.JSObjectGetPrivate(obj))
        with _object_registry_lock:
            entry = _object_registry.get(identifier)
            if entry is None:
                exception[0] = create_exception(ctx, 'No such Python object.')
                return
            string_buffer = create_string_buffer(_STRING_BUFFER_SIZE)
            JavaScriptCore.JSStringGetUTF8CString(propertyName, string_buffer, _STRING_BUFFER_SIZE)
            property_name = string_buffer.value.decode('utf-8')
            try:
                python_object = entry.obj
                if isinstance(python_object, (types.ListType, types.TupleType)):
                    _property = list_get_property(python_object, property_name)
                elif isinstance(python_object, types.DictType):
                    _property = dict_get_property(python_object, property_name)
                elif property_name == 'toString':
                    _property = _to_string(ctx, python_object)
                elif property_name not in get_exposed_properties(python_object):
                    TRACE('!! Tried to access a property that was not declared: %r.', property_name)
                    _property = None
                else:
                    _property = getattr(python_object, property_name)
            except Exception as exc:
                exception[0] = create_exception(ctx, exc)
                return

            try:
                result = _to_js_value(ctx, _property)
            except Exception as exc:
                exception[0] = create_exception(ctx, exc)
                return

            return result

    _object_definition.getProperty = JSObjectGetPropertyCallback(_get_property)

    @event_handler
    def _get_property_names(ctx, obj, acc):
        ctx = cast(ctx, JSContextRef)
        identifier = int(JavaScriptCore.JSObjectGetPrivate(obj))
        with _object_registry_lock:
            entry = _object_registry.get(identifier)
            if entry is None:
                TRACE('!! No such Python object')
                return
            try:
                python_object = entry.obj
            except:
                TRACE('!! Could not get Python object')
                return

            try:
                for p, v in python_object.iteritems():
                    unicode_value = unicode(p).encode('utf-8')
                    string_value = JavaScriptCore.JSStringCreateWithUTF8CString(unicode_value)
                    JavaScriptCore.JSPropertyNameAccumulatorAddName(acc, string_value)
                    JavaScriptCore.JSStringRelease(string_value)

            except Exception:
                TRACE('!! Object not iterable')

    _object_definition.getPropertyNames = JSObjectGetPropertyNamesCallback(_get_property_names)

    @event_handler
    def call_as_function(ctx, function, thisObject, argumentCount, arguments, exception):
        ctx = cast(ctx, JSContextRef)
        thisObject = cast(thisObject, JSValueRef)
        arguments = cast(arguments, POINTER(JSValueRef))
        identifier = int(JavaScriptCore.JSObjectGetPrivate(function))
        with _object_registry_lock:
            entry = _object_registry.get(identifier)
            if entry is None:
                exception[0] = create_exception(ctx, 'No such Python object.')
                return
            python_object = entry.obj
            if not callable(python_object):
                exception[0] = create_exception(ctx, 'Python object is not callable.')
                return
            parsed_args = []
            try:
                for i in range(argumentCount):
                    value = arguments[i]
                    parsed_args.append(_from_js_value(ctx, value, thisObject))

            except Exception as exc:
                exception[0] = create_exception(ctx, exc)
                return

            try:
                _result = python_object.__call__(*parsed_args)
                result = _to_js_value(ctx, _result)
            except Exception as exc:
                exception[0] = create_exception(ctx, exc)
                return

            return result

    _object_definition.callAsFunction = JSObjectCallAsFunctionCallback(call_as_function)

    @event_handler
    def finalize(obj):
        with _object_registry_lock:
            identifier = int(JavaScriptCore.JSObjectGetPrivate(obj))
            entry = _object_registry.get(identifier)
            if entry is None:
                report_bad_assumption('Lookup failed while finalizing!')
                return
            assert entry.js_obj == obj, 'Should be the same object.'
            del _object_registry[identifier]

    _object_definition.finalize = JSObjectFinalizeCallback(finalize)
    _object_class = JavaScriptCore.JSClassCreate(byref(_object_definition))


def _manual_incref(ctx, js_obj):
    content = JavaScriptCore.JSStringCreateWithUTF8CString("\n    if (!('__gulag' in this)) {\n        this.__gulag = {};\n        this.__gulag_id = 1;\n    }\n    this.__gulag[this.__gulag_id] = arguments[0];\n    return this.__gulag_id++;\n    ")
    try:
        func = JavaScriptCore.JSObjectMakeFunction(ctx, None, 0, None, content, None, 1, None)
        if func is None:
            raise Exception('Failed to create the incref function.')
        exception = JSValueRef()
        result = JavaScriptCore.JSObjectCallAsFunction(ctx, func, None, 1, byref(js_obj), byref(exception))
        if exception.value is not None:
            raise parse_exception(ctx, exception.value)
        key = JavaScriptCore.JSValueToNumber(ctx, result, byref(exception))
        if exception.value is not None:
            raise parse_exception(ctx, exception.value)
        return key
    except Exception:
        unhandled_exc_handler()
    finally:
        JavaScriptCore.JSStringRelease(content)


def _manual_decref(ctx, key):
    content = JavaScriptCore.JSStringCreateWithUTF8CString('delete this.__gulag[arguments[0]];')
    try:
        func = JavaScriptCore.JSObjectMakeFunction(ctx, None, 0, None, content, None, 1, None)
        key_number = cast(JavaScriptCore.JSValueMakeNumber(ctx, key), JSValueRef)
        exception = JSValueRef()
        JavaScriptCore.JSObjectCallAsFunction(ctx, func, None, 1, byref(key_number), byref(exception))
        if exception.value is not None:
            raise parse_exception(ctx, exception.value)
    except Exception:
        unhandled_exc_handler()
    finally:
        JavaScriptCore.JSStringRelease(content)


class XUIJavaScriptObject(object):
    __slots__ = ('_xui_gbl_ctx', '_xui_js_obj', '_xui_this_obj', '_xui_ensure_valid')
    _xui_count = 0

    @assert_message_queue
    def __init__(self, ctx, js_obj, this_obj = None):
        global _context_registry
        gbl_obj = JavaScriptCore.JSContextGetGlobalObject(ctx)
        gbl_ctx = _context_registry[gbl_obj]
        self._xui_gbl_ctx = gbl_ctx
        self._xui_js_obj = cast(js_obj, JSObjectRef)
        self._xui_this_obj = cast(this_obj, JSValueRef)
        JavaScriptCore.JSValueProtect(self._xui_gbl_ctx, self._xui_js_obj)
        if self._xui_this_obj.value is not None:
            JavaScriptCore.JSValueProtect(self._xui_gbl_ctx, self._xui_this_obj)

    def _xui_ensure_valid(self):
        global _context_set
        if self._xui_gbl_ctx.value not in _context_set:
            raise XUIInvalidObjectError()

    def __del__(self):
        if self._xui_gbl_ctx.value not in _context_set:
            return
        if self._xui_this_obj.value is not None:
            JavaScriptCore.JSValueUnprotect(self._xui_gbl_ctx, self._xui_this_obj)
        JavaScriptCore.JSValueUnprotect(self._xui_gbl_ctx, self._xui_js_obj)

    @assert_message_queue
    def _xui_get_property(self, name):
        _name = JavaScriptCore.JSStringCreateWithUTF8CString(name.encode('utf-8'))
        try:
            return JavaScriptCore.JSObjectGetProperty(self._xui_gbl_ctx, self._xui_js_obj, _name, None)
        finally:
            JavaScriptCore.JSStringRelease(_name)

    @assert_message_queue
    def _xui_get_property_by_index(self, index):
        return JavaScriptCore.JSObjectGetPropertyAtIndex(self._xui_gbl_ctx, self._xui_js_obj, index, None)

    def __getattribute__(self, name):
        if name.startswith('_xui') or name.startswith('__') or name.startswith('_%s_' % self.__class__.__name__):
            return object.__getattribute__(self, name)
        self._xui_ensure_valid()
        _value = self._xui_get_property(name)
        if _value is not None:
            return _from_js_value(self._xui_gbl_ctx, _value, self._xui_js_obj)
        else:
            return object.__getattribute__(self, name)

    @message_sender(AppHelper.callAfter, block=True)
    def __call__(self, *args):
        self._xui_ensure_valid()
        exception = JSValueRef()
        args_count = len(args)
        args_array = (JSValueRef * args_count)()
        for i, arg in enumerate(args):
            args_array[i] = _to_js_value(self._xui_gbl_ctx, arg)

        _result = JavaScriptCore.JSObjectCallAsFunction(self._xui_gbl_ctx, self._xui_js_obj, self._xui_this_obj, args_count, cast(args_array, JSValueRef), byref(exception))
        if _result is None:
            raise parse_exception(self._xui_gbl_ctx, exception.value)
        result = _from_js_value(self._xui_gbl_ctx, _result, None)
        return result

    @assert_message_queue
    def __getitem__(self, key):
        self._xui_ensure_valid()
        if isinstance(key, types.IntType):
            value = self._xui_get_property_by_index(key)
        elif isinstance(key, types.StringTypes):
            value = self._xui_get_property(key)
        else:
            raise Exception('Unsupported indexing type.')
        return _from_js_value(self._xui_gbl_ctx, value, self._xui_js_obj)

    @assert_message_queue
    def __iter__(self):
        raise NotImplementedError()

    @assert_message_queue
    def __len__(self):
        self._xui_ensure_valid()
        length = self._xui_get_property('length')
        return _from_js_value(self._xui_gbl_ctx, length, None)

    def __str__(self):
        return '<xuijsobject[jsc] %r>' % (self._xui_js_obj,)

    def __repr__(self):
        return self.__str__()


def _to_js_value(ctx, value):
    result = None
    if value is None:
        result = JavaScriptCore.JSValueMakeNull(ctx)
    elif isinstance(value, (types.StringType, types.UnicodeType)):
        unicode_value = unicode(value).encode('utf-8')
        string_value = JavaScriptCore.JSStringCreateWithUTF8CString(unicode_value)
        try:
            result = JavaScriptCore.JSValueMakeString(ctx, string_value)
        finally:
            JavaScriptCore.JSStringRelease(string_value)

    elif isinstance(value, types.BooleanType):
        result = JavaScriptCore.JSValueMakeBoolean(ctx, value)
    elif isinstance(value, (types.IntType, types.FloatType)):
        result = JavaScriptCore.JSValueMakeNumber(ctx, value)
    elif isinstance(value, (types.FunctionType, types.LambdaType, types.MethodType)) or isinstance(value, object):
        _initialize_object_registry()
        if isinstance(value, XUIJavaScriptObject):
            return value._xui_js_obj
        identifier = id(value)
        entry = _object_registry.get(identifier)
        if entry is not None:
            assert entry.obj is value
            assert entry.js_obj is not None
            result = entry.js_obj
        else:
            result = JavaScriptCore.JSObjectMake(ctx, _object_class, identifier)
            entry = RegistryEntry(obj=value, js_obj=result)
            _object_registry[identifier] = entry
    else:
        raise XUIException('Unsupported Python type: %r (%r).' % (value, type(value)))
    if not result:
        raise XUIException('Failed to create JavaScript value from %r.' % value)
    return result


def _convert_to_string(ctx, value, exception = None):
    string = JavaScriptCore.JSValueToStringCopy(ctx, value, exception)
    try:
        if string is None:
            return ''
        _buffer = create_string_buffer(_STRING_BUFFER_SIZE)
        JavaScriptCore.JSStringGetUTF8CString(string, _buffer, _STRING_BUFFER_SIZE)
        result = _buffer.value.decode('utf-8')
        return result
    finally:
        JavaScriptCore.JSStringRelease(string)


def _from_js_value(ctx, value, this):
    if value is None:
        raise XUIException('Null pointer.')
    if JavaScriptCore.JSValueIsString(ctx, value):
        exception = JSValueRef()
        return _convert_to_string(ctx, value, exception)
        if exception.value is not None:
            raise parse_exception(exception.value)
    else:
        if JavaScriptCore.JSValueIsNumber(ctx, value):
            exception = JSValueRef()
            value = JavaScriptCore.JSValueToNumber(ctx, value, byref(exception))
            if exception.value is not None:
                raise parse_exception(exception.value)
            return value
        if JavaScriptCore.JSValueIsUndefined(ctx, value) or JavaScriptCore.JSValueIsNull(ctx, value):
            return
        if JavaScriptCore.JSValueIsBoolean(ctx, value):
            return JavaScriptCore.JSValueToBoolean(ctx, value)
        if JavaScriptCore.JSValueIsObject(ctx, value):
            obj = JavaScriptCore.JSValueToObject(ctx, value, None)
            if obj is None:
                raise XUIException("JavaScript value wasn't an object.")
            key = JavaScriptCore.JSObjectGetPrivate(obj)
            entry = _object_registry.get(key)
            if key is not None and entry is None:
                raise Exception('JavaScript object refers to dead entry.')
            elif entry is not None:
                return entry.obj
            if JavaScriptCore.JSObjectIsFunction(ctx, obj):
                return XUIJavaScriptObject(ctx, obj, this)
            if JavaScriptCore.JSObjectIsConstructor(ctx, obj):
                raise XUIException('JavaScript constructor objects are not supported.')
            else:
                return XUIJavaScriptObject(ctx, obj)
        else:
            raise XUIException('Unknown/unsupported javascript type: %r' % (_convert_to_string(ctx, value),))


def create_exception(ctx, value):
    message = serialize_exception(value)
    string = JavaScriptCore.JSStringCreateWithUTF8CString(message.encode('utf-8'))
    try:
        exception_string = JavaScriptCore.JSValueMakeString(ctx, string)
        exception_obj = cast(JavaScriptCore.JSValueToObject(ctx, exception_string, None), JSObjectRef)
        return exception_obj
    finally:
        JavaScriptCore.JSStringRelease(string)


def parse_exception(ctx, exception):
    string = JavaScriptCore.JSValueToStringCopy(ctx, exception, None)
    try:
        _buffer = create_string_buffer(_STRING_BUFFER_SIZE)
        JavaScriptCore.JSStringGetUTF8CString(string, _buffer, _STRING_BUFFER_SIZE)
        result = _buffer.value.decode('utf-8')
        return XUIJavaScriptError(result)
    finally:
        JavaScriptCore.JSStringRelease(string)


@assert_message_queue
def register_global_context(gbl_ctx):
    gbl_ctx = cast(gbl_ctx, JSGlobalContextRef)
    gbl_obj = JavaScriptCore.JSContextGetGlobalObject(gbl_ctx)
    _context_registry[gbl_obj] = gbl_ctx
    _context_set.add(gbl_ctx.value)


@assert_message_queue
def unregister_global_context(gbl_ctx):
    gbl_ctx = cast(gbl_ctx, JSGlobalContextRef)
    gbl_obj = JavaScriptCore.JSContextGetGlobalObject(gbl_ctx)
    del _context_registry[gbl_obj]
    _context_set.remove(gbl_ctx.value)


@assert_message_queue
def inject_object(gbl_ctx, name, obj):
    exception = JSValueRef()
    gbl_ctx = JSGlobalContextRef(gbl_ctx)
    _name = JavaScriptCore.JSStringCreateWithUTF8CString(name.encode('utf-8'))
    try:
        _obj = _to_js_value(gbl_ctx, obj)
        global_obj = JavaScriptCore.JSContextGetGlobalObject(gbl_ctx)
        JavaScriptCore.JSObjectSetProperty(gbl_ctx, global_obj, _name, _obj, 0, byref(exception))
        if exception.value is not None:
            raise parse_exception(exception.value)
    finally:
        JavaScriptCore.JSStringRelease(_name)
