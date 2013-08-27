#Embedded file name: pymac/types.py
from __future__ import absolute_import
from ctypes import CFUNCTYPE, POINTER, Structure, c_char, c_char_p, c_double, c_float, c_int, c_int16, c_int32, c_int64, c_int8, c_long, c_short, c_size_t, c_ubyte, c_uint, c_uint16, c_uint32, c_uint64, c_uint8, c_ulong, c_void_p, c_ushort
from itertools import izip
UInt8 = c_uint8
UInt16 = c_uint16
UInt32 = c_uint32
SInt8 = c_int8
SInt16 = c_int16
SInt32 = c_int32
SInt64 = c_int64
Float32 = c_float
Float64 = c_double
UniChar = c_uint16
UniCharCount = c_uint32
Ptr = c_char_p
Handle = POINTER(Ptr)
Size = c_long
OSErr = SInt16
OSStatus = c_int32
OSType = c_uint32
ICAError = OSErr
Fixed = c_long
Boolean = c_uint8

class ProcessSerialNumber(Structure):
    _fields_ = [('highLongOfPSN', UInt32), ('lowLongOfPSN', UInt32)]
    _pack_ = 2


Boolean = c_uint8
CFAllocatorRef = c_void_p
CFArrayRef = c_void_p
CFDataRef = c_void_p
CFBooleanRef = c_void_p
CFErrorRef = c_void_p
CFHashCode = c_ulong
CFIndex = c_long
CFMutableArrayRef = c_void_p
CFNumberRef = c_void_p
CFNumberType = c_int
CFPropertyListRef = c_void_p
CFRunLoopSourceRef = c_void_p
CFRunLoopRef = c_void_p
CFStringEncoding = c_uint32
CFStringRef = c_void_p
CFTimeInterval = c_double
CFTypeRef = c_void_p
CFUUIDRef = c_void_p
DADiskRef = c_void_p
DASessionRef = c_void_p
CFIndex = c_long
CFTypeID = c_ulong
CFURLPathStyle = c_int
CFURLRef = c_void_p
LSSharedFileListRef = c_void_p
LSSharedFileListItemRef = c_void_p
IconRef = c_void_p
dev_t = c_int32

class CFDictionaryRef(c_void_p):
    pass


CFArrayRetainCallBack = CFUNCTYPE(c_void_p, CFAllocatorRef, c_void_p)
CFArrayReleaseCallBack = CFUNCTYPE(None, CFAllocatorRef, c_void_p)
CFArrayCopyDescriptionCallBack = CFUNCTYPE(CFStringRef, c_void_p)
CFArrayEqualCallBack = CFUNCTYPE(Boolean, c_void_p, c_void_p)

class CFUUIDBytes(Structure):
    _fields_ = [('byte0', UInt8),
     ('byte1', UInt8),
     ('byte2', UInt8),
     ('byte3', UInt8),
     ('byte4', UInt8),
     ('byte5', UInt8),
     ('byte6', UInt8),
     ('byte7', UInt8),
     ('byte8', UInt8),
     ('byte9', UInt8),
     ('byte10', UInt8),
     ('byte11', UInt8),
     ('byte12', UInt8),
     ('byte13', UInt8),
     ('byte14', UInt8),
     ('byte15', UInt8)]

    def buf(self):
        return ''.join((chr(getattr(self, d[0])) for d in self._fields_))


class CFArrayCallBacks(Structure):
    _fields_ = [('version', CFIndex),
     ('retain', CFArrayRetainCallBack),
     ('release', CFArrayReleaseCallBack),
     ('copyDescription', CFArrayCopyDescriptionCallBack),
     ('equal', CFArrayEqualCallBack)]


CFDictionaryRetainCallBack = CFUNCTYPE(c_void_p, CFAllocatorRef, c_void_p)
CFDictionaryReleaseCallBack = CFUNCTYPE(None, CFAllocatorRef, c_void_p)
CFDictionaryCopyDescriptionCallBack = CFUNCTYPE(CFStringRef, c_void_p)
CFDictionaryEqualCallBack = CFUNCTYPE(Boolean, c_void_p, c_void_p)
CFDictionaryHashCallBack = CFUNCTYPE(CFHashCode, c_void_p)

class CFDictionaryKeyCallBacks(Structure):
    _fields_ = [('version', CFIndex),
     ('retain', CFDictionaryRetainCallBack),
     ('release', CFDictionaryReleaseCallBack),
     ('copyDescription', CFDictionaryCopyDescriptionCallBack),
     ('equal', CFDictionaryEqualCallBack),
     ('hash', CFDictionaryHashCallBack)]


class CFDictionaryValueCallBacks(Structure):
    _fields_ = [('version', CFIndex),
     ('retain', CFDictionaryRetainCallBack),
     ('release', CFDictionaryReleaseCallBack),
     ('copyDescription', CFDictionaryCopyDescriptionCallBack),
     ('equal', CFDictionaryEqualCallBack)]


class CFRange(Structure):
    _fields_ = [('location', CFIndex), ('length', CFIndex)]


FSEventStreamRef = c_void_p
FSEventStreamEventFlags = c_uint32
FSEventStreamEventId = c_uint64
FSEventStreamCreateFlags = c_uint32
FSEventStreamCallback = CFUNCTYPE(None, FSEventStreamRef, c_void_p, c_size_t, POINTER(c_char_p), POINTER(FSEventStreamEventFlags), POINTER(FSEventStreamEventId))

class FSEventStreamContext(Structure):
    _fields_ = [('version', CFIndex),
     ('info', c_void_p),
     ('retain', c_void_p),
     ('release', c_void_p),
     ('copyDescription', c_void_p)]


ByteCount = c_ulong
ItemCount = c_ulong
FSCatalogInfoBitmap = c_uint32
TextEncoding = c_uint32
FSVolumeInfoBitmap = c_uint32
FSVolumeRefNum = c_int16
FSVolumeInfo = c_void_p
StrFileName = Str63 = c_char * 64

class Point(Structure):
    _fields_ = [('v', c_short), ('h', c_short)]


class UTCDateTime(Structure):
    _pack_ = 2
    _fields_ = [('highSeconds', c_uint16), ('lowSeconds', c_uint32), ('fraction', c_uint16)]


class FSSpec(Structure):
    _pack_ = 2
    _fields_ = [('vRefNum', c_short), ('parID', c_long), ('name', StrFileName)]


class HFSUniStr255(Structure):
    _pack_ = 2
    _fields_ = [('length', c_uint16), ('unicode', UniChar * 255)]


class FileInfo(Structure):
    _fields_ = [('fileType', OSType),
     ('fileCreator', OSType),
     ('finderFlags', c_uint16),
     ('location', Point),
     ('reservedField', c_uint16)]


class FSCatalogInfo(Structure):
    _fields_ = [('nodeFlags', c_uint16),
     ('volume', FSVolumeRefNum),
     ('parentDirID', c_uint32),
     ('nodeID', c_uint32),
     ('sharingFlags', c_uint8),
     ('userPrivileges', c_uint8),
     ('reserved1', c_uint8),
     ('reserved2', c_uint8),
     ('createDate', UTCDateTime),
     ('contentModDate', UTCDateTime),
     ('attributeModDate', UTCDateTime),
     ('accessDate', UTCDateTime),
     ('backupDate', UTCDateTime),
     ('permissions', c_uint32 * 4),
     ('finderInfo', FileInfo),
     ('extFinderInfo', c_uint8 * 16),
     ('dataLogicalSize', c_uint64),
     ('dataPhysicalSize', c_uint64),
     ('rsrcLogicalSize', c_uint64),
     ('rsrcPhysicalSize', c_uint64),
     ('valence', c_uint32),
     ('textEncodingHint', TextEncoding)]


class GetVolParmsInfoBuffer(Structure):
    _pack_ = 2
    _fields_ = [('vMVersion', c_int16),
     ('vMAttrib', c_int32),
     ('vMLocalHand', Handle),
     ('vMServerAdr', c_int32),
     ('vMVolumeGrade', c_int32),
     ('vMForeignPrivID', c_int16),
     ('vMExtendedAttributes', c_int32),
     ('vMDeviceID', c_void_p),
     ('vMMaxNameLength', UniCharCount)]


SecAccessRef = c_void_p
SecItemClass = OSType
SecKeychainItemRef = c_void_p
SecKeychainRef = c_void_p
SecTrustedApplicationRef = c_void_p
SecACLRef = c_void_p
CSSM_ACL_AUTHORIZATION_TAG = c_int32
AuthorizationString = c_char_p

class SecKeychainAttribute(Structure):
    _fields_ = [('tag', OSType), ('length', c_uint32), ('data', c_char_p)]


class SecKeychainAttributeList(Structure):
    _fields_ = [('count', c_uint32), ('attr', POINTER(SecKeychainAttribute))]

    @staticmethod
    def from_attrs(attr_dict):
        ret = SecKeychainAttributeList()
        ret.count = len(attr_dict)
        ret.attr = (SecKeychainAttribute * ret.count)()
        for attr, (tag, data) in izip(ret.attr, attr_dict.iteritems()):
            attr.tag = tag
            data = data.encode('utf-8')
            attr.data = data
            attr.length = len(data)

        return ret


class AuthorizationItem(Structure):
    _fields_ = [('name', AuthorizationString),
     ('valueLength', c_uint32),
     ('value', c_char_p),
     ('flags', c_uint32)]


class AuthorizationItemSet(Structure):
    _fields_ = [('count', c_uint32), ('items', POINTER(AuthorizationItem))]


AuthorizationRights = AuthorizationItemSet
AuthorizationEnvironment = AuthorizationItemSet
AuthorizationFlags = c_uint32
AuthorizationRef = c_void_p

class CSSM_ACL_KEYCHAIN_PROMPT_SELECTOR(Structure):
    _fields_ = [('version', c_uint16), ('flags', c_uint16)]


class FSRef(Structure):
    _fields_ = [('hidden', c_uint8 * 80)]


class ICAHeader(Structure):
    _fields_ = [('err', ICAError), ('refcon', c_ulong)]
    _pack_ = 2

    def __repr__(self):
        return 'ICAHeader(%r, %r)' % (self.err, self.refcon)


ICAObject = UInt32
ICACompletion = c_void_p

class ICADownloadFilePB(Structure):
    _fields_ = [('header', ICAHeader),
     ('object', ICAObject),
     ('dirFSRef', POINTER(FSRef)),
     ('flags', c_uint32),
     ('fileType', OSType),
     ('fileCreator', OSType),
     ('rotationAngle', Fixed),
     ('fileFSRef', POINTER(FSRef))]
    _pack_ = 2


class ICACopyObjectPropertyDictionaryPB(Structure):
    _fields_ = [('header', ICAHeader), ('object', ICAObject), ('theDict', POINTER(CFDictionaryRef))]
    _pack_ = 2


class ICACopyObjectDataPB(Structure):
    _fields_ = [('header', ICAHeader),
     ('object', ICAObject),
     ('startByte', c_size_t),
     ('requestedSize', c_size_t),
     ('data', POINTER(CFDataRef))]
    _pack_ = 2


class ICAGetDeviceListPB(Structure):
    _fields_ = [('header', ICAHeader), ('object', ICAObject)]
    _pack_ = 2


kern_return_t = c_int

class mach_timebase_info(Structure):
    _fields_ = [('numer', c_uint32), ('denom', c_uint32)]


mach_timebase_info_t = POINTER(mach_timebase_info)
sig_handler_t = CFUNCTYPE(c_int, c_int)

class timeval(Structure):
    _fields_ = [('tv_sec', c_long), ('tv_nsec', c_long)]

    def __repr__(self):
        return 'timeval(tv_sec=%d, tv_nsec=%d)' % (self.tv_sec, self.tv_nsec)

    def __float__(self):
        return self.tv_sec + float(self.tv_nsec) / 1000000000.0


class FILE(Structure):
    pass


close_FILE_func_t = CFUNCTYPE(c_int, POINTER(FILE))
integer_t = c_int
natural_t = c_uint

class time_value_t(Structure):
    _fields_ = (('seconds', integer_t), ('microseconds', integer_t))


policy_t = c_int

class task_basic_info(Structure):
    _pack_ = 4
    _fields_ = (('suspend_count', integer_t),
     ('virtual_size', natural_t),
     ('resident_size', natural_t),
     ('user_time', time_value_t),
     ('system_time', time_value_t),
     ('policy', policy_t))


class thread_basic_info(Structure):
    _pack_ = 4
    _fields_ = (('user_time', time_value_t),
     ('system_time', time_value_t),
     ('cpu_usage', integer_t),
     ('policy', policy_t),
     ('run_state', integer_t),
     ('flags', integer_t),
     ('suspend_count', integer_t),
     ('sleep_time', integer_t))


mach_msg_type_number_t = natural_t
mach_msg_type_number_t_p = POINTER(mach_msg_type_number_t)
mach_port_name_t = natural_t
mach_port_name_t_p = POINTER(mach_port_name_t)
mach_port_t = mach_port_name_t
task_t = mach_port_t
task_flavor_t = natural_t
task_info_t = POINTER(integer_t)
task_name_t = mach_port_t
task_port_t = task_t
thread_flavor_t = natural_t
thread_info_t = POINTER(integer_t)

class fsid_t(Structure):
    _fields_ = [('val', c_int32 * 2)]


MFSNAMELEN = 15
MNAMELEN = 90

class struct_statfs(Structure):
    _fields_ = [('f_otype', c_short),
     ('f_oflags', c_short),
     ('f_bsize', c_long),
     ('f_iosize', c_long),
     ('f_blocks', c_long),
     ('f_bfree', c_long),
     ('f_bavail', c_long),
     ('f_files', c_long),
     ('f_ffree', c_long),
     ('f_fsid', fsid_t),
     ('f_owner', c_long),
     ('f_reserved1', c_short),
     ('f_type', c_short),
     ('f_flags', c_long),
     ('f_reserved2', c_long * 2),
     ('f_fstypename', c_char * MFSNAMELEN),
     ('f_mntonname', c_char * MNAMELEN),
     ('f_mntfromname', c_char * MNAMELEN),
     ('f_reserved3', c_char),
     ('f_reserved4', c_long * 4)]


fsobj_type_t = c_uint32
attrgroup_t = c_uint32

class struct_attrlist(Structure):
    _fields_ = (('bitmapcount', c_ushort),
     ('reserved', c_uint16),
     ('commonattr', attrgroup_t),
     ('volattr', attrgroup_t),
     ('dirattr', attrgroup_t),
     ('fileattr', attrgroup_t),
     ('forkattr', attrgroup_t))


class attrreference_t(Structure):
    _fields_ = [('attr_dataoffset', c_int32), ('attr_length', c_uint32)]


io_registry_entry_t = c_void_p
io_service_t = c_void_p
mach_port_t = c_void_p
IOOptionBits = UInt32
SCDynamicStoreRef = c_void_p
SCDynamicStoreCallback = CFUNCTYPE(None, SCDynamicStoreRef, CFArrayRef, c_void_p)

class SCDynamicStoreContext(Structure):
    _fields_ = [('version', CFIndex),
     ('info', c_void_p),
     ('retain', c_void_p),
     ('release', c_void_p),
     ('copyDescription', CFStringRef)]


ByteArraySize4Type = c_uint8 * 4
ByteArraySize8Type = c_uint8 * 8
ByteArraySize12Type = c_uint8 * 12
ByteArraySize16Type = c_uint8 * 16
ByteArraySize254Type = c_uint8 * 254

class sockaddr_in(Structure):
    _fields_ = [('sin_len', c_uint8),
     ('sin_family', c_uint8),
     ('sin_port', c_uint16),
     ('sin_addr', ByteArraySize4Type),
     ('sin_zero', ByteArraySize8Type)]


class sockaddr_in6(Structure):
    _fields_ = [('sin6_len', c_uint8),
     ('sin6_family', c_uint8),
     ('sin6_port', c_uint16),
     ('sin6_flowinfo', c_uint32),
     ('sin6_addr', ByteArraySize16Type),
     ('sin6_scope_id', c_uint32)]


class sockaddr_dl(Structure):
    _fields_ = [('sdl_len', c_uint8),
     ('sdl_family', c_uint8),
     ('sdl_index', c_short),
     ('sdl_type', c_uint8),
     ('sdl_nlen', c_uint8),
     ('sdl_alen', c_uint8),
     ('sdl_slen', c_uint8),
     ('sdl_data', ByteArraySize12Type)]


class sockaddr(Structure):
    _fields_ = [('sa_len', c_uint8), ('sa_family', c_uint8), ('sa_data', ByteArraySize254Type)]


class ifaddrs(Structure):
    pass


ifaddrs._fields_ = [('ifa_next', POINTER(ifaddrs)),
 ('ifa_name', c_char_p),
 ('ifa_flags', c_uint),
 ('ifa_addr', POINTER(sockaddr)),
 ('ifa_netmask', POINTER(sockaddr)),
 ('ifa_dstaddr', POINTER(sockaddr)),
 ('ifa_data', c_void_p)]
