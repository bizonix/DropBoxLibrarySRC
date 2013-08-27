#Embedded file name: pymac/helpers/imagecapture.py
from ctypes import byref, pointer, string_at
from .core import FS, CFDictionary, releasing
from ..types import CFDataRef, ICACopyObjectDataPB, ICACopyObjectPropertyDictionaryPB, ICADownloadFilePB, ICAGetDeviceListPB
from ..dlls import Carbon, Core
from ..constants import kAdjustCreationDate
try:
    from _imagecapture import ImageCapture as IC
except ImportError:
    IMAGE_CAPTURE_ENABLED = False

    class ImageCapture(object):

        def subscribe(self, cb):
            pass

        @staticmethod
        def get_connected_devices():
            return []


else:
    IMAGE_CAPTURE_ENABLED = True

    class ImageCapture(object):

        def __init__(self):
            self.ic = IC([Carbon.kICANotificationTypeObjectAdded,
             Carbon.kICANotificationTypeObjectRemoved,
             Carbon.kICANotificationTypeObjectInfoChanged,
             Carbon.kICANotificationTypeDeviceAdded,
             Carbon.kICANotificationTypeDeviceRemoved,
             Carbon.kICANotificationTypeDeviceInfoChanged,
             Carbon.kICANotificationTypeStoreAdded,
             Carbon.kICANotificationTypeStoreRemoved,
             Carbon.kICANotificationTypeDeviceConnectionProgress])

        def subscribe(self, cb):

            def fixed_fn(data):
                data = CFDictionary(data, True)
                return cb(data)

            self.ic.subscribe(fixed_fn)

        @staticmethod
        def download_file(entry, dest_path):
            ret = FS()
            dest = FS(dest_path)
            pb = ICADownloadFilePB()
            pb.object = entry['icao']
            pb.dirFSRef = dest.pointer()
            pb.fileFSRef = ret.pointer()
            pb.flags = kAdjustCreationDate
            pb.rotationAngle = 0
            Carbon.ICADownloadFile(byref(pb), None)
            return unicode(ret)

        @staticmethod
        def get_property_dict(obj_id):
            ret = Core.CFDictionaryCreate(None, None, None, 0, None, None)
            pb = ICACopyObjectPropertyDictionaryPB()
            pb.object = obj_id
            pb.theDict = pointer(ret)
            Carbon.ICACopyObjectPropertyDictionary(byref(pb), None)
            return CFDictionary(ret, take_ownership=True)

        @staticmethod
        def get_file_data(entry, start, size):
            pb = ICACopyObjectDataPB()
            pb.object = entry['icao']
            pb.startByte = start
            pb.requestedSize = size
            with releasing(CFDataRef()) as dr:
                pb.data = pointer(dr)
                Carbon.ICACopyObjectData(byref(pb), None)
                return string_at(Core.CFDataGetBytePtr(dr), Core.CFDataGetLength(dr))

        @staticmethod
        def get_connected_devices():
            device_list = ICAGetDeviceListPB()
            Carbon.ICAGetDeviceList(byref(device_list), None)
            return ImageCapture.get_property_dict(device_list.object)['devices']
