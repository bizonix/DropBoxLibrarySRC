#Embedded file name: arch/win32/photouploader/autoplay_event_handler.py
import comtypes
import comtypes.server.localserver
from ctypes import c_ulong
from dropbox.trace import TRACE, unhandled_exc_handler
from build_number import BUILD_KEY
from .constants import DROPBOX_AUTOPLAY_PROGID, DROPBOX_AUTOPLAY_VERNO
from wpddevice import WpdDevice
from wiadevice import WiaDevice
from sdcarddevice import WinSDCardDevice
from PhotoUploaderLib import AutoplayEventHandler

class AutoplayEventHandlerImpl(AutoplayEventHandler):
    _reg_threading_ = 'Apartment'
    _reg_progid_ = '%s.%d' % (DROPBOX_AUTOPLAY_PROGID, DROPBOX_AUTOPLAY_VERNO)
    _reg_novers_progid_ = DROPBOX_AUTOPLAY_PROGID
    _reg_desc_ = BUILD_KEY + ' autoplay COM server'
    _reg_clsctx_ = comtypes.CLSCTX_LOCAL_SERVER
    _regcls_ = comtypes.server.localserver.REGCLS_MULTIPLEUSE

    def __init__(self):
        self._buffer = None
        self._block_size = 0

    def Initialize(self, init_params):
        TRACE('PHOTOUPLOADER: IAutoplayEventHandler_Initialize')
        TRACE('init_params: %s', init_params)
        return 0

    def HandleEvent(self, device_id, alt_device_id, event_type):
        try:
            TRACE('PHOTOUPLOADER: IAutoplayEventHandler_HandleEvent')
            TRACE('device_id: %s, alt_device_id: %s, event_type: %s', device_id, alt_device_id, event_type)
            if event_type != 'DeviceArrival':
                TRACE('!! HandleEvent received an event that was not a device arrival!')
                return 0
            WpdDevice(device_id, self.handler)
        except Exception:
            unhandled_exc_handler()

        return 0

    def HandleEventWithContent(self, device_id, alt_device_id, event_type, content_type_handler, obj_data):
        TRACE('!! PHOTOUPLOADER: IAutoplayEventHandler_HandleEventWithContent')
        return 0

    def DragEnter(self, data_obj, grfKeyState, pt):
        TRACE('PHOTOUPLOADER: IDropTarget::DragEnter')
        return 0

    def DragOver(self, this, grfKeyState, pt, pdwEffect):
        TRACE('PHOTOUPLOADER: IDropTarget::DragOver')
        return 0

    def DragLeave(self):
        TRACE('PHOTOUPLOADER: IDropTarget::DragLeave')
        return 0

    def Drop(self, data_obj, key_state, pt, pdw_effect):
        try:
            TRACE('PHOTOUPLOADER: IDropTarget::Drop')
            TRACE('data_obj: %r, key_state: %r, pt: %r, dw_effect: %r', data_obj, key_state, pt, pdw_effect.contents)
            WinSDCardDevice(data_obj, self.handler, self.app.uid)
            DROPEFFECT_COPY = c_ulong(1)
            pdw_effect.contents = DROPEFFECT_COPY
        except Exception:
            unhandled_exc_handler()

        return 0

    def ImageEventCallback(self, event_guid, event_description, device_id, device_description, device_type, full_item_name, event_type, reserved):
        try:
            TRACE('PHOTOUPLOADER: IWiaEventCallback::ImageEventCallback')
            TRACE('event_guid %r', event_guid)
            TRACE('bstrEventDescription %r', event_description)
            TRACE('bstrDeviceID %r', device_id)
            TRACE('bstrDeviceDescription %r', device_description)
            TRACE('dwDeviceType %r', device_type)
            TRACE('bstrFullItemName %r', full_item_name)
            TRACE('pulEventType %r', event_type)
            WiaDevice(device_id, self.handler, self.app)
        except Exception:
            unhandled_exc_handler()

        return 0
