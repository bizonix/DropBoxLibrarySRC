#Embedded file name: pymac/helpers/finder.py
from __future__ import absolute_import
import ctypes
import threading
from ..dlls import CoreServices
from ..constants import kFSCatInfoFinderInfo, kHasCustomIcon, kIsInvisible, kHasBeenInited, FourCharCode
from ..types import FSRef, FSCatalogInfo

class FinderInfoEditor(object):

    def __init__(self):
        self.fsref = FSRef()
        self.catalogInfo = FSCatalogInfo()
        self._lock = threading.Lock()

    def _load_finderinfo(self, path):
        assert type(path) is unicode
        CoreServices.FSPathMakeRef(path.encode('utf8'), ctypes.byref(self.fsref), None)
        CoreServices.FSGetCatalogInfo(ctypes.byref(self.fsref), kFSCatInfoFinderInfo, ctypes.byref(self.catalogInfo), None, None, None)

    def _save_finderinfo(self):
        CoreServices.FSSetCatalogInfo(ctypes.byref(self.fsref), kFSCatInfoFinderInfo, ctypes.byref(self.catalogInfo))

    def has_custom_icon(self, path):
        with self._lock:
            self._load_finderinfo(path)
            return bool(self.catalogInfo.finderInfo.finderFlags & kHasCustomIcon)

    def set_invisible(self, path):
        with self._lock:
            self._load_finderinfo(path)
            self.catalogInfo.finderInfo.fileType = FourCharCode('icon')
            self.catalogInfo.finderInfo.fileCreator = FourCharCode('MACS')
            self.catalogInfo.finderInfo.finderFlags = kIsInvisible
            self.catalogInfo.finderInfo.location.v = 0
            self.catalogInfo.finderInfo.location.h = 0
            self.catalogInfo.finderInfo.reservedField = 0
            self._save_finderinfo()

    def set_custom_icon(self, path):
        with self._lock:
            self._load_finderinfo(path)
            self.catalogInfo.finderInfo.finderFlags = (self.catalogInfo.finderInfo.finderFlags | kHasCustomIcon) & ~kHasBeenInited
            self._save_finderinfo()
