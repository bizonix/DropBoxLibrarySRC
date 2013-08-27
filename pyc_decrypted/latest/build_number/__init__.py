#Embedded file name: build_number/__init__.py
from __future__ import absolute_import
import re
import sys

def extract_arg(arg):
    v = None
    for argument in sys.argv:
        if re.match('%s[= ](.*)' % arg, argument):
            v = argument[len(arg) + 1:]

    return v


if hasattr(sys, 'frozen') or hasattr(sys, 'post_build'):
    from .frozen_bn import BUILD_KEY, BRANCH, BUILD_NUMBER, VERSION, USABILITY, frozen
    if frozen == 'exe':
        from .frozen_bn import DROPBOXEXT_VERSION
    _is_frozen = True
else:
    from .global_bn import BRANCH
    BUILD_KEY = None
    VERSION = None
    if not hasattr(sys, 'build_all') and not hasattr(sys, 'post_build'):
        BUILD_KEY = extract_arg('--key')
    if not BUILD_KEY:
        BUILD_KEY = 'DropboxLocal'
    BUILD_NUMBER = 99999
    VERSION = extract_arg('--version')
    if not VERSION:
        VERSION = '%s.%s.%s' % (BRANCH[0], BRANCH[1], BUILD_NUMBER)
    USABILITY = False
    DROPBOXEXT_VERSION = False
    _is_frozen = False

def is_frozen():
    return _is_frozen


def stable_build():
    return BRANCH[1] % 2 == 0
