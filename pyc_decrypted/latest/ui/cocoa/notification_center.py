#Embedded file name: ui/cocoa/notification_center.py
import os
from AppKit import NSObject, NSUserNotificationCenter, NSUserNotification
from PyObjCTools import AppHelper
from objc import typedSelector
from Queue import Empty, Queue
from dropbox.gui import message_sender, assert_message_queue
from dropbox.mac.version import MAC_VERSION, MAVERICKS
from dropbox.trace import unhandled_exc_handler, TRACE

class NotificationCenterBubbler(NSObject):
    POPUP_DURATION = 5

    @assert_message_queue
    def __new__(cls, app):
        return NotificationCenterBubbler.alloc().initWithApp_(app)

    def initWithApp_(self, app):
        self = super(NotificationCenterBubbler, self).init()
        if self is None:
            return
        self._app = app
        self._current = None
        self._q = Queue()
        NSUserNotificationCenter.defaultUserNotificationCenter().setDelegate_(self)
        return self

    @typedSelector('v@:@@')
    @assert_message_queue
    def userNotificationCenter_didActivateNotification_(self, center, notification):
        self.nextbubble()
        user_info = notification.userInfo() or {}
        if user_info.get('pid') != unicode(os.getpid()):
            TRACE("NCBubbler: pid doesn't match %r vs %r", user_info, os.getpid())
            return
        ctx_ref = user_info.get('ctx_ref')
        if ctx_ref is not None:
            try:
                self._app.bubble_context.thunk_and_expire_context_ref(int(ctx_ref))
            except Exception:
                unhandled_exc_handler()

    @typedSelector('B@:@@')
    @assert_message_queue
    def userNotificationCenter_shouldPresentNotification_(self, center, notification):
        return True

    @typedSelector('v@:@@')
    @assert_message_queue
    def userNotificationCenter_didDeliverNotification_(self, center, notification):
        if MAC_VERSION >= MAVERICKS:
            if notification in center.deliveredNotifications():
                center.removeAllDeliveredNotifications()
        else:
            center.removeDeliveredNotification_(notification)

    def still_running(self):
        return True

    @typedSelector('v@:**@')
    @message_sender(AppHelper.callAfter)
    def do_bubble(self, message, caption, ctx_ref = None):
        TRACE('NotificationCenterController: Bubbling: %s', message)
        if self._current:
            TRACE('Queuing Notification: %s', message)
            self._q.put_nowait((message, caption, ctx_ref))
            return
        user_info = {u'pid': unicode(os.getpid())}
        if ctx_ref is not None:
            user_info[u'ctx_ref'] = unicode(ctx_ref)
        n = NSUserNotification.alloc().init()
        n.setTitle_(caption)
        n.setInformativeText_(message)
        n.setHasActionButton_(False)
        n.setUserInfo_(user_info)
        self._current = n
        NSUserNotificationCenter.defaultUserNotificationCenter().deliverNotification_(n)
        AppHelper.callLater(self.POPUP_DURATION, self.timeout, n)

    @typedSelector('v@:@@')
    @assert_message_queue
    def timeout(self, notification):
        if self._current == notification:
            if MAC_VERSION >= MAVERICKS:
                NSUserNotificationCenter.defaultUserNotificationCenter().removeAllDeliveredNotifications()
            self.nextbubble()

    @typedSelector('v@:@')
    @assert_message_queue
    def nextbubble(self):
        self._current = None
        try:
            message, caption, ctx_ref = self._q.get(False)
            self.do_bubble(message, caption, ctx_ref)
        except Empty:
            pass
