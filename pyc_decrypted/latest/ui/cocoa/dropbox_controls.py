#Embedded file name: ui/cocoa/dropbox_controls.py
from __future__ import absolute_import
import functools
import threading
import time
import os
from PyObjCTools import AppHelper
import objc
from objc import YES, NO, typedSelector, ivar
from AppKit import NSAlert, NSAlertFirstButtonReturn, NSAlertSecondButtonReturn, NSApp, NSApplication, NSAttributedString, NSBackingStoreBuffered, NSBeginAlertSheet, NSBezierPath, NSBox, NSButton, NSCancelButton, NSCenterTextAlignment, NSClosableWindowMask, NSColor, NSCommandKeyMask, NSCompositeCopy, NSCompositeSourceOver, NSCursor, NSFont, NSHelpButtonBezelStyle, NSImage, NSImageAlignRight, NSImageInterpolationNone, NSImageView, NSLeftMouseDragged, NSLeftMouseDraggedMask, NSLeftMouseUp, NSLeftMouseUpMask, NSLineBreakByTruncatingMiddle, NSLinkAttributeName, NSLayoutManager, NSMenuItem, NSMutableAttributedString, NSMutableParagraphStyle, NSNumber, NSNumberFormatter, NSOffState, NSOKButton, NSOnState, NSOpenPanel, NSParagraphStyleAttributeName, NSPopUpButton, NSProgressIndicator, NSProgressIndicatorBarStyle, NSRegularControlSize, NSScaleNone, NSSingleUnderlineStyle, NSStepper, NSStringDrawingUsesLineFragmentOrigin, NSSwitchButton, NSTextContainer, NSTextField, NSTextStorage, NSTextView, NSTitledWindowMask, NSUnderlineStyleAttributeName, NSView, NSWindow, NSWorkspace
from Foundation import NSHeight, NSHomeDirectory, NSMakeRange, NSMakeRect, NSMaxX, NSMaxY, NSMinX, NSMinY, NSObject, NSPoint, NSPointInRect, NSSize, NSRect, NSURL, NSWidth, NSZeroRect
from dropbox.gui import message_sender, spawn_thread_with_name, assert_message_queue, event_handler
from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
from dropbox.preferences import OPT_PHOTO_PRIMARY
from dropbox.trace import TRACE, unhandled_exc_handler
import arch
from dropbox.sync_engine.move_dropbox import path_makes_invalid_dropbox_parent, path_endswith_dropbox
from ..common.constants import ResizeMethod
from ..common.misc import MiscStrings
from ..common.preferences import pref_strings
from ..common.setupwizard import SetupWizardStrings
from .constants import Colors, Images
from .dynamic_layouts import help_button, ManagedRadioButton, CONTENT_BORDER, NEARBY_CONTROL_BORDER
from .util import edit_attributed_string, guarded, protected_action_method, resize_image, save_graphics_state

class FlippedView(NSView):

    def __new__(cls, frame):
        return FlippedView.alloc().initWithFrame_(frame)

    def initWithFrame_(self, frame):
        self = super(FlippedView, self).initWithFrame_(frame)
        return self

    def isFlipped(self):
        return YES


class FlippedTextView(NSTextView):

    def __new__(cls, frame):
        return FlippedTextView.alloc().initWithFrame_(frame)

    def initWithFrame_(self, frame):
        self = super(FlippedTextView, self).initWithFrame_(frame)
        return self

    def isFlipped(self):
        return YES


class FlippedButton(NSButton):

    def isFlipped(self):
        return YES


class PrefView(NSView):

    @objc.typedSelector('@@:@i')
    @event_handler
    def initWithDropboxApp_width_(self, dropbox_app, width):
        self = super(PrefView, self).initWithFrame_(NSZeroRect)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        self._width = width
        self.helpButton = help_button(0, 0)
        self.helpButton.setTarget_(self)
        self.helpButton.setAction_(self.userNeedsHelp_)
        self.addSubview_(self.helpButton)
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def userNeedsHelp_(self, sender):
        self.window().userNeedsHelp_(sender)

    @objc.typedSelector('v@:')
    @event_handler
    def settingsChanged(self):
        pass

    @objc.typedSelector('i@:')
    @event_handler
    def initialHeightNeeded_(self):
        height_needed = CONTENT_BORDER
        self.helpButton.setFrameOrigin_(NSPoint(0, height_needed))
        self.helpButton.alignRightToOffset_(self._width - CONTENT_BORDER)
        item_height = self.helpButton.frame().size.height
        height_needed += item_height - NEARBY_CONTROL_BORDER
        return height_needed


class DropboxDefaultMenuDelegate(NSObject):
    first_responder_map = {'x': 'cut:',
     'c': 'copy:',
     'v': 'paste:',
     'a': 'selectAll:'}
    window_map = {'w': 'performClose:'}

    @objc.typedSelector('B@:@@o^@o^:')
    @event_handler
    def menuHasKeyEquivalent_forEvent_target_action_(self, menu, event):
        to_ret = (NO, None, None)
        try:
            chars = event.characters()
            if chars in self.first_responder_map or chars in self.window_map and event.modifierFlags() & NSCommandKeyMask:
                TRACE('got interesting menu event: %r', event)
                window = NSApplication.sharedApplication().keyWindow()
                if window:
                    if event.characters() in self.window_map:
                        if window.respondsToSelector_('wantsDropboxWindowMenuEvents') and window.wantsDropboxWindowMenuEvents():
                            to_ret = (YES, window, self.window_map[event.characters()])
                    else:
                        firstResponder = window.firstResponder()
                        theSelector = self.first_responder_map[event.characters()]
                        if firstResponder and firstResponder.respondsToSelector_(theSelector):
                            to_ret = (YES, firstResponder, theSelector)
            if to_ret != (NO, None, None):
                TRACE('responding with %r %r %r', *to_ret)
        except Exception:
            unhandled_exc_handler()
        finally:
            return to_ret


class ProgressSheet(NSWindow):
    messageToDisplay = ivar('messageToDisplay')
    progressMessage = ivar('progressMessage')
    progressBar = ivar('progressBar')
    button = ivar('button')

    def __new__(cls, width):
        return ProgressSheet.alloc().initWithWidth_(width)

    @objc.typedSelector('@@:d')
    @event_handler
    def initWithWidth_(self, width):
        self = super(ProgressSheet, self).initWithContentRect_styleMask_backing_defer_(NSZeroRect, NSTitledWindowMask | NSClosableWindowMask, NSBackingStoreBuffered, YES)
        if self is None:
            return
        self.progressMessage = NSTextField.createLabelWithText_font_('', NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize)))
        self.contentView().addSubview_(self.progressMessage)
        self.progressBar = NSProgressIndicator.alloc().initWithFrame_(NSZeroRect)
        self.progressBar.setStyle_(NSProgressIndicatorBarStyle)
        self.progressBar.setIndeterminate_(YES)
        self.contentView().addSubview_(self.progressBar)
        self.setReleasedWhenClosed_(NO)
        self.button = None
        self.layoutForWidth_(width)
        return self

    @objc.typedSelector('v@:f')
    @event_handler
    def layoutForWidth_(self, width):
        current_frame = self.frame()
        current_frame.size.width = width
        self.setFrame_display_animate_(current_frame, NO, NO)
        height_needed = CONTENT_BORDER
        if self.button is not None:
            self.button.setFrameOrigin_(NSPoint(0, height_needed))
            self.button.sizeToFitWithPadding()
            self.button.centerHorizontallyInSuperview()
            height_needed += self.button.frame().size.height
            height_needed += NEARBY_CONTROL_BORDER
        self.progressMessage.setFrameOrigin_(NSPoint(CONTENT_BORDER, height_needed))
        height_needed += self.progressMessage.wrapToWidth_(width - CONTENT_BORDER * 2).height
        self.progressMessage.centerHorizontallyInSuperview()
        height_needed += NEARBY_CONTROL_BORDER
        self.progressBar.setFrame_(NSRect((CONTENT_BORDER, height_needed), (width - CONTENT_BORDER * 2, 20)))
        height_needed += self.progressBar.frame().size.height
        height_needed += CONTENT_BORDER
        current_frame = self.frame()
        dw = width - self.contentView().frame().size.width
        dh = height_needed - self.contentView().frame().size.height
        current_frame.origin.x -= dw / 2
        current_frame.size.width += dw
        current_frame.origin.y -= dh / 2
        current_frame.size.height += dh
        self.setFrame_display_animate_(current_frame, YES, YES)

    @objc.typedSelector('v@:@@:')
    @event_handler
    def setButtonTitle_target_action_(self, title, theTarget, theAction):
        if self.button is None:
            self.button = NSButton.createNormalRoundButtonWithTitle_(title)
            self.contentView().addSubview_(self.button)
        self.button.setTitle_(title)
        self.button.setTarget_(theTarget)
        self.button.setAction_(theAction)
        self.layoutForWidth_(self.contentView().frame().size.width)

    @objc.typedSelector('v@:')
    @event_handler
    def removeButton(self):
        if self.button is not None:
            self.button.removeFromSuperview()
            self.button = None
            self.layoutForWidth_(self.contentView().frame().size.width)

    @objc.typedSelector('v@:@')
    @event_handler
    def setDisplayedMessage_(self, message):
        self.progressMessage.setStringValue_(message)
        self.layoutForWidth_(self.contentView().frame().size.width)

    @objc.typedSelector('v@:@@')
    @event_handler
    def beginModalForWindow_(self, window):
        self.progressBar.startAnimation_(self)
        NSApp().beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(self, window, self, self.progressDidEnd_returnCode_contextInfo_.selector, 0)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def progressDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        self.progressBar.stopAnimation_(self)
        self.orderOut_(self)


class MoveProgressSheet(ProgressSheet):
    lastUserUpdate = ivar('lastUserUpdate')
    filesMoved = ivar('filesMoved')
    approxFileCount = ivar('approxFileCount')

    @objc.typedSelector('@@:d')
    @event_handler
    def initWithWidth_(self, width):
        self = super(MoveProgressSheet, self).initWithWidth_(width)
        self.setDisplayedMessage_(pref_strings.loc_changer_move_progress_indeterminate)
        if self is None:
            return
        self.lastUserUpdate = time.time()
        self.filesMoved = 0
        self.oneFileExternal = message_sender(AppHelper.callAfter)(self.innerOneFile)
        return self

    @objc.typedSelector('v@:i')
    @event_handler
    def setApproxTotalFileCount_(self, approxFileCount):
        self.approxFileCount = approxFileCount

    @objc.typedSelector('v@:')
    @event_handler
    def innerOneFile(self):
        assert_message_queue()()
        self.filesMoved += 1
        t = time.time()
        if t - self.lastUserUpdate > 0.1:
            self.lastUserUpdate = t
            self.setDisplayedMessage_(pref_strings.loc_changer_move_progress_determinate_t % dict(completed=self.filesMoved, total=self.approxFileCount))
            if self.progressBar.isIndeterminate():
                self.progressBar.setIndeterminate_(NO)
                self.progressBar.setMinValue_(0.0)
                self.progressBar.setMaxValue_(self.approxFileCount)
            self.progressBar.setDoubleValue_(float(self.filesMoved))


class DBSingletonObject(NSObject):
    __the_instance = None

    @classmethod
    def sharedInstance(klass):
        if klass.__the_instance is None:
            klass.__the_instance = klass.alloc().init()
        return klass.__the_instance


class DropboxSheetErrorFactory(DBSingletonObject):
    ctxMap = ivar('ctxMap')
    index = ivar('index')

    @objc.typedSelector('@@:')
    @event_handler
    def init(self):
        self = super(DropboxSheetErrorFactory, self).init()
        if self is None:
            return
        self.ctxMap = {}
        self.index = 0
        return self

    @objc.typedSelector('i@:')
    @event_handler
    def nextIndex(self):
        this_index = self.index
        self.index = (self.index + 1) % 65536
        return this_index

    def alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self, window, caption, message, on_success, on_cancel, success_label, cancel_label):
        context = {}
        alert = NSAlert.alloc().init()
        ret_map = [NSAlertFirstButtonReturn, NSAlertSecondButtonReturn]
        n = 0
        for btn_label, btn_action in ((success_label, on_success), (cancel_label, on_cancel)):
            if btn_action:
                context[ret_map[n]] = btn_action
                alert.addButtonWithTitle_(btn_label)
                n += 1

        alert.setMessageText_(caption)
        if message:
            alert.setInformativeText_(message)
        self.ctxMap[alert] = context
        alert.beginSheetModalForWindow_modalDelegate_didEndSelector_contextInfo_(window, self, 'alertDidEnd:returnCode:contextInfo:', 0)

    def alertForWindow_withCaption_message_onSuccess_onCancel_(self, window, caption, message, on_success, on_cancel):
        self.alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(window, caption, message, on_success, on_cancel, MiscStrings.ok_button, MiscStrings.cancel_button)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def alertDidEnd_returnCode_contextInfo_(self, alert, returnCode, ctx):
        alert.window().orderOut_(alert.window())
        try:
            context = self.ctxMap.pop(alert)
            context[returnCode]()
        except Exception:
            unhandled_exc_handler()


class BaseDropboxLocationSheetMixin(object):

    def cancelled(self):
        pass

    @objc.typedSelector('v@:@')
    @event_handler
    def _changeLocation_(self, sender):
        self.open_panel = open_panel = NSOpenPanel.openPanel()
        open_panel.setCanChooseDirectories_(YES)
        open_panel.setCanCreateDirectories_(YES)
        open_panel.setCanChooseFiles_(NO)
        open_panel.setResolvesAliases_(YES)
        open_panel.setAllowsMultipleSelection_(NO)
        open_panel.setTitle_(pref_strings.loc_changer_select_title)
        open_panel.setPrompt_(pref_strings.loc_changer_select_button)
        text = pref_strings.loc_changer_select_message1 + u'\n' + pref_strings.loc_changer_select_message2 % {'folder_name': self.getFolderName()}
        open_panel.setMessage_(text)
        open_panel.beginSheetForDirectory_file_types_modalForWindow_modalDelegate_didEndSelector_contextInfo_(self.initialSelection, None, None, self.window(), self, self.openPanelDidEnd_returnCode_contextInfo_, 0)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def _openPanelDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        try:
            sheet.orderOut_(self)
            if returnCode == NSOKButton:
                sarch = self._dropbox_app.sync_engine.arch
                self.initialSelection = sheet.URLs()[0].path()
                lpath = os.path.abspath(os.path.normpath(unicode(self.initialSelection)))
                TRACE('Checking if requested parent path is invalid')
                care_about_existing_dropbox = self.syncEngine is not None
                invalid = path_makes_invalid_dropbox_parent(lpath, sync_engine=self.syncEngine, care_about_existing_dropbox=care_about_existing_dropbox, arch=sarch)
                if invalid:
                    TRACE("It's invalid thanks to: %s, notifying user and relooping" % (invalid,))
                    DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(self.window(), pref_strings.loc_changer_sel_folder_error, unicode(invalid), functools.partial(self.changeLocation_, self), None)
                else:
                    path = self.targetPath = os.path.join(self.initialSelection, self.getFolderName())
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), SetupWizardStrings.merge_title, SetupWizardStrings.merge_explanation % dict(folder_name=self.getFolderName(), folder_path=os.path.dirname(path)), functools.partial(self._action, self), functools.partial(self.changeLocation_, self), SetupWizardStrings.merge_button_ok, SetupWizardStrings.merge_button_cancel)
                        else:
                            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(self.window(), pref_strings.loc_changer_sel_folder_error, pref_strings.loc_changer_dialog_merge_is_file % path, functools.partial(self.changeLocation_, self), None)
                        return
                    contains_dropbox = path_endswith_dropbox(lpath, care_about_existing_dropbox=care_about_existing_dropbox, arch=sarch)
                    if contains_dropbox:
                        TRACE('Path ends in a folder named Dropbox: %r, prompting user', contains_dropbox)
                        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), pref_strings.loc_changer_move_confirm_caption, contains_dropbox, functools.partial(self._action, self), functools.partial(self.changeLocation_, self), pref_strings.loc_changer_move_confirm_button, pref_strings.cancel_button)
                        return
                    TRACE('OK, WANTS TO MOVE TO: %r', self.targetPath)
                    self._action(self)
            elif returnCode == NSCancelButton:
                self.cancelled()
        except Exception:
            unhandled_exc_handler()


class RemoteDropboxLocationSheetMixin(BaseDropboxLocationSheetMixin):

    def getFolderName(self):
        return self._dropbox_app.mbox.get_dropbox_folder_name()

    def is_invalid_dropbox_location(self, path):
        return self._dropbox_app.mbox.is_invalid_dropbox_location(self.initialSelection)

    def path_endswith_dropbox(self, path):
        return False


class DropboxLocationSheetMixin(BaseDropboxLocationSheetMixin):

    def getFolderName(self):
        return self._dropbox_app.default_dropbox_folder_name

    def is_invalid_dropbox_location(self, path):
        return path_makes_invalid_dropbox_parent(self.initialSelection, sync_engine=self.syncEngine, care_about_existing_dropbox=self.syncEngine is not None)

    def path_endswith_dropbox(self, path):
        return path_endswith_dropbox(self.initialSelection, care_about_existing_dropbox=self.syncEngine is not None)


class BaseLocationChangeHandler(object):

    @objc.typedSelector('v@:@')
    @event_handler
    def confirmMoveDropbox_(self, sender):
        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.window(), pref_strings.loc_changer_move_confirm_caption, pref_strings.loc_changer_move_confirm_message % {'folder_name': self.targetPath}, self.startMoveProgress_, lambda : None, pref_strings.loc_changer_move_confirm_button, MiscStrings.cancel_button)

    def stopMoveProgressSuccess_(self, value):
        AppHelper.callAfter(self.innerStopMoveProgressSuccess_, value)

    @objc.typedSelector('v@:@')
    @event_handler
    def innerStopMoveProgressSuccess_(self, value):
        NSApp().endSheet_(self.moveProgressSheet)
        self.moveProgressSheet = None
        if value:
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(self.window(), pref_strings.loc_changer_error_moving, unicode(value), self.reloadChoices, None)
        else:
            self.reloadChoices()

    def stopMoveProgressError_withExcInfo_(self, exc, exc_info):
        AppHelper.callAfter(self.innerStopMoveProgressError_withExcInfo_, exc, exc_info)

    @objc.typedSelector('v@:@@')
    @event_handler
    def innerStopMoveProgressError_withExcInfo_(self, exc, exc_info):
        NSApp().endSheet_(self.moveProgressSheet)
        self.moveProgressSheet = None
        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(self.window(), pref_strings.loc_changer_error_moving, pref_strings.loc_changer_error_unexpected_error, self.reloadChoices, None)

    @objc.typedSelector('v@:@B')
    @event_handler
    def innerSwapInWarnSheet_hasCancel_(self, message, has_cancel):
        try:
            self.moveWarningEvent.clear()
            NSApp().endSheet_(self.moveProgressSheet)
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(self.window(), pref_strings.loc_changer_moving_warning, message, self.innerSwapOutWarnSheet(), None)
        except Exception:
            unhandled_exc_handler()

    @objc.typedSelector('v@:')
    @event_handler
    def innerSwapOutWarnSheet(self):
        self.moveProgressSheet.progressBar.startAnimation_(self)
        NSApp().beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(self.moveProgressSheet, self.window(), self, self.moveProgressDidEnd_returnCode_contextInfo_, 0)
        self.moveWarningEvent.set()

    def warnExternal_(self, message, has_cancel):
        AppHelper.callAfter(self.innerSwapInWarnSheet_hasCancel_, message, has_cancel)
        self.moveWarningEvent.wait()

    @objc.typedSelector('v@:')
    @event_handler
    def startMoveProgress_(self):
        self.moveProgressSheet = MoveProgressSheet.alloc().initWithWidth_(350)
        try:
            file_count = self.syncEngine.get_dropbox_file_count()
        except Exception:
            file_count = 0

        self.moveProgressSheet.setApproxTotalFileCount_(file_count)
        self.moveProgressSheet.progressBar.startAnimation_(self)
        NSApp().beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(self.moveProgressSheet, self.window(), self, self.moveProgressDidEnd_returnCode_contextInfo_, 0)
        self.do_move()

    @objc.typedSelector('v@:@i@')
    @event_handler
    def _moveProgressDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        self.moveProgressSheet.progressBar.stopAnimation_(self)
        sheet.orderOut_(self)


class RemoteLocationChangeHandler(RemoteDropboxLocationSheetMixin, BaseLocationChangeHandler):

    def do_move(self):
        self._dropbox_app.mbox.sync_engine.move_dropbox(path=self.targetPath, progress_callback=self.moveProgressSheet.oneFileExternal, exception_callback=self.stopMoveProgressError_withExcInfo_, success_callback=self.stopMoveProgressSuccess_, warn_external_callback=self.warnExternal_)


class LocationChangeHandler(DropboxLocationSheetMixin, BaseLocationChangeHandler):

    def do_move(self):
        new_path = os.path.abspath(os.path.normpath(self.targetPath))
        message_sender(spawn_thread_with_name('MOVE'), on_success=self.stopMoveProgressSuccess_, on_exception=self.stopMoveProgressError_withExcInfo_, block=False, handle_exceptions=True, dont_post=lambda : False)(self.syncEngine.move, new_path, self.warnExternal_, progress_callback=self.moveProgressSheet.oneFileExternal, error_callback=self._dropbox_app.restart_and_unlink)()


class ProgressWindow(object):

    @event_handler
    def __init__(self, msg, max_value):
        self.prog = ProgressSheet(350)
        self.prog.setDisplayedMessage_(msg)
        self.prog.setReleasedWhenClosed_(NO)
        if self.prog.progressBar.isIndeterminate():
            self.prog.progressBar.setIndeterminate_(NO)
            self.prog.progressBar.setMinValue_(0.0)
            self.prog.progressBar.setMaxValue_(max_value)
            self.prog.progressBar.setDoubleValue_(0.0)
        self.prog.center()
        self.prog.progressBar.startAnimation_(self)
        self.prog.makeKeyAndOrderFront_(None)
        NSApp().activateIgnoringOtherApps_(True)

    @message_sender(AppHelper.callAfter, block=True)
    def set_max_value(self, max_value):
        self.prog.progressBar.setMaxValue_(max_value)

    @message_sender(AppHelper.callAfter)
    def set_progress(self, n):
        self.prog.progressBar.setDoubleValue_(n)

    @message_sender(AppHelper.callAfter, block=True)
    def set_message(self, msg):
        self.prog.setDisplayedMessage_(msg)

    @message_sender(AppHelper.callAfter, block=True)
    def close(self):
        self.prog.close()


class CocoaDropboxLocationChanger(NSView, LocationChangeHandler):
    moveProgressSheet = ivar('moveProgressSheet')
    moveWarningEvent = ivar('moveWarningEvent')
    targetPath = ivar('targetPath')
    initialSelection = ivar('initialSelection')
    syncEngine = ivar('syncEngine')

    def __new__(cls, dropbox_app, use_box = False):
        return cls.alloc().initWithFrame_dropboxApp_useBox_(NSZeroRect, dropbox_app, use_box)

    def initWithFrame_dropboxApp_useBox_(self, frame, dropbox_app, use_box):
        self = super(CocoaDropboxLocationChanger, self).initWithFrame_(frame)
        if self is not None:
            self._use_box = use_box
            self._enabled = True
            self._dropbox_app = dropbox_app
            self.box = None
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def changeLocation_(self, sender):
        return self._changeLocation_(sender)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def openPanelDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        return self._openPanelDidEnd_returnCode_contextInfo_(sheet, returnCode, ctx)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def moveProgressDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        return self._moveProgressDidEnd_returnCode_contextInfo_(sheet, returnCode, ctx)

    @objc.typedSelector('v@:c')
    @assert_message_queue
    def setEnabled_(self, enabled):
        if self._enabled == enabled:
            return
        subviews = self.subviews() if not self._use_box else self.inner_view.subviews()
        for subview in subviews:
            if subview.respondsToSelector_('setEnabled:'):
                subview.setEnabled_(enabled)
            if subview.respondsToSelector_('setTextColor:'):
                subview.setTextColor_(Colors.black if enabled else NSColor.disabledControlTextColor())

        self._enabled = enabled

    def readOnOpen_withUrlInfo_andWidth_andSyncEngine_andAction_(self, state, url_info, width, sync_engine, action):
        self.moveWarningEvent = threading.Event()
        self.syncEngine = sync_engine
        if action is not None:
            enabled = True
            self._action = action
        else:
            enabled = self.syncEngine is not None
            self._action = self.confirmMoveDropbox_
        if self._use_box:
            width -= 32
        else:
            subviews = list(self.subviews())
            for view in subviews:
                view.removeFromSuperview()

        height_needed = 5
        change_button = NSButton.createNormalRoundButtonWithTitle_default_origin_(pref_strings.loc_changer_change_dotdotdot, False, (0, height_needed))
        change_button.setTarget_(self)
        change_button.setEnabled_(enabled)
        change_button.setAction_(self.changeLocation_)
        location_wrap_width = width - change_button.frame().size.width - CONTENT_BORDER * 2
        dropbox_location = NSTextField.createLabelWithText_maxWidth_(state['dropbox_path'], location_wrap_width)
        dropbox_location.setFrameOrigin_((CONTENT_BORDER, height_needed))
        dropbox_location.setSelectable_(YES)
        self.initialSelection = os.path.dirname(state['dropbox_path'])
        height_needed += NSHeight(dropbox_location.frame())
        change_button.setFrameOrigin_(NSPoint(0, height_needed))
        change_button_height = change_button.frame().size.height
        change_button.alignRightToOffset_(width - 2)
        dropbox_location_label = NSTextField.createLabelWithText_maxWidth_(pref_strings.loc_changer_label_colon, width)
        dropbox_location_label.setFrameOrigin_((0, height_needed + 10))
        height_needed += max(NSHeight(dropbox_location_label.frame()) + 10, change_button_height)
        if self._use_box:
            old_frame = self.frame()
            old_frame.size.width = width
            old_frame.size.height = height_needed + 10
            if not self.box:
                self.box = NSBox.alloc().initWithFrame_(NSZeroRect)
                self.box.setContentViewMargins_(NSSize(16, 16))
                self.box.setTitle_('')
                self.inner_view = self.box.contentView()
                self.addSubview_(self.box)
            inner_subviews = list(self.inner_view.subviews())
            for view in inner_subviews:
                view.removeFromSuperview()

            self.inner_view.addSubview_(dropbox_location_label)
            self.inner_view.addSubview_(change_button)
            self.inner_view.addSubview_(dropbox_location)
            old_frame.size.width += 32
            old_frame.size.height += 32
            if self.box.frame().size != old_frame.size:
                self.box.setFrameSize_(old_frame.size)
                self.setFrameSize_(self.box.frame().size)
        else:
            old_frame = self.frame()
            old_frame.size.width = width
            old_frame.size.height = height_needed
            self.setFrame_(old_frame)
            self.addSubview_(dropbox_location_label)
            self.addSubview_(change_button)
            self.addSubview_(dropbox_location)


class ChoiceButton(NSPopUpButton):

    def __new__(cls, dropbox_app):
        return cls.alloc().initWithDropboxApp_(dropbox_app)

    @objc.typedSelector('v@:@')
    @event_handler
    def initWithDropboxApp_(self, dropbox_app):
        self = super(ChoiceButton, self).initWithFrame_(NSZeroRect)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        self.reloadChoices()
        self.setAutoenablesItems_(NO)
        self.sizeToFit()
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def changeLocation_(self, sender):
        return self._changeLocation_(sender)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def openPanelDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        return self._openPanelDidEnd_returnCode_contextInfo_(sheet, returnCode, ctx)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def moveProgressDidEnd_returnCode_contextInfo_(self, sheet, returnCode, ctx):
        return self._moveProgressDidEnd_returnCode_contextInfo_(sheet, returnCode, ctx)

    @event_handler
    def drawRect_(self, rect):
        with save_graphics_state() as graphics_context:
            graphics_context.setImageInterpolation_(NSImageInterpolationNone)
            super(ChoiceButton, self).drawRect_(rect)

    def reloadChoices(self):
        choices = self.get_choices()
        self.removeAllItems()
        menu = self.menu()
        for image, action, title in choices:
            if title is None:
                menuitem = NSMenuItem.separatorItem()
            else:
                menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, '')
            if action:
                menuitem.setTarget_(self)
                menuitem.setAction_(action)
            if image:
                image.setSize_((16, 16))
                menuitem.setImage_(image)
            menu.addItem_(menuitem)

        self.selectItemAtIndex_(self.get_index())
        self.setEnabled_(self.get_enabled())

    def get_choices(self):
        return []

    def get_enabled(self):
        return True

    def get_index(self):
        return 0


class BaseLocationButton(ChoiceButton):

    def get_choices(self):
        if self._dropbox_app.sync_engine:
            curr = os.path.dirname(self.get_dropbox_path())
        else:
            curr = NSHomeDirectory()
        return [(NSWorkspace.sharedWorkspace().iconForFile_(curr), None, os.path.basename(curr)), (None, None, None), (None, self.locationChange_, pref_strings.other_dotdotdot)]

    def locationChange_(self, sender):
        if self.indexOfSelectedItem() == 0:
            return
        self.initialSelection = os.path.dirname(self.get_dropbox_path())
        self.syncEngine = self._dropbox_app.sync_engine
        self._action = self.confirmMoveDropbox_
        self.changeLocation_(sender)
        self.selectItemAtIndex_(0)


class LocationButton(BaseLocationButton, LocationChangeHandler):

    def get_dropbox_path(self):
        return self._dropbox_app.pref_controller['dropbox_path']

    def get_enabled(self):
        if self._dropbox_app.ui_kit.post_link:
            return YES
        return NO


class RemoteLocationButton(BaseLocationButton, RemoteLocationChangeHandler):

    def get_dropbox_path(self):
        return self._dropbox_app.mbox.get_dropbox_location()

    def get_enabled(self):
        return YES


class CameraButton(ChoiceButton):

    def get_choices(self):
        self._actions, self._index = self._dropbox_app.camera_controller.get_actions()
        ws = NSWorkspace.sharedWorkspace()
        ret = [ (ws.iconForFile_(curr), self.select_, os.path.splitext(os.path.basename(curr))[0]) for curr in self._actions ]
        if self._index == -1:
            self._index = len(self._actions)
        self._actions.append('')
        ret.append((None, self.select_, pref_strings.no_application))
        return ret

    def get_index(self):
        return self._index

    def select_(self, sender):
        index = self.indexOfSelectedItem()
        if index == self._index:
            return
        action = self._actions[index]
        self._dropbox_app.camera_controller.set_action(action)
        self._index = self.indexOfSelectedItem()


class BackgroundImageView(NSView):

    def __new__(cls, frame, image, bottom_align = False):
        return BackgroundImageView.alloc().initWithFrame_image_bottomAlign_(frame, image, bottom_align)

    def initWithFrame_image_bottomAlign_(self, frame, image, bottom_align):
        self = super(BackgroundImageView, self).initWithFrame_(frame)
        if self:
            self._image = image
            self._bottom_align = bottom_align
            self.set_defaults()
        return self

    def set_defaults(self):
        self._alpha = 1.0

    def setImage_(self, image):
        self._image = image
        self.setNeedsDisplay_(YES)

    def setImageSize_(self, size):
        if self._image.size() != size:
            self._image = resize_image(self._image, (size.width, size.height), method=ResizeMethod.CROP)

    def image(self):
        return self._image

    def setAlpha_(self, alpha):
        self._alpha = alpha
        self.setNeedsDisplay_(YES)

    def alpha(self):
        return self._alpha

    def setBottomAlign_(self, value):
        self._bottom_align = value
        self.setNeedsDisplay_(YES)

    def bottomAlign(self):
        return self._bottom_align

    def drawRect_(self, rect):
        super(BackgroundImageView, self).drawRect_(rect)
        if self._bottom_align:
            image_origin = NSPoint(0, 0)
        else:
            image_origin = NSPoint(0, self.bounds().size.height / 2.0 - self._image.size().height / 2.0)
        self._image.drawAtPoint_fromRect_operation_fraction_(image_origin, NSZeroRect, NSCompositeSourceOver, self._alpha)


class FancyRadioGroup(NSView):
    DEFAULT_INNER_PADDING = 20

    def __new__(cls, frame):
        return FancyRadioGroup.alloc().initWithFrame_(frame)

    def initWithFrame_(self, frame):
        self = super(FancyRadioGroup, self).initWithFrame_(frame)
        if self is not None:
            self._padding = FancyRadioGroup.DEFAULT_INNER_PADDING
            self._current_y = 0
            self._choices = []
            self._selected = None
            self._action = None
        return self

    def isFlipped(self):
        return YES

    def sizeToFit(self):
        frame = self.frame()
        delta = frame.size.height - self._current_y
        frame.size.height -= delta
        self.setFrame_(frame)

    def setAction_(self, sel):
        self._action = sel

    def setSelected_(self, selected):
        for item in self._choices:
            if item.data == selected:
                item.select()
                self.selectionChanged_(item)
                return

    def setSelectedIndex_(self, selected_index):
        item = self._choices[selected_index]
        item.select()
        self.selectionChanged_(item)

    def selected(self):
        return self._selected

    def selectionChanged_(self, selected):
        self._selected = selected
        for choice in self._choices:
            if choice is not selected:
                choice.unselect()

        if self._action is not None:
            self._action(self)

    def addChoiceView_(self, choice_view):
        if len(self._choices) > 0:
            last_y = NSMaxY(self._choices[-1].frame())
            choice_view.setFrameOrigin_((0, last_y + self._padding))
        self._current_y += choice_view.bounds().size.height + self._padding
        self._choices.append(choice_view)
        if self._selected is None:
            choice_view.select()
            self._selected = choice_view
        self.addSubview_(choice_view)


class FancyRadioView(NSView):

    def __new__(cls, data, parent, image, label, sublabel, description, extra):
        return FancyRadioView.alloc().initWithPlanData_parent_image_label_subLabel_description_extra_(data, parent, image, label, sublabel, description, extra)

    def initWithPlanData_parent_image_label_subLabel_description_extra_(self, data, parent, image, label, sublabel, description, extra):
        self = super(FancyRadioView, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self._data = data
            self._parent = parent
            self._plan_image = image
            self._label_text = label
            self._sublabel_text = sublabel
            self._description_text = description
            self._extra_text = extra
            self.sizeToFit()
            self.set_defaults()
        return self

    @property
    def data(self):
        return self._data

    def _get_selected(self):
        return self._selected

    def _set_selected(self, val):
        self._selected = val
        if self._selected:
            self._parent.selectionChanged_(self)
            if not self._description:
                self._label.setTextColor_(Colors.plan_choice_text)
            if self._extra:
                self._extra.setTextColor_(Colors.plan_choice_text)
        else:
            if not self._description:
                self._label.setTextColor_(Colors.black)
            if self._extra:
                self._extra.setTextColor_(Colors.black)
        self._set_colors_for_state()

    selected = property(_get_selected, _set_selected)

    def sizeToFit(self):
        self.setFrameSize_((NSWidth(self._parent.frame()), max(77, self._plan_image.size().height + 41)))

    def set_defaults(self):
        self._selected_colors = (Colors.plan_choice_selected_background, Colors.plan_choice_selected_foreground)
        self._unselected_colors = (Colors.clear, Colors.clear)
        self._hover_colors = (Colors.plan_choice_hover_background, Colors.plan_choice_hover_foreground)
        self._radio_button = ManagedRadioButton(NSMakeRect(12, 0, 0, 0), None, None)
        self.addSubview_(self._radio_button)
        self._radio_button.centerVerticallyInSuperview()
        self._image_view = PassthroughImageView(NSMakeRect(self._radio_button.frame().origin.x + self._radio_button.frame().size.width + 12, 0, self._plan_image.size().width, self._plan_image.size().height))
        self._image_view.setImage_(self._plan_image)
        self._image_view.setFrameOrigin_(NSPoint(72 - self._plan_image.size().width / 2, 0))
        self.addSubview_(self._image_view)
        self._image_view.centerVerticallyInSuperview()
        if self._description_text:
            f = NSFont.boldSystemFontOfSize_(14)
        else:
            f = NSFont.boldSystemFontOfSize_(18)
        self._label = NSTextField.createLabelWithText_font_(self._label_text, f)
        self.addSubview_(self._label)
        label_left = 116
        if self._description_text:
            self._description = NSTextField.createLabelWithText_font_maxWidth_(self._description_text, NSFont.systemFontOfSize_(12), NSWidth(self.frame()) - label_left - self._label.verticalPadding())
            total_height = NSHeight(self._label.frame()) + self._label.horizontalPadding() + NSHeight(self._description.frame())
            outer_height = self.frame().size.height
            rians_rage = 2
            self._label.setFrameOrigin_(NSPoint(label_left, outer_height - (outer_height - total_height) / 2 - NSHeight(self._label.frame()) + rians_rage))
            self._description.setFrameOrigin_((NSMinX(self._label.frame()), NSMinY(self._label.frame()) - self._label.horizontalPadding() - NSHeight(self._description.frame())))
            self.addSubview_(self._description)
        else:
            self._label.setFrameOrigin_(NSPoint(label_left, 0))
            self._label.centerVerticallyInSuperview()
            self._description = None
        if self._sublabel_text:
            f = NSFont.systemFontOfSize_(12)
            self._sublabel = NSTextField.createLabelWithText_font_(self._sublabel_text, f)
            self._sublabel.setFrameOrigin_(NSPoint(NSMaxX(self._label.frame()), NSMinY(self._label.frame())))
            self._sublabel.setTextColor_(Colors.disabled_text)
            self.addSubview_(self._sublabel)
        else:
            self._sublabel = None
        if self._extra_text:
            f = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize))
            self._extra = NSTextField.createLabelWithText_font_(self._extra_text, f)
            self._extra.setFrameOrigin_(NSPoint(self.bounds().size.width - 132, self.bounds().size.height / 2 - self._extra.frame().size.height / 2))
            self.addSubview_(self._extra)
        else:
            self._extra = None
        self.hover = False
        self.tracking = False
        self.selected = False

    def viewDidMoveToWindow(self):
        if self.window() is not None:
            self.addTrackingRect_owner_userData_assumeInside_(self.bounds(), self, 0, 0)

    def _set_colors_for_state(self):
        if self.selected or self.tracking:
            self.setBackgroundColor_(self._selected_colors[0])
            self.setBorderColor_(self._selected_colors[1])
            if self.tracking:
                self._radio_button.highlight_(True)
            else:
                self._radio_button.highlight_(False)
                self._radio_button.setState_(NSOnState)
        elif self.hover:
            self.setBackgroundColor_(self._hover_colors[0])
            self.setBorderColor_(self._hover_colors[1])
            self._radio_button.highlight_(False)
        else:
            self.setBackgroundColor_(self._unselected_colors[0])
            self.setBorderColor_(self._unselected_colors[1])
            self._radio_button.highlight_(False)
            self._radio_button.setState_(NSOffState)

    def setBackgroundColor_(self, new_color):
        self.background_color = new_color
        self.setNeedsDisplay_(YES)

    def setBorderColor_(self, new_color):
        self.border_color = new_color
        self.setNeedsDisplay_(YES)

    def acceptsFirstResponder(self):
        return True

    @protected_action_method
    def drawRect_(self, rect):
        r = self.bounds()
        r.size.height -= 1
        r.size.width -= 1
        bgpath = NSBezierPath.bezierPathWithRect_(r)
        with save_graphics_state() as graphics_context:
            self.background_color.set()
            bgpath.fill()
            graphics_context.setShouldAntialias_(NO)
            self.border_color.set()
            bgpath.stroke()
        super(FancyRadioView, self).drawRect_(rect)

    def select(self):
        self.selected = True
        self._set_colors_for_state()

    def unselect(self):
        self.selected = False
        self._set_colors_for_state()

    @protected_action_method
    def mouseDown_(self, event):
        self.tracking = True
        self._set_colors_for_state()

    @protected_action_method
    def mouseUp_(self, event):
        self.tracking = False
        if NSPointInRect(self.convertPoint_fromView_(event.locationInWindow(), None), self.bounds()):
            if not self.selected:
                self.selected = True
        self._set_colors_for_state()

    @protected_action_method
    def mouseDragged_(self, event):
        old_tracking = self.tracking
        self.tracking = NSPointInRect(self.convertPoint_fromView_(event.locationInWindow(), None), self.bounds())
        if self.tracking != old_tracking:
            self._set_colors_for_state()

    @protected_action_method
    def mouseEntered_(self, event):
        self.hover = True
        self._set_colors_for_state()

    @protected_action_method
    def mouseExited_(self, event):
        self.hover = False
        self._set_colors_for_state()


class PlanView(FancyRadioGroup):

    def __new__(cls, frame):
        return PlanView.alloc().initWithFrame_(frame)

    def addPlanChoice_i_(self, choice, i):
        v = PlanChoiceView(choice, i, self)
        self.addChoiceView_(v)
        return v

    @property
    def selectedPlan(self):
        if self._selected is not None:
            return self._selected.data


class PlanChoiceView(FancyRadioView):

    def __new__(cls, plan_data, i, parent):
        return PlanChoiceView.alloc().initWithPlanData_i_parent_(plan_data, i, parent)

    def initWithPlanData_i_parent_(self, plan_data, i, parent):
        image = self._pick_image(plan_data, i)
        label = plan_data['name']
        extra = plan_data['description']
        self = super(PlanChoiceView, self).initWithPlanData_parent_image_label_subLabel_description_extra_(plan_data, parent, image, label, None, None, extra)
        return self

    def _pick_image(self, plan_data, i):
        if i == 0:
            return Images.Box24
        elif i == 1:
            return Images.Box42
        else:
            return Images.Box64


class PassthroughImageView(NSImageView):

    def __new__(cls, frame):
        return PassthroughImageView.alloc().initWithFrame_(frame)

    def initWithFrame_(self, frame):
        self = super(PassthroughImageView, self).initWithFrame_(frame)
        if self is not None:
            self.setEditable_(NO)
        return self

    def mouseDown_(self, event):
        self.nextResponder().mouseDown_(event)

    def mouseUp_(self, event):
        self.nextResponder().mouseUp_(event)


class LinkTrackingHelper(object):

    def __init__(self, control, selector):
        self._control = control
        self._selector = selector
        self._tracking_rect_tags = []
        self._tool_tip_tags = []

    def setup_tracking(self, offset):
        self._cursor_rects = []
        self._link_ranges = []
        self._is_tracking = False
        self.clear_tracking()
        attr_str = self._selector()
        text_storage = NSTextStorage.alloc().initWithAttributedString_(attr_str)
        layout_manager = NSLayoutManager.alloc().init()
        s = self._control.bounds().size
        s.height += 20
        text_container = NSTextContainer.alloc().initWithContainerSize_(s)
        layout_manager.addTextContainer_(text_container)
        text_storage.addLayoutManager_(layout_manager)
        title_rect = self._control.cell().titleRectForBounds_(self._control.bounds())
        i = 0
        while i < attr_str.length():
            attrs, r = attr_str.attributesAtIndex_effectiveRange_(i, None)
            if NSLinkAttributeName in attrs:
                link_rect = layout_manager.boundingRectForGlyphRange_inTextContainer_(r, text_container)
                link_rect.origin.x += title_rect.origin.x - offset
                link_rect.origin.y += title_rect.origin.y
                self._cursor_rects.append(link_rect)
                self._link_ranges.append(r)
                TRACE('Adding tracking/tooltip rect at %r' % link_rect)
                tag = self._control.addTrackingRect_owner_userData_assumeInside_(link_rect, self._control, len(self._link_ranges) - 1, NO)
                self._tracking_rect_tags.append(tag)
                tag = self._control.addToolTipRect_owner_userData_(link_rect, self._control, len(self._link_ranges) - 1)
                self._tool_tip_tags.append(tag)
            i += r.length

    def clear_tracking(self):
        for tag in self._tracking_rect_tags:
            self._control.removeTrackingRect_(tag)

        self._tracking_rect_tags = []
        for tag in self._tool_tip_tags:
            self._control.removeToolTip_(tag)

        self._tool_tip_tags = []

    def resetCursorRects(self):
        for rect in self._cursor_rects:
            self._control.addCursorRect_cursor_(rect, NSCursor.pointingHandCursor())

    def highlight_link_index(self, idx):
        assert idx <= len(self._link_ranges)
        attr_str = NSMutableAttributedString.alloc().initWithAttributedString_(self._selector())
        with edit_attributed_string(attr_str):
            r = self._link_ranges[idx]
            attr_str.addAttribute_value_range_(NSUnderlineStyleAttributeName, NSNumber.numberWithInt_(NSSingleUnderlineStyle), r)
        return attr_str

    def unhighlight_link_index(self, idx):
        assert idx <= len(self._link_ranges)
        attr_str = NSMutableAttributedString.alloc().initWithAttributedString_(self._selector())
        with edit_attributed_string(attr_str) as editing_str:
            r = self._link_ranges[idx]
            editing_str.removeAttribute_range_(NSUnderlineStyleAttributeName, r)
        return attr_str

    def get_tooltip(self, idx):
        if idx <= len(self._link_ranges):
            attr_str = self._selector()
            l, lrange = attr_str.attribute_atIndex_effectiveRange_(NSLinkAttributeName, self._link_ranges[idx].location, None)
            return l.absoluteString()

    def mouse_down_helper(self, mouse_loc, highlight, unhighlight):
        attr_str = self._selector()
        for idx, rect in enumerate(self._cursor_rects):
            if NSPointInRect(mouse_loc, rect):
                keep_on = True
                while keep_on:
                    evt = self._control.window().nextEventMatchingMask_(NSLeftMouseUpMask | NSLeftMouseDraggedMask)
                    mouse_loc = self._control.convertPoint_fromView_(evt.locationInWindow(), None)
                    is_inside = NSPointInRect(mouse_loc, rect)
                    if evt.type() == NSLeftMouseUp:
                        if is_inside:
                            l, lrange = attr_str.attribute_atIndex_effectiveRange_(NSLinkAttributeName, self._link_ranges[idx].location, None)
                            NSWorkspace.sharedWorkspace().openURL_(l)
                        keep_on = False
                    elif evt.type() == NSLeftMouseDragged:
                        if is_inside:
                            highlight(idx)
                        else:
                            unhighlight(idx)

                return True

        return False


class CheckboxWithLink(NSButton):

    def __new__(cls, title):
        return CheckboxWithLink.alloc().initWithTitle_(title)

    def initWithTitle_(self, title):
        self = super(CheckboxWithLink, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self.setButtonType_(NSSwitchButton)
            self.setFont_(NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSRegularControlSize)))
            self.setAttributedTitle_(NSAttributedString.linkify(title))
            self.sizeToFit()
            self._link_tracking_helper = LinkTrackingHelper(self, self.attributedTitle)
        return self

    def viewDidMoveToWindow(self):
        if self.window() is not None:
            TRACE('CheckboxWithLink added to a window. Setting up tracking rects.')
            self._link_tracking_helper.setup_tracking(6)
        else:
            self._link_tracking_helper.clear_tracking()

    def resetCursorRects(self):
        super(CheckboxWithLink, self).resetCursorRects()
        self._link_tracking_helper.resetCursorRects()

    def view_stringForToolTip_point_userData_(self, view, tag, point, data):
        tt = self._link_tracking_helper.get_tooltip(data)
        if tt is not None:
            return tt
        return super(CheckboxWithLink, self).view_stringForToolTip_point_userData_(view, tag, point, data)

    @protected_action_method
    def mouseDown_(self, event):
        mouse_loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        if self._link_tracking_helper.mouse_down_helper(mouse_loc, self._highlight_link, self._unhighlight_link):
            return
        super(CheckboxWithLink, self).mouseDown_(event)

    def _highlight_link(self, idx):
        attr_str = self._link_tracking_helper.highlight_link_index(idx)
        self.setAttributedTitle_(attr_str)

    def _unhighlight_link(self, idx):
        attr_str = self._link_tracking_helper.unhighlight_link_index(idx)
        self.setAttributedTitle_(attr_str)

    @protected_action_method
    def mouseEntered_(self, event):
        self._highlight_link(event.userData())

    @protected_action_method
    def mouseExited_(self, event):
        self._unhighlight_link(event.userData())


class TextFieldWithLink(NSTextField):

    def __new__(cls, text, max_width = None, font = None, center = False, bold = False, size_diff = 0, line_height = 0, color = None):
        return TextFieldWithLink.alloc().initWithFrame_text_maxWidth_font_center_bold_size_line_color_(NSZeroRect, text, max_width, font, center, bold, size_diff, line_height, color)

    def initWithFrame_text_maxWidth_font_center_bold_size_line_color_(self, frame, text, max_width, font, center, bold, size_diff, line_height, color):
        self = super(TextFieldWithLink, self).initWithFrame_(frame)
        if self is not None:
            self._center = center
            self._line_height = line_height
            self._max_width = max_width
            self.setAllowsEditingTextAttributes_(YES)
            if font is None:
                size = NSFont.systemFontSizeForControlSize_(NSRegularControlSize) + size_diff
                if bold:
                    font = NSFont.boldSystemFontOfSize_(size)
                else:
                    font = NSFont.systemFontOfSize_(size)
            self._color = color
            self.setFont_(font)
            self.setStringValue_(text)
            self.setBezeled_(NO)
            self.setDrawsBackground_(NO)
            self.setEditable_(NO)
            self.setSelectable_(NO)
            self.sizeToFit()
            self._link_tracking_helper = LinkTrackingHelper(self, self.attributedStringValue)
        return self

    def viewDidMoveToWindow(self):
        if self.window() is not None:
            TRACE('TextFieldWithLink added to a window. Setting up tracking rects.')
            self._link_tracking_helper.setup_tracking(0)
        else:
            self._link_tracking_helper.clear_tracking()

    def setStringValue_(self, text):
        attr_str = NSAttributedString.linkify(text, self.font(), self._color)
        if self._center or self._line_height:
            with edit_attributed_string(attr_str):
                style = NSMutableParagraphStyle.defaultParagraphStyle().mutableCopyWithZone_(None)
                if self._center:
                    style.setAlignment_(NSCenterTextAlignment)
                if self._line_height:
                    style.setMinimumLineHeight_(self._line_height)
                    style.setMaximumLineHeight_(self._line_height)
                r = NSMakeRange(0, attr_str.length())
                attr_str.addAttribute_value_range_(NSParagraphStyleAttributeName, style, r)
        self.setHidden_(not bool(text))
        super(TextFieldWithLink, self).setAttributedStringValue_(attr_str)

    @typedSelector('v@:')
    @assert_message_queue
    def sizeToFit(self):
        attr_str = self.attributedStringValue()
        if self._max_width is None:
            super(TextFieldWithLink, self).sizeToFit()
        else:
            max_size = NSSize(self._max_width, 0)
            self.cell().setWraps_(YES)
            if attr_str.length() > 0:
                attrs, r = attr_str.attributesAtIndex_effectiveRange_(0, None)
                text_rect = attr_str.string().boundingRectWithSize_options_attributes_(max_size, NSStringDrawingUsesLineFragmentOrigin, attrs)
                self.setFrameSize_(NSSize(self._max_width, NSHeight(text_rect)))

    def resetCursorRects(self):
        super(TextFieldWithLink, self).resetCursorRects()
        self._link_tracking_helper.resetCursorRects()

    def view_stringForToolTip_point_userData_(self, view, tag, point, data):
        tt = self._link_tracking_helper.get_tooltip(data)
        if tt is not None:
            return tt
        return super(TextFieldWithLink, self).view_stringForToolTip_point_userData_(view, tag, point, data)

    @protected_action_method
    def mouseDown_(self, event):
        mouse_loc = self.convertPoint_fromView_(event.locationInWindow(), None)
        if self._link_tracking_helper.mouse_down_helper(mouse_loc, self._highlight_link, self._unhighlight_link):
            return
        super(TextFieldWithLink, self).mouseDown_(event)

    def _highlight_link(self, idx):
        attr_str = self._link_tracking_helper.highlight_link_index(idx)
        self.setAttributedStringValue_(attr_str)

    def _unhighlight_link(self, idx):
        attr_str = self._link_tracking_helper.unhighlight_link_index(idx)
        self.setAttributedStringValue_(attr_str)

    @protected_action_method
    def mouseEntered_(self, event):
        self._highlight_link(event.userData())

    @protected_action_method
    def mouseExited_(self, event):
        self._unhighlight_link(event.userData())


class NonBlurryImageView(NSImageView):

    @event_handler
    def drawRect_(self, rect):
        with save_graphics_state() as graphics_context:
            graphics_context.setImageInterpolation_(NSImageInterpolationNone)
            super(NonBlurryImageView, self).drawRect_(rect)


class ImageView(NSView):

    def __new__(cls, image, label = None, outline = False):
        return ImageView.alloc().initWithImage_label_outline_(image, label, outline)

    @guarded('@:@@@')
    def initWithImage_label_outline_(self, image, label, outline):
        self = self.initWithFrame_(NSZeroRect)
        if self is not None:
            self._outline = outline
            self._imageView = NonBlurryImageView.alloc().initWithFrame_(NSZeroRect)
            self._imageView.setImage_(image)
            self._imageView.setImageAlignment_(NSImageAlignRight)
            self._imageView.setImageScaling_(NSScaleNone)
            self.addSubview_(self._imageView)
            self._label = None
            l_offset = 0
            if label is not None:
                self._label = NSTextField.createLabelWithText_(label)
                self.addSubview_(self._label)
                l_offset = NSWidth(self._label.frame()) + self._label.horizontalPadding()
            w = image.size().width
            h = image.size().height
            self._imageView.setFrameSize_((w, h))
            if self._outline:
                x_image_offset = 1.5
                y_image_offset = 1
                x_padding = 4
                y_padding = 2
                self._imageView.setFrameOrigin_((x_image_offset, y_image_offset))
                self.setFrameSize_(NSSize(w + l_offset + x_padding, h + y_padding))
            else:
                x_image_offset = 0
                self._imageView.setFrameOrigin_((0, 0))
                self.setFrameSize_(NSSize(w + l_offset, h))
            if self._label:
                self._label.centerVerticallyInSuperview()
                self._label.setFrameOrigin_(NSPoint(w + x_image_offset + self._label.horizontalPadding(), self._label.frame().origin.y))
            self.setBorderColor_(Colors.image_outline)
        return self

    def setBorderColor_(self, new_color):
        self._border_color = new_color
        self.setNeedsDisplay_(YES)

    @property
    def bg_rect(self):
        x, y = self._imageView.frame().origin
        w, h = self._imageView.frame().size
        w_bump = 1 if MAC_VERSION < SNOW_LEOPARD else 0
        return NSMakeRect(x - 1, y - 1, w + 1 + w_bump, h + 1)

    @event_handler
    def drawRect_(self, rect):
        if not self._outline:
            return
        bgpath = NSBezierPath.bezierPathWithRect_(self.bg_rect)
        with save_graphics_state() as graphics_context:
            graphics_context.setShouldAntialias_(NO)
            self._border_color.set()
            bgpath.stroke()


class HelpButton(NSButton):

    def __new__(cls, hover_text, url):
        return HelpButton.alloc().initWithHoverText_url_(hover_text, url)

    def initWithHoverText_url_(self, hover_text, url):
        self = super(HelpButton, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self.setBezelStyle_(NSHelpButtonBezelStyle)
            self.setTitle_(u'')
            if hover_text:
                self.setToolTip_(hover_text)
            if url:
                self._url = NSURL.alloc().initWithString_(url)
                self.setAction_(self.buttonAction_)
                self.setTarget_(self)
            self.sizeToFit()
        return self

    @protected_action_method
    def buttonAction_(self, sender):
        if self._url:
            NSWorkspace.sharedWorkspace().openURL_(self._url)


class CreditCardTypeView(NSView):
    ALL_CARD_TYPES = [u'visa', u'mastercard', u'amex']

    def __new__(cls):
        return CreditCardTypeView.alloc().init()

    def init(self):
        self = super(CreditCardTypeView, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self._setup()
            self.sizeToFit()
        return self

    def _setup(self):
        CARD_IMAGES = {u'amex': Images.Amex,
         u'mastercard': Images.Mastercard,
         u'visa': Images.Visa}
        self._padding = 5
        self._images = dict()
        for name in CreditCardTypeView.ALL_CARD_TYPES:
            whole_img = CARD_IMAGES[name]
            half_size = NSSize(whole_img.size().width / 2.0, whole_img.size().height)
            selected_img = NSImage.alloc().initWithSize_(half_size)
            selected_img.lockFocus()
            whole_img.drawAtPoint_fromRect_operation_fraction_(NSPoint(0, 0), NSZeroRect, NSCompositeSourceOver, 1.0)
            selected_img.unlockFocus()
            unselected_img = NSImage.alloc().initWithSize_(half_size)
            unselected_img.lockFocus()
            unselected_rect = NSMakeRect(whole_img.size().width / 2.0, 0, whole_img.size().width, whole_img.size().height)
            whole_img.drawAtPoint_fromRect_operation_fraction_(NSPoint(0, 0), unselected_rect, NSCompositeSourceOver, 1.0)
            unselected_img.unlockFocus()
            self._images[name] = (selected_img, unselected_img)

        self._card_types = CreditCardTypeView.ALL_CARD_TYPES

    def verticalPadding(self):
        return 8

    def sizeToFit(self):
        height = max([ img[0].size().height for img in self._images.itervalues() ])
        width = sum([ img[0].size().width for img in self._images.itervalues() ])
        width += self._padding * 2
        self.setFrameSize_(NSSize(width, height))

    def setStringValue_(self, value):
        if value in CreditCardTypeView.ALL_CARD_TYPES:
            self.setCardTypes_([value])
        else:
            self.setCardTypes_(CreditCardTypeView.ALL_CARD_TYPES)

    def setCardTypes_(self, card_types):
        self._card_types = card_types
        self.setNeedsDisplay_(YES)

    def drawRect_(self, rect):
        offset = NSPoint(0, 0)
        for cc in CreditCardTypeView.ALL_CARD_TYPES:
            if cc in self._card_types:
                img = self._images[cc][0]
            else:
                img = self._images[cc][1]
            img.drawAtPoint_fromRect_operation_fraction_(offset, NSZeroRect, NSCompositeCopy, 1.0)
            offset.x += img.size().width + self._padding


class FlagPopUpButton(NSPopUpButton):
    CHECKMARK_PIXEL_WIDTH = 10
    NUM_ITEMS_DISPLAYED = 20
    MENU_ITEM_HEIGHT = 18

    def __new__(cls, frame, flag_width):
        return cls.alloc().initWithFrame_flagWidth_(frame, flag_width)

    def initWithFrame_flagWidth_(self, frame, flag_width):
        self = super(FlagPopUpButton, self).initWithFrame_(frame)
        if not self:
            return self
        self.menu().setDelegate_(self)
        self._open_width = None
        self._flag_width = flag_width
        self.cell().setLineBreakMode_(NSLineBreakByTruncatingMiddle)
        return self

    def open_width(self):
        if self._open_width:
            return self._open_width
        w = 0
        for item in list(self.menu().itemArray()):
            title = item.attributedTitle()
            if title is None:
                title = NSAttributedString.alloc().initWithString_(item.title())
            w = max(w, title.size().width)

        self._open_width = w + self._flag_width + self.CHECKMARK_PIXEL_WIDTH
        TRACE('open width is %s', self._open_width)
        return self._open_width

    @objc.typedSelector('{_NSRect={_NSPoint=ff}{_NSSize=ff}}@:@@')
    @event_handler
    def confinementRectForMenu_onScreen_(self, menu, screen):
        try:
            button_origin_x, button_origin_y = self.superview().convertPointToBase_(self.frame().origin)
            closed_height = self.frame().size.height
            open_width = self.open_width()
            h = self.MENU_ITEM_HEIGHT * (self.NUM_ITEMS_DISPLAYED + 2)
            space_below = self.MENU_ITEM_HEIGHT * (self.NUM_ITEMS_DISPLAYED // 2 + 1)
            x = button_origin_x - self.CHECKMARK_PIXEL_WIDTH
            w = open_width
            y = button_origin_y - space_below + closed_height
            screen_origin = self.window().convertBaseToScreen_((x, y))
            if screen_origin.y < 0:
                multiple = (-screen_origin.y + self.MENU_ITEM_HEIGHT - 1) // self.MENU_ITEM_HEIGHT
                screen_origin.y += self.MENU_ITEM_HEIGHT * multiple
            return (screen_origin, (w, h))
        except Exception:
            unhandled_exc_handler()
            return NSZeroRect


class NumericStepper(NSView):

    def __new__(cls, min_val, max_val, units, label, invalid_label):
        return cls.alloc().initWithMinVal_maxVal_units_label_invalidLabel_(min_val, max_val, units, label, invalid_label)

    def initWithMinVal_maxVal_units_label_invalidLabel_(self, min_val, max_val, units, label, invalid_label):
        self = super(NumericStepper, self).initWithFrame_(NSZeroRect)
        if self is not None:
            self._setup(min_val, max_val, units, label, invalid_label)
            self.sizeToFit()
        return self

    def baselineOffset(self):
        return 3

    def isFlipped(self):
        return NO

    def _setup(self, min_val, max_val, units, label, invalid_label):
        self._control_padding = 5
        self._invalid_label = invalid_label
        self._label = label
        self._text_field = NSTextField.createNormalTextField()
        formatter = NSNumberFormatter.alloc().init()
        formatter.setFormatterBehavior_(1040)
        formatter.setMinimum_(min_val)
        formatter.setMaximum_(max_val)
        formatter.setNumberStyle_(1)
        self._text_field.setDelegate_(self)
        self._text_field.setFormatter_(formatter)
        self._text_field.setFrame_(NSRect((0, self._text_field.baselineOffset()), (56, NSHeight(self._text_field.frame()))))
        self.addSubview_(self._text_field)
        self._stepper = NSStepper.alloc().init()
        self._stepper.setTarget_(self)
        self._stepper.setAction_(self.stepperClicked_)
        self._stepper.setMinValue_(min_val)
        self._stepper.setMaxValue_(max_val)
        self._stepper.sizeToFit()
        self._stepper.setFrameOrigin_((NSWidth(self._text_field.frame()) + self._control_padding, -1))
        self._stepper.setValueWraps_(NO)
        if units is not None:
            self._units_label = NSTextField.createLabelWithText_(units)
            self._units_label.setFrameOrigin_((NSMaxX(self._stepper.frame()) + self._control_padding, self._stepper.baselineOffset()))
            self.addSubview_(self._units_label)
        else:
            self._units_label = None
        self.addSubview_(self._stepper)
        self.setIntValue_(min_val)

    def sizeToFit(self):
        height = max(NSMaxY(self._text_field.frame()), NSMaxY(self._stepper.frame()), NSMaxY(self._units_label.frame()) if self._units_label else 0)
        width = NSMaxX(self._units_label.frame()) if self._units_label else NSMaxX(self._stepper.frame())
        self.setFrameSize_((width, height))

    def setMaxValue_(self, value):
        self._stepper.setMaxValue_(value)

    def setMinValue_(self, value):
        self._stepper.setMinValue_(value)

    def intValue(self):
        return self._stepper.intValue()

    def setIntValue_(self, value):
        self._stepper.setIntValue_(value)
        self._text_field.setIntValue_(value)

    def isEnabled(self):
        return self._stepper.isEnabled() and self._text_field.isEnabled()

    def setEnabled_(self, enabled):
        self._stepper.setEnabled_(enabled)
        self._text_field.setEnabled_(enabled)
        if self._units_label:
            c = NSColor.controlTextColor() if enabled else NSColor.disabledControlTextColor()
            self._units_label.setTextColor_(c)

    def isValid(self, override = None):
        text = override if override else self._text_field.stringValue()
        valid, number, error = self._text_field.formatter().getObjectValue_forString_errorDescription_(None, text, None)
        return valid

    def safeIntValue_(self, value):
        valid, number, error = self._text_field.formatter().getObjectValue_forString_errorDescription_(None, value, None)
        if valid:
            return number

    def controlTextDidChange_(self, notification):
        new_text = notification.userInfo()['NSFieldEditor'].string()
        int_value = self.safeIntValue_(new_text)
        if int_value is not None:
            self._stepper.setIntValue_(int_value)

    def controlTextDidEndEditing_(self, notification):
        self._stepper.takeIntValueFrom_(notification.object())

    def stepperClicked_(self, sender):
        self._text_field.takeIntValueFrom_(sender)

    def tickleAlertSheet(self):
        text = self._text_field.stringValue()
        valid, number, error = self._text_field.formatter().getObjectValue_forString_errorDescription_(None, text, None)
        if not valid:
            self.control_didFailToFormatString_errorDescription_(None, None, error)

    def control_didFailToFormatString_errorDescription_(self, control, string, error):
        NSBeginAlertSheet(self._invalid_label, MiscStrings.ok_button, None, None, self.window(), self, None, None, 0, '%@', error)
        return NO
