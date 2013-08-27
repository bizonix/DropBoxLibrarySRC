#Embedded file name: arch/win32/photouploader/wiadevice.py
import functools
import sys
import comtypes
from comtypes.client import CreateObject
from comtypes.automation import VARIANT
from contextlib import contextmanager
from ctypes import POINTER, byref, cast, sizeof
import threading
from .autoplay_defaults import set_wia_default
from .constants import DROPBOX_DATA_CALLBACK_PROGID
from .helpers import handle_device_disconnect_exceptions
from ..internal import uses_com, initialized_com, is_admin
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.camera.filetypes import image_or_video
from dropbox.camera.fromfiledevice import ReadFromFile
from dropbox.debugging import easy_repr
from dropbox.win32.version import WINDOWS_VERSION, WINXP
from wiacallback import DropboxWiaDataCallbackImpl, IWiaDataTransfer, WIA_DATA_TRANSFER_INFO, IWiaDataCallback, DATA_BUFFER_SIZE
from portable_device import IWiaDevMgr, IWiaItem, IWiaPropertyStorage, PROPSPEC, WIA_ITEM_TYPE_FOLDER
from pynt.helpers.com import datetime_from_var_date, PROPVARIANT

class WiaFile(object):
    __use_advanced_allocator__ = 1048576
    __slots__ = ('id', '_name', '_size', '_time', '_chunk', '_offset', '_exc', 'wia_item', 'fail_fast')

    def __init__(self, id, name, size, mtime, wia_item):
        self.id = id
        self._name = name
        self._size = size
        self._time = mtime
        self._chunk = None
        self._offset = 0
        self._exc = None
        self.wia_item = wia_item
        self.fail_fast = True

    def name(self):
        return self._name

    def size(self):
        return self._size

    def time(self):
        return self._time

    def __repr__(self):
        return easy_repr(self, *self.__slots__)

    def _consume_exc(self):
        if self._exc is not None:
            e = self._exc
            self._exc = None
            raise e[0], e[1], e[2]

    @contextmanager
    def open(self, *n, **kw):
        callback = DropboxWiaDataCallbackImpl
        callback.stopped = False
        callback.exc = None
        callback.queue.clear()

        def handler():
            try:
                with initialized_com(comtypes.COINIT_MULTITHREADED):
                    data_transfer = self.wia_item.QueryInterface(IWiaDataTransfer)
                    transfer_settings = WIA_DATA_TRANSFER_INFO()
                    transfer_settings.ulSize = sizeof(transfer_settings)
                    transfer_settings.ulBufferSize = DATA_BUFFER_SIZE
                    transfer_settings.bDoubleBuffer = 1
                    transfer_settings.ulSection = 0
                    inst = CreateObject(progid=DROPBOX_DATA_CALLBACK_PROGID, interface=IWiaDataCallback)
                    TRACE('Writing file using callback %s.', inst)
                    result = data_transfer.idtGetBandedData(transfer_settings, inst)
                    if result:
                        exc = callback.exc
                        if exc is not None:
                            raise exc[0], exc[1], exc[2]
                        TRACE('idtGetBandedData was interrupted within the callback; result: %s.', result)
                        return
                    TRACE('idtGetBandedData is done!')
            except Exception:
                self._exc = sys.exc_info()
                unhandled_exc_handler(False)
            finally:
                callback.queue.put('', block=True)

        def read(size):
            if callback.stopped:
                report_bad_assumption('Tried to read after the transfer was interrupted!')
                return ''
            if self._chunk is None:
                chunk = callback.queue.get(block=True)
                self._consume_exc()
                if not chunk:
                    return ''
                self._chunk = chunk
                self._offset = 0
            buf = buffer(self._chunk, self._offset, size)
            self._offset += len(buf)
            if self._offset == len(chunk):
                self._chunk = None
            return buf

        transfer_thread = threading.Thread(target=handler, name='WIAHANDLER')
        transfer_thread.start()
        try:
            yield read
        finally:
            callback.stopped = True
            callback.queue.clear()
            transfer_thread.join()
            self._consume_exc()


class WiaDevice(ReadFromFile):

    def __init__(self, device_id, handler, app):
        self.exception = None
        self.disconnected = False
        try:
            super(WiaDevice, self).__init__(device_id)
            self.handle_disconnect_exceptions = functools.partial(handle_device_disconnect_exceptions, self)
            self.handler = handler
            self.app = app
            self.uid = device_id
            self.populate_device_attrs()
        except Exception:
            self.exception = sys.exc_info()
            unhandled_exc_handler()
        finally:
            handler.connected(self)

    def override_disabled(self):
        return True

    def make_default(self):
        if WINDOWS_VERSION < WINXP:
            return
        if not is_admin():
            TRACE("Non-admins can't change WIA settings.")
            return
        TRACE('Making device %s default to Dropbox on AutoPlay.', self)
        try:
            set_wia_default(self.id)
        except Exception:
            unhandled_exc_handler()

    @uses_com
    def populate_device_attrs(self):
        device_mgr = None
        item_root = None
        try:
            device_mgr = CreateObject(progid='WiaDevMgr', interface=IWiaDevMgr)
            item_root = device_mgr.CreateDevice(self.uid)
            property_store = item_root.QueryInterface(IWiaPropertyStorage)
            propspec = PROPSPEC()
            propspec.ulKind = 1
            var = VARIANT()
            propspec.u.propid = 3
            property_store.ReadMultiple(1, byref(propspec), byref(var))
            self.manufacturer = var.value
            propspec.u.propid = 4
            property_store.ReadMultiple(1, byref(propspec), byref(var))
            self.model = var.value
            if self.manufacturer and self.model and self.model.startswith(self.manufacturer):
                self.model = self.model[len(self.manufacturer):].strip()
            propspec.u.propid = 7
            property_store.ReadMultiple(1, byref(propspec), byref(var))
            self.name = var.value
        finally:
            del device_mgr
            del item_root

    def delete_files(self, fobjs):
        if self.disconnected:
            return
        TRACE('Deleting %d objects from the camera', len(fobjs))
        for fobj in fobjs:
            try:
                fobj.wia_item.DeleteItem(0)
                fobj.wia_item = None
            except Exception:
                unhandled_exc_handler()

    @contextmanager
    def files(self):
        if self.exception is not None:
            e, self.exception = self.exception, None
            raise e[0], e[1], e[2]
        with initialized_com(comtypes.COINIT_MULTITHREADED):
            yield self.get_wia_files()

    def get_wia_files(self):
        device_mgr = CreateObject(progid='WiaDevMgr', interface=IWiaDevMgr)
        targets = [device_mgr.CreateDevice(self.id)]
        while targets:
            target = targets.pop()
            enum = target.EnumChildItems()
            NUM_OBJECTS_TO_REQUEST = 20
            num_fetched = NUM_OBJECTS_TO_REQUEST
            while num_fetched == NUM_OBJECTS_TO_REQUEST:
                items = (POINTER(IWiaItem) * NUM_OBJECTS_TO_REQUEST)()
                num_fetched = enum.Next(NUM_OBJECTS_TO_REQUEST, items)
                for i in xrange(num_fetched):
                    try:
                        item = items[i]
                        flags = item.GetItemType()
                        if flags & WIA_ITEM_TYPE_FOLDER:
                            targets.append(item)
                            continue
                        property_store = item.QueryInterface(IWiaPropertyStorage)
                        propspec = PROPSPEC()
                        propspec.ulKind = 1
                        propspec.u.propid = 4098
                        name = VARIANT()
                        property_store.ReadMultiple(1, byref(propspec), byref(name))
                        propspec.u.propid = 4123
                        ext = VARIANT()
                        property_store.ReadMultiple(1, byref(propspec), byref(ext))
                        try:
                            filename = name.value
                            if ext.value:
                                filename = filename + '.' + ext.value
                        except Exception:
                            unhandled_exc_handler()
                            continue

                        if not image_or_video(filename):
                            TRACE('Skipping %s, not photo or video', filename)
                            continue
                        try:
                            if ext.value and ext.value.lower() == 'bmp':
                                report_bad_assumption('Bitmap in a WIA device')
                                continue
                        except Exception:
                            unhandled_exc_handler()

                        propspec.u.propid = 4116
                        filesize = VARIANT()
                        property_store.ReadMultiple(1, byref(propspec), byref(filesize))
                        propspec.u.propid = 4100
                        filetime = PROPVARIANT()
                        property_store.ReadMultiple(1, byref(propspec), cast(byref(filetime), POINTER(VARIANT)))
                        spec_tymed = PROPSPEC()
                        spec_tymed.ulKind = 1
                        spec_tymed.u.propid = 4108
                        var_tymed = VARIANT()
                        var_tymed.value = 128
                        property_store.WriteMultiple(1, byref(spec_tymed), byref(var_tymed), 4098)
                        filetime = datetime_from_var_date(filetime)
                        yield WiaFile(id=filename, name=filename, size=filesize.value, mtime=filetime, wia_item=item)
                    except Exception as e:
                        self.handle_disconnect_exceptions(e)
                        unhandled_exc_handler()

    def release(self):
        self.handler.disconnected(self)
