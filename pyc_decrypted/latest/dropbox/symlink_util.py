#Embedded file name: dropbox/symlink_util.py
from __future__ import absolute_import
import os
import stat
from dropbox.functions import is_case_insensitive_path
from dropbox.platform import platform
from dropbox.trace import unhandled_exc_handler

def _iterate_up_to(rel, path, case_insensitive = True):
    if rel.lower() == path.lower() if case_insensitive else rel == path:
        return
    while True:
        path = os.path.dirname(path)
        yield path
        if path.lower() == rel.lower() if case_insensitive else path == rel:
            break


if platform == 'win':

    def should_recurse(path, rel = u'/', case_insensitive = True):
        return True


else:

    def should_recurse(path, rel = u'/', case_insensitive = None):
        if case_insensitive is None:
            try:
                case_insensitive = is_case_insensitive_path(path)
            except:
                unhandled_exc_handler()
                case_insensitive = True

        if path == rel:
            return True
        try:
            st = os.stat(path)
        except OSError:
            return False

        if not stat.S_ISDIR(st.st_mode):
            return False
        dest_dev = st.st_dev
        dest_ino = st.st_ino
        for path in _iterate_up_to(rel, path, case_insensitive=case_insensitive):
            try:
                b = os.stat(path)
            except OSError:
                continue

            if b.st_dev == dest_dev and b.st_ino == dest_ino:
                return False

        return True
