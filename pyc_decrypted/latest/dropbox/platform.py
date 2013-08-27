#Embedded file name: dropbox/platform.py
from __future__ import absolute_import
import sys
if sys.platform.startswith('win'):
    platform = 'win'
elif sys.platform.startswith('linux'):
    platform = 'linux'
elif sys.platform.startswith('darwin'):
    platform = 'mac'
else:
    raise Exception('Unsupported Platform')
