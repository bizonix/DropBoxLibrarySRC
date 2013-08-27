#Embedded file name: pynt/helpers/fileapi.py
import errno
import time
import uuid
from ctypes import addressof, byref, cast, create_string_buffer, create_unicode_buffer, sizeof, string_at, memmove
from ..dlls.kernel32 import kernel32
from ..dlls.advapi32 import advapi32
from ..types import PSECURITY_DESCRIPTOR
from ..headers.windows import FILE_SHARE_READ, FILE_SHARE_WRITE, FILE_SHARE_DELETE, OPEN_EXISTING, INVALID_HANDLE_VALUE, BY_HANDLE_FILE_INFORMATION, FILE_FLAG_BACKUP_SEMANTICS, FILE_FLAG_NO_BUFFERING, REPLACEFILE_WRITE_THROUGH, FILE_FLAG_WRITE_THROUGH, MOVEFILE_REPLACE_EXISTING, FILE_OBJECTID_BUFFER, FSCTL_CREATE_OR_GET_OBJECT_ID, FSCTL_GET_OBJECT_ID, GENERIC_READ, GENERIC_WRITE, WRITE_DAC, READ_CONTROL, WRITE_OWNER, DWORD, BYTE, MAX_PATH, FILE_ATTRIBUTE_NORMAL, FILE_ATTRIBUTE_DIRECTORY, FILE_ATTRIBUTE_NOT_CONTENT_INDEXED, VOLUME_NAME_NT
from ..types import PSECURITY_DESCRIPTOR
from .general import windows_error

def _python_to_c(ctype, str_):
    fit = min(len(str_), sizeof(ctype))
    memmove(addressof(ctype), str(str_), fit)


class ObjectID(object):

    def __init__(self, bytes_):
        assert len(bytes_) == 16, 'ObjectIDs are 16 bytes! %r' % (bytes_,)
        self._bytes = bytes_

    @classmethod
    def generate_random(cls):
        return cls(uuid.uuid4().bytes)

    def to_hex(self):
        return str(self).encode('hex')

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self._bytes

    def __repr__(self):
        return 'ObjectID(%r)' % (str(self),)


class FileObjectID(object):

    def __init__(self, object_id, birth_volume_id, birth_object_id, domain_id):
        self.object_id = object_id
        self.birth_volume_id = birth_volume_id
        self.birth_object_id = birth_object_id
        self.domain_id = domain_id

    @classmethod
    def generate_random(cls):
        return cls(ObjectID.generate_random(), ObjectID.generate_random(), ObjectID.generate_random(), ObjectID.generate_random())

    def __eq__(self, other):
        return type(other) == type(self) and self.object_id == other.object_id

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'FileObjectID(%r, %r, %r, %r)' % (self.object_id,
         self.birth_volume_id,
         self.birth_object_id,
         self.domain_id)

    @classmethod
    def from_file_objectid_buffer(cls, file_objectid_buffer):
        args = []
        for a in ('ObjectId', 'BirthVolumeId', 'BirthObjectId', 'DomainId'):
            oid = getattr(file_objectid_buffer, a)
            args.append(ObjectID(string_at(addressof(oid), sizeof(oid))))

        return cls(*args)


def get_object_id(handle):
    object_id = FILE_OBJECTID_BUFFER()
    bytes_returned = DWORD()
    ret = kernel32.DeviceIoControl(handle, FSCTL_GET_OBJECT_ID, None, 0, byref(object_id), sizeof(object_id), byref(bytes_returned), None)
    if not ret:
        raise windows_error()
    return FileObjectID.from_file_objectid_buffer(object_id)


def create_or_get_object_id(handle):
    object_id = FILE_OBJECTID_BUFFER()
    bytes_returned = DWORD()
    time.sleep(0.001)
    ret = kernel32.DeviceIoControl(handle, FSCTL_CREATE_OR_GET_OBJECT_ID, None, 0, byref(object_id), sizeof(object_id), byref(bytes_returned), None)
    if not ret:
        raise windows_error()
    return FileObjectID.from_file_objectid_buffer(object_id)


def create_file(path, desired_access, share_mode, creation_dispostion, flags_and_attributes, security_attributes = None, template_file = None):
    if security_attributes is not None:
        raise NotImplementedError("Don't support non-None security_attributes yet: %r" % (security_attributes,))
    h = kernel32.CreateFileW(path, desired_access, share_mode, security_attributes, creation_dispostion, flags_and_attributes, template_file)
    if h == INVALID_HANDLE_VALUE:
        raise windows_error(filename=path)
    return h


def _low_high(low, high):
    return high << sizeof(DWORD) * 8 | low


def _filetime_to_int(ft):
    WINDOWS_TICK = 10000000
    SEC_TO_UNIX_EPOCH = 11644473600L
    return _low_high(ft.dwLowDateTime, ft.dwHighDateTime) / WINDOWS_TICK - SEC_TO_UNIX_EPOCH


def get_file_information_by_handle(handle):
    finfo = BY_HANDLE_FILE_INFORMATION()
    ret = kernel32.GetFileInformationByHandle(handle, byref(finfo))
    if not ret:
        raise windows_error()

    class by_handle_file_information(object):
        file_attributes = finfo.dwFileAttributes
        creation_time = _filetime_to_int(finfo.ftCreationTime)
        last_access_time = _filetime_to_int(finfo.ftLastAccessTime)
        last_write_time = _filetime_to_int(finfo.ftLastWriteTime)
        volume_serial_number = finfo.dwVolumeSerialNumber
        file_size = _low_high(finfo.nFileSizeLow, finfo.nFileSizeHigh)
        number_of_links = finfo.nNumberOfLinks
        file_index = _low_high(finfo.nFileIndexLow, finfo.nFileIndexHigh)

    return by_handle_file_information


def close_handle(h):
    if not kernel32.CloseHandle(h):
        raise windows_error()


def replace_file(replaced_file_name, replacement_file_name, replace_flags, backup_file_name = None):
    ret = kernel32.ReplaceFileW(replaced_file_name, replacement_file_name, backup_file_name, replace_flags, None, None)
    if not ret:
        raise windows_error()


def move_file(existing_file_name, new_file_name):
    ret = kernel32.MoveFileW(existing_file_name, new_file_name)
    if not ret:
        raise windows_error()


def move_file_ex(src, dst, replace_existing = False):
    flags = 0
    if replace_existing:
        flags |= MOVEFILE_REPLACE_EXISTING
    ret = kernel32.MoveFileExW(src, dst, flags)
    if not ret:
        raise windows_error()


def get_file_attributes(path):
    return kernel32.GetFileAttributesW(path)


def set_file_attributes(path, attrs):
    return kernel32.SetFileAttributesW(path, attrs)


def get_file_security(path, requested_information):
    sd_size = DWORD()
    ret = advapi32.GetFileSecurityW(path, requested_information, None, 0, byref(sd_size))
    size_necessary = sd_size.value
    sd = create_string_buffer(size_necessary)
    ret = advapi32.GetFileSecurityW(path, requested_information, cast(sd, PSECURITY_DESCRIPTOR), size_necessary, byref(sd_size))
    if not ret:
        raise windows_error()
    return buffer(sd)


def set_file_security(path, security_information, security_descriptor):
    csec = (BYTE * len(security_descriptor))()
    _python_to_c(csec, security_descriptor)
    if not advapi32.SetFileSecurityW(path, security_information, cast(csec, PSECURITY_DESCRIPTOR)):
        raise windows_error()


def get_final_path_name_by_handle(handle, flags):
    path = create_unicode_buffer(MAX_PATH)
    while True:
        ret = kernel32.GetFinalPathNameByHandleW(handle, path, len(path), flags)
        if not ret:
            raise windows_error()
        if ret < len(path):
            return path[:ret]
        path = create_unicode_buffer(ret)
