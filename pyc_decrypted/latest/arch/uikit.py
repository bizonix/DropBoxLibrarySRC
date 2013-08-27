#Embedded file name: arch/uikit.py
from __future__ import absolute_import
import sys
from . import constants
if constants.platform == 'win':
    from .win32 import uikit as implementation_module
elif constants.platform == 'linux':
    from .linux import uikit as implementation_module
elif constants.platform == 'mac':
    from .mac import uikit as implementation_module
else:
    raise Exception('Unsupported platform')
sys.modules[__name__] = implementation_module
