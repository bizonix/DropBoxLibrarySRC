#Embedded file name: ui/wxpython/camera.py
from __future__ import absolute_import
import cStringIO
import os
import re
import sys
import threading
import time
import wx
import arch
from ..common.camera import CameraStrings, CameraUI, rect_to_centered_square
from ..common.misc import MiscStrings
from ..common.preferences import pref_strings
from .constants import platform, Colors
from .dialogs import DropboxModalDialog, WxSplashDialog, WxSplashButtonPanel, make_line
from .dropbox_controls import TransparentPanel
from .static_link_text import StaticLinkText
from dropbox.gui import TimedThrottler, assert_message_queue, event_handler, message_sender
from dropbox.trace import unhandled_exc_handler
from ui.images import wximages as Images
if sys.platform.startswith('win'):
    from .dialogs import UACButton
    from dropbox.win32.version import WIN7, WIN8, WINDOWS_VERSION, VISTA

class WxCameraSplashFrame(WxSplashDialog):
    ALWAYS_SIZE = 10
    ALWAYS_PADDING = 27.5
    ALWAYS_CHECK_PADDING = 10
    ALWAYS_MAX_WIDTH = 545
    PATTERN_BOLD_TAG = '<b>|</b>'

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, device, start_cb, cancel_cb, never_cb, never_text, always_text, always_initial = True, always_enabled = True, always_tip_text = None):
        self._device = device
        self._start_cb = start_cb
        self._cancel_cb = cancel_cb
        self._never_cb = never_cb
        self._always_text = always_text
        self._always_initial = always_initial
        self._always_enabled = always_enabled
        self._always_tip_text = always_tip_text
        callbacks = ((wx.ID_OK,
          CameraStrings.splash_start_button,
          self.handle_start,
          True), (wx.ID_CANCEL,
          CameraStrings.splash_cancel_button,
          self.handle_cancel,
          False))
        if never_text and never_cb:
            left_callbacks = ((wx.ID_ANY,
              never_text,
              self.handle_never,
              False),)
        else:
            left_callbacks = None
        super(WxCameraSplashFrame, self).__init__(title=CameraStrings.splash_title, image=Images.CameraSplashDrawing, header=CameraStrings.splash_heading, subheader=CameraStrings.splash_subheading, left_callbacks=left_callbacks, callbacks=callbacks)
        self.Bind(wx.EVT_CLOSE, self.handle_close)

    @event_handler
    def handle_close(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Destroy()
        self._cancel_cb(self._device)

    @event_handler
    def handle_start(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._start_cb(self._device, always=self.always_checkbox.IsChecked())

    @event_handler
    def handle_cancel(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._cancel_cb(self._device)

    @event_handler
    def handle_never(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._never_cb(self._device)

    @assert_message_queue
    def _init_elems(self, parent, sizer):
        super(WxCameraSplashFrame, self)._init_elems(parent, sizer)
        always_font = platform.get_tour_font(parent, self.ALWAYS_SIZE)
        always_font.SetWeight(wx.FONTWEIGHT_NORMAL)
        always_font_bold = platform.get_tour_font(parent, self.ALWAYS_SIZE)
        always_font_bold.SetWeight(wx.FONTWEIGHT_BOLD)
        sizer.Add((0, self.ALWAYS_PADDING))
        checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
        always_checkbox = wx.CheckBox(parent, style=wx.CHK_2STATE)
        always_checkbox.SetFont(always_font)
        always_checkbox.SetValue(self._always_initial)
        always_checkbox.Show(self._always_enabled)
        if self._always_tip_text:
            always_checkbox.SetToolTip(wx.ToolTip(self._always_tip_text))
        checkbox_sizer.Add(always_checkbox, border=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.TOP)
        self.always_checkbox = always_checkbox
        checkbox_sizer.Add((self.ALWAYS_CHECK_PADDING, 0))
        test_label = wx.StaticText(parent, label=self._always_text)
        test_label.SetFont(always_font)
        if test_label.Size[0] > self.ALWAYS_MAX_WIDTH:
            self._always_text = CameraStrings.splash_always_import_no_name
        parts = re.split(self.PATTERN_BOLD_TAG, self._always_text)
        for i, text in enumerate(parts):
            if i == 0:
                label = test_label
            else:
                label = wx.StaticText(parent)
            label.SetLabel(text)
            label.SetForegroundColour(Colors.camera_font)
            label.SetFont(always_font_bold if i % 2 else always_font)
            if self._always_tip_text:
                label.SetToolTip(wx.ToolTip(self._always_tip_text))
            label.Show(self._always_enabled)
            if self._always_enabled:

                def left_button_up(event):
                    always_checkbox.SetValue(not always_checkbox.IsChecked())

                label.Bind(wx.EVT_LEFT_UP, left_button_up)
            checkbox_sizer.Add(label)

        sizer.Add(checkbox_sizer, flag=wx.CENTER)


class WxQuotaSplashFrame(WxSplashDialog):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, upgrade_cb, cancel_cb, cancel_text, files_imported_label, quota_message):
        self._upgrade_cb = upgrade_cb
        self._cancel_cb = cancel_cb
        callbacks = ((wx.ID_ANY,
          CameraStrings.quota_more_space_button,
          self.handle_upgrade,
          True), (wx.ID_CANCEL,
          cancel_text,
          self.handle_cancel,
          False))
        super(WxQuotaSplashFrame, self).__init__(title=CameraStrings.splash_title, image=Images.CameraQuotaSplash, header=CameraStrings.quota_heading, subheader=quota_message, callbacks=callbacks, progress_text=files_imported_label)
        self.Bind(wx.EVT_CLOSE, self.handle_close)

    @event_handler
    def handle_close(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Destroy()
        self._cancel_cb()

    @event_handler
    def handle_upgrade(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._upgrade_cb()

    @event_handler
    def handle_cancel(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._cancel_cb()


class WxGalleryImporterSplashFrame(WxSplashDialog):

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, import_cb, never_cb, cancel_cb):
        self._import_cb = import_cb
        self._cancel_cb = cancel_cb
        self._never_cb = never_cb
        callbacks = ((wx.ID_OK,
          CameraStrings.gallery_import_start_button,
          self.handle_import,
          True), (wx.ID_CANCEL,
          CameraStrings.gallery_import_later_button,
          self.handle_cancel,
          False))
        left_callbacks = ((wx.ID_ANY,
          CameraStrings.gallery_import_never_button,
          self.handle_never,
          False),)
        super(WxGalleryImporterSplashFrame, self).__init__(title=CameraStrings.gallery_import_title, image=Images.CameraSplashDrawing, header=CameraStrings.gallery_import_heading, subheader=CameraStrings.gallery_import_subheading, left_callbacks=left_callbacks, callbacks=callbacks)
        self.Bind(wx.EVT_CLOSE, self.handle_close)

    @event_handler
    def handle_close(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Destroy()
        self._cancel_cb()

    @event_handler
    def handle_import(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._import_cb()

    @event_handler
    def handle_cancel(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._cancel_cb()

    @event_handler
    def handle_never(self, event):
        self.Unbind(wx.EVT_CLOSE)
        self.Close()
        self._never_cb()


class WxCameraUI(CameraUI):

    def __init__(self, **kw):
        super(WxCameraUI, self).__init__(**kw)
        self.window_controller = None

    def generate_never_text(self, never_ever, old_action):
        if never_ever:
            return CameraStrings.splash_never_ever_button
        else:
            return CameraStrings.splash_never_button

    @message_sender(wx.CallAfter, block=True)
    def ask_user(self, device, start_cb, cancel_cb, never_cb, old_action, always_state, never_ever):
        is_sd_card = isinstance(device, arch.photouploader.sdcarddevice.SDCardDevice)
        if is_sd_card:
            always_text = CameraStrings.splash_always_import_removable
        elif device.name or device.model:
            always_text = CameraStrings.splash_always_import % dict(name=device.name or device.model)
        else:
            always_text = CameraStrings.splash_always_import_no_name
        always_enabled = True
        always_tooltip = None
        always_initial = always_state
        if not device.is_trackable():
            always_enabled = False
            always_tooltip = CameraStrings.splash_always_import_disabled
            always_initial = False
        if WINDOWS_VERSION < VISTA and (not arch.util.is_admin() or is_sd_card):
            always_enabled = False
        if WINDOWS_VERSION in (WIN7, WIN8):
            never_text = self.generate_never_text(never_ever, old_action)
        else:
            never_text = self.generate_never_text(False, old_action)
        splash = WxCameraSplashFrame(device, start_cb, cancel_cb, never_cb, never_text, always_text, always_initial, always_enabled, always_tooltip)
        splash.Show(True)

    @message_sender(wx.CallAfter)
    def call_later(self, seconds, fn, *args, **kwargs):
        wx.CallLater(seconds * 1000, fn, args, kwargs)

    @message_sender(wx.CallAfter)
    def progress_window_hide(self):
        if self.window_controller:
            self.window_controller.Hide()
        self.showing_bubbles = True

    @message_sender(wx.CallAfter)
    def progress_window_show(self):
        self.showing_bubbles = False
        if not self.window_controller:
            self.window_controller = WxCameraProgressBarFrame(self)
        self.window_controller.Unhide()
        self.window_controller.Raise()

    @message_sender(wx.CallAfter)
    def prompt_sel_sync(self, on_enable, on_disable, on_cancel):
        dlg = DropboxModalDialog(None, title=CameraStrings.splash_title, caption=CameraStrings.sel_sync_question, message=CameraStrings.sel_sync_message, buttons=[CameraStrings.sel_sync_no, CameraStrings.sel_sync_enable])
        ret = dlg.show_modal()
        if ret == 1:
            on_enable()
        else:
            on_cancel()

    @message_sender(wx.CallAfter, block=True)
    def out_of_space_show(self, upgrade_cb, cancel_cb, cancel_text, never_cb, never_text, quota_message, files_imported_label = None):
        splash = WxQuotaSplashFrame(upgrade_cb, cancel_cb, cancel_text, files_imported_label, quota_message)
        splash.Show(True)

    @message_sender(wx.CallAfter)
    def error_dialog(self, caption, message = '', okay_caption = None):
        if okay_caption is None:
            okay_caption = MiscStrings.ok_button
        dlg = DropboxModalDialog(None, title='', caption=caption, message=message, buttons=[okay_caption])
        dlg.show_modal()


class CameraThumbnailResizer(threading.Thread):
    MAX_PHOTO_THUMBNAIL_SIZE = 20971520
    THUMBNAIL_TIMEOUT = 2

    def __init__(self, progress_bar, format_thumbnail):
        super(CameraThumbnailResizer, self).__init__(name='CAMERATHUMBNAIL')
        self.progress_bar = progress_bar
        self.last_resized_path = None
        self.last_shown_path = None
        self.next_photo_path = None
        self.thumbnail = None
        self.format_thumbnail = format_thumbnail
        self.last_photo_time = 0
        self.start()

    def run(self):
        try:
            while self.progress_bar._running:
                with self.progress_bar._thumbnail_cond:
                    self.progress_bar._thumbnail_cond.wait()
                    self.next_photo_path = self.progress_bar.next_photo_path
                if time.time() - self.last_photo_time < self.THUMBNAIL_TIMEOUT:
                    continue
                if self.last_resized_path != self.last_shown_path:
                    if self.thumbnail and self.thumbnail.Ok():
                        self.update_progress_bar(self.thumbnail, self.last_resized_path)
                if self.last_resized_path != self.next_photo_path:
                    stream = None
                    with open(self.next_photo_path, 'rb') as f:
                        f.seek(0, 2)
                        if f.tell() <= self.MAX_PHOTO_THUMBNAIL_SIZE:
                            f.seek(0, 0)
                            stream = cStringIO.StringIO(f.read())
                    if stream:
                        thumbnail = wx.EmptyImage(1, 1)
                        nolog = wx.LogNull()
                        thumbnail.LoadStream(stream, wx.BITMAP_TYPE_ANY)
                        del nolog
                        if thumbnail.Ok():
                            self.thumbnail = self.format_thumbnail(thumbnail)
                            if self.thumbnail is not None:
                                self.last_resized_path = self.next_photo_path
                                self.update_progress_bar(self.thumbnail, self.last_resized_path)

        except Exception:
            unhandled_exc_handler()

    def update_progress_bar(self, thumbnail, path):
        if self.progress_bar._visible:
            wx.CallAfter(self.progress_bar.thumbnail_image.SetBitmap, thumbnail)
            self.last_photo_time = time.time()
            self.last_shown_path = path


class WxCameraProgressBarFrameBase(wx.Dialog):
    PROGRESS_FRAME_SIZE = (485, 100)
    THUMBNAIL_SIZE = (68, 68)
    THUMBNAIL_LEFT_BORDER = 13
    THUMBNAIL_INNER_BORDER = 7
    REMAINING_TIME_TEXT_TOP_SPACER = 6
    REMAINING_TEXT_FONT_SIZE = 7
    GAUGE_GRANULARITY = 100000
    PULSE_FREQUENCY = 0.05

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, ui):
        self.ui = ui
        self._running = True
        self._visible = False
        pre = wx.PreDialog()
        pre.Show(False)
        pre.Create(None, size=self.PROGRESS_FRAME_SIZE, style=platform.simple_frame_style)
        self.PostCreate(pre)
        self.CenterOnScreen()
        self.Title = CameraStrings.progress_title
        platform.frame_icon(self)
        self._init_ui()
        self._default_bitmap = Images.CameraProgressLogo.GetImage().Rescale(*self.THUMBNAIL_SIZE).ConvertToBitmap()
        self._photo_background_image = Images.CameraProgressPhoto.GetImage().Rescale(*self.THUMBNAIL_SIZE)
        self.ui.found_files.register(self.HandleFoundFile)
        self.ui.message.register(self.HandleMessage)
        self.ui.total_bytes.register(self.HandleTotalBytes)
        self.ui.cur_bytes.register(self.HandleCurBytes)
        self.ui.last_photo.register(self.HandleLastPhoto)
        self._thumbnail_cond = threading.Condition()
        self.next_photo_path = None
        self._resizer_thread = CameraThumbnailResizer(self, self.format_thumbnail)
        self.Bind(wx.EVT_CLOSE, self.handle_close)

    @event_handler
    def handle_close(self, event):
        self.Hide()
        if event.CanVeto():
            event.Veto()
        else:
            self.Destroy()

    @message_sender(wx.CallAfter, block=True)
    def Hide(self):
        self._visible = False
        self.Show(False)

    @message_sender(wx.CallAfter, block=True)
    def Unhide(self):
        self._visible = True
        self.HandleFoundFile(self.ui.found_files.get())
        self.HandleMessage(self.ui.message.get())
        self.HandleTotalBytes(self.ui.total_bytes.get())
        self.HandleCurBytes(self.ui.cur_bytes.get())
        self.HandleLastPhoto(self.ui.last_photo.get())
        self.Show(True)
        self.Raise()

    def HandleCancelButton(self, event):
        self.ui.on_cancel()

    def HandleHideButton(self, event):
        self.ui.progress_window_hide()

    @message_sender(wx.CallAfter)
    def HandleFoundFile(self, num_found):
        self._gauge_indeterminate_update()

    @message_sender(wx.CallAfter)
    def HandleMessage(self, message):
        self._status_text.SetLabel(message)

    @message_sender(wx.CallAfter)
    def HandleTotalBytes(self, total_bytes):
        if total_bytes:
            self._total_bytes = total_bytes
            self.HandleCurBytes(self.ui.cur_bytes.get())

    @message_sender(wx.CallAfter)
    def HandleCurBytes(self, cur_bytes):
        granules = float(cur_bytes) / self._total_bytes * self.GAUGE_GRANULARITY + 0.5
        self._gauge.SetValue(int(granules))
        self._remaining_time_text.SetLabel(self.ui.get_remaining_message())

    @message_sender(wx.CallAfter)
    def HandleLastPhoto(self, path):
        if path:
            pathu = unicode(path)
            if os.path.exists(pathu):
                with self._thumbnail_cond:
                    self.next_photo_path = pathu
                    self._thumbnail_cond.notify()
        elif not path:
            self.thumbnail_image.SetBitmap(self._default_bitmap)

    def close(self):
        self.Hide()
        self._running = False
        with self._thumbnail_cond:
            self._thumbnail_cond.notify()
        self._resizer_thread.join()
        self.Close()

    def format_thumbnail(self, thumbnail):
        size = thumbnail.GetSize()
        wmin, hmin, wmax, hmax = rect_to_centered_square(size.width, size.height)
        if wmax - wmin <= 0 or hmax - hmin <= 0:
            return None
        thumbnail.Resize((wmax - wmin, hmax - hmin), (-wmin, -hmin))
        if not thumbnail.Ok():
            return None
        thumbnail.Rescale(self.THUMBNAIL_SIZE[0] - 2 * self.THUMBNAIL_INNER_BORDER, self.THUMBNAIL_SIZE[1] - 2 * self.THUMBNAIL_INNER_BORDER)
        if not thumbnail.Ok():
            return None
        newcopy = self._photo_background_image.Copy()
        newcopy.Paste(thumbnail, self.THUMBNAIL_INNER_BORDER, self.THUMBNAIL_INNER_BORDER)
        if not newcopy.Ok():
            return None
        return newcopy.ConvertToBitmap()

    @assert_message_queue
    def _init_button_control(self, parent):
        return WxSplashButtonPanel(parent, ((wx.ID_CANCEL,
          MiscStrings.hide_button,
          self.HandleHideButton,
          True), (wx.ID_ANY,
          MiscStrings.cancel_button,
          self.HandleCancelButton,
          False)))

    @assert_message_queue
    def _init_thumbnail_control(self, parent):
        self.thumbnail_image = wx.StaticBitmap(parent, -1, size=self.THUMBNAIL_SIZE)
        thumbsizer = wx.BoxSizer(wx.VERTICAL)
        thumbsizer.Add((0, self.THUMBNAIL_TOP_BORDER))
        thumbsizer.Add(self.thumbnail_image, flag=wx.EXPAND)
        thumbsizer.Add((0, self.THUMBNAIL_BOTTOM_BORDER))
        return thumbsizer

    @assert_message_queue
    def _init_gauge_control(self, parent):
        remaining_time_text = wx.StaticText(parent, -1, '')
        font = platform.get_tour_font(remaining_time_text)
        font.SetPointSize(self.REMAINING_TEXT_FONT_SIZE)
        platform.apply_tour_font(remaining_time_text)
        self._remaining_time_text = remaining_time_text
        gauge = wx.Gauge(parent, -1, 1, size=self.GAUGE_SIZE, style=wx.GA_HORIZONTAL)
        gauge.SetRange(self.GAUGE_GRANULARITY)
        self._total_bytes = self.GAUGE_GRANULARITY
        self._gauge_indeterminate_update = TimedThrottler(gauge.Pulse, frequency=self.PULSE_FREQUENCY)
        self._gauge = gauge
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add((0, self.GAUGE_TOP_SPACER))
        vsizer.Add(gauge, 1, flag=wx.EXPAND | wx.ALL)
        vsizer.Add((0, self.REMAINING_TIME_TEXT_TOP_SPACER))
        vsizer.Add(remaining_time_text, 1, flag=wx.EXPAND | wx.ALL)
        return vsizer

    @assert_message_queue
    def _init_status_bar(self, parent):
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add((self.THUMBNAIL_LEFT_BORDER, 0))
        hsizer.Add(self._init_thumbnail_control(parent))
        hsizer.Add((self.GAUGE_LEFT_BORDER, 0))
        hsizer.Add(self._init_gauge_control(parent), border=self.THUMBNAIL_TOP_BORDER, flag=wx.TOP | wx.BOTTOM | wx.RIGHT)
        hsizer.SetMinSize(self.PROGRESS_FRAME_SIZE)
        return hsizer


class WxCameraProgressBarFrameXP(WxCameraProgressBarFrameBase):
    GAUGE_TOP_SPACER = 14
    GAUGE_SIZE = (385, 20)
    GAUGE_LEFT_BORDER = 14
    THUMBNAIL_TOP_BORDER = 14
    THUMBNAIL_BOTTOM_BORDER = 16
    STATUS_TEXT_FONT_SIZE = 11
    STATUS_TEXT_SPACER = 15

    @assert_message_queue
    def _init_ui(self):
        header_panel = self._init_header_panel(self)
        status_panel = self._init_status_panel(self)
        button_controls = self._init_button_control(self)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(header_panel, 0, flag=wx.EXPAND)
        vsizer.Add(status_panel, 0, flag=wx.EXPAND)
        vsizer.Add(button_controls, 0, flag=wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(vsizer)

    @assert_message_queue
    def _init_header_panel(self, parent):
        header_panel = wx.Panel(parent, -1)
        header_panel.SetBackgroundColour(Colors.white)
        status_text = self._init_status_text(header_panel)
        line = make_line(self)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(status_text, 1, border=self.STATUS_TEXT_SPACER, flag=wx.EXPAND | wx.ALL)
        vsizer.Add(line, flag=wx.EXPAND | wx.TOP | wx.BOTTOM)
        header_panel.SetSizerAndFit(vsizer)
        return header_panel

    @assert_message_queue
    def _init_status_text(self, parent):
        status_text = wx.StaticText(parent, -1, CameraStrings.progress_finding % dict(num_found=0))
        font = platform.get_tour_font(status_text)
        font.SetPointSize(self.STATUS_TEXT_FONT_SIZE)
        font.SetWeight(wx.BOLD)
        status_text.SetFont(font)
        self._status_text = status_text
        return status_text

    @assert_message_queue
    def _init_status_panel(self, parent):
        status_panel = wx.Panel(parent, -1)
        status_panel.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        status_panel.SetSizerAndFit(self._init_status_bar(status_panel))
        return status_panel


class WxCameraProgressBarFrame7(WxCameraProgressBarFrameBase):
    GAUGE_TOP_SPACER = 12
    GAUGE_SIZE = (385, 10)
    GAUGE_LEFT_BORDER = 14
    THUMBNAIL_TOP_BORDER = 15
    THUMBNAIL_BOTTOM_BORDER = 15
    STATUS_TEXT_FONT_SIZE = 12
    STATUS_TEXT_SPACER = 15

    @assert_message_queue
    def _init_ui(self):
        status_panel = self._init_status_panel(self)
        button_controls = self._init_button_control(self)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(status_panel, 0, flag=wx.EXPAND)
        vsizer.Add(button_controls, 0, flag=wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(vsizer)

    @assert_message_queue
    def _init_status_text(self, parent):
        status_text = wx.StaticText(parent, -1, CameraStrings.progress_finding % dict(num_found=0))
        font = platform.get_tour_font(status_text)
        font.SetPointSize(self.STATUS_TEXT_FONT_SIZE)
        status_text.SetFont(font)
        status_text.SetForegroundColour(Colors.camera_font)
        self._status_text = status_text
        return status_text

    @assert_message_queue
    def _init_status_panel(self, parent):
        status_panel = wx.Panel(parent, -1)
        status_panel.SetBackgroundColour(Colors.white)
        status_text = self._init_status_text(status_panel)
        status_bar = self._init_status_bar(status_panel)
        panelsizer = wx.BoxSizer(wx.VERTICAL)
        panelsizer.Add(status_text, 0, border=self.STATUS_TEXT_SPACER, flag=wx.EXPAND | wx.LEFT | wx.TOP)
        panelsizer.Add(status_bar, 0, flag=wx.EXPAND | wx.ALL)
        status_panel.SetSizerAndFit(panelsizer)
        return status_panel


if sys.platform.startswith('win'):
    from dropbox.win32.version import WINDOWS_VERSION, VISTA
    if WINDOWS_VERSION < VISTA:
        WxCameraProgressBarFrame = WxCameraProgressBarFrameXP
    else:
        WxCameraProgressBarFrame = WxCameraProgressBarFrame7

class AutoplayLinkText(StaticLinkText):

    def link_handler(self, link):
        arch.photouploader.open_autoplay_settings()


class CameraUploadLauncher(TransparentPanel):
    LAUNCH_LABEL_INITIAL_WIDTH = 150

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, app):
        super(CameraUploadLauncher, self).__init__(parent, transparent_hack=False)
        if not arch.photouploader.USE_PHOTOUPLOADER:
            raise NotImplementedError('CameraUploadLauncher not compatible with this version of Windows.')
        self.app = app
        self.parent = parent
        self.label = wx.StaticText(self, label=pref_strings.camera_message)
        self.label.Wrap(self.LAUNCH_LABEL_INITIAL_WIDTH)
        self.button = UACButton(self, label=pref_strings.camera_launch_button)
        self.link = AutoplayLinkText(self, label=pref_strings.camera_launch_link)
        self.link.SetBackgroundColour(self.GetBackgroundColour())
        self.button.Bind(wx.EVT_BUTTON, self.handle_camera_launch_button)
        self.camera_box = wx.StaticBox(self, label=pref_strings.camera_label)
        self.camera_vsizer = wx.StaticBoxSizer(self.camera_box, wx.VERTICAL)
        self.camera_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.camera_subvsizer = wx.BoxSizer(wx.VERTICAL)
        self.camera_subvsizer.Add(self.button, flag=wx.ALIGN_RIGHT)
        self.camera_subvsizer.Add(self.link, flag=wx.ALIGN_RIGHT)
        self.camera_hsizer.Add(self.label, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        self.camera_hsizer.AddStretchSpacer()
        self.camera_hsizer.Add(self.camera_subvsizer, border=platform.button_baseline_adjustment, flag=wx.ALIGN_CENTER | wx.BOTTOM)
        self.camera_vsizer.Add(self.camera_hsizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=platform.radio_static_box_interior)
        self.SetSizerAndFit(self.camera_vsizer)

    @event_handler
    def handle_camera_launch_button(self, event):
        arch.photouploader.run_photo_update(self.app)
        self.on_show()
        self.parent.Layout()
        self.parent.parent.panel.Layout()

    @event_handler
    def on_show(self):
        if arch.photouploader.is_photouploader_installed():
            self.button.Hide()
            self.link.Show()
            width = self.link.GetSize().GetWidth()
        else:
            self.link.Hide()
            self.button.Show()
            width = self.button.GetSize().GetWidth()
        self.label.SetLabel(pref_strings.camera_message)
        self.label.Wrap(self.camera_hsizer.GetSize().GetWidth() - width - platform.statictext_textctrl_horizontal_spacing)
        self.camera_vsizer.SetSizeHints(self)


class PhotoImportLauncher(TransparentPanel):
    IMPORT_LABEL_INITIAL_WIDTH = 150

    @message_sender(wx.CallAfter, block=True)
    def __init__(self, parent, app):
        super(PhotoImportLauncher, self).__init__(parent, transparent_hack=False)
        self.app = app
        self.parent = parent
        self.label = wx.StaticText(self, label=pref_strings.photo_library_import_message)
        self.label.Wrap(self.IMPORT_LABEL_INITIAL_WIDTH)
        self.button = wx.Button(self, label=pref_strings.photo_library_import_button)
        self.button.Bind(wx.EVT_BUTTON, self.handle_photo_import_button)
        self.import_box = wx.StaticBox(self, label=pref_strings.photo_library_import_label)
        self.import_vsizer = wx.StaticBoxSizer(self.import_box, wx.VERTICAL)
        self.import_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.import_subvsizer = wx.BoxSizer(wx.VERTICAL)
        self.import_subvsizer.Add(self.button, flag=wx.ALIGN_RIGHT)
        self.import_hsizer.Add(self.label, border=platform.statictext_baseline_adjustment, flag=wx.ALIGN_BOTTOM | wx.BOTTOM)
        self.import_hsizer.AddStretchSpacer()
        self.import_hsizer.Add(self.import_subvsizer, border=platform.button_baseline_adjustment, flag=wx.ALIGN_CENTER | wx.BOTTOM)
        self.import_vsizer.Add(self.import_hsizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=platform.radio_static_box_interior)
        self.SetSizerAndFit(self.import_vsizer)

    @event_handler
    def handle_photo_import_button(self, event):
        self.app.stuff_importer.prompt_import()
        self.button.Disable()

    @event_handler
    def on_show(self):
        import_photos = False
        if self.app.stuff_importer:
            import_photos, _ = self.app.stuff_importer.show_import_button(self.app)
        if import_photos:
            self.button.Enable()
            self.label.SetLabel(pref_strings.photo_library_import_message)
            self.label.Wrap(self.import_hsizer.GetSize().GetWidth() - self.button.GetSize().GetWidth() - platform.statictext_textctrl_horizontal_spacing)
            self.import_vsizer.SetSizeHints(self)
        else:
            self.import_box.Hide()
            self.import_vsizer.Clear(True)
