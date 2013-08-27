#Embedded file name: dropbox/symlink_tracker.py
from __future__ import absolute_import
import errno
import os
import sys
from dropbox.platform import platform
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.fastwalk_bridge import fastwalk_with_exception_handling
from dropbox.sync_engine_file_system.constants import FILE_TYPE_POSIX_SYMLINK
if platform == 'win':
    from dropbox.dirtraverse_win32 import WIN32_REPARSE_TAGS

class SymlinkTrackHandler(object):

    def __init__(self, symlink_tracker, event_reporter, wait_secs):
        self.symlink_tracker = symlink_tracker
        self.event_reporter = event_reporter
        self.wait_secs = wait_secs
        self.last_call = 0.0

    def __call__(self):
        cur_time = get_monotonic_time_seconds()
        if cur_time > self.last_call + self.wait_secs:
            self.last_call = cur_time
            data = dict(((key, val) for key, val in self.symlink_tracker.get_symlink_data().items() if key != 'sample-paths'))
            data['is-unix'] = self.symlink_tracker.is_unix
            self.event_reporter.report('symlink-stats', data=data)


class SymlinkTracker(object):
    NUM_SAMPLE_PATHS = 5

    def __init__(self, dir):
        self.is_unix = sys.platform.startswith('darwin') or sys.platform.startswith('linux')
        self.dir = os.path.realpath(dir)
        self.data = None

    def process_unix_dirent(self, dirent):
        if dirent.type != FILE_TYPE_POSIX_SYMLINK:
            return
        valid_link = False
        abs_link = False
        link_in_dropbox = False
        eloop = False
        try:
            linkpath = os.readlink(dirent.fullpath)
            decodable = isinstance(linkpath, unicode)
            self.data['total'] += 1
            if not decodable:
                self.data['undecodable-symlink-target'] += 1
                return
            if len(self.data['sample-paths']) < self.NUM_SAMPLE_PATHS:
                self.data['sample-paths'].append((dirent.fullpath, linkpath))
            abs_link = linkpath.startswith('/')
            abs_link_path = ''
            if abs_link:
                abs_link_path = os.path.realpath(linkpath)
            else:
                curdir = dirent.fullpath[:dirent.fullpath.rindex('/')]
                abs_link_path = os.path.realpath(os.path.join(curdir, linkpath))
            valid_link = os.path.exists(abs_link_path)
            link_in_dropbox = abs_link_path.startswith(self.dir)
            eloop = abs_link_path == dirent.fullpath
            if eloop:
                self.data['eloop'] += 1
            elif valid_link and abs_link and link_in_dropbox:
                self.data['valid-absolute-inside'] += 1
            elif valid_link and abs_link and not link_in_dropbox:
                self.data['valid-absolute-outside'] += 1
            elif valid_link and not abs_link and link_in_dropbox:
                self.data['valid-relative-inside'] += 1
            elif valid_link and not abs_link and not link_in_dropbox:
                self.data['valid-relative-outside'] += 1
            elif not valid_link and abs_link and link_in_dropbox:
                self.data['invalid-absolute-inside'] += 1
            elif not valid_link and abs_link and not link_in_dropbox:
                self.data['invalid-absolute-outside'] += 1
            elif not valid_link and not abs_link and link_in_dropbox:
                self.data['invalid-relative-inside'] += 1
            elif not valid_link and not abs_link and not link_in_dropbox:
                self.data['invalid-relative-outside'] += 1
        except OSError as e:
            if e.errno != errno.EINVAL:
                unhandled_exc_handler()
        except Exception:
            unhandled_exc_handler()

    def process_win32_dirent(self, dirent):
        reparse_type = dirent.win32_reparse_type
        if reparse_type is not None:
            self.data[reparse_type] += 1
            if len(self.data['sample-paths']) < self.NUM_SAMPLE_PATHS:
                self.data['sample-paths'].append((dirent.fullpath, reparse_type))

    def get_symlink_data(self, cached = False):
        if self.data is not None and cached:
            return self.data
        if self.is_unix:
            fields = ['total',
             'undecodable-symlink-target',
             'eloop',
             'valid-absolute-inside',
             'valid-absolute-outside',
             'valid-relative-inside',
             'valid-relative-outside',
             'invalid-absolute-inside',
             'invalid-absolute-outside',
             'invalid-relative-inside',
             'invalid-relative-outside']
        else:
            fields = WIN32_REPARSE_TAGS
        self.data = dict(((key, 0) for key in fields))
        self.data['sample-paths'] = []
        TRACE('Gathering stats on symlinks...')
        for parent, ents in fastwalk_with_exception_handling(self.dir, follow_symlinks=False):
            for dirent in ents:
                if self.is_unix:
                    self.process_unix_dirent(dirent)
                else:
                    self.process_win32_dirent(dirent)

        if self.is_unix:
            TRACE('Symlink stats: %s total symlinks', self.data['total'])
            if self.data['total']:
                TRACE('In-depth stats: %s', self.data)
        else:
            total_reparse = sum((self.data[tag] for tag in WIN32_REPARSE_TAGS))
            TRACE('Reparse point stats: %s total reparse points', total_reparse)
            if total_reparse:
                TRACE('In-depth stats: %s', self.data)
        TRACE('Finished gathering symlink stats')
        return self.data
