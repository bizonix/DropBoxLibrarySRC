#Embedded file name: dropbox/client/multiaccount/proxy.py
import functools
import types
from dropbox.trace import report_bad_assumption
from ui.common.notifications import MetaStickyNotification, MetaUserNotification, StickyNotification, UserNotification

class MultiboxProxy(object):

    def __init__(self, mbox):
        self.mbox = mbox


class MultiaccountProxies(object):

    @property
    def config(self):
        assert self.is_primary
        return dict(self.secondary.get_config().items())

    @property
    def recently_changed(self):
        return RecentlyChangedProxy(self)

    @property
    def notification_controller(self):
        return UserNotificationProxy(self)

    @property
    def sync_engine(self):
        return SyncEngineProxy(self)


class RecentlyChangedProxy(MultiboxProxy):

    def get_latest(self, *args, **kwargs):
        if not self.mbox.has_secondary:
            return []
        return self.mbox.recently_changed_get_latest(*args, **kwargs)


class UserNotificationProxy(MultiboxProxy):

    def get_latest(self, *args, **kwargs):
        if not self.mbox.has_secondary:
            return []
        notifications = self.mbox.notifications_get_latest(*args, **kwargs)
        return self._load_serialized(MetaUserNotification, notifications)

    def get_stickies(self, *args, **kwargs):
        if not self.mbox.has_secondary:
            return []
        stickies = self.mbox.notifications_get_stickies(*args, **kwargs)
        return self._load_serialized(MetaStickyNotification, stickies)

    def acknowledge(self, notifications):
        if not self.mbox.has_secondary:
            report_bad_assumption('tried to ack secondary notifications without second process!')
            return
        serialized = [ notification._get_serialized() for notification in notifications ]
        self.mbox.notifications_acknowledge(serialized)

    def _get_unread_count(self, *args, **kwargs):
        if not self.mbox.has_secondary:
            return 0
        return self.mbox.notifications_get_unread_count(*args, **kwargs)

    def _load_serialized(self, metaclass, notifications):
        notification_objs = []
        for notification in notifications:
            obj = metaclass._from_serialized(notification)

            @functools.wraps(obj.perform_action)
            def proxied_method(notif_self, primary_app, target):
                if isinstance(obj, UserNotification):
                    self.mbox.notifications_perform_action(obj.key, target)
                elif isinstance(obj, StickyNotification):
                    self.mbox.stickies_perform_action(obj.key, target)
                else:
                    assert isinstance(obj, (UserNotification, StickyNotification)), 'Unknown notification type! %r' % type(obj)

            obj.perform_action = types.MethodType(proxied_method, notification)
            notification_objs.append(obj)

        return notification_objs


class DesktopLoginProxy(MultiboxProxy):

    def login_and_redirect(self, *n, **kw):
        return self.mbox.desktop_login.login_and_redirect(*n, **kw)


class SyncEngineProxy(MultiboxProxy):

    def add_remote_file_event_callback(self, cb = None):
        assert self.mbox.is_primary
        if cb:
            self.mbox.remote_file_event_callback = cb
            self.mbox.secondary.add_remote_file_event_callback()

    def remove_remote_file_event_callback(self, cb = None):
        assert self.mbox.is_primary
        self.mbox.remote_file_event_callback = None
        self.mbox.secondary.remove_remote_file_event_callback()

    @property
    def config(self):
        return self.mbox.config

    @property
    def desktop_login(self):
        return DesktopLoginProxy(self.mbox)

    def move_dropbox(self, path, progress_callback, exception_callback, success_callback, warn_external_callback):
        self.move_progress_callback = progress_callback
        self.move_exception_callback = exception_callback
        self.move_success_callback = success_callback
        self.move_warn_external_callback = warn_external_callback
        self.mbox.move_dropbox(path)

    def get_directory_ignore_set(self, *n, **kw):
        return self.mbox.get_directory_ignore_set(*n, **kw)

    def change_directory_ignore_set(self, *n, **kw):
        return self.mbox.change_directory_ignore_set(*n, **kw)

    def get_root_namespaces(self, *n, **kw):
        return self.mbox.get_root_namespaces(*n, **kw)

    def get_server_dir_children(self, *n, **kw):
        return self.mbox.get_server_dir_children(*n, **kw)

    def get_mount_points(self, *n, **kw):
        return self.mbox.get_mount_points(*n, **kw)

    def get_tag_info(self, *n, **kw):
        return self.mbox.get_tag_info(*n, **kw)

    def is_directory(self, *n, **kw):
        return self.mbox.is_directory(*n, **kw)

    def local_case_filenames(self, *n, **kw):
        return self.mbox.local_case_filenames(*n, **kw)

    def local_to_server(self, *n, **kw):
        return self.mbox.local_to_server(*n, **kw)

    def mount_relative_server_path(self, *n, **kw):
        return self.mbox.mount_relative_server_path(*n, **kw)

    def root_relative_server_path(self, *n, **kw):
        return self.mbox.root_relative_server_path(*n, **kw)

    def server_dir_exists(self, *n, **kw):
        return self.mbox.server_dir_exists(*n, **kw)

    def server_to_local(self, *n, **kw):
        return self.mbox.server_to_local(*n, **kw)

    def target_ns(self, *n, **kw):
        return self.mbox.target_ns(*n, **kw)


class StuffImporterMultiaccountProxy(object):

    def __init__(self, app):
        self.app = app

    @staticmethod
    def show_import_button(app):
        return app.mbox.show_import_button()

    def prompt_import(self):
        return self.app.mbox.prompt_iphoto_import()
