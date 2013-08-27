#Embedded file name: babel/__init__.py
from babel.core import *
__docformat__ = 'restructuredtext en'
try:
    from pkg_resources import get_distribution, ResolutionError
    try:
        __version__ = get_distribution('Babel').version
    except ResolutionError:
        __version__ = None

except ImportError:
    __version__ = None
