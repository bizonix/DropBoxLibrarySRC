#Embedded file name: arch/win32/photouploader/wpddevice.py
import functools
from ctypes import byref, create_string_buffer, cast, POINTER, sizeof
from ctypes.wintypes import LPCWSTR, LPWSTR
from comtypes import COMError
from comtypes.client import CreateObject
from comtypes.GUID import GUID
from comtypes.util import byref_at
from comtypes.automation import VARIANT
from contextlib import contextmanager
from portable_device import IPortableDeviceValues, IPortableDevicePropVariantCollection, IPortableDevice, PROPERTYKEY
from pynt.constants import COM_ERROR_INVALID_PARAMETER, COM_ERROR_NOT_FOUND
from pynt.dlls.ole32 import ole32
from dropbox.camera import Device
from dropbox.camera.filetypes import image_or_video, nonphoto_image
from dropbox.debugging import easy_repr
from dropbox.functions import convert_to_twos_complement
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.win32.version import WINDOWS_VERSION, VISTA
from .autoplay_defaults import change_autoplay_default
from .constants import DROPBOX_AUTOPLAY_HANDLER_NAME, DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME
from .helpers import handle_device_disconnect_exceptions
from ..internal import initialized_com
WPD_OBJECT_CONTENT_TYPE = PROPERTYKEY(GUID('{EF6B490D-5CD8-437A-AFFC-DA8B60EE4A3C}'), 7)
WPD_OBJECT_ORIGINAL_FILE_NAME = PROPERTYKEY(GUID('{EF6B490D-5CD8-437A-AFFC-DA8B60EE4A3C}'), 12)
WPD_OBJECT_SIZE = PROPERTYKEY(GUID('{EF6B490D-5CD8-437A-AFFC-DA8B60EE4A3C}'), 11)
WPD_OBJECT_DATE_CREATED = PROPERTYKEY(GUID('{EF6B490D-5CD8-437A-AFFC-DA8B60EE4A3C}'), 18)
WPD_OBJECT_DATE_MODIFIED = PROPERTYKEY(GUID('{EF6B490D-5CD8-437A-AFFC-DA8B60EE4A3C}'), 19)
WPD_CLIENT_DESIRED_ACCESS = PROPERTYKEY(GUID('{204D9F0C-2292-4080-9F42-40664E70F859}'), 9)
WPD_RESOURCE_DEFAULT = PROPERTYKEY(GUID('{E81E79BE-34F0-41BF-B53F-F1A06AE87842}'), 0)
WPD_OBJECT_ISHIDDEN = PROPERTYKEY(GUID('{EF6B490D-5CD8-437A-AFFC-DA8B60EE4A3C}'), 9)
WPD_DEVICE_MANUFACTURER = PROPERTYKEY(GUID('{26D4979A-E643-4626-9E2B-736DC0C92FDC}'), 7)
WPD_DEVICE_MODEL = PROPERTYKEY(GUID('{26D4979A-E643-4626-9E2B-736DC0C92FDC}'), 8)
WPD_DEVICE_SERIAL_NUMBER = PROPERTYKEY(GUID('{26D4979A-E643-4626-9E2B-736DC0C92FDC}'), 9)
WPD_DEVICE_FRIENDLY_NAME = PROPERTYKEY(GUID('{26D4979A-E643-4626-9E2B-736DC0C92FDC}'), 12)
WPD_CONTENT_TYPE_FUNCTIONAL_OBJECT = GUID('{99ED0160-17FF-4C44-9D98-1D7A6F941921}')
WPD_CONTENT_TYPE_FOLDER = GUID('{27e2e392-a111-48e0-ab0c-e17705a05f85}')
WPD_CONTENT_TYPE_IMAGE = GUID('{ef2107d5-a52a-4243-a26b-62d4176d7603}')
WPD_CONTENT_TYPE_VIDEO = GUID('{9261b03c-3d78-4519-85e3-02c5e1f50bb9}')
GENERIC_READ = 2147483648L
GENERIC_WRITE = 1073741824
WPD_DEVICE_OBJECT_ID = LPCWSTR('DEVICE')

class WpdFile(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('id', 'resource', '_name', '_size', '_time', 'curpos', 'transfer_block_size', 'stream', '_buffer', 'opened')

    def __init__(self, id, resource, name, size, mtime):
        self.id = id
        self._name = name
        self._size = size
        self._time = mtime
        self.resource = resource
        self.opened = False

    def name(self):
        return self._name

    def size(self):
        return self._size

    def time(self):
        return self._time

    def __repr__(self):
        return easy_repr(self, *self.__slots__)

    @contextmanager
    def open(self, *n, **kw):
        if self.opened:
            raise Exception('Already opened')
        with initialized_com():
            STGM_READ = 0
            self.transfer_block_size, self.stream = self.resource.GetStream(self.id, byref(WPD_RESOURCE_DEFAULT), STGM_READ)
            self._buffer = create_string_buffer(self.transfer_block_size)
            self.curpos = 0
            self.opened = True
            yield self.read
            self.opened = False
            if self.stream is not None:
                bytes_read = 1
                while bytes_read > 0:
                    bytes_read = self.stream.Read(self._buffer, self.transfer_block_size)

            self.stream = None
            self.curpos = 0

    def read(self, size = -1):
        remaining = self._size - self.curpos
        TRACE('file_read: %s, id: %s, curpos = %d, size = %d, remaining = %d', self._name, self.id, self.curpos, size, remaining)
        if size < 0 or size > remaining:
            size = remaining
        read_size = min(self.transfer_block_size, size)
        bytes_read = self.stream.Read(self._buffer, read_size)
        TRACE('Read %d bytes from %s', bytes_read, self.name)
        self.curpos += bytes_read
        return self._buffer[:bytes_read]


class WpdDevice(Device):

    def __init__(self, device_id, handler):
        self.exception = None
        self.disconnected = False
        try:
            super(WpdDevice, self).__init__(device_id)
            self.handler = handler
            self._buffer = None
            self._buf_size = 0
            self.handle_disconnect_exceptions = functools.partial(handle_device_disconnect_exceptions, self)
            PORTABLE_DEVICE_CLSID = '{728a21c5-3d9e-48d7-9810-864848f0f404}'
            self.device = CreateObject(progid=PORTABLE_DEVICE_CLSID, interface=IPortableDevice)
            PORTABLE_DEVICE_VALUES_CLSID = '{0c15d503-d017-47ce-9016-7b3f978721cc}'
            client_info = CreateObject(progid=PORTABLE_DEVICE_VALUES_CLSID, interface=IPortableDeviceValues)
            client_info.SetUnsignedIntegerValue(byref(WPD_CLIENT_DESIRED_ACCESS), GENERIC_READ | GENERIC_WRITE)
            try:
                self.device.Open(LPCWSTR(device_id), client_info)
            except Exception as e:
                TRACE("!! Couldn't open the device. Attempting to open read-only. Error info: %r", e)
                client_info.SetUnsignedIntegerValue(byref(WPD_CLIENT_DESIRED_ACCESS), GENERIC_READ)
                self.device.Open(LPCWSTR(device_id), client_info)

            self.device_content = self.device.Content()
            self.device_resources = self.device_content.Transfer()
            self.device_properties = self.device_content.Properties()
            props = self.device_properties.GetValues(WPD_DEVICE_OBJECT_ID, None)
            self.uid = self.id
            self.name = props.GetStringValue(byref(WPD_DEVICE_FRIENDLY_NAME))
            self.serialnum = props.GetStringValue(byref(WPD_DEVICE_SERIAL_NUMBER))
            self.manufacturer = props.GetStringValue(byref(WPD_DEVICE_MANUFACTURER))
            self.model = props.GetStringValue(byref(WPD_DEVICE_MODEL))
            if self.manufacturer and self.model and self.model.startswith(self.manufacturer):
                self.model = self.model[len(self.manufacturer):].strip()
        except Exception as e:
            self.exception = e
            unhandled_exc_handler()
        finally:
            handler.connected(self)

    def override_disabled(self):
        return True

    def formatted_device_id(self):
        try:
            if self.id.startswith(u'\\\\?\\'):
                device_id = self.id[4:]
            else:
                raise Exception('Device ID improperly prefixed.')
            device_id = device_id.split('#')[:3]
            device_id = '#'.join(device_id).upper()
            return u'WpdDeviceHandler_%s' % device_id
        except Exception:
            unhandled_exc_handler()
            return self.id

    def make_default(self):
        TRACE('Making device %s default to Dropbox on AutoPlay.', self)
        try:
            device_id = self.formatted_device_id()
            if WINDOWS_VERSION > VISTA:
                handler = DROPBOX_AUTOPLAY_HANDLER_NAME
            else:
                handler = DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME
            change_autoplay_default(device_id, handler)
        except Exception:
            unhandled_exc_handler()

    @contextmanager
    def files(self):
        if self.exception is not None:
            raise self.exception
        dcim_obj_id = self._find_dcim(WPD_DEVICE_OBJECT_ID)
        if dcim_obj_id:
            root = dcim_obj_id
            blacklist_nonphotos = False
        else:
            TRACE("Didn't find DCIM or other media folders. Searching all folders for photos and videos")
            root = WPD_DEVICE_OBJECT_ID
            blacklist_nonphotos = True
        yield self._enumerate_files_recursive(root, blacklist_nonphotos)

    def percent(self):
        return 100

    def delete_files(self, fobjs):
        if self.disconnected:
            return
        TRACE('Deleting %d objects from the camera', len(fobjs))
        PROP_VARIANT_COLLECTION_CLSID = '{08a99e2f-6d6d-4b80-af5a-baf2bcbe4cb9}'
        objs_to_delete = CreateObject(progid=PROP_VARIANT_COLLECTION_CLSID, interface=IPortableDevicePropVariantCollection)
        for fobj in fobjs:
            try:
                fobj.stream = None
                objs_to_delete.Add(VARIANT(fobj.id))
            except Exception:
                unhandled_exc_handler()

        try:
            PORTABLE_DEVICE_DELETE_NO_RECURSION = 0
            self.device_content.Delete(PORTABLE_DEVICE_DELETE_NO_RECURSION, objs_to_delete, None)
        except Exception:
            unhandled_exc_handler()

    def release(self):
        try:
            if hasattr(self, 'device'):
                del self.device
            if hasattr(self, 'device_content'):
                del self.device_content
            if hasattr(self, 'device_resources'):
                del self.device_resources
            self.disconnected = True
        except Exception:
            unhandled_exc_handler()

        self.handler.disconnected(self)

    def _find_dcim(self, root_obj_id):
        ret = None
        obj_id = None
        dirs_to_search = [root_obj_id]
        NUM_OBJECTS_TO_REQUEST = 50
        obj_ids_array = (LPWSTR * NUM_OBJECTS_TO_REQUEST)()
        while ret is None and dirs_to_search:
            enum_obj_ids = self.device_content.EnumObjects(0, dirs_to_search.pop(0), None)
            num_fetched = NUM_OBJECTS_TO_REQUEST
            if num_fetched == 0 and obj_id is None:
                report_bad_assumption('Device %s %s reported 0 objects to enumerate!', self.manufacturer, self.model)
            while num_fetched == NUM_OBJECTS_TO_REQUEST:
                num_fetched = enum_obj_ids.Next(NUM_OBJECTS_TO_REQUEST, obj_ids_array)
                for i in xrange(num_fetched):
                    try:
                        obj_id = obj_ids_array[i]
                        if obj_id is None:
                            report_bad_assumption('Enumerated device object ID is None')
                            continue
                        obj_props = self.device_content.Properties().GetValues(obj_id, None)
                        content_type = obj_props.GetGuidValue(byref(WPD_OBJECT_CONTENT_TYPE))
                        if content_type == WPD_CONTENT_TYPE_FOLDER:
                            objname = _get_obj_name(obj_id, obj_props)
                            if objname and objname.lower() == 'dcim':
                                ret = obj_id
                                break
                        if content_type == WPD_CONTENT_TYPE_FUNCTIONAL_OBJECT:
                            dirs_to_search.append(obj_id)
                    finally:
                        _wstr_array_free(obj_ids_array, i)

                if ret is not None:
                    return ret

    def _enumerate_files_recursive(self, root_obj_id, blacklist_nonphotos = False):
        TRACE('Searching for images and videos in: %r', root_obj_id)
        enum_obj_ids = self.device_content.EnumObjects(0, root_obj_id, None)
        NUM_OBJECTS_TO_REQUEST = 50
        num_fetched = NUM_OBJECTS_TO_REQUEST
        obj_ids_array = (LPWSTR * NUM_OBJECTS_TO_REQUEST)()
        while num_fetched == NUM_OBJECTS_TO_REQUEST:
            num_fetched = enum_obj_ids.Next(NUM_OBJECTS_TO_REQUEST, obj_ids_array)
            for i in xrange(num_fetched):
                try:
                    obj_id = obj_ids_array[i]
                    assert obj_id != None, 'Enumerated device object ID is None'
                    obj_props = self.device_content.Properties().GetValues(obj_id, None)
                    try:
                        is_hidden = obj_props.GetGuidValue(byref(WPD_OBJECT_ISHIDDEN))
                    except COMError as e:
                        if not hasattr(e, 'hresult') or convert_to_twos_complement(e.hresult) not in (COM_ERROR_INVALID_PARAMETER, COM_ERROR_NOT_FOUND):
                            unhandled_exc_handler()
                    except Exception:
                        unhandled_exc_handler()
                    else:
                        if is_hidden:
                            TRACE('Skipping hidden object %r', obj_id)
                            continue

                    filename = _get_obj_name(obj_id, obj_props)
                    content_type = obj_props.GetGuidValue(byref(WPD_OBJECT_CONTENT_TYPE))
                    photo_video_types = [WPD_CONTENT_TYPE_IMAGE, WPD_CONTENT_TYPE_VIDEO]
                    if content_type in photo_video_types or image_or_video(filename) and not (blacklist_nonphotos and nonphoto_image(filename)):
                        yield _create_file_object(self.device_resources, obj_id, obj_props, filename)
                    elif content_type in (WPD_CONTENT_TYPE_FOLDER, WPD_CONTENT_TYPE_FUNCTIONAL_OBJECT):
                        for fobj in self._enumerate_files_recursive(obj_id, blacklist_nonphotos):
                            yield fobj

                    else:
                        TRACE('Skipping %s, not photo or video (content type %r)', filename, content_type)
                except Exception as e:
                    self.handle_disconnect_exceptions(e)
                    unhandled_exc_handler()
                finally:
                    _wstr_array_free(obj_ids_array, i)


def _wstr_array_free(obj_ids_array, i):
    pwchar = cast(byref_at(obj_ids_array, sizeof(LPWSTR) * i), POINTER(LPWSTR)).contents
    ole32.CoTaskMemFree(pwchar)


def _get_obj_name(obj_id, obj_props):
    try:
        name = obj_props.GetStringValue(byref(WPD_OBJECT_ORIGINAL_FILE_NAME))
    except Exception:
        name = None

    if name == None:
        name = obj_id + '.data'
    return name


def _create_file_object(resource, obj_id, obj_props, name):
    filesize = int(obj_props.GetStringValue(byref(WPD_OBJECT_SIZE)))
    filename = name
    mtime = _get_obj_mtime(obj_props)
    TRACE('Found image file %s', filename)
    return WpdFile(id=obj_id, resource=resource, name=filename, size=filesize, mtime=mtime)


def _get_obj_mtime(obj_props):
    ret = None
    try:
        ctime = obj_props.GetValue(byref(WPD_OBJECT_DATE_CREATED))
    except Exception:
        pass
    else:
        ret = ctime

    try:
        mtime = obj_props.GetValue(byref(WPD_OBJECT_DATE_MODIFIED))
    except Exception:
        if not ret:
            TRACE('!! No creation or modification time on this file!')
        else:
            TRACE('Returning creation time: %r', ret)
    else:
        TRACE('Returning modification time: %r', mtime)
        ret = mtime

    return ret
