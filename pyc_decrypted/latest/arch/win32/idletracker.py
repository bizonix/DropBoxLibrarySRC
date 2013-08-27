#Embedded file name: arch/win32/idletracker.py
import ctypes
from ctypes import c_uint, sizeof, byref
from dropbox.debugging import ReprStructure
from dropbox.trace import report_bad_assumption, unhandled_exc_handler

class LASTINPUTINFO(ReprStructure):
    _fields_ = [('cbSize', c_uint), ('dwTime', c_uint)]


class IdleTracker(object):

    def __init__(self):
        self.trackable = False
        try:
            self.lastInputInfo = LASTINPUTINFO()
            self.lastInputInfo.cbSize = sizeof(self.lastInputInfo)
            if not hasattr(ctypes.windll.user32, 'GetLastInputInfo'):
                report_bad_assumption('win32: GetLastInputInfo not available')
                return
        except:
            unhandled_exc_handler()
        else:
            self.trackable = True

    def is_trackable(self):
        return self.trackable

    def seconds_idle(self):
        assert self.is_trackable(), 'called seconds_idle on an untrackable client'
        ctypes.windll.user32.GetLastInputInfo(byref(self.lastInputInfo))
        millis = ctypes.windll.kernel32.GetTickCount() - self.lastInputInfo.dwTime
        return millis / 1000
