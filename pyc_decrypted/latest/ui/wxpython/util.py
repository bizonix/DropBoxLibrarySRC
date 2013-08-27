#Embedded file name: ui/wxpython/util.py
from __future__ import absolute_import
from contextlib import contextmanager
import re
import wx
from dropbox.i18n import get_current_code
from ..common.constants import ResizeMethod

def dirty_rects(window):
    ri = wx.RegionIterator(window.GetUpdateRegion())
    while ri:
        yield ri.GetRect()
        ri.Next()


@contextmanager
def draw_on_bitmap(bmp):
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    try:
        yield dc
    finally:
        dc.SelectObject(wx.NullBitmap)
        del dc


_JA_OPENING_BRACKETS = u'\uff5b\u3014\u3008\u300a\u300c\u300e\u3010\u3018\u3016\u301d\u2018\u201c\uff5f\xab\\[\\('
_JA_CLOSING_BRACKETS = u'\uff5d\u3015\u3009\u300b\u300d\u300f\u3011\u3019\u3017\u301f\u2019\u201d\uff60\xbb\\]\\)'
_JA_DO_NOT_SPLIT = u'0-9\u2014\u2026\u2025\u3033\u3034\u3035'
_JA_CHAR_NOT_AT_LINE_START = u'\u30fd\u30fe\u30fc\u30a1\u30a3\u30a5\u30a7\u30a9\u30c3\u30e3\u30e5\u30e7\u30ee\u30f5\u30f6' + u'\u3041\u3043\u3045\u3047\u3049\u3063\u3083\u3085\u3087\u308e\u3095\u3096\u31f0\u31f1\u31f2' + u'\u31f3\u31f4\u31f5\u31f6\u31f7\u31f8\u31f9\u31fa\u31fb\u31fc\u31fd\u31fe\u31ff\u3005\u303b'
_JA_HYPHENS = u'\u2010\u30a0\u2013\u301c'
_JA_DELIMITERS = u'?!\u203c\u2047\u2048\u2049'
_JA_MID_AND_END_SENTENCE_PUNCTUATION = u'\u30fb\u3001:;,\u3002.'
_JA_NOT_ALLOWED_AT_END_OF_LINE = _JA_OPENING_BRACKETS + _JA_DO_NOT_SPLIT + 'a-zA-Z.'
_JA_NOT_ALLOWED_AT_START_OF_LINE = _JA_CLOSING_BRACKETS + _JA_CHAR_NOT_AT_LINE_START + _JA_HYPHENS + _JA_DELIMITERS + _JA_MID_AND_END_SENTENCE_PUNCTUATION
JA_BREAK_RE = re.compile(u'[^%s][^%s]' % (_JA_NOT_ALLOWED_AT_END_OF_LINE, _JA_NOT_ALLOWED_AT_START_OF_LINE))

def wordwrap_helper(text, width, dc, breakLongWords = True, margin = 0):
    wrapped_lines = []
    if dc.GetTextExtent(text)[0] <= width - margin * 2:
        return text.split('\n')
    text = text.split('\n')
    is_japanese = get_current_code() == 'ja'
    for line in text:
        pte = dc.GetPartialTextExtents(line)
        wid = width - (2 * margin + 1) * dc.GetTextExtent(' ')[0] - max([0] + [ pte[i] - pte[i - 1] for i in range(1, len(pte)) ])
        idx = 0
        start = 0
        startIdx = 0
        spcIdx = -1
        while idx < len(pte):
            if line[idx] == ' ':
                spcIdx = idx
            if is_japanese and re.match(JA_BREAK_RE, line[idx:]):
                spcIdx = idx
            if pte[idx] - start > wid and (spcIdx != -1 or breakLongWords):
                if spcIdx != -1:
                    idx = spcIdx + 1
                wrapped_lines.append(' ' * margin + line[startIdx:idx] + ' ' * margin)
                start = pte[idx]
                startIdx = idx
                spcIdx = -1
            idx += 1

        wrapped_lines.append(' ' * margin + line[startIdx:idx] + ' ' * margin)

    return wrapped_lines


def wordwrap(text, width, dc, breakLongWords = True, margin = 0):
    return '\n'.join(wordwrap_helper(text, width, dc, breakLongWords, margin))


HREF_RE = re.compile('<a href="(?P<url>[^"]*)">(?P<text>[^<]*)</a>')

class ExtendedLinkedText(unicode):
    __slots__ = ('raw_text', 'url', 'start', 'end')

    def __new__(cls, raw_text):
        match = HREF_RE.search(raw_text)
        if not match:
            raise Exception('No HREF match in %r' % (raw_text,))
        text = raw_text[:match.start()] + match.group('text') + raw_text[match.end():]
        return unicode.__new__(cls, text)

    def __init__(self, raw_text):
        self.raw_text = raw_text
        match = HREF_RE.search(raw_text)
        if HREF_RE.search(self.raw_text, match.end()):
            raise Exception('More than one HREF match in %r' % (raw_text,))
        link_text = match.group('text')
        self.url = match.group('url')
        self.start = match.start()
        self.end = self.start + len(link_text)


SPACE_TOKENS = ' \t\n'
_SLASH_TOKENS = '/\\'
_POSS_BREAK = re.compile('[%s%s<]' % (SPACE_TOKENS, _SLASH_TOKENS))

def tokenize(s):
    is_japanese = get_current_code() == 'ja'
    poss_break = JA_BREAK_RE if is_japanese else _POSS_BREAK
    in_link = False
    pieces = []
    _len = len(s)
    i = 0
    last_offset = 0
    while i < _len:
        match = poss_break.search(s, i)
        if not match:
            break
        i = match.start()
        c = s[i]
        if c == '<':
            link_match = HREF_RE.match(s, i)
            if link_match:
                if in_link == True:
                    if last_offset < i:
                        pieces.append((s[last_offset:i], in_link))
                    last_offset = i
                in_link = True
                i = link_match.end()
                continue
        if c in SPACE_TOKENS:
            if last_offset < i:
                pieces.append((s[last_offset:i], in_link))
            in_link = False
            pieces.append((c, False))
            last_offset = i + 1
        elif is_japanese or c in _SLASH_TOKENS:
            pieces.append((s[last_offset:i + 1], in_link))
            in_link = False
            last_offset = i + 1
        i += 1

    if last_offset < _len:
        pieces.append((s[last_offset:_len], in_link))
    tokens = [ (ExtendedLinkedText(text) if in_link else text) for text, in_link in pieces ]
    return tokens


def resize_image(source_img, dimensions, method = ResizeMethod.FIT):
    initial_width = float(dimensions[0])
    initial_height = float(dimensions[1])
    width = source_img.GetWidth()
    height = source_img.GetHeight()
    pixel_size = (width, height)
    width_ratio = initial_width / pixel_size[0]
    height_ratio = initial_height / pixel_size[1]
    if method == ResizeMethod.FIT:
        width_ratio = min(width_ratio, height_ratio)
        height_ratio = min(width_ratio, height_ratio)
    if method == ResizeMethod.CROP:
        width_ratio = max(width_ratio, height_ratio)
        height_ratio = max(width_ratio, height_ratio)
    resized_width = width * width_ratio
    resized_height = height * height_ratio
    crop_width = width
    crop_height = height
    if method is ResizeMethod.CROP:
        crop_width = initial_width / resized_width * width
        crop_height = initial_height / resized_height * height
    final_width = min(resized_width, initial_width)
    final_height = min(resized_height, initial_height)
    rect = wx.Rect((width - crop_width) / 2, (height - crop_height) / 2, crop_width, crop_height)
    sub_image = source_img.GetSubImage(rect)
    target_img = sub_image.Rescale(final_width, final_height, quality=wx.IMAGE_QUALITY_HIGH)
    return target_img
