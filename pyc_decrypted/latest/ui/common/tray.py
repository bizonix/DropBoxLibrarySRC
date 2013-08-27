#Embedded file name: ui/common/tray.py
from __future__ import absolute_import
import functools
import pprint
import socket
import threading
import time
from collections import OrderedDict
from itertools import count
from build_number import is_frozen, BUILD_KEY, VERSION
from dropbox.bubble import BubbleKind, Bubble
from dropbox.client.profile import plop_profile
from dropbox.client.status import StatusController
from dropbox.client.multiaccount.constants import Roles
from dropbox.debugging import easy_repr
from dropbox.event import report
from dropbox.functions import frozendict, handle_exceptions, snippet
from dropbox.gui import message_sender, spawn_thread_with_name
from dropbox.i18n import format_number, format_percent, trans
from dropbox.low_functions import tail
from dropbox.platform import platform
from dropbox.threadutils import stop_all_threads
from dropbox.trace import TRACE, unhandled_exc_handler, debugging_features_are_enabled, trace_threads
from ui.common.notifications import QuotaFullStickyNotification
from ui.common.strings import UIStrings
import arch
PHOTO_STATE_SHOW_NOTHING = 0
PHOTO_STATE_SHOW_LAST_IMPORT = 1
PHOTO_STATE_SHOW_UPLOADS_FOLDER = 2
PHOTO_STATE_SHOW_PROGRESS = 3
PHOTO_STATE_SHOW_PROGRESS_BUSY = 4

class TrayOptionStrings(UIStrings):
    _strings = dict(open_dropbox=(u'Open Dropbox Folder', 'open is a verb'), open_personal_dropbox=(u'Open Personal Dropbox Folder', 'open is a verb'), open_business_dropbox=(u'Open Business Dropbox Folder', 'open is a verb'), launch_website=u'Launch Dropbox Website', recently_changed=u'Recently Changed Files', usage_text=(u'%(percentage)s of %(total_space)sGB used', 'for example "23.4% of 50.0GB used"'), out_of_space=u'Out of Dropbox space', get_more_space=u'Get More Space', preferences_dotdotdot=u'Preferences...', help_center=u'Help Center', pause_syncing=(u'Pause Syncing', 'pause is a verb. this means, halt file syncing for the time being.'), resume_syncing=(u'Resume Syncing', 'resume is a verb'), view_photo_import_progress=u'View Import Progress...', view_last_photo_import=u'View Recently Imported Photos', view_camera_uploads_folder=u'View Camera Uploads Folder', exit_dropbox=u'Quit Dropbox')
    _platform_overrides = dict(win=dict(open_dropbox=u'Open Dropbox folder', launch_website=u'Launch Dropbox website', recently_changed=u'Recently changed files', get_more_space=u'Get more space', help_center=u'Help center', pause_syncing=u'Pause syncing', resume_syncing=u'Resume syncing', view_photo_import_progress=u'View import progress...', view_last_photo_import=u'View recently imported photos', exit_dropbox=u'Exit Dropbox'))


class TrayController(object):
    OPTION_OPEN_FOLDER = 0
    OPTION_OPEN_WEBSITE = 1
    OPTION_OPEN_PREFERENCES = 2
    OPTION_PAUSE = 3
    OPTION_RESUME = 4
    OPTION_OPEN_HELP = 5
    OPTION_QUIT = 6
    OPTION_RECENTLY_CHANGED = 7
    OPTION_OPEN_PERSONAL_FOLDER = 8
    OPTION_OPEN_BUSINESS_FOLDER = 9
    OPTION_PRIMARY_QUOTA = 10
    STATE_INITIALIZING = 0
    STATE_LINKING = 1
    STATE_ACTIVE = 2
    IDLE = 0
    BUSY = 1
    CONNECTING = 2
    BROKEN = 3
    CAM = 4
    PAUSED = 5

    def __repr__(self):
        return easy_repr(self, 'option_callbacks', 'icon_state', 'last_update', 'last_status', 'ui_flags', 'in_use', 'quota')

    def __init__(self, dropbox_app):
        self.dropbox_app = dropbox_app
        self.status_controller = self.dropbox_app.status_controller
        self.sync_engine = None
        self.status_controller.add_status_callback(self.trigger_update)
        self._debugging_options = ((u'Soft Sync Engine Resync', self.soft_resync),
         (u'Resync Notifications', lambda : self.dropbox_app.notification_controller._trigger_resync()),
         (u'Test Bubble', self.test_bubble),
         (u'Test Sticky Notification', self.test_sticky_notification),
         (u'Show Badge', functools.partial(self.update_badge, 2, False)),
         (u'Show Badge + Ping', functools.partial(self.update_badge, 1, True)),
         (u'Clear Badge', functools.partial(self.update_badge, 0, False)),
         (u'Save profile to file', self.profile),
         (u'Send trace logs', functools.partial(self.choose_option, 'send_trace_log')),
         (u'Send events to server', lambda : self.dropbox_app.event.flush_events()),
         (u'Restart', lambda : arch.util.restart()),
         (u'Trace thread stacks', trace_threads))
        if platform == 'win':
            self._debugging_options += ((u'Promote Tray Icon', functools.partial(arch.startup._fix_explorer, True)),)
        self._debugging_options_non_frozen = ((u'Reconnect all', self.reconnect_all),
         (u'Stop profile', self.stop_all_threads),
         (u'Tray arrow', self.test_tray_arrow),
         (u'Segfault', self.segfault),
         (u'Test Download Updater CDN', self.test_download_updator_via_cdn),
         (u'Test Download Updater BlockServer', self.test_end_to_end_auto_update_download),
         (u'Test End to End Auto Update Logic', self.test_end_to_end_auto_update_download))

        def open_url_thunk(name):
            return functools.partial(self.dropbox_app.desktop_login.login_and_redirect, name)

        self.open_tray_login = open_url_thunk('home')
        self.launch_upgrade = open_url_thunk('plans')
        self.open_discussion_forum = open_url_thunk('forum')
        self.open_help_center = open_url_thunk('help')
        self.open_web_tour = open_url_thunk('tour')
        self.low_disk_space = open_url_thunk('help/164')
        self.hard_exit = self.quit = functools.partial(arch.util.hard_exit, flush=False)
        self.option_callbacks = {}
        self.option_callbacks_funcs = {}
        self.option_callbacks_lock = threading.Lock()
        self.lock = threading.Lock()
        self.icon_state = self.IDLE
        self.last_trace = None
        self.ui_flags = frozendict()
        self.in_use, self.quota = (0, 0)
        self.secondary_in_use, self.secondary_quota = (0, 0)
        self.generation = 0
        self.last_low_disk_space_bubble = None
        self.photo_menu_state = PHOTO_STATE_SHOW_NOTHING
        self.open_dropbox = self.click_track(self.open_dropbox, 'open_folder')
        self.open_tray_login = self.click_track(self.open_tray_login, 'launch_website')
        self.out_of_space = self.click_track(self.launch_upgrade, 'out_of_space')
        self.launch_upgrade = self.click_track(self.launch_upgrade, 'get_more_space')
        self.do_pause = self.click_track(self.do_pause, 'pause')
        self.do_resume = self.click_track(self.do_resume, 'resume')
        self.open_help_center = self.click_track(self.open_help_center, 'help_center')
        self.low_disk_space = self.click_track(self.low_disk_space, 'low_disk_space')
        self.open_personal_dropbox = self.click_track(self.open_personal_dropbox, 'open_personal_dropbox')
        self.open_business_dropbox = self.click_track(self.open_business_dropbox, 'open_business_dropbox')
        self._badge_count = 0
        self._triggering_ping = False
        self.trigger_update()

    def update_badge(self, badge_count, trigger_ping):
        changed = False
        with self.lock:
            if badge_count and trigger_ping:
                self._triggering_ping = True
                changed = True
            elif badge_count != self._badge_count:
                changed = True
            self._badge_count = badge_count
        if changed:
            report('jewel-count', value=badge_count)
            self.trigger_update()

    def open_dropbox(self):
        if not (self.status_controller.is_mounted() or self.status_controller.is_linked()):
            return
        self.dropbox_app.open_dropbox()

    def open_personal_dropbox(self):
        if not (self.status_controller.is_mounted() or self.status_controller.is_linked()):
            return
        personal_path = self.dropbox_app.mbox.dropbox_locations.personal
        self.dropbox_app._open_dropbox(personal_path)

    def open_business_dropbox(self):
        if not (self.status_controller.is_mounted() or self.status_controller.is_linked()):
            return
        business_path = self.dropbox_app.mbox.dropbox_locations.business
        self.dropbox_app._open_dropbox(business_path)

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine

    def set_secondary_quota_usage(self, in_use, quota):
        self.secondary_in_use = in_use
        self.secondary_quota = quota
        self.trigger_update()

    def handle_list(self, ret):
        changed = False
        with self.lock:
            in_use, quota = self.in_use, self.quota
            try:
                self.in_use, self.quota = ret['in_use'], ret['quota']
            except KeyError:
                pass

            changed = in_use != self.in_use or quota != self.quota
            if isinstance(ret.get('ui_flags'), dict):
                self.ui_flags = ret['ui_flags']
        if changed:
            if self.dropbox_app.mbox.is_secondary:
                self.dropbox_app.mbox.primary.set_secondary_quota_usage(self.in_use, self.quota)
            self.trigger_update()

    def change_photo_menu_state(self, new_state):
        changed = False
        with self.lock:
            if self.photo_menu_state != new_state:
                self.photo_menu_state = new_state
                changed = True
        if changed:
            self.trigger_update()

    def soft_resync(self):
        self.sync_engine.queue_resync()

    def add_callbacks_for_options(self, option_to_callback):
        for option in option_to_callback:
            with self.option_callbacks_lock:
                self.option_callbacks[option] = self.option_callbacks.get(option, []) + [option_to_callback[option]]

        self.trigger_update()

    def reconnect_all(self):
        self.app.conn.reconnect()

    def stop_all_threads(self):
        stop_all_threads()

    def profile(self):
        plop_profile(self.dropbox_app)

    def segfault(self):
        TRACE('about to segfault')
        time.sleep(1)
        import ctypes
        print ctypes.c_int.from_address(0)

    @message_sender(spawn_thread_with_name('PAUSE'))
    def do_pause(self):
        if self.status_controller.set_status_labels(pausing=True, _fail_if_set=['pausing', 'paused']):
            self.sync_engine.stop()
            if self.dropbox_app.mbox.enabled:
                self.dropbox_app.mbox.pause()
            self.status_controller.set_status_labels(pausing=False, paused=True)

    @message_sender(spawn_thread_with_name('RESUME'))
    def do_resume(self):
        if self.status_controller.set_status_labels(initializing=True, paused=False, _fail_if_not_set=['paused']):
            self.sync_engine.start()
            if self.dropbox_app.mbox.enabled:
                self.dropbox_app.mbox.resume()
            self.status_controller.set_status_labels(initializing=False)

    def test_sticky_notification(self):
        from ui.common.notifications import PhotoGalleryStickyNotification

        def printer(*args, **kwargs):
            TRACE('Notification action taken!')
            return 'go'

        notification = PhotoGalleryStickyNotification(2, 'outer space', printer, printer)
        self.dropbox_app.notification_controller.add_sticky(notification)

    def test_update(self):
        arch.update.can_update()
        threading.Thread(target=arch.update.update_with_archive, args=(u'/tmp/\u2041\u0104/testupdate.tar.bz2', None)).start()

    def test_bubble(self):
        inner_partial = functools.partial(self.dropbox_app.ui_kit.show_bubble, Bubble(BubbleKind.DEBUG_BUBBLE_LONG, u'And here we have a nontrivial amount of text. It should take up several lines in the notification and cause us to make a pretty large bubble.', u"This is a really long title that shouldn't wrap, but rather should truncate in the middle"))
        self.dropbox_app.ui_kit.show_bubble(Bubble(BubbleKind.DEBUG_BUBBLE_HELLO, u'How are you, \u3068\u306f?', u'Hello -> ' + trans(u'Hello'), self.dropbox_app.bubble_context, self.dropbox_app.bubble_context.make_func_context_ref(self.dropbox_app.ui_kit.show_bubble, Bubble(BubbleKind.DEBUG_BUBBLE_PARTIAL, u'albert sucks!', u'ouch!', self.dropbox_app.bubble_context, self.dropbox_app.bubble_context.make_func_context_ref(inner_partial)))))

    def test_tray_arrow(self):
        try:
            self.dropbox_app.ui_kit.start_tray_arrow()
        except Exception:
            unhandled_exc_handler()

    def choose_option(self, option):
        with self.option_callbacks_lock:
            for callback in self.option_callbacks.get(option, []):
                try:
                    callback()
                except Exception:
                    unhandled_exc_handler()

    def menu_item_for_callback(self, option, click):
        with self.option_callbacks_lock:
            if option in self.option_callbacks:
                if option not in self.option_callbacks_funcs:
                    self.option_callbacks_funcs[option] = self.click_track(functools.partial(self.choose_option, option), click)
                return (option, self.option_callbacks_funcs[option])
        return (option, None)

    def view_recently_changed(self, entry):
        if not self.sync_engine:
            return
        local_path = self.sync_engine.server_to_local(entry.server_path)
        arch.util.highlight_file(unicode(local_path))

    def click_track(self, func, label):
        if func == None:
            return

        def w(*args, **kwds):
            try:
                if self.dropbox_app:
                    self.dropbox_app.event.report('click-tray', {'label': label})
            except Exception:
                unhandled_exc_handler()

            func(*args, **kwds)

        return w

    def format_quota_usage(self, in_use, quota):
        percentage = format_percent(0 if not quota else float(in_use) / quota, frac_precision=1)
        total_space = format_number(float(quota) / 1073741824, frac_precision=1)
        return TrayOptionStrings.usage_text % dict(percentage=percentage, total_space=total_space)

    def test_download_updator_via_cdn(self):
        self.dropbox_app.upgrade_logic.handle_list({'update_to_dict': {'version': 'whatever',
                            'blocklist': 'oR1MKlFfGFqECVUSNqt5vv_ndxUmCKwU3vBSlRv69Gk,zVIi3ny4FXK439T5t3bxDw1hJvIZwSekOYzSOdPk8bo,eJNIXpWOpYwteM_QImdN3jy0tCzUw6ZmLipXg9RctHg,-Y216KH4Dbf77PKKChmtzYUUxzwqRyb7i2Oz8FftFvY,F3CyWPt8hcmVmPUY5_uVL0fakJhXZUFw7Mhmyg3Ua-c,AJ-Vna2OvzVd0ESzNZAN6L3wGOtL9KK0iJmNH4EwrUs,uoz_mUKfw4o9AzsYMYBzlAmGSuxxSDzqwOlRoacUSC4,s1UmwnP7CZaP96ChXksV1VWLxyBDPsMEmDNwfKGjKJ8',
                            'url': 'https://d1ilhw0800yew8.cloudfront.net/client/Dropbox-darwin-update-2.3.12.tar.bz2'}})

    def test_download_updator_blockserver(self):
        self.dropbox_app.upgrade_logic.handle_list({'update_to': ('2.3.12', 'oR1MKlFfGFqECVUSNqt5vv_ndxUmCKwU3vBSlRv69Gk,zVIi3ny4FXK439T5t3bxDw1hJvIZwSekOYzSOdPk8bo,eJNIXpWOpYwteM_QImdN3jy0tCzUw6ZmLipXg9RctHg,-Y216KH4Dbf77PKKChmtzYUUxzwqRyb7i2Oz8FftFvY,F3CyWPt8hcmVmPUY5_uVL0fakJhXZUFw7Mhmyg3Ua-c,AJ-Vna2OvzVd0ESzNZAN6L3wGOtL9KK0iJmNH4EwrUs,uoz_mUKfw4o9AzsYMYBzlAmGSuxxSDzqwOlRoacUSC4,s1UmwnP7CZaP96ChXksV1VWLxyBDPsMEmDNwfKGjKJ8')})

    def test_end_to_end_auto_update_download(self):
        ret = self.sync_engine.conn.register_host(self.sync_engine.conn.host_id, socket.gethostname(), u'Dropbox-mac-1.4.0')
        last_revision = self.sync_engine.last_revisions()
        ret = self.sync_engine.conn.list(u'Dropbox-mac-1.4.0', last_revision)
        TRACE(u"ret['update_to'] is %r", pprint.pformat(ret['update_to']))
        if 'update_to_dict' in ret:
            TRACE(u"ret['update_to_dict'] is %r", pprint.pformat(ret['update_to_dict']))
        self.dropbox_app.upgrade_logic.handle_list(ret)

    def pause_or_resume(self):
        if not self.status_controller.is_true('moving') and not self.status_controller.is_true('pausing') and not self.status_controller.is_true('initializing') and not self.status_controller.is_true('starting'):
            if self.sync_engine:
                if not self.status_controller.is_true('paused'):
                    return self.OPTION_PAUSE
                return self.OPTION_RESUME

    def _make_options(self, display_labels, is_linked, is_mounted):
        _UNIQUE_ID = ('unique_%s' % i for i in count(0)).next
        ret = OrderedDict()
        if is_linked:
            if self.dropbox_app.mbox.enabled:
                ret[self.OPTION_OPEN_PERSONAL_FOLDER] = (TrayOptionStrings.open_personal_dropbox, self.open_personal_dropbox)
                ret[self.OPTION_OPEN_BUSINESS_FOLDER] = (TrayOptionStrings.open_business_dropbox, self.open_business_dropbox)
            else:
                ret[self.OPTION_OPEN_FOLDER] = (TrayOptionStrings.open_dropbox, self.open_dropbox)
            ret[self.OPTION_OPEN_WEBSITE] = (TrayOptionStrings.launch_website, self.open_tray_login)
            if self.dropbox_app.recently_changed is not None:
                try:
                    items = [ (snippet(entry.name), functools.partial(self.view_recently_changed, entry)) for entry in self.dropbox_app.recently_changed.get_latest() ]
                    if not items:
                        items = [(trans(u'(None)'), None)]
                except Exception:
                    unhandled_exc_handler()
                else:
                    ret[self.OPTION_RECENTLY_CHANGED] = (TrayOptionStrings.recently_changed, items)

            ret[_UNIQUE_ID()] = (None, None)
            if self.photo_menu_state in (PHOTO_STATE_SHOW_PROGRESS, PHOTO_STATE_SHOW_PROGRESS_BUSY):
                ret[_UNIQUE_ID()] = self.menu_item_for_callback(TrayOptionStrings.view_photo_import_progress, 'importing')
            elif self.photo_menu_state == PHOTO_STATE_SHOW_LAST_IMPORT:
                ret[_UNIQUE_ID()] = self.menu_item_for_callback(TrayOptionStrings.view_last_photo_import, 'view-imported')
            elif self.photo_menu_state == PHOTO_STATE_SHOW_UPLOADS_FOLDER:
                ret[_UNIQUE_ID()] = self.menu_item_for_callback(TrayOptionStrings.view_camera_uploads_folder, 'view-camera-uploads')
            if ret[tail(ret, None)] != (None, None):
                ret[_UNIQUE_ID()] = (None, None)
            usage_text = []
            our_usage_text = self.format_quota_usage(self.in_use, self.quota)
            ret[self.OPTION_PRIMARY_QUOTA] = (our_usage_text, None)
            ret[_UNIQUE_ID()] = (None, None)
        elif is_mounted:
            ret[self.OPTION_OPEN_FOLDER] = (TrayOptionStrings.open_dropbox, self.open_dropbox)
            ret[_UNIQUE_ID()] = (None, None)
        for x in display_labels:
            ret[_UNIQUE_ID()] = (x, None)

        ret[_UNIQUE_ID()] = (None, None)
        if self.in_use > self.quota and self.ui_flags.get('upgrade_prompt', False):
            ret[_UNIQUE_ID()] = (TrayOptionStrings.out_of_space, self.out_of_space)
        elif self.in_use <= self.quota and self.ui_flags.get('upgrade_prompt', False) and ret.get(self.OPTION_OPEN_FOLDER) is not None:
            ret[_UNIQUE_ID()] = (TrayOptionStrings.get_more_space, self.launch_upgrade)
        pause_or_resume = self.pause_or_resume()
        if pause_or_resume == self.OPTION_PAUSE:
            ret[self.OPTION_PAUSE] = (TrayOptionStrings.pause_syncing, self.do_pause)
        elif pause_or_resume == self.OPTION_RESUME:
            ret[self.OPTION_RESUME] = (TrayOptionStrings.resume_syncing, self.do_resume)
        if ret[tail(ret, None)] != (None, None):
            ret[_UNIQUE_ID()] = (None, None)
        ret[self.OPTION_OPEN_PREFERENCES] = self.menu_item_for_callback(TrayOptionStrings.preferences_dotdotdot, 'preferences')
        ret[self.OPTION_OPEN_HELP] = (TrayOptionStrings.help_center, self.open_help_center)
        ret[_UNIQUE_ID()] = (None, None)
        if debugging_features_are_enabled():
            debugging_menu = self._debugging_options
            if not is_frozen():
                debugging_menu += self._debugging_options_non_frozen
            ret[_UNIQUE_ID()] = (u'Debug', debugging_menu)
            ret[_UNIQUE_ID()] = (None, None)
        return ret

    def _make_tooltip(self, display_labels):
        short_tooltip = u'%s %s' % (BUILD_KEY, VERSION)
        long_tooltip = u'%s\n%s' % (short_tooltip, u'\n'.join(display_labels))
        return (short_tooltip, long_tooltip)

    @handle_exceptions
    def trigger_update(self):
        with self.lock:
            labels = self.status_controller.get_labels()
            display_labels = [ string for label, string in labels.iteritems() if label != StatusController.LABEL_SYNCING ]
            collapsed_labels = [ string for label, string in labels.iteritems() if label not in StatusController.TRANSFER_LABELS ]
            is_linked = self.status_controller.is_linked()
            is_mounted = self.status_controller.is_mounted()
            badge_count = self._badge_count
            trigger_ping = self._triggering_ping
            self._triggering_ping = False
            if StatusController.LABEL_LOW_DISK_SPACE in labels or StatusController.LABEL_CANT_MOUNT in labels or StatusController.LABEL_SSL_ERROR in labels:
                icon_state = self.BROKEN
            elif StatusController.LABEL_PAUSED in labels:
                icon_state = self.PAUSED
            elif StatusController.LABEL_CONNECTING in labels or StatusController.LABEL_PRELINK in labels:
                icon_state = self.CONNECTING
            elif StatusController.LABEL_BLANK not in labels:
                icon_state = self.BUSY
            else:
                icon_state = self.IDLE
            popup_icon_state = icon_state
            if self.in_use > self.quota:
                icon_state = self.BROKEN
            elif self.photo_menu_state == PHOTO_STATE_SHOW_PROGRESS:
                icon_state = self.CAM
            elif self.photo_menu_state == PHOTO_STATE_SHOW_PROGRESS_BUSY:
                icon_state = self.BUSY
            elif not is_linked:
                icon_state = self.CONNECTING
            tray_state = self.STATE_INITIALIZING
            if StatusController.LABEL_PRELINK in labels:
                tray_state = self.STATE_LINKING
            elif self.status_controller.is_linked():
                tray_state = self.STATE_ACTIVE
            should_display_quota = not self.dropbox_app.mbox.is_dfb_user_without_linked_pair
            is_personal_secondary = self.dropbox_app.mbox.has_secondary and self.dropbox_app.mbox.secondary_role == Roles.PERSONAL
            percent = None
            quota_message = None
            in_use = self.secondary_in_use if is_personal_secondary else self.in_use
            quota = self.secondary_quota if is_personal_secondary else self.quota
            if in_use is None or quota is None:
                should_display_quota = False
            else:
                quota_message = self.format_quota_usage(in_use, quota)
                if self.dropbox_app.mbox.has_secondary:
                    quota_message += ' (%s)' % trans(u'Personal')
                if in_use and quota:
                    percent = float(in_use) / quota
                else:
                    percent = 0.0
            if self.dropbox_app.notification_controller is not None and self.dropbox_app.mbox.role == Roles.PERSONAL:
                sticky_key = QuotaFullStickyNotification.STICKY_KEY
                if self.in_use > self.quota:
                    if not self.dropbox_app.notification_controller.has_sticky(sticky_key):
                        if self.dropbox_app.mbox.linked:
                            tag = self.dropbox_app.mbox.account_labels_plain.personal
                        else:
                            tag = None
                        sticky = QuotaFullStickyNotification(tag)
                        self.dropbox_app.notification_controller.add_sticky(sticky)
                elif self.dropbox_app.notification_controller.has_sticky(sticky_key):
                    self.dropbox_app.notification_controller.remove_sticky(sticky_key)
        to_trace = u', '.join(labels.itervalues())
        if to_trace != self.last_trace:
            if self.sync_engine is not None and not self.sync_engine.perf_logged and icon_state == self.IDLE:
                self.sync_engine.perf_tracker.event('sync_complete')
                report('sync_engine_perf', **self.sync_engine.perf_tracker.report)
                self.sync_engine.perf_logged = True
            TRACE(u'Status: %s', to_trace)
            self.last_trace = to_trace
        tooltip = self._make_tooltip(display_labels)
        options = self._make_options(display_labels, is_linked, is_mounted)
        ui_kit = self.dropbox_app.ui_kit
        if not ui_kit:
            TRACE("Can't update tray because UI kit isn't available.")
            return
        with self.lock:
            try:
                ui_kit.update_status(popup_icon_state, tray_state, collapsed_labels[0], should_display_quota, percent, quota_message)
            except Exception:
                unhandled_exc_handler()

            try:
                ui_kit.update_tray_icon(icon_state=icon_state, tooltip=tooltip, badge_count=badge_count, trigger_ping=trigger_ping)
            except Exception:
                unhandled_exc_handler()

            try:
                ui_kit.update_options(options)
            except Exception:
                unhandled_exc_handler()

        if StatusController.LABEL_LOW_DISK_SPACE in labels:
            if self.last_low_disk_space_bubble is None or time.time() > self.last_low_disk_space_bubble + 1800:
                if self.dropbox_app.bubble_context is None:
                    return
                ui_kit.show_bubble(Bubble(BubbleKind.LOW_DISK_SPACE, trans(u"Dropbox can't sync until you free some disk space on your computer."), trans(u'Your hard drive space is low.'), self.dropbox_app.bubble_context, self.dropbox_app.bubble_context.make_func_context_ref(self.low_disk_space)))
                self.last_low_disk_space_bubble = time.time()
