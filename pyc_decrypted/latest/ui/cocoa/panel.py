#Embedded file name: ui/cocoa/panel.py
import functools
import math
import os
import signal
import threading
import time
import random as insecure_random
from objc import YES, nil, NO, selector
from Foundation import NSRect, NSMakeRange, NSDefaultRunLoopMode, NSRunLoop, NSAffineTransform
from AppKit import NSWindow, NSView, NSColor, NSBezierPath, NSTimer, NSShadow, NSWindowAbove, NSRectFill, NSEventTrackingRunLoopMode, NSTitledWindowMask, NSClosableWindowMask, NSApplication, NSObject, NSBox, NSLineBorder, NSBoxSecondary, NSImageView, NSImage, NSTextView, NSGraphicsContext, NSURL, NSImageFramePhoto, NSCenterTextAlignment, NSScaleProportionally, NSScaleToFit, NSBezelBorder, NSViewWidthSizable, NSSmallControlSize, NSFont, NSRegularControlSize, NSViewHeightSizable, NSBorderlessWindowMask, NSApp, NSScrollView, NSFloatingWindowLevel, NSMiniaturizableWindowMask, NSBackingStoreBuffered
from Quartz import CIContext, CIImage, CIFilter, CIVector, CIColor
from PyObjCTools import AppHelper
import build_number

def scrollViewScrollHeight(sv, scrollVal):
    sv.contentView().scrollToPoint_((0, scrollVal))
    sv.reflectScrolledClipView_(sv.contentView())


class LinearAnimator(NSObject):

    def initWithStartVal_endVal_duration_interval_valueCb_doneCb_(self, start_val, end_val, duration, update_period, value_callback, done_callback):
        self = super(LinearAnimator, self).init()
        if not self:
            return
        self.start_time = time.time()
        self.duration = duration
        self.end_val = end_val
        self.start_val = start_val
        self.value_callback = value_callback
        self.done_callback = done_callback
        self.timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(update_period, self, 'period:', None, True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSEventTrackingRunLoopMode)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)

    def period_(self, timer):
        now = time.time()
        if now > self.start_time + self.duration:
            self.value_callback(self.end_val)
            if self.done_callback:
                self.done_callback()
            timer.invalidate()
            return
        self.value_callback((self.end_val - self.start_val) * (now - self.start_time) / self.duration + self.start_val)

    def invalidate(self):
        self.timer.invalidate()


class SineAnimator(NSObject):

    def initWithStartVal_endVal_duration_interval_valueCb_(self, start_val, end_val, duration, update_period, value_callback):
        self = super(SineAnimator, self).init()
        if not self:
            return
        self.start_val = start_val
        self.end_val = end_val
        self.duration = duration
        self.update_period = update_period
        self.value_callback = value_callback
        self.start_time = time.time()
        self.timer = NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(update_period, self, 'period:', None, True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSEventTrackingRunLoopMode)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
        self.inv = False
        return self

    def period_(self, timer):
        if self.inv:
            return
        elapsed = time.time() - self.start_time
        val = (1 - math.cos(elapsed * math.pi / self.duration)) / 2.0 * (self.end_val - self.start_val) + self.start_val
        self.value_callback(val)

    def invalidate(self):
        self.inv = True
        self.timer.invalidate()


class InfiniteLinearAnimator(NSObject):

    def initWithStartVal_endVal_duration_interval_valueCb_(self, start_val, end_val, duration, update_period, value_callback):
        self = super(InfiniteLinearAnimator, self).init()
        if not self:
            return
        self.start_val = start_val
        self.end_val = end_val
        self.duration = duration
        self.update_period = update_period
        self.value_calback = value_callback
        self.time = 0
        self._done_callback()

    def _done_callback(self):
        if self.time % 2:
            start, end = self.start_val, self.end_val
        else:
            start, end = self.end_val, self.start_val
        self.time += 1
        self.cur = LinearAnimator.alloc().initWithStartVal_endVal_duration_interval_valueCb_doneCb_(start, end, self.duration, self.update_period, self.value_calback, self._done_callback)


class SpringAnimator(object):

    def __init__(self, start_val, end_val, k, damp, duration, update_period, value_cb, done_cb):
        self.last_time = self.start_time = time.time()
        self.start_val = self.cur_val = start_val
        self.end_val = end_val
        self.cur_velocity = 0
        self.damp = damp
        self.k = k
        self.duration = duration
        self.value_cb = value_cb
        self.done_cb = done_cb
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(update_period, self, selector(self.period, signature='v@:'), None, True)
        NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSEventTrackingRunLoopMode)

    def period(self):
        cur_time = time.time()
        delta = cur_time - self.last_time
        self.last_time = cur_time
        force = self.k * (self.end_val - self.cur_val) - self.damp * self.cur_velocity
        self.cur_val += self.cur_velocity * delta
        self.cur_velocity += force * delta
        if cur_time > self.start_time + self.duration:
            self.value_cb(self.end_val)
            if self.done_cb:
                self.done_cb()
            self.timer.invalidate()
            return
        self.value_cb(self.cur_val)

    def invalidate(self):
        self.timer.invalidate()


class GreetingsToView(NSView):
    DELAY = 1.0

    def initWithFrame_(self, frame):
        self = super(GreetingsToView, self).initWithFrame_(frame)
        if not self:
            return None
        self.timers = []
        poem = ('thanks for watching!', 'we love working on', 'Dropbox', 'and we really hope', 'it makes your life', 'easier.', '~~~', 'remember,', "do what's right", 'love thy neighbor', 'and', 'be yourself', '<3', '~~~', 'find us on the web at', 'http://dropbox.com/', '~~~', '4/15/2011')
        self.views = []
        total_height = 0
        for a in poem:
            vv = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
            vv.setDrawsBackground_(NO)
            vv.setEditable_(NO)
            vv.setSelectable_(NO)
            vv.setAlignment_range_(NSCenterTextAlignment, NSMakeRange(0, vv.string().length()))
            vv.textStorage().beginEditing()
            vv.textStorage().mutableString().setString_(a)
            vv.textStorage().setFont_(NSFont.labelFontOfSize_(14))
            vv.textStorage().setForegroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.0))
            vv.textStorage().endEditing()
            vv.layoutManager().glyphRangeForTextContainer_(vv.textContainer())
            size = vv.layoutManager().usedRectForTextContainer_(vv.textContainer()).size
            vv.setFrameSize_(size)
            total_height += size[1]
            self.addSubview_(vv)
            self.views.append(vv)

        SPACING = 11
        total_height += SPACING * (len(self.views) - 1)
        placement = frame.size[1] - (frame.size[1] - total_height) / 2.0
        for a in self.views:
            w, h = a.frame().size
            placement -= h
            a.setFrameOrigin_(((frame.size[0] - w) / 2.0, placement))
            placement -= SPACING

        return self

    def forView_reverseExponent_(self, view, val):
        view.textStorage().setForegroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1 - math.exp(-val * 2.0)))
        view.setNeedsDisplay_(YES)

    def createAnimator(self, a):

        def makeTimer():
            self.timers.append(LinearAnimator.alloc().initWithStartVal_endVal_duration_interval_valueCb_doneCb_(0, 2.0, 0.6, 1 / 60.0, functools.partial(self.forView_reverseExponent_, a), None))

        return makeTimer

    def stopTimers(self):
        for t in self.timers:
            t.invalidate()

    def dealloc(self):
        self.stopTimers()
        super(GreetingsToView, self).dealloc()

    def doPresentation_(self, cb):
        for i, a in enumerate(self.views):
            AppHelper.callLater(i * self.DELAY, self.createAnimator(a))

        if cb:
            AppHelper.callLater(len(self.views) * self.DELAY + 5, cb)


class ShadowedImage(NSImageView):

    def initWithFrame_(self, frame):
        self = super(ShadowedImage, self).initWithFrame_(frame)
        if not self:
            return
        self._shadow = NSShadow.alloc().init()
        return self

    def setShadowColor_(self, color):
        self._shadow.setShadowColor_(color)

    def setShadowOffset_(self, size):
        self._shadow.setShadowOffset_(size)

    def setShadowBlurRadius_(self, blur):
        self._shadow.setShadowBlurRadius_(blur)

    def drawRect_(self, theRect):
        self._shadow.set()
        super(ShadowedImage, self).drawRect_(theRect)


class IntroView(NSView):

    def initWithFrame_imageDir_(self, frame, imageDir):
        self = super(IntroView, self).initWithFrame_(frame)
        if not self:
            return None
        dropboxImage = NSImage.alloc().initWithContentsOfFile_(os.path.join(imageDir, u'box_stroked_150.png'))
        iW, iH = dropboxImage.size()
        newHeight = iH * 300.0 / iW
        self.dropboxViewFinalPosition = NSRect((25, frame.size[1] - 43 - newHeight), (300, newHeight))
        self.dropboxView = ShadowedImage.alloc().initWithFrame_(self.dropboxViewFinalPosition)
        self.dropboxView.setImageScaling_(NSScaleToFit)
        self.dropboxView.setImage_(dropboxImage)
        self.dropboxView.setShadowColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 0.5))
        self.dropboxView.setShadowOffset_((0.0, -2.0))
        self.dropboxView.setShadowBlurRadius_(5.0)
        logoImage = NSImage.alloc().initWithContentsOfFile_(os.path.join(imageDir, u'dropboxlogo.png'))
        iW, iH = logoImage.size()
        newHeight = iH * 300.0 / iW
        self.logoViewFinalPosition = NSRect((25, frame.size[1] - 334 - newHeight), (300, newHeight))
        self.logoView = NSImageView.alloc().initWithFrame_(self.logoViewFinalPosition)
        self.logoView.setImage_(logoImage)
        self.versionView = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
        self.versionView.setDrawsBackground_(NO)
        self.versionView.setEditable_(NO)
        self.versionView.setSelectable_(NO)
        self.versionView.textStorage().mutableString().setString_(u'Version %s' % build_number.VERSION)
        self.versionView.textStorage().setFont_(NSFont.labelFontOfSize_(14))
        self.versionView.layoutManager().glyphRangeForTextContainer_(self.versionView.textContainer())
        textSize1 = self.versionView.layoutManager().usedRectForTextContainer_(self.versionView.textContainer()).size
        textAnchor1 = 5
        self.versionView2 = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
        self.versionView2.setDrawsBackground_(NO)
        self.versionView2.setEditable_(NO)
        self.versionView2.setSelectable_(NO)
        self.versionView2.textStorage().mutableString().setString_(u'Copyright \xa9 2007-2010 Dropbox Inc.')
        self.versionView2.setFont_(NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSSmallControlSize)))
        self.versionView2.layoutManager().glyphRangeForTextContainer_(self.versionView2.textContainer())
        textSize2 = self.versionView2.layoutManager().usedRectForTextContainer_(self.versionView2.textContainer()).size
        textAnchor2 = 4
        bottomToLogoViewBaseline = self.logoView.frame().origin[1] + 17
        textSeparation = 10
        combinedHeight = textSize1[1] + textSize2[1] + textSeparation
        self.versionView2FinalPosition = NSRect(((frame.size[0] - textSize2[0]) / 2.0, (bottomToLogoViewBaseline - combinedHeight) / 2.0), (textSize2[0], textSize2[1] + textAnchor2))
        self.versionView2.setFrame_(self.versionView2FinalPosition)
        self.versionViewFinalPosition = NSRect(((frame.size[0] - textSize1[0]) / 2.0, self.versionView2.frame().origin[1] + textSeparation + self.versionView2.frame().size[1]), (textSize1[0], textSize1[1] + textAnchor1))
        self.versionView.setFrame_(self.versionViewFinalPosition)
        for _view in (self.dropboxView,
         self.logoView,
         self.versionView,
         self.versionView2):
            self.addSubview_(_view)

        return self

    def doPresentation_(self, whenDone):
        if whenDone:
            whenDone()


class TextPane(NSView):
    SIZE = 24

    def initWithFrame_andText_(self, frame, text):
        self = super(TextPane, self).initWithFrame_(frame)
        if not self:
            return
        self.tx = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
        self.tx.setDrawsBackground_(NO)
        self.tx.setEditable_(NO)
        self.tx.setSelectable_(NO)
        self.tx.textStorage().mutableString().setString_(text)
        self.tx.setAlignment_range_(NSCenterTextAlignment, NSMakeRange(0, self.tx.string().length()))
        self.tx.setFont_(NSFont.userFontOfSize_(self.SIZE))
        self.tx.layoutManager().glyphRangeForTextContainer_(self.tx.textContainer())
        textSize2 = self.tx.layoutManager().usedRectForTextContainer_(self.tx.textContainer()).size
        self.tx.setFrame_(NSRect(((frame.size[0] - textSize2[0]) / 2.0, (frame.size[1] - textSize2[1]) / 2.0), textSize2))
        self.addSubview_(self.tx)
        return self


class PictureView(NSView):

    def initWithFrame_view_size_name_captionText_(self, frame, view, size, name, caption_text):
        self = super(PictureView, self).initWithFrame_(frame)
        if not self:
            return
        _size = iW, iH = size
        xOffset = (frame.size[0] - iW) / 2.0
        yOffset = frame.size[1] - xOffset - iH
        self.dropboxViewFinalPosition = NSRect((xOffset, yOffset), _size)
        self.dropboxView = view
        self.dropboxView.setFrame_(self.dropboxViewFinalPosition)
        self.addSubview_(self.dropboxView)
        self.versionView = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
        self.versionView.setDrawsBackground_(NO)
        self.versionView.setEditable_(NO)
        self.versionView.setSelectable_(NO)
        self.versionView.textStorage().beginEditing()
        self.versionView.textStorage().mutableString().setString_(name)
        self.versionView.textStorage().setForegroundColor_(NSColor.whiteColor())
        self.versionView.textStorage().setFont_(NSFont.labelFontOfSize_(18))
        self.versionView.textStorage().endEditing()
        self.versionView.setAlignment_range_(NSCenterTextAlignment, NSMakeRange(0, self.versionView.string().length()))
        self.versionView.layoutManager().glyphRangeForTextContainer_(self.versionView.textContainer())
        textSize1 = self.versionView.layoutManager().usedRectForTextContainer_(self.versionView.textContainer()).size
        textAnchor1 = 0
        self.versionView2 = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
        self.versionView2.setDrawsBackground_(NO)
        self.versionView2.setEditable_(NO)
        self.versionView2.setSelectable_(NO)
        self.versionView2.textStorage().beginEditing()
        self.versionView2.textStorage().mutableString().setString_(u'"%s"' % (caption_text,))
        self.versionView2.textStorage().setForegroundColor_(NSColor.whiteColor())
        self.versionView2.textStorage().setFont_(NSFont.labelFontOfSize_(13))
        self.versionView2.textStorage().endEditing()
        self.versionView2.setAlignment_range_(NSCenterTextAlignment, NSMakeRange(0, self.versionView2.string().length()))
        self.versionView2.layoutManager().glyphRangeForTextContainer_(self.versionView2.textContainer())
        textSize2 = self.versionView2.layoutManager().usedRectForTextContainer_(self.versionView2.textContainer()).size
        textAnchor2 = 0
        bottomToLogoViewBaseline = yOffset
        textSeparation = (yOffset - textSize1[1] - textSize2[1]) * 0.2
        combinedHeight = textSize1[1] + textSize2[1] + textSeparation
        self.versionView2FinalPosition = NSRect(((frame.size[0] - textSize2[0]) / 2.0, (bottomToLogoViewBaseline - combinedHeight) / 2.0), (textSize2[0], textSize2[1] + textAnchor2))
        self.versionView2.setFrame_(self.versionView2FinalPosition)
        self.versionViewFinalPosition = NSRect(((frame.size[0] - textSize1[0]) / 2.0, self.versionView2.frame().origin[1] + textSeparation + self.versionView2.frame().size[1]), (textSize1[0], textSize1[1] + textAnchor1))
        self.versionView.setFrame_(self.versionViewFinalPosition)
        self.addSubview_(self.versionView)
        self.addSubview_(self.versionView2)
        return self

    def pictureView(self):
        return self.dropboxView

    def drawRect_(self, rect):
        super(PictureView, self).drawRect_(rect)
        pos = self.dropboxViewFinalPosition.origin
        size = self.dropboxViewFinalPosition.size
        a = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSRect((pos[0] - 3, pos[1] - 3), (size[0] + 6, size[1] + 6)), 5.0, 5.0)
        a.setLineWidth_(2)
        NSColor.whiteColor().set()
        a.fill()


class BasicPictureView(PictureView):

    def initWithFrame_picture_name_captionText_(self, frame, picture, name, caption_text):
        dropboxImage = NSImage.alloc().initWithContentsOfFile_(picture)
        view = NSImageView.alloc().init()
        view.setImage_(dropboxImage)
        return self.initWithFrame_view_size_name_captionText_(frame, view, dropboxImage.size(), name, caption_text)


class _PixelView(NSView):

    def initWithImage_andFilter_(self, image, _filter):
        self = super(_PixelView, self).initWithFrame_(NSRect((0, 0), (0, 0)))
        if not self:
            return
        self.image = image
        self._filter = _filter
        self._filter.setValue_forKey_(self.image, 'inputImage')
        return self

    def filter(self):
        return self._filter

    def drawRect_(self, rect):
        NSColor.whiteColor().set()
        NSBezierPath.bezierPathWithRect_(NSRect((0, 0), self.frame().size)).fill()
        NSGraphicsContext.currentContext().CIContext().drawImage_atPoint_fromRect_(self._filter.valueForKey_('outputImage'), (0, 0), self.image.extent())

    def isOpaque(self):
        return YES


class FilterView(PictureView):

    def initWithFrame_filepath_filter_name_captionText_(self, frame, filepath, _filter, name, caption_text):
        image = CIImage.imageWithContentsOfURL_(NSURL.URLWithString_(u'file://' + filepath))
        view = _PixelView.alloc().initWithImage_andFilter_(image, _filter)
        return self.initWithFrame_view_size_name_captionText_(frame, view, image.extent()[1], name, caption_text)


WIDTH = 350
BASE_HEIGHT = 525

def identity(x):
    return x


class _PersonView(NSView):
    WIDTH = WIDTH
    BASE_HEIGHT = BASE_HEIGHT

    def initWithFrame_imageDir_(self, frame, imageDir):
        self = super(_PersonView, self).initWithFrame_(frame)
        if not self:
            return None
        self.timers = []
        random_scale_x = insecure_random.random() * 5.0
        random_scale_y = insecure_random.random() * 5.0

        def create_transform(x):
            new_t = NSAffineTransform.transform()
            new_t.translateXBy_yBy_(128, 171)
            new_t.scaleXBy_yBy_((random_scale_x - 1.0) * x + 1.0, (random_scale_y - 1.0) * x + 1.0)
            new_t.rotateByDegrees_(360 * x)
            new_t.translateXBy_yBy_(-128, -171)
            return new_t

        filters = ((CIFilter.filterWithName_('CIPixellate'),
          'inputScale',
          1,
          15,
          2.5,
          identity),
         (CIFilter.filterWithName_('CIBloom'),
          'inputRadius',
          0,
          10,
          4,
          identity),
         (CIFilter.filterWithName_('CIZoomBlur'),
          'inputAmount',
          0,
          15,
          4,
          identity),
         (CIFilter.filterWithName_('CIHueAdjust'),
          'inputAngle',
          0,
          3.14,
          2,
          identity),
         (CIFilter.filterWithName_('CIAffineTransform'),
          'inputTransform',
          0,
          1.0,
          2,
          create_transform),
         (CIFilter.filterWithName_('CIColorPosterize'),
          'inputLevels',
          1,
          90,
          3,
          identity),
         (CIFilter.filterWithName_('CIHexagonalPixellate'),
          'inputScale',
          1,
          10,
          2,
          identity),
         (CIFilter.filterWithName_('CITorusLensDistortion'),
          'inputRadius',
          0,
          225,
          2,
          identity))
        fvinit = 'initWithFrame_filepath_filter_name_captionText_'
        panes = ((FilterView, fvinit, (os.path.join(imageDir, u'rian.jpg'),
           filters[0][0],
           u'Rian Hunter',
           u'Bam dollar')),
         (FilterView, fvinit, (os.path.join(imageDir, u'david.jpg'),
           filters[1][0],
           u'David Euresti',
           u"Yeah! We're on stage!")),
         (FilterView, fvinit, (os.path.join(imageDir, u'tom.jpg'),
           filters[2][0],
           u'Tom Hoover',
           u'Just want to focus + get the new tour + ss changes out asap.')),
         (FilterView, fvinit, (os.path.join(imageDir, u'mike.jpg'),
           filters[3][0],
           u'Michael Haimes',
           u"Don't worry Sameer")),
         (FilterView, fvinit, (os.path.join(imageDir, u'martin.jpg'),
           filters[4][0],
           u'Martin Baker',
           u' Alanis Morissette it is.')),
         (FilterView, fvinit, (os.path.join(imageDir, u'jon.png'),
           filters[5][0],
           u'Jon Ying',
           u'Dosh gets what dosh wants')),
         (FilterView, fvinit, (os.path.join(imageDir, u'arash3.jpg'),
           filters[6][0],
           u'Arash Ferdowsi',
           u"I'm so hungry")),
         (FilterView, fvinit, (os.path.join(imageDir, u'drew.jpg'),
           filters[7][0],
           u'Drew Houston',
           u'Wanna schrock it?')))
        self.panes = []
        for i, info in enumerate(panes):
            klass, init_func_name, addl_args = info
            frame = NSRect((0, self.BASE_HEIGHT * (len(panes) - 1 - i)), (self.WIDTH, self.BASE_HEIGHT))
            _p = klass.alloc()
            init_func = getattr(_p, init_func_name)
            _p = init_func(frame, *addl_args)
            self.panes.append(_p)
            self.addSubview_(_p)

        for j, (f, key, start, stop, dur, mapper) in enumerate(filters):
            _v1 = self.panes[j].pictureView()
            _f1 = _v1.filter()
            _f1.setDefaults()
            _s = _v1.frame().size
            try:
                _f1.setValue_forKey_(CIVector.vectorWithX_Y_(_s[0] / 2.0, _s[1] / 2.0), 'inputCenter')
            except KeyError:
                pass

            if j == len(filters) - 1:
                try:
                    _f1.setValue_forKey_(40.0, 'inputWidth')
                except KeyError:
                    pass

            def prebind():
                _k = key
                _v = _v1
                _f = _f1
                _m = mapper

                def setVal(x):
                    try:
                        v = _m(x)
                        _f.setValue_forKey_(v, _k)
                        _v.setNeedsDisplay_(YES)
                    except:
                        import traceback
                        print _k, v, _f
                        traceback.print_exc()

                return setVal

            self.timers.append(SineAnimator.alloc().initWithStartVal_endVal_duration_interval_valueCb_(start, stop, dur, 1 / 30.0, prebind()))

        return self

    def sizeToFit(self):
        self.setFrame_(NSRect(self.frame().origin, (self.WIDTH, len(self.panes) * self.BASE_HEIGHT)))

    def stopTimers(self):
        for t in self.timers:
            t.invalidate()

    def dealloc(self):
        self.stopTimers()
        super(_PersonView, self).dealloc()

    def numberOfPeoplePanes(self):
        return len(self.panes)


class PersonView(NSScrollView):

    def initWithFrame_imageDir_(self, frame, imageDir):
        self = super(PersonView, self).initWithFrame_(frame)
        if not self:
            return
        self.sv = _PersonView.alloc().initWithFrame_imageDir_(NSRect((0, 0), frame.size), imageDir)
        self.sv.sizeToFit()
        self.setDrawsBackground_(NO)
        self.setDocumentView_(self.sv)
        self.updateScrollBar_(self.sv.frame().size[1] - BASE_HEIGHT)
        self.started = False
        self.start_offset = 0
        return self

    def updateScrollBar_(self, scrollVal):
        return scrollViewScrollHeight(self, scrollVal)

    def numberOfPeoplePanes(self):
        return self.sv.numberOfPeoplePanes()


class _SickView(NSView):
    WIDTH = WIDTH
    BASE_HEIGHT = BASE_HEIGHT

    def initWithFrame_imageDir_(self, frame, imageDir):
        self = super(_SickView, self).initWithFrame_(frame)
        if not self:
            return
        self.person_animator = None
        panes = ((IntroView, 'initWithFrame_imageDir_', (imageDir,)),
         (TextPane, 'initWithFrame_andText_', (u"and now the moment you've all been waiting for",)),
         (TextPane, 'initWithFrame_andText_', (u'we proudly present for your viewing pleasure',)),
         (TextPane, 'initWithFrame_andText_', (u'the elite members of the dropbox client team!',)),
         (PersonView, 'initWithFrame_imageDir_', (imageDir,)))
        self.panes = []
        for i, info in enumerate(panes):
            klass, init_func_name, addl_args = info
            frame = NSRect((0, self.BASE_HEIGHT * (len(panes) - 1 - i)), (self.WIDTH, self.BASE_HEIGHT))
            _p = klass.alloc()
            init_func = getattr(_p, init_func_name)
            _p = init_func(frame, *addl_args)
            self.panes.append(_p)
            self.addSubview_(_p)

        gradient = CIFilter.filterWithName_('CILinearGradient')
        gradient.setValue_forKey_(CIVector.vectorWithX_Y_(0, self.BASE_HEIGHT * 3), 'inputPoint0')
        gradient.setValue_forKey_(CIColor.colorWithRed_green_blue_alpha_(0, 81 / 255.0, 164 / 255.0, 0), 'inputColor0')
        gradient.setValue_forKey_(CIVector.vectorWithX_Y_(0, 0), 'inputPoint1')
        gradient.setValue_forKey_(CIColor.colorWithRed_green_blue_alpha_(0, 81 / 255.0, 164 / 255.0, 1.0), 'inputColor1')
        self.outputGradient1 = gradient.valueForKey_('outputImage')
        gradient.setValue_forKey_(CIVector.vectorWithX_Y_(0, self.BASE_HEIGHT), 'inputPoint0')
        gradient.setValue_forKey_(CIColor.colorWithRed_green_blue_alpha_(0, 81 / 255.0, 164 / 255.0, 1.0), 'inputColor0')
        gradient.setValue_forKey_(CIVector.vectorWithX_Y_(0, 0), 'inputPoint1')
        gradient.setValue_forKey_(CIColor.colorWithRed_green_blue_alpha_(32 / 255.0, 127 / 255.0, 209 / 255.0, 1.0), 'inputColor1')
        self.outputGradient2 = gradient.valueForKey_('outputImage')
        return self

    def sizeToFit(self):
        self.setFrame_(NSRect(self.frame().origin, (self.WIDTH, len(self.panes) * self.BASE_HEIGHT)))

    def numberOfPeoplePanes(self):
        return self.panes[-1].numberOfPeoplePanes()

    def goToNthPerson_completion_(self, i, completion):
        if self.person_animator:
            self.person_animator.invalidate()
            self.person_animator = None
        personScrollView = self.panes[-1]
        start_val = personScrollView.contentView().documentVisibleRect().origin[1]
        end = self.BASE_HEIGHT * (personScrollView.numberOfPeoplePanes() - 1 - i)
        self.person_animator = SpringAnimator(start_val, end, 60.0, 8.0, 4, 1 / 30.0, personScrollView.updateScrollBar_, completion)

    def stopTimers(self):
        if self.person_animator:
            self.person_animator.invalidate()

    def dealloc(self):
        self.stopTimers()
        super(_SickView, self).dealloc()

    def drawRect_(self, rect):
        cictx = NSGraphicsContext.currentContext().CIContext()
        cictx.drawImage_atPoint_fromRect_(self.outputGradient1, (0, self.BASE_HEIGHT), NSRect((0, 0), (self.WIDTH, self.BASE_HEIGHT * 4)))
        cictx.drawImage_atPoint_fromRect_(self.outputGradient2, (0, 0), NSRect((0, 0), (self.WIDTH, self.BASE_HEIGHT)))
        super(_SickView, self).drawRect_(rect)


PERSON_DELAY = 5

class Introduction(NSScrollView):

    def initWithFrame_imageDir_(self, frame, imageDir):
        self = super(Introduction, self).initWithFrame_(frame)
        if not self:
            return
        self.ani = None
        self.sv = _SickView.alloc().initWithFrame_imageDir_(NSRect((0, 0), frame.size), imageDir)
        self.sv.sizeToFit()
        self.setDrawsBackground_(NO)
        self.setDocumentView_(self.sv)
        self.updateScrollBar_(self.sv.frame().size[1] - BASE_HEIGHT)
        self.start_offset = 0
        return self

    def updateScrollBar_(self, scrollVal):
        return scrollViewScrollHeight(self, scrollVal)

    def scrollTop(self):
        self.updateScrollBar_(self.sv.frame().size[1] - BASE_HEIGHT)

    def doPresentation_(self, done_cb):
        self.ani = LinearAnimator.alloc().initWithStartVal_endVal_duration_interval_valueCb_doneCb_(self.sv.frame().size[1] - BASE_HEIGHT, 0, 8.0, 1 / 60.0, self.updateScrollBar_, self.atRian)
        self.start_offset = 0
        self.done_cb = done_cb

    def stopTimers(self):
        if self.ani:
            self.ani.invalidate()

    def dealloc(self):
        self.stopTimers()
        super(Introduction, self).dealloc()

    def atRian(self):
        self.start_offset += 1
        if self.start_offset == self.sv.numberOfPeoplePanes():
            if self.done_cb:
                AppHelper.callLater(PERSON_DELAY, self.done_cb)
            return
        AppHelper.callLater(PERSON_DELAY, self.proceedToDavid)

    def proceedToDavid(self):
        self.sv.goToNthPerson_completion_(self.start_offset, self.atRian)


class GreetingsTo(NSView):
    DELAY = 0.5

    def initWithFrame_(self, frame):
        self = super(GreetingsTo, self).initWithFrame_(frame)
        if not self:
            return
        self.timers = []
        for __text in ('greetings',
         'to',
         'AAPL',
         'GOOG',
         'MSFT',
         (':)', '_smile'),
         (':P', '_wink')):
            if type(__text) is str:
                _text = attr = __text
            else:
                _text, attr = __text
            vv = NSTextView.alloc().initWithFrame_(NSRect((0, 0), frame.size))
            vv.setDrawsBackground_(NO)
            vv.setEditable_(NO)
            vv.setSelectable_(NO)
            vv.setAlignment_range_(NSCenterTextAlignment, NSMakeRange(0, vv.string().length()))
            vv.textStorage().beginEditing()
            vv.textStorage().mutableString().setString_(_text)
            vv.textStorage().setFont_(NSFont.labelFontOfSize_(42 if _text in ('greetings', 'to') else 36))
            vv.textStorage().setForegroundColor_(NSColor.whiteColor())
            vv.textStorage().endEditing()
            vv.layoutManager().glyphRangeForTextContainer_(vv.textContainer())
            vv.setFrameSize_(vv.layoutManager().usedRectForTextContainer_(vv.textContainer()).size)
            setattr(self, attr, vv)
            vv.setHidden_(True)
            self.addSubview_(vv)

        self.blast_order = (self.greetings,
         self.to,
         self.AAPL,
         self.GOOG,
         self.MSFT,
         self._smile)
        self.greetings.setHidden_(False)
        self.greetings.setFrameOrigin_(((frame.size[0] - self.greetings.frame().size[0]) / 2.0, BASE_HEIGHT - 100))
        self.to.setFrameOrigin_(((frame.size[0] - self.to.frame().size[0]) / 2.0, BASE_HEIGHT - 100 - self.greetings.frame().size[1] - 20))
        offset = (frame.size[0] - (self.AAPL.frame().size[0] + self.GOOG.frame().size[0] + 60)) / 2.0
        self.AAPL_POS = (offset, 220)
        self.GOOG_POS = (WIDTH - self.GOOG.frame().size[0] - offset, 220)
        self.MSFT_POS = ((frame.size[0] - self.MSFT.frame().size[0]) / 2.0, 200 - self.AAPL.frame().size[1] - 80)
        self._wink.setFrameOrigin_(((frame.size[0] - self._wink.frame().size[0]) / 2.0, 200 - self._wink.frame().size[1]))
        self._smile.setFrameOrigin_(((frame.size[0] - self._wink.frame().size[0]) / 2.0, 200 - self._wink.frame().size[1]))
        return self

    def doPresentation_(self, done_cb):
        self.done_cb = done_cb
        AppHelper.callLater(self.DELAY * 2, self.playTo)

    def playTo(self):
        self.to.setHidden_(False)
        AppHelper.callLater(self.DELAY * 2, self.playAAPL)

    def moveAAPL_(self, new_height):
        self.AAPL.setFrameOrigin_((self.AAPL_POS[0], new_height))

    def playAAPL(self):
        self.AAPL.setHidden_(False)
        self.timers.append(SpringAnimator(0 - self.AAPL.frame().size[1], self.AAPL_POS[1], 60.0, 8.0, 2, 1 / 30.0, self.moveAAPL_, None))
        AppHelper.callLater(self.DELAY, self.playGOOG)

    def moveGOOG_(self, new_height):
        self.GOOG.setFrameOrigin_((self.GOOG_POS[0], new_height))

    def playGOOG(self):
        self.GOOG.setHidden_(False)
        self.timers.append(SpringAnimator(0 - self.GOOG.frame().size[1], self.GOOG_POS[1], 60.0, 8.0, 2, 1 / 30.0, self.moveGOOG_, None))
        AppHelper.callLater(self.DELAY, self.playMSFT)

    def moveMSFT_(self, new_height):
        self.MSFT.setFrameOrigin_((self.MSFT_POS[0], new_height))

    def playMSFT(self):
        self.MSFT.setHidden_(False)
        self.timers.append(SpringAnimator(0 - self.MSFT.frame().size[1], self.MSFT_POS[1], 60.0, 8.0, 2, 1 / 30.0, self.moveMSFT_, None))
        AppHelper.callLater(self.DELAY * 2, self.winky)

    def winky(self):
        self._smile.setHidden_(False)
        AppHelper.callLater(self.DELAY * 2, self.winky2)

    def winky2(self):
        self._smile.setHidden_(True)
        self._wink.setHidden_(False)
        AppHelper.callLater(self.DELAY * 2, self.winky3)

    def winky3(self):
        self._smile.setHidden_(False)
        self._wink.setHidden_(True)
        self.blast_idx = 0
        AppHelper.callLater(self.DELAY * 2, self.start_blast)

    def move_view(self, startx, starty, destx, desty, view, param):
        view.setFrameOrigin_((startx + destx * param, starty + desty * param))

    def saveTimerForFunc_args_kwargs_(self, func, n, kw):

        def new():
            self.timers.append(func(*n, **kw))

        return new

    def stopTimers(self):
        for t in self.timers:
            t.invalidate()

    def dealloc(self):
        self.stopTimers()
        super(GreetingsTo, self).dealloc()

    def start_blast(self):
        w, h = self.frame().size
        radius = math.sqrt((w / 2) ** 2 + (h / 2) ** 2) + 100
        for i, _vi in enumerate(self.blast_order):
            startx, starty = _vi.frame().origin
            direction = insecure_random.random() * 2 * math.pi
            newx = radius * math.cos(direction) + w / 2.0
            newy = radius * math.sin(direction) + h / 2.0
            AppHelper.callLater(self.DELAY * i, self.saveTimerForFunc_args_kwargs_(SpringAnimator, (0,
             1.0,
             60.0,
             8.0,
             4,
             1 / 30.0,
             functools.partial(self.move_view, startx, starty, newx - startx, newy - starty, _vi),
             None), {}))

        if self.done_cb:
            AppHelper.callLater((len(self.blast_order) + 2) * self.DELAY, self.done_cb)


class BackgroundView(NSView):

    def initWithFrame_(self, frame):
        self = super(BackgroundView, self).initWithFrame_(frame)
        if not self:
            return
        full_rect = NSRect((0, 0), frame.size)
        self.msg = GreetingsToView.alloc().initWithFrame_(full_rect)
        self.addSubview_(self.msg)
        self.msg.setHidden_(True)
        self.fview = GreetingsTo.alloc().initWithFrame_(full_rect)
        self.addSubview_(self.fview)
        gradient = CIFilter.filterWithName_('CILinearGradient')
        gradient.setValue_forKey_(CIVector.vectorWithX_Y_(0, BASE_HEIGHT), 'inputPoint0')
        gradient.setValue_forKey_(CIColor.colorWithRed_green_blue_alpha_(0, 81 / 255.0, 164 / 255.0, 1.0), 'inputColor0')
        gradient.setValue_forKey_(CIVector.vectorWithX_Y_(0, 0), 'inputPoint1')
        gradient.setValue_forKey_(CIColor.colorWithRed_green_blue_alpha_(32 / 255.0, 127 / 255.0, 209 / 255.0, 1.0), 'inputColor1')
        self.outputGradient2 = gradient.valueForKey_('outputImage')
        return self

    def doPresentation_(self, done_cb):
        self.done_cb = done_cb
        self.window().fadeIn(functools.partial(self.fview.doPresentation_, self.when_done))

    def when_done(self):
        self.fview.setHidden_(True)
        self.msg.setHidden_(False)
        self.msg.doPresentation_(self.done_cb)

    def isOpaque(self):
        return YES

    def drawRect_(self, rect):
        super(BackgroundView, self).drawRect_(rect)
        NSGraphicsContext.currentContext().CIContext().drawImage_atPoint_fromRect_(self.outputGradient2, (0, 0), NSRect((0, 0), (WIDTH, BASE_HEIGHT)))


class SickView(NSView):

    def initWithFrame_imageDir_(self, frame, imageDir):
        self = super(SickView, self).initWithFrame_(frame)
        if not self:
            return
        r = NSRect((0, 0), frame.size)
        self.intro = Introduction.alloc().initWithFrame_imageDir_(r, imageDir)
        self.greetings_to = BackgroundView.alloc().initWithFrame_(r)
        self.greetings_to.setHidden_(True)
        self.addSubview_(self.intro)
        self.addSubview_(self.greetings_to)
        return self

    def doPresentation_(self, done_cb):
        self.done_cb = done_cb
        self.intro.doPresentation_(self.whenDone)

    def whenDone(self):
        self.greetings_to.setHidden_(False)
        self.intro.setHidden_(True)
        self.greetings_to.doPresentation_(self.whenDone2)

    def whenDone2(self):
        self.greetings_to.setHidden_(True)
        self.intro.setHidden_(False)
        self.intro.scrollTop()
        self.window().fadeIn(self.done_cb)


class ColorView(NSView):

    def initWithFrame_(self, frame):
        self = super(ColorView, self).initWithFrame_(frame)
        if not self:
            return
        self.color = NSColor.whiteColor()
        return self

    def setColor_(self, color):
        self.color = color
        self.setNeedsDisplay_(YES)

    def isOpaque(self):
        return YES

    def drawRect_(self, rect):
        super(ColorView, self).drawRect_(rect)
        self.color.set()
        NSRectFill(self.bounds())


class SickWindow(NSWindow):
    WIDTH = WIDTH
    HEIGHT = BASE_HEIGHT

    def initWithImageDir_(self, imageDir):
        self = super(SickWindow, self).initWithContentRect_styleMask_backing_defer_(NSRect((0, 0), (self.WIDTH, self.HEIGHT)), NSTitledWindowMask | NSClosableWindowMask | NSMiniaturizableWindowMask, NSBackingStoreBuffered, YES)
        if not self:
            return
        self.ani = None
        self.setContentView_(SickView.alloc().initWithFrame_imageDir_(NSRect((0, 0), (self.WIDTH, self.HEIGHT)), imageDir))
        self.setTitle_(u'X marks the spot')
        self.started = False
        self.fade_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(NSRect(self.frame().origin, (self.WIDTH, self.HEIGHT)), NSBorderlessWindowMask, NSBackingStoreBuffered, YES)
        self.fade_window.setOpaque_(NO)
        self.fade_window.setLevel_(NSFloatingWindowLevel)
        self.fade_window.setIgnoresMouseEvents_(YES)
        self.fade_window.setAlphaValue_(0.0)
        self.fade_window.setContentView_(ColorView.alloc().initWithFrame_(NSRect((0, 0), (self.WIDTH, self.HEIGHT))))
        self.fade_window.orderFront_(self)
        self.fade_window.setReleasedWhenClosed_(NO)
        self.addChildWindow_ordered_(self.fade_window, NSWindowAbove)
        self.setReleasedWhenClosed_(NO)
        return self

    def center(self):
        super(SickWindow, self).center()
        self.fade_window.setFrameOrigin_(self.frame().origin)

    def reverseExponent_(self, val):
        self.fade_window.setAlphaValue_(math.exp(-val * 2))

    def stopTimers(self):
        if self.ani:
            self.ani.invalidate()
        _v = self.contentView()
        if not _v:
            return
        d = [_v]
        while d:
            v = d.pop()
            try:
                v.stopTimers()
            except:
                pass

            d.extend(v.subviews())

    def windowShouldClose_(self, sender):
        try:
            self.stopTimers()
        except:
            pass

        return YES

    def dealloc(self):
        try:
            self.stopTimers()
        except:
            pass

        super(SickWindow, self).dealloc()

    def fadeIn(self, when_done):
        if self.ani:
            self.ani.invalidate()
        self.done_cb = when_done
        self.ani = LinearAnimator.alloc().initWithStartVal_endVal_duration_interval_valueCb_doneCb_(0, 2.0, 2.0, 1 / 60.0, self.reverseExponent_, self.when_done)

    def when_done(self):
        self.fade_window.setAlphaValue_(0.0)
        if self.done_cb:
            self.done_cb()

    def mouseDown_(self, theev):
        try:
            if not self.started:
                self.contentView().doPresentation_(self.done_cb)
                self.started = True
        except:
            pass

    def doPresentation_(self, done_cb):
        AppHelper.callLater(5, self.mouseDown_, (None,))
        self.done_cb = done_cb

    def makeKeyAndOrderFront_(self, sender):
        super(SickWindow, self).makeKeyAndOrderFront_(sender)
        self.doPresentation_(self.done)

    def done(self):
        pass


if __name__ == '__main__':
    yo = [0, 0]

    class WindowDelegate(NSObject):

        def windowWillClose_(self, notification):
            AppHelper.stopEventLoop()


    class ApplicationDelegate(NSObject):

        def __new__(cls):
            return ApplicationDelegate.alloc().init()

        def applicationWillFinishLaunching_(self, notication):
            try:
                img_dir = os.path.join(os.getcwd(), u'images/about')
                if not os.path.exists(img_dir):
                    raise Exception("Can't find images dir; looking in %s" % (img_dir,))
                yo[0] = SickWindow.alloc().initWithImageDir_(img_dir)
                yo[1] = WindowDelegate.alloc().init()
                yo[0].setDelegate_(yo[1])
                yo[0].makeKeyAndOrderFront_(nil)
                yo[0].orderFrontRegardless()
                yo[0].center()
                NSApp().activateIgnoringOtherApps_(True)
            except:
                import traceback
                traceback.print_exc()


    app = NSApplication.sharedApplication()
    holder = ApplicationDelegate()
    app.setDelegate_(holder)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    AppHelper.runEventLoop()
