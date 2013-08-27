#Embedded file name: pymac/dlls/__init__.py
from __future__ import absolute_import
from .c import libc
from .Carbon import Carbon
from .CoreFoundation import Core
from .CoreServices import CoreServices
from .DiskArbitration import DiskArbitration
from .FSEvent import FSEvent
from .IOKit import IOKit
from .PythonApi import PythonAPI
from .SecurityFoundation import Security
from .SystemConfiguration import SystemConfiguration

def preload_dlls(on_error = None):
    for lib in (libc,
     Carbon,
     Core,
     CoreServices,
     DiskArbitration,
     FSEvent,
     IOKit,
     PythonAPI,
     Security,
     SystemConfiguration):
        try:
            lib.init()
        except Exception:
            if on_error:
                on_error()
