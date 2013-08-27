#Embedded file name: dropbox/client/multiaccount/callbacks.py
import arch
from dropbox import gui
from dropbox.client.multiaccount.manager import DropboxManager, other_client
from dropbox.client import preferences
from dropbox.event import report
from dropbox.sync_engine import move_dropbox
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler

class MultiBoxCallbacks(object):

    def __init__(self, app, mbox):
        self.app = app
        self.mbox = mbox
        for method in MultiBoxCallbacks.__dict__.keys():
            if method.startswith('_') or not callable(getattr(self, method)):
                continue
            DropboxManager.register(method, callable=getattr(self, method))

    def other_client_exit(self, exit_code = 0):
        if self.mbox.is_secondary:
            TRACE('Primary client is exiting, we should go')
            arch.util.hard_exit(exit_code)
        else:
            TRACE('Secondary client is exiting. Cleaning up some state')
            try:
                self.set_secondary_quota_usage(None, None)
            except Exception:
                unhandled_exc_handler()

            self.mbox.on_secondary_link.run_handlers(None)

    def chain(self, content, reqtype, path):
        arch.util.named_pipe_inqueue.put((path, reqtype))
        reply = arch.util.named_pipe_outqueue.get()
        return reply

    def notify_primary(self, command_name, args):
        return arch.util._ct.ifaces_request(command_name, args)

    def set_secondary_quota_usage(self, in_use, quota):
        self.app.tray_controller.set_secondary_quota_usage(in_use, quota)

    def set_secondary_status_label(self, _clear_previous = False, refresh_icon = False, **labels_and_states):
        self.app.status_controller.set_status_labels(set_secondary=True, _clear_previous=_clear_previous, **labels_and_states)
        if refresh_icon:
            self.app.status_controller.status_callbacks.run_handlers()

    def set_secondary_transfer_status(self, upload_status, download_status, hash_status):
        self.app.status_controller.set_secondary_transfer_status(upload_status=upload_status, download_status=download_status, hash_status=hash_status)

    def remove_pref_callback(self, linked):
        if linked is False:
            TRACE('Removing forward preferences callback due to secondary exit.')
            self.app.pref_controller.remove_pref_callback('.*', self._forward_preferences)

    def register_secondary(self, address):
        assert self.mbox.is_primary
        self.mbox.secondary = other_client(address)
        self.mbox.initialize_handlers()
        self.app.pref_controller.add_pref_callback('.*', self._forward_preferences)
        self._forward_preferences(self.app.pref_controller)
        self.mbox.on_secondary_link.add_handler(self.remove_pref_callback)

    def complete_link(self, email, displayname):
        assert self.mbox.is_primary
        self.app.config['secondary_client_email'] = email
        self.app.config['secondary_client_userdisplayname'] = displayname
        self.mbox.has_secondary = True
        self.mbox.on_secondary_link.run_handlers(True)
        self.app.enable_multiaccount()
        report('multiaccount', action='second link complete')

    def open_dropbox(self):
        self.app.open_dropbox()

    def _forward_preferences(self, pref_controller):
        if not self.mbox.enabled:
            TRACE('Not forwarding preferences because secondary does not exist!')
            return
        assert isinstance(pref_controller, preferences.DropboxPrefController)
        config = pref_controller.get_config_for_secondary()
        self.mbox.update_preferences(config)

    def update_preferences(self, config):
        self.app.pref_controller.update(config)

    def show_bubble(self, bubble):
        bubble_context = self.app.bubble_context
        bubble.bubble_context = bubble_context
        if bubble.ctxt_ref is not None:
            bubble.ctxt_ref = bubble_context.make_multibox_secondary_context_ref(bubble.ctxt_ref)
        self.app.ui_kit.show_bubble(bubble)

    def bubble_context_thunk(self, ctxt_ref):
        self.app.bubble_context.get_context_ref(ctxt_ref).thunk()

    def bubble_context_expire(self, ctxt_ref):
        self.app.bubble_context.expire_context_ref(ctxt_ref)

    def get_dropbox_location(self):
        return self.app.pref_controller['dropbox_path']

    def get_dropbox_folder_name(self):
        return self.app.default_dropbox_folder_name

    def get_config(self, *n, **kw):
        return dict(self.app.sync_engine.config)

    def is_invalid_dropbox_location(self, location):
        return move_dropbox.path_makes_invalid_dropbox_parent(location, self.app.sync_engine, True)

    def move_dropbox(self, path):
        gui.message_sender(gui.spawn_thread_with_name('REMOTE_MOVE'), on_success=self.mbox.move_signal_success, on_exception=self.mbox.move_signal_exception, block=False, handle_exceptions=True, dont_post=lambda : False)(self.app.sync_engine.move)(path, self.mbox.move_signal_warn_external, progress_callback=self.mbox.move_signal_progress, error_callback=self.mbox.move_signal_error)

    def move_signal_progress(self):
        self.mbox.move_progress_callback()

    def move_signal_exception(self, exc, exc_info):
        self.mbox.move_exception_callback(exc, exc_info)

    def move_signal_success(self, value):
        self.mbox.move_success_callback(value)

    def move_signal_error(self):
        TRACE('!! Got a horrible error while moving, unlinking the second client')
        self.mbox.unlink_secondary()

    def move_signal_warn_external(self, message, has_cancel):
        self.mbox.move_warn_external_callback(message, has_cancel)

    def pause(self):
        self.app.tray_controller.do_pause()

    def resume(self):
        self.app.tray_controller.do_resume()

    def get_directory_ignore_set(self, *n, **kw):
        return self.app.sync_engine.get_directory_ignore_set(*n, **kw)

    def change_directory_ignore_set(self, *n, **kw):
        return self.app.sync_engine.change_directory_ignore_set(*n, **kw)

    def get_root_namespaces(self, *n, **kw):
        return self.app.sync_engine.get_root_namespaces(*n, **kw)

    def get_server_dir_children(self, *n, **kw):
        return self.app.sync_engine.get_server_dir_children(*n, **kw)

    def root_relative_server_path(self, *n, **kw):
        return self.app.sync_engine.root_relative_server_path(*n, **kw)

    def mount_relative_server_path(self, *n, **kw):
        return self.app.sync_engine.mount_relative_server_path(*n, **kw)

    def get_mount_points(self, *n, **kw):
        return self.app.sync_engine.get_mount_points(*n, **kw)

    def get_tag_info(self, *n, **kw):
        return self.app.sync_engine.get_tag_info(*n, **kw)

    def target_ns(self, *n, **kw):
        return self.app.sync_engine.target_ns(*n, **kw)

    def server_to_local(self, *n, **kw):
        return self.app.sync_engine.server_to_local(*n, **kw)

    def is_directory(self, *n, **kw):
        return self.app.sync_engine.is_directory(*n, **kw)

    def login_and_redirect(self, *n, **kw):
        return self.app.sync_engine.desktop_login.login_and_redirect(*n, **kw)

    def server_dir_exists(self, *n, **kw):
        return self.app.sync_engine.server_dir_exists(*n, **kw)

    def local_case_filenames(self, *n, **kw):
        return self.app.sync_engine.local_case_filenames(*n, **kw)

    def add_remote_file_event_callback(self, *n, **kw):
        assert self.mbox.is_secondary
        cb = self.mbox.primary.fire_remote_file_event_callback
        self.app.sync_engine.add_remote_file_event_callback(cb)

    def remove_remote_file_event_callback(self, *n, **kw):
        assert self.mbox.is_secondary
        cb = self.mbox.primary.fire_remote_file_event_callback
        self.app.sync_engine.remove_remote_file_event_callback(cb)

    def fire_remote_file_event_callback(self, *n, **kw):
        assert self.mbox.is_primary
        if self.mbox.remote_file_event_callback:
            self.mbox.remote_file_event_callback()

    def get_secondary_email(self, *n, **kw):
        assert self.mbox.is_primary
        return self.mbox.secondary_email

    def recently_changed_get_latest(self, *n, **kw):
        if not self.app.recently_changed:
            return []
        return self.app.recently_changed.get_latest(*n, **kw)

    def notifications_get_latest(self, *n, **kw):
        if not self.app.notification_controller:
            return []
        return [ notification._get_serialized() for notification in self.app.notification_controller.get_latest(*n, **kw) ]

    def notifications_get_stickies(self, *n, **kw):
        if not self.app.notification_controller:
            return []
        return [ sticky._get_serialized() for sticky in self.app.notification_controller.get_stickies(*n, **kw) ]

    def notifications_get_unread_count(self, *n, **kw):
        if not self.app.notification_controller:
            return 0
        return self.app.notification_controller._get_unread_count(*n, **kw)

    def notifications_acknowledge(self, serialized_notifications):
        if not self.app.notification_controller:
            msg = 'Tried to acknowledge to secondary without notification controller!'
            report_bad_assumption(msg)
            return
        from ui.common.notifications import MetaUserNotification
        notifications = self.mbox.notification_controller._load_serialized(MetaUserNotification, serialized_notifications)
        self.app.notification_controller.acknowledge(notifications)

    def notifications_perform_action(self, notification_key, target):
        return self._notification_or_sticky_perform_action(notification_key, target, self.app.notification_controller._timeline.get)

    def stickies_perform_action(self, sticky_key, target):
        return self._notification_or_sticky_perform_action(sticky_key, target, self.app.notification_controller._stickies.get)

    def _notification_or_sticky_perform_action(self, notification_key, target, notification_search_fn):
        if not self.app.notification_controller:
            report_bad_assumption('Secondary notification controller went away!')
            return
        notification = notification_search_fn(notification_key)
        if not notification:
            TRACE('!! Notification %s disappeared from _timeline or _stickies!', notification_key)
            return
        notification.perform_action(self.app, target)

    def notifications_update_unread(self, should_ping, secondary_count):
        if self.mbox.is_secondary:
            report_bad_assumption('Primary pinged secondary not-controller')
        elif not self.app.merged_notification_controller:
            report_bad_assumption("Secondary tried to ping primary's nonexistent not-controller")
        elif secondary_count is None:
            report_bad_assumption("Secondary didn't provide secondary_count")
        else:
            self.app.merged_notification_controller._update_unread(should_ping, secondary_count=secondary_count)

    def recently_changed_retrieve_thumbnail(self, name, blocklist, format):
        return self.app.conn.retrieve_thumbnail(name, blocklist, format=format)

    def screenshots_provider_cb(self, file_path, copy_link = True, show_bubble = True):
        assert self.mbox.is_secondary
        self.app.screenshots_controller.screenshot_handler(file_path, copy_link, show_bubble)

    def register_screenshots_cb(self):
        assert self.mbox.is_primary
        try:
            self.app.screenshots_callbacks.set_secondary(self.mbox.screenshots_provider_cb)

            def remove_secondary(linked):
                if linked is False:
                    self.app.screenshots_callbacks.set_secondary(None)

            self.mbox.on_secondary_link.add_handler(remove_secondary)
        except Exception:
            unhandled_exc_handler()

    def update_screenshot_preferences(self):
        assert self.mbox.is_primary
        self.app.screenshots_controller.update_preferences()

    def handle_splash_result_on_thread(self):
        assert self.mbox.is_secondary
        self.app.screenshots_controller.handle_splash_result_on_thread()

    def show_screenshot_success_bubble(self, new_path):
        assert self.mbox.is_primary
        self.app.screenshots_controller.show_success_bubble(new_path)

    def show_import_button(self):
        return self.app.stuff_importer.show_import_button(self.app)

    def prompt_iphoto_import(self):
        TRACE('MULTIACCOUNT: IPHOTOIMPORT: other client asking to prompt for iPhoto import')
        return self.app.stuff_importer.prompt_import()
