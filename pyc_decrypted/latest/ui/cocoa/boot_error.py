#Embedded file name: ui/cocoa/boot_error.py
from threading import Event
from AppKit import NSAlert, NSApplication, NSCriticalAlertStyle, NSTextField, NSWorkspace
from Foundation import NSObject, NSURL, NSWidth, NSAutoreleasePool
from objc import YES
from PyObjCTools import AppHelper
from dropbox.mac.internal import raise_application
from dropbox.trace import TRACE
from .dropbox_controls import TextFieldWithLink
import time

class BootErrorAlert(object):

    @classmethod
    def runModal(self, title, message, help_link, text = ''):
        pool = NSAutoreleasePool.alloc().init()
        try:
            app = NSApplication.sharedApplication()
            if app.isRunning():
                death_event = Event()
                app_delegate = BootErrorAppDelegate(title, message, help_link, text, death_event)
                AppHelper.callAfter(app_delegate.applicationWillFinishLaunching_, None)
                death_event.wait()
            else:
                AppHelper.installMachInterrupt()
                app_delegate = BootErrorAppDelegate(title, message, help_link, text, None)
                app.setDelegate_(app_delegate)
                AppHelper.runEventLoop()
        finally:
            del pool


class BootErrorAppDelegate(NSObject):

    def __new__(cls, title, message, help_link, text, done_event):
        return BootErrorAppDelegate.alloc().initWithTitle_message_helpLink_tracebackText_doneEvent_(title, message, help_link, text, done_event)

    def initWithTitle_message_helpLink_tracebackText_doneEvent_(self, title, message, help_link, text, done_event):
        self = super(BootErrorAppDelegate, self).init()
        if self is not None:
            self._title = title
            self._message = message
            self._help_link = help_link
            self._text = text
            self._done_event = done_event
        return self

    def applicationWillFinishLaunching_(self, notification):
        AppHelper.callAfter(self.alertLoop)

    def alertLoop(self):
        raise_application()
        alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(self._title, None, None, None, self._message)
        alert.setAlertStyle_(NSCriticalAlertStyle)
        if self._help_link:
            alert.setShowsHelp_(YES)
            alert.setHelpAnchor_(self._help_link)
            alert.setDelegate_(self)
        if hasattr(alert, 'setAccessoryView_') and self._text:
            alert.setAccessoryView_(self.createAccessoryView(alert))
        alert.runModal()
        AppHelper.stopEventLoop()
        if self._done_event:
            self._done_event.set()

    def createAccessoryView(self, alert):
        text_width = 0
        font = None
        for subview in alert.window().contentView().subviews():
            if isinstance(subview, NSTextField):
                text_width = max(NSWidth(subview.frame()), text_width)
                font = subview.font()

        if text_width == 0 or font is None:
            TRACE('!! Unknown NSAlert implementation')
            return
        acc_view = TextFieldWithLink(self._text, text_width, font)
        return acc_view

    def alertShowHelp_(self, alert):
        TRACE('Help button clicked on boot error dialog')
        help_link = alert.helpAnchor()
        if help_link is not None:
            url = NSURL.alloc().initWithString_(help_link)
            NSWorkspace.sharedWorkspace().openURL_(url)
        return YES
