#Embedded file name: dropbox/camera/fromfiledevice.py
import errno
import os
import uuid
import dropbox.platform
from dropbox.camera import Device
from dropbox.trace import TRACE, unhandled_exc_handler
MAX_READ_SIZE = 4194304

class ReadFromFile(Device):

    def delete_files(self, fobjs):
        TRACE('Deleting %d objects from the camera', len(fobjs))
        for fobj in fobjs:
            try:
                os.remove(fobj.srcpath)
            except Exception:
                unhandled_exc_handler()
