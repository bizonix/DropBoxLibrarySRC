#Embedded file name: dropbox/sync_engine_arch/__init__.py
from __future__ import absolute_import
import sys
if sys.platform == 'darwin':
    from .macosx import Arch as make_arch
elif sys.platform.startswith('linux'):
    from .linux import Arch as make_arch_

    def make_arch():
        from mock import Mock
        return make_arch_(Mock())


elif sys.platform.startswith('win'):
    from .win import Arch as make_arch
else:

    def make_arch():
        raise Exception('Current platform not supported!')
