#Embedded file name: arch/mac/idletracker.py
import ctypes, ctypes.util
from dropbox.trace import report_bad_assumption, unhandled_exc_handler

class IdleTracker(object):

    def __init__(self):
        self.trackable = False
        try:
            path = ctypes.util.find_library('ApplicationServices')
            if not path:
                report_bad_assumption('Mac: ApplicationServices not found')
                return
            self.cglib = ctypes.cdll.LoadLibrary(path)
            self.cglib.CGSSecondsSinceLastInputEvent.restype = ctypes.c_double
        except:
            report_bad_assumption('Mac: CGSSecondsSinceLastInputEvent not found')
            unhandled_exc_handler(False)
        else:
            self.trackable = True

    def is_trackable(self):
        return self.trackable

    def seconds_idle(self):
        assert self.is_trackable(), 'called seconds_idle on an untrackable client'
        ret = self.cglib.CGSSecondsSinceLastInputEvent(-1)
        if ret > 31104000:
            return 0
        return int(ret)
