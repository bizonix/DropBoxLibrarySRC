#Embedded file name: pymac/helpers/core.py
from __future__ import absolute_import
import contextlib
import ctypes
import operator
import uuid
import os
from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
from UserDict import DictMixin
from ..constants import kCFAllocatorDefault, kCFNumberCFIndexType, kCFNumberCharType, kCFNumberDoubleType, kCFNumberFloat32Type, kCFNumberFloat64Type, kCFNumberFloatType, kCFNumberIntType, kCFNumberLongLongType, kCFNumberLongType, kCFNumberSInt16Type, kCFNumberSInt32Type, kCFNumberSInt64Type, kCFNumberSInt8Type, kCFNumberShortType, kCFURLPOSIXPathStyle, kCFStringEncodingMacRoman, kCFStringEncodingUTF8
from ..types import Boolean, CFStringRef, CFArrayRef, CFDictionaryRef, FSRef, SInt8, SInt16, SInt32, SInt64, Float32, Float64, CFIndex, CFErrorRef, CFBooleanRef
from ..dlls import Core, CoreServices
from ..dlls.CoreServices import OSStatusError
CFRelease = Core.CFRelease

def python_object_to_cfstringref(ref):
    if isinstance(ref, unicode):
        ref = Core.CFStringCreateWithCString(kCFAllocatorDefault, ref.encode('utf-8'), kCFStringEncodingUTF8)
    elif isinstance(ref, str):
        ref = Core.CFStringCreateWithCString(kCFAllocatorDefault, ref, kCFStringEncodingUTF8)
    else:
        raise NotImplementedError("Can't cast a CFString from this object! %r" % ref)
    return ref


class CFString(object):

    def __init__(self, ref, take_ownership = False):
        if not isinstance(ref, CFStringRef):
            ref = CFStringRef(ref)
        if Core.CFGetTypeID(ref) != Core.CFStringGetTypeID():
            raise ValueError('Ref type id was not an CFString type')
        self.value = ref
        if not take_ownership:
            Core.CFRetain(ref)

    def get_ref(self):
        return self.value

    @classmethod
    def from_python(cls, ref):
        return cls(python_object_to_cfstringref(ref), take_ownership=True)

    @staticmethod
    def to_unicode(cfstringref):
        if not cfstringref:
            return u''
        p = Core.CFStringGetCStringPtr(cfstringref, kCFStringEncodingMacRoman)
        if p:
            return p.decode('mac-roman')
        p = Core.CFStringGetCStringPtr(cfstringref, kCFStringEncodingUTF8)
        if p:
            return p.decode('utf-8')
        length = 1 + Core.CFStringGetMaximumSizeForEncoding(Core.CFStringGetLength(cfstringref), kCFStringEncodingUTF8)
        buf = ctypes.create_string_buffer(length)
        if not Core.CFStringGetCString(cfstringref, buf, length, kCFStringEncodingUTF8):
            raise Exception("Couldn't convert string")
        return buf.value.decode('utf-8')

    def __unicode__(self):
        return self.to_unicode(self.value)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        if Core._debug:
            return '<CFString(%r)>' % self.value
        return unicode(self)

    def __del__(self):
        if self.value:
            Core.CFRelease(self.value)


class CFArray(object):

    def __init__(self, ref, take_ownership = False):
        if not isinstance(ref, CFArrayRef):
            ref = CFArrayRef(ref)
        if Core.CFGetTypeID(ref) != Core.CFArrayGetTypeID():
            raise ValueError('ref type was not an CFArray type')
        self.value = ref
        if not take_ownership:
            Core.CFRetain(ref)

    def get_ref(self):
        return self.value

    def __getitem__(self, key):
        if isinstance(key, slice):
            raise NotImplementedError('__getitem__ for slices is not yet implemented')
        else:
            i = operator.index(key)
            return property_to_python(Core.CFArrayGetValueAtIndex(self.value, i))

    def __setitem__(self, key, value):
        raise NotImplementedError('__setitem__ for CFArray is not yet implemented')

    def refs(self):
        for i in xrange(Core.CFArrayGetCount(self.value)):
            yield Core.CFArrayGetValueAtIndex(self.value, i)

    def __nonzero__(self):
        return Core.CFArrayGetCount(self.value) != 0

    def __iter__(self):
        for ref in self.refs():
            yield property_to_python(ref)

    def __del__(self):
        if self.value:
            Core.CFRelease(self.value)

    def __repr__(self):
        return 'CFArray(%r)' % (list(self),)


class CFDictionary(object, DictMixin):
    __slots__ = ['value']

    def __init__(self, ref, take_ownership = False):
        if not isinstance(ref, CFDictionaryRef):
            ref = CFDictionaryRef(ref)
        if Core.CFGetTypeID(ref) != Core.CFDictionaryGetTypeID():
            raise ValueError('ref type was not a dictionary type')
        self.value = ref
        if not take_ownership:
            Core.CFRetain(ref)

    def get_ref(self):
        return self.value

    def __getitem__(self, key):
        with releasing(python_to_property(key)) as keyref:
            ref = Core.CFDictionaryGetValue(self.value, keyref)
            if ref:
                return property_to_python(ref)
            raise KeyError(key)

    def __setitem__(self, key, value):
        raise NotImplemented('__setitem__')

    def __delitem__(self, key):
        raise NotImplemented('__delitem__')

    def keys(self):
        cnt = Core.CFDictionaryGetCount(self.value)
        keys = (ctypes.c_void_p * cnt)()
        Core.CFDictionaryGetKeysAndValues(self.value, keys, None)
        return [ property_to_python(i) for i in keys ]

    def __del__(self):
        if self.value:
            Core.CFRelease(self.value)

    def __repr__(self):
        return 'CFDictionary(%r)' % (dict(self),)


class FS(FSRef):

    def __init__(self, ref = None):
        super(FS, self).__init__()
        if isinstance(ref, unicode):
            CoreServices.FSPathMakeRef(ref.encode('utf-8'), ctypes.byref(self), None)
        elif isinstance(ref, str):
            CoreServices.FSPathMakeRef(ref, ctypes.byref(self), None)
        elif ref:
            self.value = ref

    def pointer(self):
        return ctypes.cast(ctypes.pointer(self), ctypes.POINTER(FSRef))

    @staticmethod
    def to_unicode(fsref):
        if not fsref:
            return u''
        buf = ctypes.create_string_buffer(1024)
        CoreServices.FSRefMakePath(ctypes.byref(fsref), buf, 1024)
        return buf.value.decode('utf-8')

    def __unicode__(self):
        return self.to_unicode(self)


def property_to_python(value):
    tid = Core.CFGetTypeID(value)
    if tid == Core.CFArrayGetTypeID():
        return CFArray(value)
    if tid == Core.CFStringGetTypeID():
        return CFString.to_unicode(value)
    if tid == Core.CFNumberGetTypeID():
        number_type = Core.CFNumberGetType(value)
        res = {kCFNumberSInt8Type: SInt8,
         kCFNumberSInt16Type: SInt16,
         kCFNumberSInt32Type: SInt32,
         kCFNumberSInt64Type: SInt64,
         kCFNumberFloat32Type: Float32,
         kCFNumberFloat64Type: Float64,
         kCFNumberCharType: ctypes.c_char,
         kCFNumberShortType: ctypes.c_short,
         kCFNumberIntType: ctypes.c_int,
         kCFNumberLongType: ctypes.c_long,
         kCFNumberLongLongType: ctypes.c_longlong,
         kCFNumberFloatType: ctypes.c_float,
         kCFNumberDoubleType: ctypes.c_double,
         kCFNumberCFIndexType: CFIndex}[number_type]
        a = res()
        if Core.CFNumberGetValue(value, number_type, ctypes.byref(a)):
            return a.value
        raise Exception('Unable to convert number to int')
    else:
        if tid == Core.CFUUIDGetTypeID():
            return uuid.UUID(bytes=Core.CFUUIDGetUUIDBytes(value).buf())
        if tid == Core.CFDictionaryGetTypeID():
            return CFDictionary(value)
        if tid == Core.CFBooleanGetTypeID():
            return Core.CFBooleanGetValue(value)
        if tid == Core.CFURLGetTypeID():
            return CFString.to_unicode(Core.CFURLGetString(value))
        if tid == Core.CFDataGetTypeID():
            return ctypes.string_at(Core.CFDataGetBytePtr(value), Core.CFDataGetLength(value))
        return 'Unable to convert Property type %s (%d)' % (CFString(Core.CFCopyTypeIDDescription(tid), take_ownership=True), tid)


def python_to_property(obj):
    try:
        return python_object_to_cfstringref(obj)
    except NotImplementedError:
        pass

    if isinstance(obj, list):
        ret = Core.CFArrayCreateMutable(None, 0, ctypes.byref(Core.kCFTypeArrayCallBacks))
        for item in obj:
            with releasing(python_to_property(item)) as cf_item:
                Core.CFArrayAppendValue(ret, cf_item)

        return ret
    if obj is None:
        return
    raise NotImplementedError("don't know how to handle %r" % obj)


def get_preference(application, property_key):
    with releasing(python_to_property(application)) as appid:
        with releasing(python_to_property(property_key)) as key:
            Core.CFPreferencesAppSynchronize(appid)
            with releasing(Core.CFPreferencesCopyAppValue(key, appid)) as value:
                if value:
                    return property_to_python(value)
                raise KeyError(property_key)


def set_preference(application, property_key, value, this_host_only = False):
    with releasing(python_to_property(application)) as appid:
        with releasing(python_to_property(property_key)) as key:
            with releasing(python_to_property(value)) as val:
                if this_host_only:
                    Core.CFPreferencesSetValue(key, val, appid, Core.kCFPreferencesCurrentUser, Core.kCFPreferencesCurrentHost)
                else:
                    Core.CFPreferencesSetAppValue(key, val, appid)
                Core.CFPreferencesAppSynchronize(appid)


class Preference(DictMixin):

    def __init__(self, application, host_only = False):
        self.app = application
        self.host_only = host_only

    def __getitem__(self, key):
        return get_preference(self.app, key)

    def __setitem__(self, key, item):
        return set_preference(self.app, key, item, self.host_only)


def is_alias_file(path):
    if os.path.islink(path) or os.path.isdir(path):
        return False
    if MAC_VERSION >= SNOW_LEOPARD:
        path_cfstr = CFString.from_python(path)
        ret = False
        with releasing(Core.CFURLCreateWithFileSystemPath(kCFAllocatorDefault, path_cfstr.get_ref(), kCFURLPOSIXPathStyle, 0)) as cf_url:
            if not cf_url:
                return False
            with releasing(CFBooleanRef()) as aliasProperty:
                with releasing(CFErrorRef()) as error_ref:
                    ret = Core.CFURLCopyResourcePropertyForKey(cf_url, Core.kCFURLIsAliasFileKey, ctypes.byref(aliasProperty), ctypes.byref(error_ref))
                    if not ret:
                        return False
                    is_alias = aliasProperty and Core.CFBooleanGetValue(aliasProperty)
        return is_alias
    path_ref = FS(path)
    is_alias = Boolean(False)
    is_folder = Boolean(False)
    CoreServices.FSIsAliasFile(ctypes.byref(path_ref), ctypes.byref(is_alias), ctypes.byref(is_folder))
    if is_alias:
        return True
    return False


@contextlib.contextmanager
def releasing(ref):
    try:
        yield ref
    finally:
        if ref:
            CFRelease(ref)
