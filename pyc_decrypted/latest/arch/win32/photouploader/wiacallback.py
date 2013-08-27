#Embedded file name: arch/win32/photouploader/wiacallback.py
import ctypes
from ctypes import POINTER, c_void_p, string_at
from ctypes.wintypes import BOOL, HRESULT, ULONG
import comtypes
from comtypes.GUID import GUID
from comtypes import IUnknown, COMMETHOD
from .constants import DROPBOX_DATA_CALLBACK_PROGID, DROPBOX_DATA_CALLBACK_VERNO, DROPBOX_DATA_CALLBACK_DESC
from dropbox.native_queue import Queue
from dropbox.trace import TRACE, unhandled_exc_handler
import sys
from PhotoUploaderLib import IWiaDataCallback, DropboxWiaDataCallback
CALLBACK_MESSAGES = {1: 'IT_MSG_DATA_HEADER',
 2: 'IT_MSG_DATA',
 3: 'IT_MSG_STATUS',
 4: 'IT_MSG_TERMINATION',
 5: 'IT_MSG_NEW_PAGE',
 6: 'IT_MSG_FILE_PREVIEW_DATA',
 7: 'IT_MSG_FILE_PREVIEW_DATA_HEADER'}

class WIA_DATA_TRANSFER_INFO(ctypes.Structure):
    _fields_ = [('ulSize', ULONG),
     ('ulSection', ULONG),
     ('ulBufferSize', ULONG),
     ('bDoubleBuffer', BOOL),
     ('ulReserved1', ULONG),
     ('ulReserved2', ULONG),
     ('ulReserved3', ULONG)]


class IWiaDataTransfer(IUnknown):
    _iid_ = GUID('{A6CEF998-A5B0-11D2-A08F-00C04F72DC3C}')
    _idlflags_ = []
    _methods_ = [COMMETHOD([], HRESULT, 'idtGetData', (['in, out'], POINTER(c_void_p), 'pMedium'), (['in'], POINTER(IWiaDataCallback), 'pIWiaDataCallback')), COMMETHOD([], HRESULT, 'idtGetBandedData', (['in'], POINTER(WIA_DATA_TRANSFER_INFO), 'pWiaDataTransInfo'), (['in'], POINTER(IWiaDataCallback), 'pIWiaDataCallback'))]


DATA_BUFFER_SIZE = 262144
DATA_QUEUE_SIZE = 5
DATA_QUEUE_TIMEOUT = 10

class _TransferStopped(Exception):
    pass


class DropboxWiaDataCallbackImpl(DropboxWiaDataCallback):
    _reg_threading_ = 'Apartment'
    _reg_progid_ = '%s.%d' % (DROPBOX_DATA_CALLBACK_PROGID, DROPBOX_DATA_CALLBACK_VERNO)
    _reg_novers_progid_ = DROPBOX_DATA_CALLBACK_PROGID
    _reg_desc_ = DROPBOX_DATA_CALLBACK_DESC
    _reg_clsctx_ = comtypes.CLSCTX_LOCAL_SERVER
    _regcls_ = comtypes.server.localserver.REGCLS_MULTIPLEUSE
    queue = Queue(maxsize=DATA_QUEUE_SIZE)
    stopped = False
    exc = None

    def BandedDataCallback(self, this, lMessage, lStatus, lPercentComplete, lOffset, lLength, lReserved, lResLength, pbBuffer):
        cls = DropboxWiaDataCallbackImpl

        def check_stopped():
            if cls.stopped:
                raise _TransferStopped()

        try:
            message = CALLBACK_MESSAGES.get(lMessage)
            TRACE('WIA message received: %r', message)
            check_stopped()
            if message == 'IT_MSG_DATA':
                datum = string_at(pbBuffer, lLength)
                cls.queue.put(datum, block=True, timeout=DATA_QUEUE_TIMEOUT)
            check_stopped()
            return 0
        except _TransferStopped:
            TRACE('Cancelling WIA transfer because of an external request.')
        except Exception:
            cls.exc = sys.exc_info()
            unhandled_exc_handler(False)
            TRACE('Cancelling WIA transfer because an error occurred.')

        return 1
