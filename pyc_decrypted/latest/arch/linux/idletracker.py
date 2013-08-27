#Embedded file name: arch/linux/idletracker.py
import os
import ctypes, ctypes.util
from dropbox.debugging import ReprStructure
from dropbox.trace import report_bad_assumption, unhandled_exc_handler, TRACE

class XScreenSaverInfo(ReprStructure):
    _fields_ = [('window', ctypes.c_ulong),
     ('state', ctypes.c_int),
     ('kind', ctypes.c_int),
     ('since', ctypes.c_ulong),
     ('idle', ctypes.c_ulong),
     ('event_mask', ctypes.c_ulong)]


class IdleTracker(object):

    def __init__(self):
        TRACE('hello from main loop!')
        self.trackable = False
        if True:
            return
        try:
            from .xlib import xlib
            self.xlib = xlib
            self.xss = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Xss'))
            self.xss.XScreenSaverAllocInfo.argtypes = []
            self.xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
        except Exception:
            report_bad_assumption('xlib/xss not available')
            unhandled_exc_handler(False)
        else:
            try:
                self.dpy = self.xlib.XOpenDisplay(os.environ.get('DISPLAY'))
                if self.dpy:
                    self.root_window = self.xlib.XDefaultRootWindow(self.dpy)
                    if self.root_window:
                        self.trackable = True
                    else:
                        report_bad_assumption('no root window or xssinfo: %r %r' % (self.root_window, self.info))
                else:
                    report_bad_assumption('No X DISPLAY set')
            except Exception:
                unhandled_exc_handler()

    def is_trackable(self):
        return self.trackable

    def seconds_idle(self):
        assert self.is_trackable(), 'called seconds_idle on an untrackable client'
        info = self.xss.XScreenSaverAllocInfo()
        if not info:
            raise Exception('XScreenSaverAllocInfo failed')
        try:
            self.xss.XScreenSaverQueryInfo(self.dpy, self.root_window, info)
            return info.contents.idle / 1000
        finally:
            self.xlib.XFree(info)
