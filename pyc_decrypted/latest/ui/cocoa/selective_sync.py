#Embedded file name: ui/cocoa/selective_sync.py
from __future__ import absolute_import
import os
import time
from objc import YES, NO, ivar
from Foundation import NSFileTypeForHFSTypeCode, NSMakeRect, NSMakeSize, NSMaxX, NSMaxY, NSObject, NSPoint, NSRect, NSSize, NSZeroRect
from AppKit import NSApp, NSBackingStoreBuffered, NSBezierPath, NSBrowser, NSBrowserCell, NSButtonCell, NSBrowserNoColumnResizing, NSBrowserUserColumnResizing, NSClosableWindowMask, NSCompositeSourceOver, NSFocusRingTypeNone, NSFont, NSImage, NSMatrix, NSNotificationCenter, NSTextField, NSTitledWindowMask, NSResizableWindowMask, NSSmallControlSize, NSSwitchButton, NSView, NSViewHeightSizable, NSViewWidthSizable, NSWindow, NSWindowDidBecomeKeyNotification, NSWindowDidResignKeyNotification, NSWorkspace
from PyObjCTools import AppHelper
from .constants import ENTER_KEY, ESCAPE_KEY
from .dropbox_controls import DropboxSheetErrorFactory
from .dropbox_menu import DropboxNSMenu
from .dynamic_layouts import align_center_to_offset, height_for_fixed_width, BOTTOM_BUTTON_BORDER, HORIZ_BUTTON_BORDER, HORIZ_BUTTON_SPACING, NEARBY_CONTROL_BORDER, STATICTEXT_TO_BUTTON_BASELINE_ADJUSTMENT
from ..common.selective_sync import CachingLazySelectiveSyncUI, selsync_strings, failed_unignores_message_from_failures
from dropbox.gui import message_sender, event_handler, spawn_thread_with_name
from dropbox.trace import unhandled_exc_handler, TRACE
import build_number
import objc
REMOTE_EVENT_CHILLOUT = 1
BROWSER_ROW_HEIGHT = 18
DEFAULT_ADVANCED_WIDTH = 630
DEFAULT_SIMPLE_WIDTH = 450
DEFAULT_BROWSER_HEIGHT = 15 * BROWSER_ROW_HEIGHT + 2
CHECK_CELL_LEFT_PADDING = 3

class SelectiveSyncBrowserCell(NSBrowserCell):

    @objc.typedSelector('i@:{NSPoint=ff}')
    @event_handler
    def isViewRelativePointInCheckCell_(self, view_point):
        return view_point.x < self._checkCell.cellSize().width + CHECK_CELL_LEFT_PADDING

    def setPath_callbackTarget_(self, path, callbackTarget):
        self._path = path
        self._callbackTarget = callbackTarget
        self._checkCell = NSButtonCell.alloc().init()
        self._checkCell.setButtonType_(NSSwitchButton)
        self._checkCell.setControlSize_(NSSmallControlSize)
        self._checkCell.setTitle_('')
        self._checkCell.setAllowsMixedState_(YES)

    def path(self):
        if hasattr(self, '_path'):
            return self._path

    @event_handler
    def cellSizeForBounds_(self, bounds):
        ret = super(SelectiveSyncBrowserCell, self).cellSizeForBounds_(bounds)
        if hasattr(self, '_path'):
            checksize = self._checkCell.cellSize()
            ret.width += checksize.width
            ret.height = max(ret.height, checksize.height)
        return ret

    @objc.typedSelector('v@:')
    @event_handler
    def invalidateFolderTag(self):
        if hasattr(self, '_image'):
            del self._image

    @event_handler
    def drawWithFrame_inView_(self, frame, view):
        if hasattr(self, '_path'):
            if not hasattr(self, '_image'):
                self._image = self._callbackTarget.imageForPath_(self._path)
                self.setTitle_(self._callbackTarget.titleForPath_(self._path))
            self._checkCell.setIntValue_(self._callbackTarget.stateForPath_(self._path))
            x = frame.origin.x
            y = frame.origin.y + 1
            height = frame.size.height - 1
            if self.state() or self.isHighlighted():
                highlight_rect = NSMakeRect(x, y, frame.size.width, height)
                if view.needsToDrawRect_(highlight_rect):
                    self.highlightColorInView_(view).set()
                    NSBezierPath.bezierPathWithRect_(highlight_rect).fill()
            x += CHECK_CELL_LEFT_PADDING
            checkCellSize = self._checkCell.cellSize()
            check_cell_rect = NSMakeRect(x, y, checkCellSize.width, height)
            if view.needsToDrawRect_(check_cell_rect):
                self._checkCell.drawWithFrame_inView_(check_cell_rect, view)
            x += checkCellSize.width - 1
            imageSize = self._image.size()
            image_rect = NSMakeRect(x, y, imageSize.width, imageSize.height)
            if view.needsToDrawRect_(image_rect):
                self._image.drawInRect_fromRect_operation_fraction_(image_rect, NSZeroRect, NSCompositeSourceOver, 1.0)
            x += imageSize.width + 4
            rest_of_cell_rect = NSMakeRect(x, y, frame.size.width - x, height)
            if view.needsToDrawRect_(rest_of_cell_rect):
                super(SelectiveSyncBrowserCell, self).drawWithFrame_inView_(rest_of_cell_rect, view)
        else:
            super(SelectiveSyncBrowserCell, self).drawWithFrame_inView_(frame, view)

    @objc.typedSelector(NSButtonCell.intValue.signature)
    @event_handler
    def valueForToggle(self):
        if self._checkCell.intValue() == 0:
            return 1
        return 0

    @objc.typedSelector(NSButtonCell.intValue.signature)
    @event_handler
    def intValue(self):
        return self._checkCell.intValue()

    @objc.typedSelector(NSButtonCell.setIntValue_.signature)
    @event_handler
    def setIntValue_(self, intValue):
        if intValue != self._checkCell.intValue():
            self._checkCell.setIntValue_(intValue)
            self._callbackTarget.checkState_fromPath_(intValue, self._path)

    def setIntValueFromForest_(self, intValue):
        if intValue != self._checkCell.intValue():
            self._checkCell.setIntValue_(intValue)
            return YES
        else:
            return NO

    @objc.typedSelector(NSButtonCell.setHighlighted_.signature)
    @event_handler
    def setCheckHighlighted_(self, boolean):
        self._checkCell.setHighlighted_(boolean)

    @objc.typedSelector(NSButtonCell.isHighlighted.signature)
    @event_handler
    def isCheckHighlighted(self):
        return self._checkCell.isHighlighted()


class SelectiveSyncBrowserMatrix(NSMatrix):

    @event_handler
    def mouseDown_(self, event):
        the_cell = self.selectiveSyncCellForMouseEvent_(event)
        if the_cell:
            self.down_in_cell = the_cell
            the_cell.setCheckHighlighted_(YES)
            self.setNeedsDisplay_(YES)
        else:
            super(SelectiveSyncBrowserMatrix, self).mouseDown_(event)
            self.down_in_cell = None

    @event_handler
    def mouseDragged_(self, event):
        the_cell = self.selectiveSyncCellForMouseEvent_(event)
        if self.down_in_cell is not None:
            if self.down_in_cell != the_cell:
                if self.down_in_cell.isCheckHighlighted():
                    self.down_in_cell.setCheckHighlighted_(NO)
                    self.setNeedsDisplay_(YES)
            elif not self.down_in_cell.isCheckHighlighted():
                self.down_in_cell.setCheckHighlighted_(YES)
                self.setNeedsDisplay_(YES)

    @event_handler
    def mouseUp_(self, event):
        if self.down_in_cell is None:
            super(SelectiveSyncBrowserMatrix, self).mouseUp_(event)
        else:
            the_cell = self.selectiveSyncCellForMouseEvent_(event)
            if self.down_in_cell == the_cell:
                the_cell.setIntValue_(the_cell.valueForToggle())
                the_cell.setCheckHighlighted_(NO)
                self.setNeedsDisplay_(YES)
            self.down_in_cell = None

    @event_handler
    def keyDown_(self, event):
        self.spacebar_cell = None
        if event.keyCode() == 49:
            cell = self.keyCell()
            if cell:
                cell.setCheckHighlighted_(YES)
                self.setNeedsDisplay_(YES)
                self.spacebar_cell = cell
                return
        super(SelectiveSyncBrowserMatrix, self).keyDown_(event)

    @event_handler
    def keyUp_(self, event):
        if event.keyCode() == 49 and self.spacebar_cell is not None:
            self.spacebar_cell.setIntValue_(self.spacebar_cell.valueForToggle())
            self.spacebar_cell.setCheckHighlighted_(NO)
            self.setNeedsDisplay_(YES)
            self.spacebar_cell = None
            return
        super(SelectiveSyncBrowserMatrix, self).keyUp_(event)

    @objc.typedSelector('@@:@')
    @event_handler
    def selectiveSyncCellForMouseEvent_(self, event):
        window_point = event.locationInWindow()
        view_point = self.convertPoint_fromView_(window_point, self.window().contentView())
        successful, row, column = self.getRow_column_forPoint_(None, None, view_point)
        if successful:
            the_cell = self.cellAtRow_column_(row, column)
            if the_cell.isViewRelativePointInCheckCell_(view_point):
                return the_cell

    @event_handler
    def cellSize(self):
        ret = super(SelectiveSyncBrowserMatrix, self).cellSize()
        return NSSize(ret.width, max(ret.height, BROWSER_ROW_HEIGHT))


class SelectiveSyncBrowserDelegate(NSObject):
    syncEngine = ivar('syncEngine')

    def __new__(cls, browser, forest, reloadInvalidState):
        return SelectiveSyncBrowserDelegate.alloc().initWithBrowser_andForest_reloadInvalidState_(browser, forest, reloadInvalidState)

    def initWithBrowser_andForest_reloadInvalidState_(self, browser, forest, reloadInvalidState):
        self = super(SelectiveSyncBrowserDelegate, self).init()
        if self is None:
            return
        from dropbox.mac.internal import get_resources_dir
        self.default_width = None
        icons_path = get_resources_dir() if hasattr(build_number, 'frozen') else u'icons/'
        self.images = {}
        for key, icon in (('dropbox', 'DropboxFolderIcon_leopard.icns'),
         ('shared', 'shared_leopard.icns'),
         ('public', 'public_leopard.icns'),
         ('photos', 'photos_leopard.icns'),
         ('sandbox', 'sandbox_leopard.icns'),
         ('camerauploads', 'camerauploads_leopard.icns')):
            image = NSImage.alloc().initByReferencingFile_(os.path.join(icons_path, icon))
            image.setSize_((16, 16))
            image.setFlipped_(YES)
            image.recache()
            self.images[key] = image

        images_path = get_resources_dir() if hasattr(build_number, 'frozen') else u'images/mac'
        folder_image = NSWorkspace.sharedWorkspace().iconForFileType_(NSFileTypeForHFSTypeCode('fldr'))
        folder_image.setFlipped_(YES)
        folder_image.setSize_(NSMakeSize(16, 16))
        self.images['folder'] = folder_image
        self.forest = forest
        self.browser_reloadAdvancedView_(browser, self.forest.advanced_view)
        self.reloadInvalidState = reloadInvalidState
        TRACE('initialized %r', self.forest)
        self.browser = browser
        return self

    def checkState_fromPath_(self, checkState, path):
        self.forest.set_check_state_from_ui(path, checkState)
        try:
            for x in range(self.browser.firstVisibleColumn(), self.browser.lastVisibleColumn() + 1):
                matrix = self.browser.matrixInColumn_(x)
                needs_update = NO
                for y in range(matrix.numberOfRows()):
                    cell = matrix.cellAtRow_column_(y, 0)
                    if cell.setIntValueFromForest_(self.stateForPath_(cell.path())):
                        needs_update = YES

                if needs_update:
                    matrix.setNeedsDisplay_(YES)

        except:
            unhandled_exc_handler()

        self.reloadInvalidState()

    def imageForPath_(self, path):
        image_tag = self.forest.image_tag_for_path(path)
        return self.images[image_tag]

    def titleForPath_(self, path):
        return self.forest.title_for_path(path)

    def stateForPath_(self, path):
        return self.forest.check_state_for_path(path)

    @objc.typedSelector('v@:@B')
    @event_handler
    def browser_reloadAdvancedView_(self, browser, advancedView):
        self.last_ui_invalidation = None
        self.pending_paths_to_invalidate = {}
        if advancedView:
            browser.setColumnResizingType_(NSBrowserUserColumnResizing)
            browser.setHasHorizontalScroller_(YES)
        else:
            browser.setColumnResizingType_(NSBrowserNoColumnResizing)
            browser.setHasHorizontalScroller_(NO)
        if browser.respondsToSelector_('setAutohidesScroller:'):
            browser.setAutohidesScroller_(YES)

    def intelligentlyRefreshMatrix_withDirChildren_restoreSelection_(self, matrix, dirChildren, restoreSelection):
        if restoreSelection:
            selected = matrix.selectedCell()
            if selected:
                selected = selected.path().lower()
        else:
            selected = False
        matrix.renewRows_columns_(len(dirChildren), 1)
        to_select = -1
        for i, dir_child in enumerate(dirChildren):
            path, num_children = dir_child
            cell = SelectiveSyncBrowserCell.alloc().init()
            cell.setPath_callbackTarget_(path, self)
            cell.setLeaf_(not num_children)
            try:
                ctxmenu = self.forest.context_menu_for_path(path)
            except:
                unhandled_exc_handler()
            else:
                cell.setMenu_(DropboxNSMenu.menuWithDropboxMenuDescriptor_(ctxmenu))

            matrix.putCell_atRow_column_(cell, i, 0)
            if selected and path.lower() == selected:
                to_select = i

        if to_select > -1:
            matrix.selectCellAtRow_column_(to_select, 0)
            return to_select
        if selected:
            return -1
        return -2

    @objc.typedSelector('v@:@')
    @event_handler
    def invalidateUICallback_(self, paths_to_invalidate):
        TRACE('++ remote events told me to invalidate the following folders: %r' % (paths_to_invalidate,))
        self.pending_paths_to_invalidate.update(paths_to_invalidate)
        incoming = time.time()
        if self.last_ui_invalidation is not None and incoming - self.last_ui_invalidation < REMOTE_EVENT_CHILLOUT:
            TRACE('chilling out for a bit')
            AppHelper.callLater(REMOTE_EVENT_CHILLOUT - (incoming - self.last_ui_invalidation), self.invalidateUICallback_, {})
            return
        self.last_ui_invalidation = incoming
        last_selected = None
        for x in range(0, self.browser.lastColumn() + 1):
            dir_children_for_refresh = None
            if x == 0:
                for path in self.pending_paths_to_invalidate:
                    if path.ns_rel()[1] == '/':
                        dir_children_for_refresh = self.pending_paths_to_invalidate[path]
                        break

            else:
                selected = self.browser.matrixInColumn_(x - 1).selectedCell()
                dir_children_for_refresh = self.pending_paths_to_invalidate.get(selected.path().lower()) if selected else None
            matrix = self.browser.matrixInColumn_(x)
            if matrix:
                if dir_children_for_refresh:
                    TRACE('+++++ refreshing: %r, %r' % (x, dir_children_for_refresh))
                    ret = self.intelligentlyRefreshMatrix_withDirChildren_restoreSelection_(matrix, dir_children_for_refresh, True)
                    matrix.sizeToCells()
                    matrix.setNeedsDisplay_(YES)
                    if ret > -1:
                        last_selected = (ret, x)
                    elif ret == -1:
                        if last_selected is not None:
                            self.browser.selectRow_inColumn_(last_selected[0], last_selected[1])
                        else:
                            self.browser.setPath_(self.browser.pathSeparator())
                        break
                needs_display = False
                for y in range(matrix.numberOfRows()):
                    cell = matrix.cellAtRow_column_(y, 0)
                    path = cell.path().lower()
                    if path in self.pending_paths_to_invalidate:
                        new_state = NO if self.pending_paths_to_invalidate[path] else YES
                        if cell.isLeaf() != new_state:
                            TRACE('<> refreshing leaf state for %r' % (path,))
                            cell.setLeaf_(new_state)
                            cell.invalidateFolderTag()
                            needs_display = True
                            if cell == matrix.selectedCell():
                                self.browser.selectRow_inColumn_(y, x)
                                break

                if needs_display:
                    matrix.setNeedsDisplay_(YES)

        self.pending_paths_to_invalidate = {}

    @objc.typedSelector('v@:')
    @event_handler
    def removeInvalidationCallbacks(self):
        self.forest.clear_invalidate_ui_callback()
        self.forest.remove_remote_file_event_callback()

    def browser_isColumnValid_(self, browser, column):
        return YES

    def browser_createRowsForColumn_inMatrix_(self, browser, column, matrix):
        try:
            if column > 0:
                cell = browser.selectedCellInColumn_(column - 1)
                dir_children = self.forest.dir_children_for_path(cell.path())
            else:
                dir_children = self.forest.dir_children_for_path(self.forest.get_root_paths()[0])
            self.intelligentlyRefreshMatrix_withDirChildren_restoreSelection_(matrix, dir_children, False)
        except:
            unhandled_exc_handler()

    def browser_titleOfColumn_(self, browser, column):
        return ''

    def browser_shouldSizeColumn_forUserResize_toWidth_(self, browser, column, userResize, suggestedWidth):
        try:
            if self.forest.advanced_view:
                if self.default_width is None:
                    self.default_width = browser.frame().size.width / 3 - 1
                return self.default_width
            return browser.frame().size.width - 1
        except:
            unhandled_exc_handler()


class SelectiveSyncBrowser(NSBrowser):
    forest = ivar('forest')
    delegate = ivar('delegate')

    def __new__(cls):
        return SelectiveSyncBrowser.alloc().init()

    @event_handler
    def init(self):
        self = super(SelectiveSyncBrowser, self).initWithFrame_(NSZeroRect)
        if self is None:
            return
        self.setMatrixClass_(SelectiveSyncBrowserMatrix)
        self.setCellClass_(SelectiveSyncBrowserCell)
        return self

    def allowsTypeSelect(self):
        return YES

    def dealloc(self):
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            unhandled_exc_handler()

        super(SelectiveSyncBrowser, self).dealloc()

    @event_handler
    def viewWillMoveToWindow_(self, window):
        if not window:
            return
        notification_center = NSNotificationCenter.defaultCenter()
        notification_center.addObserver_selector_name_object_(self, 'windowChangedKeyNotification:', NSWindowDidBecomeKeyNotification, window)
        notification_center.addObserver_selector_name_object_(self, 'windowChangedKeyNotification:', NSWindowDidResignKeyNotification, window)

    @objc.typedSelector('v@:@')
    @event_handler
    def windowChangedKeyNotification_(self, notification):
        self.setNeedsDisplay_(YES)


class SelectiveSyncSheet(NSWindow):

    def __new__(cls, dropbox_app, initial_ignore_list = None, take_action = False, callback = None, remote = False):
        return SelectiveSyncSheet.alloc().initWithDropboxApp_initialIgnoreList_takeAction_callback_remote_(dropbox_app, initial_ignore_list, take_action, callback, remote)

    def initWithDropboxApp_initialIgnoreList_takeAction_callback_remote_(self, dropbox_app, initial_ignore_list, take_action, callback, remote):
        self = super(SelectiveSyncSheet, self).initWithContentRect_styleMask_backing_defer_(NSZeroRect, NSTitledWindowMask | NSClosableWindowMask | NSResizableWindowMask, NSBackingStoreBuffered, YES)
        if self is None:
            return
        try:
            self.innerView = SelectiveSyncView(dropbox_app, initial_ignore_list, take_action, callback, remote)
            self.contentView().addSubview_(self.innerView)
            self.setContentMinSize_(self.innerView.frame().size)
            self.setContentSize_(self.innerView.frame().size)
            self.setReleasedWhenClosed_(NO)
        except:
            unhandled_exc_handler()

        return self

    def beginSheetForWindow_(self, window):
        try:
            self.innerView.beginSheetForWindow_(window)
        except:
            unhandled_exc_handler()


class SelectiveSyncView(NSView):
    syncEngine = ivar('syncEngine')
    forest = ivar('forest')
    browser = ivar('browser')
    infoLabel = ivar('infoLabel')
    VERT_TEXT_SPACING = 14

    def __new__(cls, dropbox_app, initial_ignore_list = None, take_action = False, callback = None, remote = False):
        return SelectiveSyncView.alloc().initWithDropboxApp_initialIgnoreList_takeAction_callback_remote_(dropbox_app, initial_ignore_list, take_action, callback, remote)

    def initWithDropboxApp_initialIgnoreList_takeAction_callback_remote_(self, dropbox_app, initial_ignore_list, take_action, callback, remote):
        self = super(SelectiveSyncView, self).initWithFrame_(NSZeroRect)
        if self is None:
            return
        self._initial_ignore_list = initial_ignore_list
        self._callback = callback
        self._take_action = take_action
        self._remote = remote
        self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self._dropbox_app = dropbox_app
        self.initBrowser(self._remote)
        self.initButtons()
        f = NSFont.systemFontOfSize_(NSFont.smallSystemFontSize())
        self.infoLabel = NSTextField.createLabelWithText_font_(selsync_strings.info, f)
        self.addSubview_(self.infoLabel)
        self.reloadInvalidState()
        self.layoutForWidth_(DEFAULT_ADVANCED_WIDTH if self.forest.advanced_view else DEFAULT_SIMPLE_WIDTH)
        return self

    def initButtons(self):
        if not self.forest.advanced_view:
            self._switchButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.switch_to_advanced_view, self.switchToAdvancedView_)
        else:
            self._switchButton = None
        self._cancelButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.cancel_button, self.windowCancel_)
        self._cancelButton.setKeyEquivalent_(ESCAPE_KEY)
        self._okButton = self.addNormalRoundButtonWithTitle_action_(selsync_strings.window_ok_button, self.windowOk_)

    def initBrowser(self, remote):
        se = self._dropbox_app.sync_engine if not remote else self._dropbox_app.mbox.sync_engine
        self.forest = CachingLazySelectiveSyncUI(self._dropbox_app, se, self._dropbox_app.dropbox_url_info, use_tri_state_checks=True, initial_directory_ignore_set=self._initial_ignore_list)
        if self._dropbox_app.pref_controller['selsync_advanced_view_hint']:
            self.forest.advanced_view = True
        self.browser = SelectiveSyncBrowser()
        self.browser.setTitled_(NO)
        self.browser.setFocusRingType_(NSFocusRingTypeNone)
        self.browserDelegate = SelectiveSyncBrowserDelegate(self.browser, self.forest, self.reloadInvalidState)
        self.forest.set_invalidate_ui_callback(lambda events: AppHelper.callAfter(self.browserDelegate.invalidateUICallback_, events))
        self.browser.setDelegate_(self.browserDelegate)
        self.addSubview_(self.browser)

    def reloadInvalidState(self):
        if self.forest.invalid():
            self._okButton.setEnabled_(YES)
            self._okButton.setKeyEquivalent_(ENTER_KEY)
        else:
            self._okButton.setEnabled_(NO)

    def layoutForWidth_(self, width):
        height_needed = BOTTOM_BUTTON_BORDER
        button_row_height = 0
        button_row_width = 0
        if self._switchButton is not None:
            button_row_height = max(button_row_height, NSMaxY(self._switchButton.frame()))
            button_row_width += NSMaxX(self._switchButton.frame()) + HORIZ_BUTTON_BORDER
            self._switchButton.setFrameOrigin_(NSPoint(HORIZ_BUTTON_BORDER, height_needed))
        self._okButton.setFrameOrigin_(NSPoint(0, height_needed))
        button_row_height = max(button_row_height, NSMaxY(self._okButton.frame()))
        button_row_width += NSMaxX(self._okButton.frame()) + HORIZ_BUTTON_BORDER
        self._cancelButton.setFrameOrigin_(NSPoint(0, height_needed))
        button_row_height = max(button_row_height, NSMaxY(self._cancelButton.frame()))
        button_row_width += NSMaxX(self._cancelButton.frame()) + HORIZ_BUTTON_BORDER
        height_needed += button_row_height + NEARBY_CONTROL_BORDER
        width = max(width, button_row_width)
        self.browser.setFrame_(NSRect((0, height_needed), (width, DEFAULT_BROWSER_HEIGHT)))
        self.browser.setWidth_ofColumn_(width / (3 if self.forest.advanced_view else 1) - 1, -1)
        height_needed += self.browser.frame().size.height
        top_of_browser = height_needed
        height_needed += self.VERT_TEXT_SPACING
        height_needed += height_for_fixed_width(self.infoLabel, width)
        height_needed += self.VERT_TEXT_SPACING
        self.top_padding = height_needed - top_of_browser
        self.setFrameSize_(NSSize(width, height_needed))

    @event_handler
    def setFrameSize_(self, newSize):
        super(SelectiveSyncView, self).setFrameSize_(newSize)
        self._okButton.alignRightToOffset_(newSize.width - HORIZ_BUTTON_BORDER)
        self._cancelButton.alignRightToOffset_(newSize.width - HORIZ_BUTTON_BORDER - self._okButton.frame().size.width - HORIZ_BUTTON_SPACING)
        self.browser.setFrameSize_(NSSize(newSize.width, newSize.height - self.browser.frame().origin.y - self.top_padding))
        self.infoLabel.setFrameOrigin_(NSPoint(0, newSize.height - self.VERT_TEXT_SPACING - self.infoLabel.frame().size.height))
        align_center_to_offset(self.infoLabel, newSize.width / 2)

    @event_handler
    def resizeWithOldSuperviewSize_(self, oldBoundsSize):
        new_size = self.superview().frame().size
        self.setFrameSize_(new_size)
        if not self.forest.advanced_view:
            self.browser.setWidth_ofColumn_(new_size.width - 1, 0)

    @objc.typedSelector('v@:@i@')
    @event_handler
    def selsyncSheetDidEnd_returnCode_contextInfo_(self, sheet, returnCode, contextInfo):
        sheet.orderOut_(self)

    @objc.typedSelector('v@:@')
    @event_handler
    def beginSheetForWindow_(self, window):
        self.relevantWindow = window
        NSApp().beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(self.window(), self.relevantWindow, self, self.selsyncSheetDidEnd_returnCode_contextInfo_.selector, 0)

    @objc.typedSelector('v@:@')
    @event_handler
    def switchToAdvancedView_(self, sender):
        self._switchButton.removeFromSuperview()
        self._switchButton = None
        current_frame = self.window().frame()
        if current_frame.size.width < DEFAULT_ADVANCED_WIDTH:
            diff = DEFAULT_ADVANCED_WIDTH - current_frame.size.width
            current_frame.size.width = DEFAULT_ADVANCED_WIDTH
            current_frame.origin.x -= diff / 2
            self.window().setFrame_display_animate_(current_frame, YES, YES)
        self.browser.setWidth_ofColumn_(DEFAULT_ADVANCED_WIDTH / 3 - 1, 0)
        self.browser.setWidth_ofColumn_(DEFAULT_ADVANCED_WIDTH / 3 - 1, -1)
        self.forest.set_advanced_view(True)
        self.browserDelegate.browser_reloadAdvancedView_(self.browser, True)
        self.browser.loadColumnZero()

    @objc.typedSelector('v@:@')
    @event_handler
    def windowOk_(self, sender):
        assert self.forest.invalid(), "button shouldn't have been clickable"
        NSApp().endSheet_(self.window())
        if self.forest.advanced_view:
            self._dropbox_app.pref_controller.update({'selsync_advanced_view_hint': True})
        if self._take_action:
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(self.relevantWindow, selsync_strings.confirmation_caption, self.forest.get_confirmation_message(), self.confirmationOkay, self.confirmationCancel, selsync_strings.confirmation_ok_button, selsync_strings.cancel_button)
        else:
            self.endShowSheet()
        if self._callback:
            self._callback(self)

    @objc.typedSelector('v@:@')
    @event_handler
    def windowCancel_(self, sender):
        NSApp().endSheet_(self.window())
        self.endShowSheet()

    @objc.typedSelector('v@:')
    @event_handler
    def confirmationCancel(self):
        self.beginSheetForWindow_(self.relevantWindow)

    @objc.typedSelector('v@:')
    @event_handler
    def confirmationOkay(self):
        self._take_action(True)
        message_sender(spawn_thread_with_name('PREP_SELSYNC'), on_success=message_sender(AppHelper.callAfter)(self.prepSelsyncFinishedWithFailures_), on_exception=message_sender(AppHelper.callAfter)(self.prepSelsyncFinishedWithException_andExcInfo_), block=False, handle_exceptions=True, dont_post=lambda : False)(self.browserDelegate.forest.write_changes_to_sync_engine)(self._dropbox_app.sync_engine if not self._remote else self._dropbox_app.mbox.sync_engine)
        self.endShowSheet()

    @objc.typedSelector('v@:')
    @event_handler
    def endShowSheet(self):
        self.browserDelegate.removeInvalidationCallbacks()

    @objc.typedSelector('v@:@')
    @event_handler
    def prepSelsyncFinishedWithFailures_(self, failures):
        self._take_action(False)
        if failures:
            DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_(None, selsync_strings.unignore_error_caption, failed_unignores_message_from_failures(failures, self._dropbox_app.default_dropbox_path), lambda : None, None)

    @objc.typedSelector('v@:@@')
    @event_handler
    def prepSelsyncFinishedWithException_andExcInfo_(self, exc, exc_info):
        self._take_action(False)
        DropboxSheetErrorFactory.sharedInstance().alertForWindow_withCaption_message_onSuccess_onCancel_successLabel_cancelLabel_(None, selsync_strings.really_bad_error_caption, selsync_strings.really_bad_error_message, lambda : None, None, selsync_strings.really_bad_error_button, None)

    def ignoreList(self):
        return self.forest.current_directory_ignore_set


class SelectiveSyncLauncher(NSView):

    def __new__(cls, dropbox_app, take_action = True, hide_text = False, width = 0):
        return cls.alloc().initWithDropboxApp_takeAction_hideText_width_(dropbox_app, take_action, hide_text, width)

    @objc.typedSelector('v@:@@@@')
    @event_handler
    def initWithDropboxApp_takeAction_hideText_width_(self, dropbox_app, take_action, hide_text, width):
        self = super(SelectiveSyncLauncher, self).initWithFrame_(NSZeroRect)
        if self is None:
            return
        self._dropbox_app = dropbox_app
        self._action = None
        self._take_action = take_action
        self.current_ignore_list = None
        self._width = width
        self.listingProgress = None
        if not hide_text:
            self.info_label = NSTextField.createLabelWithText_(selsync_strings.prefs_launch_label)
            self.addSubview_(self.info_label)
        else:
            self.info_label = None
        self.launch_button = self.addNormalRoundButtonWithTitle_action_(selsync_strings.prefs_launch_button, self.launch_)
        self.setEnabled_(self._dropbox_app.ui_kit.post_link)
        self.sizeToFit()
        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def launch_(self, sender):
        self.showSelectiveSyncSheet()

    @objc.typedSelector('v@:c')
    @event_handler
    def setEnabled_(self, enabled):
        self.launch_button.setEnabled_(enabled)

    @objc.typedSelector('v@:c')
    @event_handler
    def setBusy_(self, busy):
        self.launch_button.setTitle_(selsync_strings.prefs_working_button if busy else selsync_strings.prefs_launch_button)
        self.launch_button.setEnabled_(not busy)

    @objc.typedSelector('v@:')
    @event_handler
    def endShowSheet(self):
        pass

    @objc.typedSelector('v@:')
    @event_handler
    def beginShowSheet(self):
        pass

    @event_handler
    @objc.typedSelector('v@:')
    def showSelectiveSyncSheet(self):
        TRACE('showing user selective sync')
        self.beginShowSheet()
        ignore_list = self.current_ignore_list if not self._take_action else None
        self.selectiveSyncSheet = SelectiveSyncSheet(self._dropbox_app, initial_ignore_list=ignore_list, take_action=self._take_action and self.setBusy_, callback=self.sheetCallback_)
        self.selectiveSyncSheet.beginSheetForWindow_(self.window())

    @objc.typedSelector('v@:f')
    @event_handler
    def sizeToFit(self):
        height_needed = 0
        if self.info_label:
            self.info_label.setFrameOrigin_(NSPoint(0, height_needed + STATICTEXT_TO_BUTTON_BASELINE_ADJUSTMENT))
            if self._width:
                self.info_label.wrapToWidth_(self._width - self.launch_button.frame().size.width)
            total_size = self.info_label.placeButtonToRight(self.launch_button)
        else:
            total_size = self.launch_button.frame().size
        self.setFrameSize_(total_size)
        return total_size

    def sheetCallback_(self, sheet):
        self.current_ignore_list = sheet.ignoreList()
        if self._action:
            self._action(self)

    def setAction_(self, action):
        self._action = action
