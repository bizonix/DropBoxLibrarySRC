#Embedded file name: ui/cocoa/tray_icon.py
from __future__ import with_statement, absolute_import
import itertools
import os
import objc
from AppKit import NSAlternateKeyMask, NSCompositeSourceOver, NSImage, NSNotificationCenter, NSRunLoop, NSStatusBar, NSTimer, NSToolTipManager, NSUserDefaults, NSView, NSWindowDidMoveNotification
from Foundation import NSDefaultRunLoopMode, NSMakeRect, NSMakeSize, NSZeroRect
from PyObjCTools import AppHelper
try:
    from Quartz import CGPoint, CGRect, CGSize
except ImportError:
    pass

try:
    from Quartz import CAAnimationGroup, CAKeyframeAnimation, CALayer, CAMediaTimingFunction, kCAMediaTimingFunctionEaseOut
except ImportError:
    pass

import arch
import build_number
from build_number import BUILD_KEY
from dropbox.build_common import get_icon_suffix, ICON_SUFFIX_LEOPARD, ICON_SUFFIX_LEOPARD_INV
from dropbox.gui import assert_message_queue, event_handler, message_sender
from dropbox.i18n import trans
from dropbox.mac.internal import get_resources_dir
from dropbox.mac.version import LEOPARD, MAC_VERSION
from dropbox.trace import TRACE, unhandled_exc_handler
from ui.cocoa.dropbox_menu import DropboxNSMenu
from ui.cocoa.util import CocoaSettings
from ui.common.tray import TrayController

class TrayIconView(NSView):
    ICON_MAP = {TrayController.IDLE: 'idle',
     TrayController.BUSY: 'busy',
     TrayController.CONNECTING: 'logo',
     TrayController.BROKEN: 'x',
     TrayController.CAM: 'cam',
     TrayController.PAUSED: 'pause'}
    ICON_SUFFIX = get_icon_suffix(BUILD_KEY)
    ICON_RECT = NSMakeRect(4, 2, 18, 18)
    BADGE_WIDTH = BADGE_HEIGHT = 10

    @message_sender(AppHelper.callAfter, block=True)
    def __new__(cls, tray_icon, using_xui):
        return TrayIconView.alloc().initWithTrayIcon_usingXUI_(tray_icon, using_xui)

    def initWithTrayIcon_usingXUI_(self, tray_icon, using_xui):
        self = super(TrayIconView, self).init()
        if self is None:
            return
        try:
            defaults = NSUserDefaults.standardUserDefaults()
            if defaults.boolForKey_('NSGrayBackground'):
                defaults.setBool_forKey_(0, 'NSGrayBackground')
                assert not defaults.boolForKey_('NSGrayBackground'), "User has NSGrayBackground set in their defaults, and changing it didn't work"
        except Exception:
            unhandled_exc_handler()

        try:
            self.canDisplayBadgeCount = using_xui
            self.badgeCount = 0
            self.shouldDrawAttentionRequest = False
            self.setupImages()
            self.setupLayers()
            self.tray_icon = tray_icon
            self.tray_icon_has_images = True
            self.menu_is_visible = False
            self.flashing_state = None
            self.flash_timer = None
            self.busy_timer = None
            self._menu = None
            self.updateIcon_(TrayController.CONNECTING)
            self.updateMenu_(())
            try:
                self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(self.desiredWidth())
            except Exception:
                try:
                    defaults = NSUserDefaults.standardUserDefaults()
                except Exception:
                    unhandled_exc_handler()
                else:
                    if defaults.boolForKey_('NSGrayBackground'):
                        raise Exception("User has NSGrayBackground set in their defaults (and we couldn't fix it to not affect the NSStatusItem)")
                    else:
                        raise

                unhandled_exc_handler()
            else:
                self.status_item.setView_(self)
                NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, self.windowDidMove_, NSWindowDidMoveNotification, self.window())

        except Exception:
            self.tray_icon_has_images = False
            unhandled_exc_handler()

        return self

    def dealloc(self):
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            unhandled_exc_handler()

        super(TrayIconView, self).dealloc()

    @objc.typedSelector('v@:')
    def setupLayers(self):
        resources_dir = get_resources_dir() if hasattr(build_number, 'frozen') else u'images/status'
        badgePath = os.path.join(resources_dir, 'notification-badge.tiff')
        self.badgeImage = NSImage.alloc().initWithContentsOfFile_(badgePath)
        self.overlayLayer = None
        self.badgeRect = NSMakeRect(self.ICON_RECT.origin.x + self.ICON_RECT.size.width - self.BADGE_WIDTH, self.ICON_RECT.origin.y, self.BADGE_WIDTH, self.BADGE_HEIGHT)
        if not CocoaSettings.is_accelerated_compositing_supported():
            return
        self.setWantsLayer_(objc.YES)
        layer = self.layer()
        overlayPosition = CGPoint(self.ICON_RECT.origin.x + self.ICON_RECT.size.width - self.BADGE_WIDTH / 2.0, self.ICON_RECT.origin.y + self.BADGE_HEIGHT)
        overlayRect = CGRect(CGPoint(0, 0), CGSize(self.BADGE_WIDTH, self.BADGE_HEIGHT))
        self.overlayLayer = overlayLayer = CALayer.layer()
        overlayLayer.setBounds_(overlayRect)
        overlayLayer.setPosition_(overlayPosition)
        overlayLayer.setContents_(self.badgeImage)
        overlayLayer.setAnchorPoint_(CGPoint(0.5, 1.0))
        overlayLayer.setHidden_(True)
        self.appearAnimation = CAAnimationGroup.animation()
        self.appearAnimation.setDuration_(2)
        self.appearAnimation.setRepeatCount_(1)
        animations = []
        scale = CAKeyframeAnimation.animationWithKeyPath_('transform.rotation.z')
        scale.setDuration_(0.825)
        scale.setKeyTimes_((0, 0.2, 0.4, 0.6, 0.8, 1.0))
        scale.setValues_((0, 0.34906585, -0.34906585, 0.261799388, -0.261799388, 0))
        scale.setRemovedOnCompletion_(True)
        scale.setTimingFunction_(CAMediaTimingFunction.functionWithName_(kCAMediaTimingFunctionEaseOut))
        animations.append(scale)
        self.appearAnimation.setAnimations_(animations)
        layer.addSublayer_(overlayLayer)

    @objc.typedSelector('v@:')
    def setupImages(self):
        resources_dir = get_resources_dir() if hasattr(build_number, 'frozen') else u'images/status'
        try:
            self.blank_icon = NSImage.alloc().initWithSize_(NSMakeSize(18, 18))
            self.blank_icon.lockFocus()
            self.blank_icon.unlockFocus()
        except Exception:
            unhandled_exc_handler()

        try:
            path = os.path.join(resources_dir, 'dropboxstatus-glow-lep.tiff')
            self.leopard_glow = NSImage.alloc().initWithContentsOfFile_(path)
        except Exception:
            unhandled_exc_handler()

        self.color_icons = {}
        self.leopard_icons = {}
        self.leopard_alternate_icons = {}

        def load_class(container, suffix, icon_keys):
            file_name = 'dropboxstatus-%s%s.%s'
            path = os.path.join(resources_dir, file_name)
            for key in icon_keys:
                effective_path = path % (key, suffix, 'tiff')
                try:
                    image = NSImage.alloc().initWithContentsOfFile_(effective_path)
                except Exception:
                    TRACE('!! No suitable image could be found for key "%s" at %r', key, effective_path)
                else:
                    container[key] = image

            TRACE('Loaded %r icons for class %r!', len(container), suffix if suffix else 'default')

        default_icons = ('logo', 'idle', 'busy', 'busy2', 'busy3', 'busy4', 'x', 'cam', 'cam2', 'cam3', 'cam4', 'pause')
        load_class(self.color_icons, self.ICON_SUFFIX, default_icons)
        load_class(self.leopard_icons, ICON_SUFFIX_LEOPARD, default_icons)
        load_class(self.leopard_alternate_icons, ICON_SUFFIX_LEOPARD_INV, default_icons)

    @objc.typedSelector('v@:')
    @event_handler
    def refreshStatusImage(self):
        self.updateStatusImage_((self.current_target,))

    @objc.typedSelector('v@:@')
    @event_handler
    def updateStatusImage_(self, timer):
        if isinstance(timer, tuple):
            target_image = timer[0]
        elif isinstance(timer, NSTimer):
            target_image = timer.userInfo()[0]
        use_leopard_icons = self.tray_icon.app.pref_controller['leopard_icons']
        if target_image == 'busy':
            target_image = self.busy_timer_image
            if self.busy_timer_state == 5:
                self.busy_timer_state = 1
                self.current_target = target_image
            else:
                self.current_target = '%s%d' % (target_image, self.busy_timer_state)
            self.busy_timer_state += 1
        elif target_image == 'flash':
            self.flashing_state = not self.flashing_state
        else:
            self.current_target = target_image
        self.shouldDrawAttentionRequest = False
        if target_image != 'flash' or self.flashing_state:
            render_attention = self.canDisplayBadgeCount and self.badgeCount
            if render_attention:
                if use_leopard_icons:
                    self.no_highlight_image = self.leopard_glow
                    self.highlight_image = self.leopard_alternate_icons['idle']
                else:
                    self.no_highlight_image = self.highlight_image = self.color_icons['logo']
                    self.shouldDrawAttentionRequest = True
            elif use_leopard_icons:
                self.no_highlight_image = self.leopard_icons[self.current_target]
                self.highlight_image = self.leopard_alternate_icons[self.current_target]
            else:
                self.no_highlight_image = self.highlight_image = self.color_icons[self.current_target]
        if self.overlayLayer is not None:
            self.overlayLayer.setHidden_(not self.shouldDrawAttentionRequest)
        self.setNeedsDisplay_(1)

    @objc.typedSelector('v@:B')
    @event_handler
    def setFlash_(self, on):
        if on and self.flash_timer is None:
            self.flashing_state = True
            self.flash_timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(0.5, self, self.updateStatusImage_, ('flash',), True)
            self.flash_timer.fire()
            NSRunLoop.currentRunLoop().addTimer_forMode_(self.flash_timer, NSDefaultRunLoopMode)
        elif not on and self.flashing_state is not None:
            if self.flash_timer is not None:
                self.flash_timer.invalidate()
                self.flash_timer = None
                self.flashing_state = None
                self.setNeedsDisplay_(1)

    @objc.typedSelector('v@:')
    def triggerPing(self):
        if self.overlayLayer is not None:
            self.overlayLayer.removeAnimationForKey_('appearAnimation')
            self.overlayLayer.addAnimation_forKey_(self.appearAnimation, 'appearAnimation')

    @objc.typedSelector('v@:B')
    def setCanDisplayBadgeCount_(self, value):
        self.canDisplayBadgeCount = value
        self.refreshStatusImage()

    @objc.typedSelector('v@:B')
    def setBadgeCount_(self, value):
        self.badgeCount = value

    @objc.typedSelector('v@:@')
    @event_handler
    def updateIcon_(self, icon_state):
        target_image = self.ICON_MAP.get(icon_state)
        assert target_image is not None, 'invalid icon state'
        if target_image in ('busy', 'cam'):
            self.busy_timer_image = target_image
            if self.busy_timer is None:
                self.busy_timer_state = 5
                self.busy_timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(0.4, self, self.updateStatusImage_, ('busy',), True)
                self.busy_timer.fire()
                NSRunLoop.currentRunLoop().addTimer_forMode_(self.busy_timer, NSDefaultRunLoopMode)
        else:
            if self.busy_timer is not None:
                self.busy_timer.invalidate()
                self.busy_timer = None
            self.updateStatusImage_((target_image,))

    @objc.typedSelector('v@:@')
    @event_handler
    def updateMenu_(self, opts):
        self._menu = DropboxNSMenu.menuWithDropboxMenuDescriptor_(itertools.chain(opts, ((trans(u'Quit %s') % BUILD_KEY, arch.util.hard_exit),)))
        self._menu.setDelegate_(self)

    @objc.typedSelector('v@:')
    @event_handler
    def showMenu(self):
        self.status_item.popUpStatusItemMenu_(self._menu)

    @event_handler
    def mouseDown_(self, theEvent):
        option_pressed = theEvent.modifierFlags() & NSAlternateKeyMask
        self.tray_icon.app.ui_kit.show_tray_popup(context_menu=option_pressed)

    @event_handler
    def rightMouseDown_(self, theEvent):
        self.tray_icon.app.ui_kit.show_tray_popup()

    @event_handler
    def drawRect_(self, dirtyRect):
        self.status_item.drawStatusBarBackgroundInRect_withHighlight_(self.bounds(), self.menu_is_visible)
        if self.flashing_state is False and not self.menu_is_visible:
            draw_image = None
        elif self.menu_is_visible:
            draw_image = self.highlight_image
        else:
            draw_image = self.no_highlight_image
        if draw_image is not None:
            draw_image.drawInRect_fromRect_operation_fraction_(self.ICON_RECT, NSZeroRect, NSCompositeSourceOver, 1.0)
        if self.shouldDrawAttentionRequest and self.overlayLayer is None:
            self.badgeImage.drawInRect_fromRect_operation_fraction_(self.badgeRect, NSZeroRect, NSCompositeSourceOver, 1.0)
        super(TrayIconView, self).drawRect_(dirtyRect)

    @objc.typedSelector('f@:')
    @event_handler
    def desiredWidth(self):
        return self.blank_icon.size().width + 8

    @objc.typedSelector('f@:')
    @event_handler
    def hide(self):
        TRACE('Hiding status item')
        NSStatusBar.systemStatusBar().removeStatusItem_(self.status_item)

    def menuWillOpen_(self, menu):
        if self.tray_icon.app and menu is not None:
            self.tray_icon.app.event.report('tray-menu')
        if MAC_VERSION >= LEOPARD:
            tool_tip_manager = NSToolTipManager.sharedToolTipManager()
            if tool_tip_manager.isRegularToolTipVisible():
                tool_tip_manager.orderOutToolTip()
            else:
                tool_tip_manager.abortToolTip()
        self.menu_is_visible = True
        self.setNeedsDisplay_(1)

    def menuDidClose_(self, menu):
        self.menu_is_visible = False
        self.setNeedsDisplay_(1)

    def windowDidMove_(self, notification):
        rect = self.windowRect()
        self.tray_icon.app.ui_kit.move_tray_popup(rect)

    def windowRect(self):
        frame = self.window().frame()
        return (frame.origin.x,
         frame.origin.y,
         frame.size.width,
         frame.size.height)


class TrayIcon(object):

    def __init__(self, app):
        self.app = app
        self.icon_state = TrayController.CONNECTING
        self.initial_menu = None
        self.status_item_view = None
        self.initial_tooltip = None
        disable_handler = lambda *args, **kwargs: self.disable()
        self.app.add_quit_handler(disable_handler)

    @assert_message_queue
    def enable(self, cocoa_ui_kit):
        TRACE('Initializing tray icon')
        try:
            self.app.pref_controller.add_pref_callback('leopard_icons', lambda *args, **kwargs: self._on_icon_class_changed())
        except Exception:
            unhandled_exc_handler()

        self.status_item_view = TrayIconView(self, cocoa_ui_kit.using_xui)
        try:
            cocoa_ui_kit.tray_popup.setMenuDelegate_(self.status_item_view)
        except AttributeError:
            pass

        if self.initial_tooltip is not None:
            self.status_item_view.setToolTip_(self.initial_tooltip)
            self.initial_tooltip = None
        if self.icon_state is not None:
            self.status_item_view.updateIcon_(self.icon_state)
        if self.initial_menu is not None:
            self.status_item_view.updateMenu_(self.initial_menu)
            self.initial_menu = None

    @assert_message_queue
    def disable(self):
        TRACE('Disabling tray icon')
        if self.status_item_view is not None:
            self.status_item_view.hide()

    def get_screen_rect(self):
        if self.status_item_view.tray_icon_has_images:
            return self.status_item_view.windowRect()

    @message_sender(AppHelper.callAfter)
    def _on_icon_class_changed(self):
        if self.status_item_view is not None and self.icon_state is not None:
            self.status_item_view.updateIcon_(self.icon_state)

    @message_sender(AppHelper.callAfter)
    def update_tray_icon(self, icon_state = None, tooltip = None, flashing = None, badge_count = 0, trigger_ping = False):
        can_update = self.status_item_view is not None
        if can_update and flashing is not None:
            self.status_item_view.setFlash_(flashing)
        if can_update and trigger_ping:
            self.status_item_view.triggerPing()
        if can_update:
            self.status_item_view.setBadgeCount_(badge_count)
        if icon_state is not None:
            self.icon_state = icon_state
            if can_update:
                self.status_item_view.updateIcon_(self.icon_state)
        if tooltip is not None:
            long_tooltip = tooltip[1]
            if can_update:
                self.status_item_view.setToolTip_(long_tooltip)
            else:
                self.initial_tooltip = long_tooltip

    @message_sender(AppHelper.callAfter)
    def update_tray_menu(self, menu):
        if self.status_item_view and self.status_item_view.tray_icon_has_images:
            self.status_item_view.updateMenu_(menu)
        else:
            self.initial_menu = menu

    @message_sender(AppHelper.callAfter)
    def show_tray_menu(self):
        if self.status_item_view:
            self.status_item_view.showMenu()

    @message_sender(AppHelper.callAfter)
    def disable_badge_count(self):
        if self.status_item_view:
            self.status_item_view.setCanDisplayBadgeCount_(False)
