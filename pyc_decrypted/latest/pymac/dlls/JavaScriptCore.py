#Embedded file name: pymac/dlls/JavaScriptCore.py
from ctypes import Structure, POINTER, c_size_t, c_char_p, c_double, c_bool, c_int, CFUNCTYPE, c_void_p, c_uint
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework
kJSTypeUndefined = 0
kJSTypeNull = 1
kJSTypeBoolean = 2
kJSTypeNumber = 3
kJSTypeString = 4
kJSTypeObject = 5
JSType = c_uint
kJSPropertyAttributeNone = 0
kJSPropertyAttributeReadOnly = 2
kJSPropertyAttributeDontEnum = 4
kJSPropertyAttributeDontDelete = 8
JSPropertyAttributes = c_uint
kJSClassAttributeNone = 0
kJSClassAttributeNoAutomaticPrototype = 2
JSClassAttributes = c_uint
JSContextRef = c_void_p
JSGlobalContextRef = c_void_p
JSObjectRef = c_void_p
JSClassRef = c_void_p
JSStringRef = c_void_p
JSObjectRef = c_void_p
JSValueRef = c_void_p
JSPropertyNameAccumulatorRef = c_void_p
JSObjectInitializeCallback = CFUNCTYPE(c_void_p, JSContextRef, JSObjectRef)
JSObjectFinalizeCallback = CFUNCTYPE(c_void_p, JSObjectRef)
JSObjectHasPropertyCallback = CFUNCTYPE(c_bool, JSContextRef, JSObjectRef, JSStringRef)
JSObjectGetPropertyCallback = CFUNCTYPE(JSValueRef, JSContextRef, JSObjectRef, JSStringRef, POINTER(JSValueRef))
JSObjectSetPropertyCallback = CFUNCTYPE(c_bool, JSContextRef, JSObjectRef, JSStringRef, JSValueRef, POINTER(JSValueRef))
JSObjectDeletePropertyCallback = CFUNCTYPE(c_bool, JSContextRef, JSObjectRef, JSStringRef, POINTER(JSValueRef))
JSObjectGetPropertyNamesCallback = CFUNCTYPE(c_void_p, JSContextRef, JSObjectRef, JSPropertyNameAccumulatorRef)
JSObjectCallAsFunctionCallback = CFUNCTYPE(JSValueRef, JSContextRef, JSObjectRef, JSObjectRef, c_size_t, JSValueRef, POINTER(JSValueRef))
JSObjectCallAsConstructorCallback = CFUNCTYPE(JSObjectRef, JSContextRef, JSObjectRef, c_size_t, JSValueRef, POINTER(JSValueRef))
JSObjectHasInstanceCallback = CFUNCTYPE(c_bool, JSContextRef, JSObjectRef, JSValueRef, POINTER(JSValueRef))
JSObjectConvertToTypeCallback = CFUNCTYPE(JSValueRef, JSContextRef, JSObjectRef, JSType, POINTER(JSValueRef))

class JSStaticValue(Structure):
    _fields_ = [('name', c_char_p),
     ('getProperty', JSObjectGetPropertyCallback),
     ('setProperty', JSObjectSetPropertyCallback),
     ('attributes', JSPropertyAttributes)]


class JSStaticFunction(Structure):
    _fields_ = [('name', c_char_p), ('callAsFunction', JSObjectCallAsFunctionCallback), ('attributes', JSPropertyAttributes)]


class JSClassDefinition(Structure):
    _fields_ = [('version', c_int),
     ('attributes', JSClassAttributes),
     ('className', c_char_p),
     ('parentClass', JSClassRef),
     ('staticValues', POINTER(JSStaticValue)),
     ('staticFunctions', POINTER(JSStaticFunction)),
     ('initialize', JSObjectInitializeCallback),
     ('finalize', JSObjectFinalizeCallback),
     ('hasProperty', JSObjectHasPropertyCallback),
     ('getProperty', JSObjectGetPropertyCallback),
     ('setProperty', JSObjectSetPropertyCallback),
     ('deleteProperty', JSObjectDeletePropertyCallback),
     ('getPropertyNames', JSObjectGetPropertyNamesCallback),
     ('callAsFunction', JSObjectCallAsFunctionCallback),
     ('callAsConstructor', JSObjectCallAsConstructorCallback),
     ('hasInstance', JSObjectHasInstanceCallback),
     ('convertToType', JSObjectConvertToTypeCallback)]


class _JavaScriptCore(LazyFramework):

    def __init__(self):
        super(_JavaScriptCore, self).__init__()
        self._dllname = u'JavaScriptCore'
        self._func_defs = {}

        def F(name, ret = None, args = []):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        F('JSEvaluateScript', JSValueRef, [JSContextRef,
         JSStringRef,
         JSObjectRef,
         JSStringRef,
         c_int,
         POINTER(JSValueRef)])
        F('JSGarbageCollect', None, [JSContextRef])
        F('JSGlobalContextCreate', JSGlobalContextRef, [JSClassRef])
        F('JSGlobalContextRetain', JSGlobalContextRef, [JSGlobalContextRef])
        F('JSGlobalContextRelease', None, [JSGlobalContextRef])
        F('JSContextGetGlobalObject', JSObjectRef, [JSContextRef])
        F('JSClassCreate', JSClassRef, [POINTER(JSClassDefinition)])
        F('JSClassRelease', None, [JSClassRef])
        F('JSClassRetain', JSClassRef, [JSClassRef])
        F('JSObjectMake', JSObjectRef, [JSContextRef, JSClassRef, c_void_p])
        F('JSObjectIsFunction', c_bool, [JSContextRef, JSObjectRef])
        F('JSObjectIsConstructor', c_bool, [JSContextRef, JSObjectRef])
        F('JSObjectGetPrivate', c_void_p, [JSObjectRef])
        F('JSPropertyNameAccumulatorAddName', c_void_p, [JSPropertyNameAccumulatorRef, JSStringRef])
        F('JSObjectSetPrivate', c_bool, [JSObjectRef, c_void_p])
        F('JSObjectDeleteProperty', c_bool, [JSContextRef,
         JSObjectRef,
         JSStringRef,
         POINTER(JSValueRef)])
        F('JSObjectGetProperty', JSValueRef, [JSContextRef,
         JSObjectRef,
         JSStringRef,
         POINTER(JSValueRef)])
        F('JSObjectGetPropertyAtIndex', JSValueRef, [JSContextRef,
         JSObjectRef,
         c_uint,
         POINTER(JSValueRef)])
        F('JSObjectSetProperty', None, [JSContextRef,
         JSObjectRef,
         JSStringRef,
         JSValueRef,
         JSPropertyAttributes,
         POINTER(JSValueRef)])
        F('JSObjectSetPropertyAtIndex', None, [JSContextRef,
         JSObjectRef,
         c_uint,
         JSValueRef,
         POINTER(JSValueRef)])
        F('JSObjectMakeFunction', JSObjectRef, [JSContextRef,
         JSStringRef,
         c_uint,
         JSStringRef,
         JSStringRef,
         JSStringRef,
         c_int,
         POINTER(JSValueRef)])
        F('JSObjectCallAsFunction', JSValueRef, [JSContextRef,
         JSObjectRef,
         JSObjectRef,
         c_size_t,
         JSValueRef,
         POINTER(JSValueRef)])
        F('JSObjectMakeArray', JSObjectRef, [JSContextRef,
         c_size_t,
         JSValueRef,
         POINTER(JSValueRef)])
        F('JSValueToBoolean', c_bool, [JSContextRef, JSValueRef])
        F('JSValueToNumber', c_double, [JSContextRef, JSValueRef, POINTER(JSValueRef)])
        F('JSValueToStringCopy', JSStringRef, [JSContextRef, JSValueRef, POINTER(JSValueRef)])
        F('JSValueToObject', JSObjectRef, [JSContextRef, JSValueRef, POINTER(JSValueRef)])
        F('JSValueMakeUndefined', JSValueRef, [JSContextRef])
        F('JSValueMakeNull', JSValueRef, [JSContextRef])
        F('JSValueMakeBoolean', JSValueRef, [JSContextRef, c_bool])
        F('JSValueMakeNumber', JSValueRef, [JSContextRef, c_double])
        F('JSValueMakeString', JSValueRef, [JSContextRef, JSStringRef])
        F('JSValueIsUndefined', c_bool, [JSContextRef, JSValueRef])
        F('JSValueIsNull', c_bool, [JSContextRef, JSValueRef])
        F('JSValueIsBoolean', c_bool, [JSContextRef, JSValueRef])
        F('JSValueIsNumber', c_bool, [JSContextRef, JSValueRef])
        F('JSValueIsString', c_bool, [JSContextRef, JSValueRef])
        F('JSValueIsObject', c_bool, [JSContextRef, JSValueRef])
        F('JSValueIsObjectOfClass', c_bool, [JSContextRef, JSValueRef, JSClassRef])
        F('JSValueProtect', None, [JSContextRef, JSValueRef])
        F('JSValueUnprotect', None, [JSContextRef, JSValueRef])
        F('JSStringCreateWithUTF8CString', JSStringRef, [c_char_p])
        F('JSStringGetLength', c_size_t, [JSStringRef])
        F('JSStringGetUTF8CString', c_size_t, [JSStringRef, c_char_p, c_size_t])
        F('JSStringRelease', None, [JSStringRef])
        F('JSStringRetain', JSStringRef, [JSStringRef])


JavaScriptCore = FakeDLL(_JavaScriptCore)
