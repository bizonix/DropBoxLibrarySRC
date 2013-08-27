#Embedded file name: arch/win32/photouploader/helpers.py
from comtypes import COMError
from dropbox.camera import PhotoImportDisconnected
from dropbox.camera.util import is_apple_device
from dropbox.functions import convert_to_twos_complement
from dropbox.trace import TRACE, report_bad_assumption
from pynt.constants import COM_ERROR_BUSY, COM_ERROR_DEVICE_NOT_CONNECTED, COM_ERROR_FILE_NOT_FOUND, COM_ERROR_GEN_FAILURE, COM_ERROR_NOT_FOUND, COM_ERROR_OPERATION_ABORTED, COM_ERROR_SEM_TIMEOUT, E_FAIL, E_WPD_DEVICE_IS_HUNG, E_WPD_DEVICE_NOT_OPEN, WIA_ERROR_BUSY, WIA_ERROR_OFFLINE
DISCONNECTED_ERRORS = set([COM_ERROR_BUSY,
 COM_ERROR_DEVICE_NOT_CONNECTED,
 COM_ERROR_FILE_NOT_FOUND,
 COM_ERROR_GEN_FAILURE,
 COM_ERROR_NOT_FOUND,
 COM_ERROR_OPERATION_ABORTED,
 COM_ERROR_SEM_TIMEOUT,
 E_FAIL,
 E_WPD_DEVICE_IS_HUNG,
 E_WPD_DEVICE_NOT_OPEN,
 WIA_ERROR_BUSY,
 WIA_ERROR_OFFLINE])
MAX_DISCONNECTED_ERRORS = 5

def handle_device_disconnect_exceptions(device, exc):
    if is_disconnected_error(exc):
        try:
            device.num_disconnected_errors += 1
        except AttributeError:
            device.num_disconnected_errors = 1

        TRACE('Caught a potential disconnected error')
        if is_apple_device(device) and exc.hresult == E_WPD_DEVICE_IS_HUNG:
            report_bad_assumption('Transfer interrupted due to iTunes backup!')
        if device.num_disconnected_errors >= MAX_DISCONNECTED_ERRORS:
            TRACE('!! Too many disconnected errors.  Raising PhotoImportDisconnected')
            device.disconnected = True
            raise PhotoImportDisconnected()
        return True
    if isinstance(exc, PhotoImportDisconnected):
        raise exc


def is_disconnected_error(exc):
    if isinstance(exc, COMError) and convert_to_twos_complement(exc.hresult) in DISCONNECTED_ERRORS:
        return True
    return False
