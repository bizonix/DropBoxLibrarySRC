#Embedded file name: dropbox/client/notifications.py
import os
import threading
import time
from collections import deque, OrderedDict
from functools import partial
from itertools import islice
from dropbox.bubble import Bubble, BubbleKind
from dropbox.client.background_worker import MessageProcessingThread
from dropbox.client.multiaccount.controller import MergedController
from dropbox.client.notifications_exceptions import MalformedRawNotification, StickyNotificationKeyError, UnsupportedNotificationType, UnsupportedNotificationVersion
from dropbox.debugging import easy_repr
from dropbox.functions import lrudict
from dropbox.gui import message_sender
from dropbox.low_functions import group_by
from dropbox.native_event import AutoResetEvent
from dropbox.sqlite3_helpers import VersionedSqlite3Cache, locked_and_handled
from dropbox.threadutils import StoppableThread
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from ui.common.notifications import MetaUserNotification, UserNotification

class UserNotificationDatabase(VersionedSqlite3Cache):
    _USER_VERSION = 3

    def __init__(self, filename, **kwargs):
        self.tables = ['map']
        self.migrations = [self.migrate_0_to_3, self.migrate_1_to_2, self.migrate_2_to_3]
        super(UserNotificationDatabase, self).__init__(filename, **kwargs)

    def migrate_0_to_3(self, cursor):
        TRACE('%s: Migrating 0->3', self.__class__.__name__)
        cursor.execute('CREATE TABLE map(uid INTEGER PRIMARY KEY NOT NULL,nid INTEGER)')
        cursor.execute('PRAGMA user_version = 3')

    def migrate_1_to_2(self, cursor):
        TRACE('%s: Migrating 1->2', self.__class__.__name__)
        cursor.execute('CREATE TABLE snapshot(key TEXT PRIMARY KEY NOT NULL,timestamp INTEGER NOT NULL, value BLOB NOT NULL)')
        cursor.execute('PRAGMA user_version = 2')

    def migrate_2_to_3(self, cursor):
        TRACE('%s: Migrating 2->3', self.__class__.__name__)
        cursor.execute('DROP TABLE snapshot')
        cursor.execute('PRAGMA user_version = 3')

    @locked_and_handled()
    def set_nid(self, uid, nid):
        with self.connhub.cursor() as cursor:
            cursor.execute('INSERT OR REPLACE INTO map (uid, nid) VALUES (?, ?)', (uid, nid))

    @locked_and_handled()
    def get_nid(self, uid, default = None):
        with self.connhub.cursor() as cursor:
            row = cursor.execute('SELECT nid FROM map WHERE uid=?', (uid,)).fetchone()
            if row and row[0] is not None:
                return row[0]
            return default


class UserNotificationThread(MessageProcessingThread):

    def __init__(self, *args, **kwargs):
        kwargs['name'] = 'USERNOTIFICATION'
        super(UserNotificationThread, self).__init__(*args, **kwargs)


class UserNotificationController(object):
    TIMELINE_SIZE = 3
    TIMELINE_CACHE_SIZE = 100
    BUBBLING_PERIOD = 300
    CUTOFF = 604800
    RESYNC_KEY = 'last_notifications_resync'
    ACK_LIMIT = 32

    def __init__(self, app, uid, path):
        self._app = app
        self._lock = threading.RLock()
        self._thread = UserNotificationThread()
        self._thread.start()
        database_path = os.path.join(path, 'notifications.dbx')
        self._db = UserNotificationDatabase(database_path, keystore=app.keystore)
        self._timeline = OrderedDict()
        self._overflow = deque(maxlen=self.TIMELINE_CACHE_SIZE)
        self._ack_pending = lrudict(cache_size=100)
        self._ack_complete = lrudict(cache_size=100)
        self._stickies = OrderedDict()
        self._reset_state()
        self._sync_engine = None
        self._uid = uid
        self._popup_nid = self._db.get_nid(uid, default=0)
        self._last_resync_ts = self._app.config.get(self.RESYNC_KEY, 0)
        TRACE('Initialized %r.', self)

    def __repr__(self):
        return easy_repr(self, '_uid', '_nid', '_last_resync_ts')

    def _reset_state(self):
        self._nid = 0
        self._first = True
        self._timeline.clear()
        self._ack_pending.clear()
        self._ack_complete.clear()
        self._stickies.clear()

    def last_nid(self):
        assert self._uid is not None, 'last_nid is being called too early'
        return (self._uid, self._nid)

    def _update_resync_ts(self, resync_ts):
        self._last_resync_ts = resync_ts
        self._app.config[self.RESYNC_KEY] = resync_ts

    def _update_nid(self, nid):
        self._nid = nid
        self._popup_nid = nid
        self._db.set_nid(self._uid, nid)

    def get_latest(self, count = TIMELINE_SIZE):
        now = self._app.server_time or time.time()

        def generate():
            for k in reversed(self._timeline):
                notification = self._timeline[k]
                if now - notification.timestamp >= self.CUTOFF and notification.status != UserNotification.STATUS_UNREAD:
                    continue
                if notification.is_visible():
                    yield notification

        with self._lock:
            return list(islice(generate(), count))

    def _get_unread_count(self):
        unread = [ notification for notification in self.get_latest() if notification.status == UserNotification.STATUS_UNREAD and notification.nid not in self._ack_pending and notification.nid not in self._ack_complete ]
        return len(unread)

    def _update_unread(self, should_ping = False):
        unread = self._get_unread_count()
        if self._app.mbox.is_secondary:
            self._app.mbox.notifications_update_unread(should_ping, unread)
        elif self._app.merged_notification_controller:
            self._app.merged_notification_controller._update_unread(should_ping, primary_count=unread)
        else:
            self._app.tray_controller.update_badge(unread, unread and should_ping)

    def has_sticky(self, key):
        return key in self._stickies

    def get_stickies(self, count = 1):
        return self._stickies.values()[:count]

    def add_sticky(self, sticky_notification):
        self._stickies[sticky_notification.key] = sticky_notification
        self._stickies = OrderedDict(sorted(self._stickies.iteritems(), key=lambda tup: tup[1]._priority))

    def remove_sticky(self, key):
        try:
            del self._stickies[key]
        except KeyError:
            raise StickyNotificationKeyError

    def acknowledge(self, notifications):
        with self._lock:
            target = ((notification.nid, None) for notification in notifications if notification.status == UserNotification.STATUS_UNREAD and notification.nid not in self._ack_complete)
            target = list(target)
            self._ack_pending.update(target)
        return self._do_ack()

    @message_sender(UserNotificationThread.call_after, handle_exceptions=True)
    def _do_ack(self):
        with self._lock:
            to_ack = list(islice(self._ack_pending.iterkeys(), self.ACK_LIMIT))
        try:
            if not to_ack:
                TRACE('Nothing to acknowledge!')
                return
            TRACE('Attempting to acknowledge %d notifications.', len(to_ack))
            self._app.conn.ack_user_notifications(to_ack)
            with self._lock:
                self._ack_complete.update(((nid, None) for nid in to_ack))
                for nid in to_ack:
                    try:
                        del self._ack_pending[nid]
                    except KeyError:
                        pass

        except Exception:
            unhandled_exc_handler()
        finally:
            self._unread = None
            self._update_unread()

    def _trigger_resync(self):
        TRACE('!! Resyncing notifications state!')
        self._reset_state()
        self._update_nid(0)
        self.handle_ping(resyncing=True)

    def handle_ping(self, resyncing = False):
        result = self._app.conn.list_user_notifications(start_nid=self._nid + 1 if self._nid else None, limit=self.TIMELINE_CACHE_SIZE)
        self._app.check_for_reboot_and_deletedata_flags(result)
        with self._lock:
            resync_ts = result.get('resync_ts')
            if resync_ts is not None:
                if self._nid == 0:
                    TRACE('Got server request to resync, but had no state.')
                    self._update_resync_ts(resync_ts)
                elif resync_ts != self._last_resync_ts:
                    TRACE('Got server request to resync.')
                    self._update_resync_ts(resync_ts)
                    self._trigger_resync()
                    return
            notifications = result.get('list', ())
            TRACE('Processing %r notifications.', len(notifications))
            self._handle_list(reversed(notifications), bubble=not resyncing)

    def _handle_list(self, notifications, bubble = True):
        self._unread = None
        has_new_unread = False
        changed = False
        current_timestamp = self._app.server_time or time.time()
        highest_nid = self._nid
        for raw_notification in notifications:
            nid = raw_notification['nid']
            if nid > highest_nid:
                highest_nid = nid
            try:
                notification = self._create_notification(raw_notification)
            except (UnsupportedNotificationType, UnsupportedNotificationVersion) as e:
                TRACE('Hit an unsupported notification: %r: %r, %r', nid, e.type_id, e.version)
                self._app.event.report('notification-unsupported', **{'nid': nid,
                 'type_id': e.type_id,
                 'version': e.version})
                continue
            except Exception:
                unhandled_exc_handler()
                continue

            if notification.nid in self._ack_complete and notification.status == UserNotification.STATUS_UNREAD:
                del self._ack_complete[notification.nid]
            if notification.key in self._timeline:
                current_notification = self._timeline[notification.key]
                if notification.timestamp != current_notification.timestamp:
                    if notification.timestamp < current_notification.timestamp:
                        report_bad_assumption('A notification is moving into the past!')
                    del self._timeline[notification.key]
                    self._insert_notification(notification)
                else:
                    self._timeline[notification.key] = notification
            else:
                self._insert_notification(notification)
            changed = True
            if notification.status == UserNotification.STATUS_UNREAD:
                has_new_unread = True
            if bubble:
                self._try_create_popup(notification, current_timestamp)

        self._update_nid(highest_nid)
        try:
            if changed:
                self._app.ui_kit.update_notifications()
        except Exception:
            unhandled_exc_handler()

        self._update_unread(should_ping=has_new_unread)

    def _insert_notification(self, notification):
        if len(self._timeline) >= self.TIMELINE_CACHE_SIZE:
            oldest_notification = self._timeline.itervalues().next()
            if notification.timestamp >= oldest_notification.timestamp:
                self._timeline.popitem(last=False)
            else:
                return
        while self._timeline:
            key, current = self._timeline.popitem()
            self._overflow.append((key, current))
            if notification.timestamp > current.timestamp:
                self._timeline[key] = current
                break

        self._timeline[notification.key] = notification
        for key, value in reversed(self._overflow):
            self._timeline[key] = value

        self._overflow.clear()

    def _create_notification(self, raw_notification):
        try:
            type_id = raw_notification['type_id']
            version = raw_notification['version']
        except Exception:
            raise MalformedRawNotification('Malformed notification: %r' % (raw_notification,))

        type_class = MetaUserNotification._notification_types.get(type_id)
        if type_class is None:
            raise UnsupportedNotificationType('Unsupported type identifier: %r' % (type_id,), type_id=type_id)
        if version < type_class._min_supported_version:
            raise UnsupportedNotificationVersion('Unsupported version: %r(%r)@%r' % (type_id, type_class, version), type_id=type_id, version=version)
        notification = type_class(raw_notification['nid'], raw_notification['target_object_key'], raw_notification['feed_time'], raw_notification['payload'], raw_notification['status'], raw_notification['client_alert_level'])
        return notification

    def _try_create_popup(self, notification, base):
        if notification.nid <= self._popup_nid:
            TRACE('Skipping popup because notification was already displayed: %r.', notification.nid)
            return
        if notification.status in (UserNotification.STATUS_INVISIBLE, UserNotification.STATUS_READ):
            TRACE('Skipping popup because notification is becoming invisible or read: %r.', notification.nid)
            return
        if notification.client_alert_level == UserNotification.CLIENT_ALERT_NO_BUBBLE:
            TRACE('Skipping popup because of notification client_alert_level: %r.', notification.client_alert_level)
            return
        if base - notification.timestamp > self.BUBBLING_PERIOD:
            TRACE('Skipping popup because notification is too old: %r.', notification.nid)
            return
        ret = notification.get_bubble()
        if ret is None:
            TRACE("Skipping popup because notification doesn't produce one: %r.", notification.nid)
            return
        title, message, action = ret
        bubbler = partial(Bubble, BubbleKind.USER_NOTIFICATION_BUBBLE, message, title)

        def bubble_callback():
            self.acknowledge([notification])
            if action is not None:
                notification.perform_action(self._app, action)

        ctx = self._app.bubble_context.make_func_context_ref(bubble_callback)
        bubble = bubbler(self._app.bubble_context, ctx)
        self._app.ui_kit.show_bubble(bubble)
        self._app.event.report('notification-popup', **{'nid': notification.nid,
         'type_id': notification._type_id,
         'target_object_key': notification.target_object_key,
         'status': notification.status})


class MultiaccountNotifications(MergedController):
    TIMELINE_SIZE = 4

    def __init__(self, app):
        super(MultiaccountNotifications, self).__init__(app)
        if not app.notification_controller:
            report_bad_assumption('Multiaccount notifications initialized without primary')
        self.primary = app.notification_controller
        self.secondary = app.mbox.notification_controller

    def get_stickies(self, count = None):
        count = count or 1
        stickies = self.tag_and_merge(primary_method=self.primary.get_stickies, secondary_method=self.secondary.get_stickies, count=count)
        return stickies

    def get_latest(self, count = None):
        if self.show_primary and self.show_secondary:
            count = count or self.TIMELINE_SIZE
        else:
            count = count or self.primary.TIMELINE_SIZE
        notifications = self.tag_and_merge(primary_method=self.primary.get_latest, secondary_method=self.secondary.get_latest, count=count)
        return notifications

    def acknowledge(self, notifications):
        for n in notifications:
            if not hasattr(n, 'primary'):
                report_bad_assumption('multiaccount notification missing primary attr: %s', n)
                n.primary = True

        for is_primary, notifs in group_by(lambda n: n.primary, notifications).iteritems():
            controller = self.primary if is_primary else self.secondary
            controller.acknowledge(notifs)

    def _update_unread(self, should_ping, primary_count = None, secondary_count = None):
        if primary_count is None and self.show_primary:
            primary_count = self.primary._get_unread_count()
        if secondary_count is None and self.show_secondary:
            secondary_count = self.secondary._get_unread_count() if self.show_secondary else 0
        total_unread = sum([primary_count if self.show_primary else 0, secondary_count if self.show_secondary else 0])
        self.app.tray_controller.update_badge(total_unread, total_unread and should_ping)
