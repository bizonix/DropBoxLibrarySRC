#Embedded file name: ui/cocoa/wizkit_window.py
import objc
import os
from objc import typedSelector
from AppKit import NSAlert, NSAlertAlternateReturn, NSAlertFirstButtonReturn, NSApp, NSBeginAlertSheet, NSClosableWindowMask, NSColor, NSCriticalAlertStyle, NSFloatingWindowLevel, NSLeftMouseDragged, NSLeftMouseUp, NSMakeSize, NSNormalWindowLevel, NSNotificationCenter, NSPoint, NSRunningApplication, NSScreen, NSTitledWindowMask
from Cocoa import NSEvent, NSMouseMoved, NSMakePoint
from Foundation import NSMakeRect
from PyObjCTools import AppHelper
from WebKit import WebViewProgressFinishedNotification
from dropbox.gui import assert_message_queue, event_handler, TRACE, message_sender
from ui.cocoa.util import get_main_screen_rect, get_origin_of_centered_window
from ui.cocoa.xui import WebViewXUIHost
from ui.cocoa.titleless import TitlelessWindow
from dropbox.trace import unhandled_exc_handler
from ui.common.xui.wizkit import WizkitStrings
from .dropbox_controls import DropboxLocationSheetMixin
from .selective_sync import SelectiveSyncSheet

class WizkitView(WebViewXUIHost):
    pass


class WizkitWindow(TitlelessWindow, DropboxLocationSheetMixin):
    SCREEN_PADDING = 8
    BASE_WIDTH = 310
    BASE_HEIGHT = 448
    SCREEN_SIZE = (BASE_WIDTH, BASE_HEIGHT)

    @assert_message_queue
    def init(self, app, controller):
        self._app = app
        self._controller = controller
        self._controller.window = self
        self._when_done = None
        self._dropbox_app = controller.dropbox_app
        self._cancelled = None
        self.screen_frame = get_main_screen_rect()
        center = get_origin_of_centered_window(self.screen_frame, NSMakeSize(self.BASE_WIDTH, self.BASE_HEIGHT))
        rect = NSMakeRect(center.x, center.y, self.BASE_WIDTH, self.BASE_HEIGHT)
        mask = NSClosableWindowMask | NSTitledWindowMask
        self.host = WizkitView.alloc().initWithFrame_controller_(rect, controller)
        self = super(WizkitWindow, self).initWithContentRect_styleMask_view_(rect, mask, self.host)
        self.setHasShadow_(objc.YES)
        self.setDelegate_(self)
        self.setBackgroundColor_(NSColor.clearColor())
        self.setOpaque_(objc.NO)
        self.host.setDrawsBackground_(objc.NO)
        self.setMovableByWindowBackground_(objc.NO)
        self.setMovable_(objc.YES)
        self.window_frame = self.frame()
        self.setAcceptsMouseMovedEvents_(objc.YES)
        self._hasLoaded = False
        self._visible = False
        self._firstDrag = True
        self._firstDragOffset = None
        self._dragOnInputNode = False
        self.setLevel_(NSFloatingWindowLevel)
        NSApp().activateIgnoringOtherApps_(True)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.frameHasLoaded_, WebViewProgressFinishedNotification, self.host)
        return self

    def dealloc(self):
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            unhandled_exc_handler()

        super(WizkitWindow, self).dealloc()

    def frameHasLoaded_(self, event):
        self._hasLoaded = True
        if self._visible:
            self.show_(True)

    def mouseDragged_(self, event):
        pointerLocInWindow = self.mouseLocationOutsideOfEventStream()
        currentDragLocation = self.convertBaseToScreen_(pointerLocInWindow)
        newOrigin = NSMakePoint(currentDragLocation.x - self._firstDragOffset.x, currentDragLocation.y - self._firstDragOffset.y)
        if newOrigin.y + self.window_frame.size.height > self.screen_frame.origin.y + self.screen_frame.size.height:
            newOrigin.y = self.screen_frame.origin.y + (self.screen_frame.size.height - self.window_frame.size.height)
        self.setFrameOrigin_(newOrigin)
        super(WizkitWindow, self).mouseDragged_(event)

    def sendEvent_(self, event):
        if event.type() == NSLeftMouseUp:
            self._firstDrag = True
            self._dragOnInputNode = False
        if event.type() == NSLeftMouseDragged and not self._dragOnInputNode:
            if self._firstDrag:
                self._firstDragOffset = event.locationInWindow()
                self._firstDrag = False
            else:
                self.mouseDragged_(event)
        super(WizkitWindow, self).sendEvent_(event)

    def windowShouldClose_(self, sender):
        if self._controller.done:
            self._controller.do_finish()
        else:
            alert = NSAlert.alloc().init()
            alert.addButtonWithTitle_(WizkitStrings.ok_text)
            alert.addButtonWithTitle_(WizkitStrings.cancel_text)
            alert.setInformativeText_(WizkitStrings.exit_wizard_prompt)
            alert.setMessageText_(WizkitStrings.exit_wizard_caption)
            alert.setAlertStyle_(NSCriticalAlertStyle)
            alert.beginSheetModalForWindow_modalDelegate_didEndSelector_contextInfo_(self, self, self.alertDidEnd_returnCode_contextInfo_.selector, 0)
        return objc.NO

    def alertDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        TRACE(returnCode)
        if returnCode == NSAlertFirstButtonReturn:
            self._controller.exit()

    def canBecomeKeyWindow(self):
        return objc.YES

    def canBecomeMainWindow(self):
        return objc.YES

    @objc.typedSelector('v@:B')
    @assert_message_queue
    def show_(self, show = True):
        assert not self.host.failed, 'Host has failed!'
        self._visible = show
        if not self._hasLoaded:
            return
        if show:
            self.makeKeyAndOrderFront_(None)
        else:
            self.orderOut_(None)

    def linked_successfully(self, when_done = None):
        TRACE('OK, AUTHENTICATE claims we linked!')
        self._when_done = when_done

    def onFinish(self):
        if self._when_done is not None:
            self._when_done(dict(dropbox_path=self._controller.dropbox_path, show_bubbles=True, directory_ignore_set=self._controller.directory_ignore_set, enable_xattrs=True, open_dropbox_folder=True))
            self._when_done = None
        self.close()

    @typedSelector('v@:@@@')
    @message_sender(AppHelper.callAfter)
    def ask_yes_no(self, prompt, yes_button_text, no_button_text, expl_text = None, on_yes = None, on_no = None):
        TRACE("Asking user '%r'" % prompt)
        self._on_yes = on_yes
        self._on_no = on_no
        NSBeginAlertSheet(prompt, yes_button_text, no_button_text, None, self, self, self.askYesNoSheet_returnCode_contextInfo_, None, 0, '%@', expl_text if expl_text else '')

    @typedSelector('v@:@ii')
    def askYesNoSheet_returnCode_contextInfo_(self, sheet, return_code, context_info):
        if return_code == NSAlertAlternateReturn:
            if callable(self._on_no):
                self._on_no()
        elif callable(self._on_yes()):
            self._on_yes()
        del self._on_no
        del self._on_yes

    @typedSelector('v@:@')
    @event_handler
    def changeLocation_(self, sender):
        return self._changeLocation_(sender)

    @typedSelector('v@:@i@')
    @event_handler
    def openPanelDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        return self._openPanelDidEnd_returnCode_contextInfo_(sheet, returnCode, ctx)

    def cancelled(self):
        if self._cancelled is not None:
            self._cancelled()

    @typedSelector('v@:')
    @message_sender(AppHelper.callAfter)
    def choose_dropbox_location(self, on_location = None, on_cancel = None):
        self.initialSelection = os.path.dirname(self._controller.dropbox_path)
        self.syncEngine = None
        self.window = lambda : self
        if callable(on_location):

            def callback(sender):
                on_location(sender.targetPath)

            self._action = callback
        else:
            self._action = None
        if callable(on_cancel):
            self._cancelled = on_cancel
        else:
            self._cancelled = None
        self.changeLocation_(self)

    def disallow_covering(self):
        self.setLevel_(NSFloatingWindowLevel)

    def allow_covering(self):
        self.setLevel_(NSNormalWindowLevel)

    def selective_sync_callback(self, sheet):
        self._controller.directory_ignore_set = set([ unicode(a) for a in sheet.ignoreList() ])
        self.selectiveSyncSheet = None

    def choose_selective_sync_folders(self):
        self.selectiveSyncSheet = SelectiveSyncSheet(self._controller.dropbox_app, initial_ignore_list=self._controller.directory_ignore_set, take_action=False, callback=self.selective_sync_callback)
        self.selectiveSyncSheet.beginSheetForWindow_(self)
