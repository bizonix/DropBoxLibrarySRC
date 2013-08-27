#Embedded file name: ui/common/selective_sync.py
from __future__ import absolute_import
import os
import pprint
import bisect
import threading
import itertools
import functools
import urllib
import arch
from collections import deque
from dropbox.path import ServerPath
from dropbox.trace import unhandled_exc_handler, report_bad_assumption, TRACE
from dropbox.functions import lrudict
from dropbox.debugging import easy_repr
from dropbox.file_cache.exceptions import NamespaceNotMountedError
from .strings import UIStrings

class SelectiveSyncStrings(UIStrings):
    _platform_overrides = {'win': {'switch_to_advanced_view': (u'Switch to Advanced view', u'Windows-specific capitalization change.')}}
    _strings = {'prefs_group_label': u'Selective Sync',
     'prefs_group_label_colon': u'Selective Sync:',
     'prefs_change_label': (u'Change Settings...', u'BUTTON'),
     'prefs_launch_label': (u'Select which folders sync to this computer:', u'SHORT. Limited space! Please keep to about this length!'),
     'prefs_launch_button': (u'Selective Sync...', u'BUTTON'),
     'prefs_working_button': (u'Updating...', u"BUTTON. Indicates the program is in the process of working on the user's request."),
     'window_title': u'Selective Sync',
     'info': (u'Only checked folders will sync to this computer.', '"checked" as is "a checked checkbox"'),
     'switch_to_advanced_view': u'Switch to Advanced View',
     'window_ok_button': (u'Update', u'BUTTON. This is an imperative verb.'),
     'cancel_button': (u'Cancel', u'BUTTON. This is an imperative verb.'),
     'downloading_file_list': u'Connecting to Dropbox. Hold tight...',
     'completing_initial_index': (u'Connecting to Dropbox. Hold tight...', 'see index/indexing in our terminology file.'),
     'confirmation_caption': u'Update Selective Sync settings?',
     'confirmation_message_ignore_only': u"Unchecked folders will be removed from this computer's Dropbox. They will still be available on the web and other devices.",
     'confirmation_message_ignore_and_unignore': u'Dropbox on this computer will be updated with your changes.',
     'confirmation_ok_button': (u'Update', u'BUTTON'),
     'unignore_error_caption': (u'Some Changes Failed', u"this means: some changes to the user's settings have failed"),
     'unignore_error_message_template': (u'The following folder couldn\'t be added to this computer\'s Dropbox: "%(path)s".', u'path is a file path, for example, C:\\\\Users\\Steve\\Documents\\Dropbox\\Photos'),
     'unignore_error_message_more_template': (u'The following folder couldn\'t be added to this computer\'s Dropbox: "%(path)s", and %(num_extra_folders)s more as well.', u'path is a file path, for example, C:\\\\Users\\Steve\\Documents\\Dropbox\\Photos. num_extra_folders is a number.'),
     'really_bad_error_caption': u'Unexpected Error',
     'really_bad_error_message': u'Dropbox was unable to update your selective sync preferences. Please contact support if the problem persists.',
     'really_bad_error_button': (u'OK', u'BUTTON'),
     'context_menu_open_folder': (u'Open Folder', 'This is an action, meaning, open the folder.'),
     'context_menu_browse_on_website': u'View on Dropbox.com...'}


selsync_strings = SelectiveSyncStrings

def failed_unignores_message_from_failures(failures, default_dropbox_folder_name):
    first_failure_path = os.path.join(default_dropbox_folder_name, *ServerPath(failures[0]).ns_rel()[1].split('/')[1:])
    if len(failures) > 1:
        return selsync_strings.unignore_error_message_more_template % dict(path=first_failure_path, num_extra_folders=len(failures) - 1)
    else:
        return selsync_strings.unignore_error_message_template % dict(path=first_failure_path)


class LazySelectiveSync(object):

    def __init__(self, app, sync_engine, url_info, use_tri_state_checks = False, initial_directory_ignore_set = None):
        self.app = app
        self.use_tri_state_checks = use_tri_state_checks
        self.dir_children_sort_cmp = arch.util.natural_basename_sort_cmp
        if initial_directory_ignore_set is None or len(initial_directory_ignore_set) == 0:
            initial_directory_ignore_set = sync_engine.get_directory_ignore_set()
        self.initial_directory_ignore_set = set((ServerPath(s).lower() for s in initial_directory_ignore_set))
        self.current_directory_ignore_set = set(self.initial_directory_ignore_set)
        self.root_namespaces = sync_engine.get_root_namespaces()
        self.get_server_dir_children = sync_engine.get_server_dir_children
        self.server_dir_exists = sync_engine.server_dir_exists
        self.local_case_filenames = sync_engine.local_case_filenames
        self.root_relative_server_path = sync_engine.root_relative_server_path
        self.mount_relative_server_path = sync_engine.mount_relative_server_path
        self.get_mount_points = sync_engine.get_mount_points
        self.get_tag_info = sync_engine.get_tag_info
        self.target_ns = sync_engine.target_ns
        self.invalidate_ui_callback = None
        sync_engine.add_remote_file_event_callback(self.remote_invalidate)
        self.remove_remote_file_event_callback = functools.partial(sync_engine.remove_remote_file_event_callback, self.remote_invalidate)
        self.server_to_local = sync_engine.server_to_local
        self.local_to_server = sync_engine.local_to_server
        self.url_info = url_info
        self.desktop_login = sync_engine.desktop_login
        if 'dropbox_path' in sync_engine.config:
            try:
                self.dropbox_basename = os.path.basename(sync_engine.config['dropbox_path'])
            except Exception:
                unhandled_exc_handler()
                self.dropbox_basename = self.app.default_dropbox_folder_name

        else:
            self.dropbox_basename = self.app.default_dropbox_folder_name

    def __repr__(self):
        return easy_repr(self, 'initial_directory_ignore_set', 'current_directory_ignore_set', 'root_namespaces', 'get_server_dir_children', 'root_relative_server_path', 'mount_relative_server_path')

    def set_invalidate_ui_callback(self, callback):
        self.invalidate_ui_callback = callback

    def clear_invalidate_ui_callback(self):
        self.invalidate_ui_callback = None

    def get_root_paths(self):
        return [ ServerPath('%d:/' % ns) for ns in self.root_namespaces ]

    def dir_children_for_path(self, rr_server_path, lower = True):
        the_dir = rr_server_path
        if lower:
            rr_server_path = rr_server_path.lower()
        results = self.get_server_dir_children(self.mount_relative_server_path(rr_server_path), lower=False)
        results_on_server_lower_set = set([ the_dir.join(tup[0]).lower() for tup in results ])
        for ignored in self.current_directory_ignore_set:
            if ignored.ns == the_dir.ns and not ignored.is_root and ignored.dirname == the_dir and ignored not in results_on_server_lower_set:
                try:
                    local_path = self.server_to_local(ignored)
                    local_case_paths = self.local_case_filenames(local_path)
                    if local_case_paths:
                        local_path = local_case_paths[0]
                        display_path = self.local_to_server(local_path)
                        result = (display_path.basename, 0)
                        results.append(result)
                except NamespaceNotMountedError:
                    continue

        if self.dir_children_sort_cmp:
            results.sort(lambda tup1, tup2: self.dir_children_sort_cmp(tup1[0], tup2[0]))
        results = [ (the_dir.join(ent[0]), ent[1]) for ent in results ]
        return results

    def query_check_state(self, rr_server_path):
        lowered = rr_server_path.lower()
        if lowered in self.current_directory_ignore_set or any((ignored_path.lower().is_parent_of(lowered) for ignored_path in self.current_directory_ignore_set)):
            return 0
        if self.use_tri_state_checks and any((lowered.is_parent_of(ignored_path.lower()) for ignored_path in self.current_directory_ignore_set)):
            return -1
        return 1

    def set_check_state_from_ui(self, rr_server_path, check_state):
        lowered = rr_server_path.lower()
        if check_state == 1:
            while lowered is not None and lowered not in self.current_directory_ignore_set:
                if lowered.ns_rel()[1] == '/':
                    lowered = None
                else:
                    parent_lowered = lowered.dirname
                    for sibling_ent in self.dir_children_for_path(parent_lowered):
                        sibling_lowered = self.root_relative_server_path(sibling_ent[0]).lower()
                        if sibling_lowered != lowered:
                            self.current_directory_ignore_set.add(sibling_lowered)

                    lowered = parent_lowered

            if lowered is not None:
                self.current_directory_ignore_set.remove(lowered)
        else:
            self.current_directory_ignore_set = set((ignored_path for ignored_path in self.current_directory_ignore_set if not lowered.is_parent_of(ignored_path)))
            self.current_directory_ignore_set.add(lowered)
        TRACE('ignore set now: %s' % (pprint.pformat(self.current_directory_ignore_set),))

    def invalid(self):
        return self.current_directory_ignore_set != self.initial_directory_ignore_set

    def reset(self):
        self.current_directory_ignore_set = set(self.initial_directory_ignore_set)

    def remote_invalidate(self, events):
        if self.invalidate_ui_callback:
            paths_to_invalidate_ui_under = {}
            for fast_details in events:
                if fast_details is not None:
                    if fast_details.dir or fast_details.size < 0:
                        invalid = self.root_relative_server_path(fast_details.server_path).dirname.lower()
                        if invalid not in paths_to_invalidate_ui_under:
                            paths_to_invalidate_ui_under[invalid] = self.dir_children_for_path(invalid)

            cb = self.invalidate_ui_callback
            if cb is not None:
                cb(paths_to_invalidate_ui_under)

    def write_changes_to_sync_engine(self, sync_engine):
        return sync_engine.change_directory_ignore_set([ unicode(a) for a in self.current_directory_ignore_set ])

    def get_confirmation_message(self):
        if self.initial_directory_ignore_set <= self.current_directory_ignore_set:
            return selsync_strings.confirmation_message_ignore_only
        else:
            return selsync_strings.confirmation_message_ignore_and_unignore


def lrumemoized(cache_size):
    the_cache = lrudict(cache_size=cache_size)

    def wrapper(f):

        def inner(*args, **kw):
            if 'invalidate' in kw:
                the_cache.clear()
                return
            try:
                return the_cache[args]
            except KeyError:
                the_cache[args] = value = f(*args)
                return value
            except TypeError:
                report_bad_assumption("Can't memoize this function and args: %r(*%r)" % (f, args))
                return f(*args)

        return inner

    return wrapper


class LazySelectiveSyncUI(LazySelectiveSync):

    def __init__(self, *n, **kw):
        super(LazySelectiveSyncUI, self).__init__(*n, **kw)
        self.advanced_view = any((len(path.ns_rel()[1].split('/')) > 2 for path in self.initial_directory_ignore_set))

    def set_advanced_view(self, advanced_view):
        self.advanced_view = advanced_view

    def dir_children_for_path(self, rr_server_path):
        if self.advanced_view:
            return super(LazySelectiveSyncUI, self).dir_children_for_path(rr_server_path)
        else:
            ns, rel = rr_server_path.ns_rel()
            if rel != '/':
                return []
            return [ (ent[0], 0) for ent in super(LazySelectiveSyncUI, self).dir_children_for_path(rr_server_path) ]

    def image_tag_for_path(self, rr_server_path):
        try:
            rel = rr_server_path.ns_rel()[1]
            if rel == u'/':
                return 'dropbox'
            tag_info = self.get_tag_info(server_path=rr_server_path)
            if tag_info:
                return tag_info[0]
        except Exception:
            unhandled_exc_handler()

        return 'folder'

    def title_for_path(self, rr_server_path):
        ns, rel = rr_server_path.ns_rel()
        if rel == '/':
            return self.dropbox_basename
        return rr_server_path.basename

    def check_state_for_path(self, rr_server_path):
        return self.query_check_state(rr_server_path)

    def context_menu_for_path(self, rr_server_path):
        server_path = self.mount_relative_server_path(rr_server_path)
        try:
            local_pathu = unicode(self.server_to_local(server_path))
        except NamespaceNotMountedError:
            local_pathu = u''

        ret = []
        if os.path.exists(local_pathu):
            ret.append((selsync_strings.context_menu_open_folder, functools.partial(arch.util.launch_folder, local_pathu)))
        if self.server_dir_exists(server_path):
            ns_id, rel_path = server_path.ns_rel()
            ret.append((selsync_strings.context_menu_browse_on_website, functools.partial(self.desktop_login.login_and_redirect, 'c/%s%s?ns_id=%s' % ('browse', urllib.quote(rel_path.encode('utf-8')), ns_id))))
        return ret


class CachingLazySelectiveSyncUI(LazySelectiveSyncUI):

    def set_advanced_view(self, advanced_view):
        self.dir_children_for_path(invalidate=True)
        super(CachingLazySelectiveSyncUI, self).set_advanced_view(advanced_view)

    @lrumemoized(40)
    def dir_children_for_path(self, rr_server_path):
        return super(CachingLazySelectiveSyncUI, self).dir_children_for_path(rr_server_path)

    @lrumemoized(500)
    def image_tag_for_path(self, rr_server_path):
        return super(CachingLazySelectiveSyncUI, self).image_tag_for_path(rr_server_path)

    @lrumemoized(500)
    def check_state_for_path(self, rr_server_path):
        return super(CachingLazySelectiveSyncUI, self).check_state_for_path(rr_server_path)

    @lrumemoized(40)
    def context_menu_for_path(self, rr_server_path):
        return super(CachingLazySelectiveSyncUI, self).context_menu_for_path(rr_server_path)

    def set_check_state_from_ui(self, rr_server_path, check_state):
        self.check_state_for_path(invalidate=True)
        super(CachingLazySelectiveSyncUI, self).set_check_state_from_ui(rr_server_path, check_state)

    def remote_invalidate(self, events):
        self.dir_children_for_path(invalidate=True)
        self.image_tag_for_path(invalidate=True)
        self.check_state_for_path(invalidate=True)
        self.context_menu_for_path(invalidate=True)
        super(CachingLazySelectiveSyncUI, self).remote_invalidate(events)
