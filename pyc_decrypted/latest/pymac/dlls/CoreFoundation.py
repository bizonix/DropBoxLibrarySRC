#Embedded file name: pymac/dlls/CoreFoundation.py
from __future__ import absolute_import
from ctypes import c_char, c_char_p, c_int, c_int32, c_short, c_ubyte, c_ulong, c_void_p, POINTER
from ..types import CFAllocatorRef, CFArrayCallBacks, CFArrayRef, CFDataRef, CFDictionaryKeyCallBacks, CFDictionaryRef, CFDictionaryValueCallBacks, CFErrorRef, CFIndex, CFMutableArrayRef, CFNumberRef, CFNumberType, CFPropertyListRef, CFRunLoopRef, CFRunLoopSourceRef, CFStringEncoding, CFStringRef, CFTimeInterval, CFTypeRef, CFUUIDRef, CFUUIDBytes, CFURLPathStyle, CFURLRef, FSRef, UInt8, Boolean, CFTypeID, UniChar
from ..lazydll import FakeDLL
from ..lazyframework import LazyFramework

class CoreFoundation(LazyFramework):

    def __init__(self):
        super(CoreFoundation, self).__init__()
        self._dllname = u'CoreFoundation'
        self._func_defs = {}

        def F(name, ret = None, args = []):
            self._func_defs[name] = {'restype': ret,
             'argtypes': args}

        def C(name, const_type):
            self._const_defs[name] = const_type

        F('CFRetain', CFTypeRef, [CFTypeRef])
        F('CFRelease', None, [CFTypeRef])
        F('CFGetTypeID', c_ulong, [CFPropertyListRef])
        F('CFCopyTypeIDDescription', CFStringRef, [c_ulong])
        F('CFArrayCreate', CFArrayRef, [CFAllocatorRef,
         POINTER(c_void_p),
         CFIndex,
         POINTER(CFArrayCallBacks)])
        F('CFArrayCreateMutable', CFArrayRef, [CFAllocatorRef, CFIndex, POINTER(CFArrayCallBacks)])
        F('CFArrayCreateMutableCopy', CFMutableArrayRef, [CFAllocatorRef, CFIndex, CFArrayRef])
        F('CFArrayAppendValue', None, [CFMutableArrayRef, c_void_p])
        F('CFArrayGetCount', c_ulong, [CFArrayRef])
        F('CFArrayGetTypeID', c_ulong)
        F('CFArrayGetValueAtIndex', c_void_p, [CFArrayRef, c_ulong])
        F('CFArrayRemoveValueAtIndex', None, [CFMutableArrayRef, CFIndex])
        F('CFBooleanGetTypeID', c_ulong)
        F('CFBooleanGetValue', bool, [c_void_p])
        F('CFDictionaryCreate', CFDictionaryRef, [CFAllocatorRef,
         POINTER(c_void_p),
         POINTER(c_void_p),
         CFIndex,
         POINTER(CFDictionaryKeyCallBacks),
         POINTER(CFDictionaryValueCallBacks)])
        F('CFDictionaryGetTypeID', c_ulong)
        F('CFDictionaryGetValue', c_void_p, [CFDictionaryRef, c_void_p])
        F('CFDictionaryGetKeysAndValues', None, [CFDictionaryRef, POINTER(c_void_p), POINTER(c_void_p)])
        F('CFDictionaryGetCount', c_ulong, [CFDictionaryRef])
        F('CFNumberGetTypeID', c_ulong)
        F('CFNumberGetValue', Boolean, [CFNumberRef, CFNumberType, c_void_p])
        F('CFNumberGetType', CFNumberType, [CFNumberRef])
        F('CFPreferencesCopyAppValue', CFPropertyListRef, [CFStringRef, CFStringRef])
        F('CFPreferencesSetAppValue', None, [CFStringRef, CFPropertyListRef, CFStringRef])
        F('CFPreferencesAppSynchronize', Boolean, [CFStringRef])
        F('CFPreferencesSetValue', None, [CFStringRef,
         CFPropertyListRef,
         CFStringRef,
         CFStringRef,
         CFStringRef])
        F('CFStringCreateWithCString', CFStringRef, [CFAllocatorRef, c_char_p, CFStringEncoding])
        F('CFStringCreateWithCharacters', CFStringRef, [CFAllocatorRef, POINTER(UniChar), CFIndex])
        F('CFStringGetCString', c_short, [CFStringRef,
         c_char_p,
         c_int32,
         CFStringEncoding])
        F('CFStringGetCStringPtr', c_char_p, [CFStringRef, CFStringEncoding])
        F('CFStringGetLength', c_int32, [CFStringRef])
        F('CFStringGetMaximumSizeForEncoding', c_int32, [c_int32, CFStringEncoding])
        F('CFStringGetTypeID', c_ulong, [])
        F('CFDataGetTypeID', CFTypeID, [])
        F('CFDataGetLength', CFIndex, [CFDataRef])
        F('CFDataGetBytePtr', POINTER(UInt8), [CFDataRef])
        F('CFRunLoopGetCurrent', c_void_p)
        F('CFRunLoopStop', None, [c_void_p])
        F('CFRunLoopRun')
        F('CFRunLoopRunInMode', c_int, [CFStringRef, CFTimeInterval, c_ubyte])
        F('CFRunLoopAddSource', None, [CFRunLoopRef, CFRunLoopSourceRef, CFStringRef])
        F('CFRunLoopSourceInvalidate', None, [CFRunLoopSourceRef])
        F('CFURLCreateFromFSRef', CFURLRef, [CFAllocatorRef, POINTER(FSRef)])
        F('CFURLCreateWithFileSystemPath', CFURLRef, [CFAllocatorRef,
         CFStringRef,
         CFURLPathStyle,
         Boolean])
        F('CFURLGetFileSystemRepresentation', Boolean, [CFURLRef,
         Boolean,
         c_char_p,
         CFIndex])
        F('CFURLGetTypeID', CFTypeID, [])
        F('CFURLGetString', CFStringRef, [CFURLRef])
        F('CFURLCopyPath', CFStringRef, [CFURLRef])
        F('CFURLCopyFileSystemPath', CFStringRef, [CFURLRef, CFURLPathStyle])
        F('CFURLCopyResourcePropertyForKey', Boolean, [CFURLRef,
         CFStringRef,
         c_void_p,
         POINTER(CFErrorRef)])
        F('CFUUIDCreateString', CFStringRef, [CFAllocatorRef, CFUUIDRef])
        F('CFUUIDGetTypeID', CFTypeID, [])
        F('CFUUIDGetUUIDBytes', CFUUIDBytes, [CFUUIDRef])
        C('kCFTypeArrayCallBacks', CFArrayCallBacks)
        C('kCFPreferencesAnyApplication', CFStringRef)
        C('kCFPreferencesAnyHost', CFStringRef)
        C('kCFPreferencesAnyUser', CFStringRef)
        C('kCFPreferencesCurrentApplication', CFStringRef)
        C('kCFPreferencesCurrentHost', CFStringRef)
        C('kCFPreferencesCurrentUser', CFStringRef)
        C('kCFRunLoopDefaultMode', CFStringRef)
        C('kCFRunLoopCommonModes', CFStringRef)
        C('kCFURLIsAliasFileKey', CFStringRef)


Core = FakeDLL(CoreFoundation)
