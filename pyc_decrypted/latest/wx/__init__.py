#Embedded file name: wx/__init__.py
import __version__
__version__ = __version__.VERSION_STRING
__all__ = ['build',
 'lib',
 'py',
 'tools',
 'animate',
 'aui',
 'calendar',
 'combo',
 'grid',
 'html',
 'media',
 'richtext',
 'webkit',
 'wizard',
 'xrc',
 'gizmos',
 'glcanvas',
 'stc']
from wx._core import *
del wx
if 'wxMSW' in PlatformInfo:
    __all__ += ['activex']
import wx._core
__docfilter__ = wx._core.__DocFilter(globals())
__all__ += [ name for name in dir(wx._core) if not name.startswith('_') ]
