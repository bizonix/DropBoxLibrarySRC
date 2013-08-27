#Embedded file name: babel/util.py
import codecs
from datetime import timedelta, tzinfo
import os
import re
try:
    set = set
except NameError:
    from sets import Set as set

import textwrap
import time
from itertools import izip, imap
missing = object()
__all__ = ['distinct',
 'pathmatch',
 'relpath',
 'wraptext',
 'odict',
 'UTC',
 'LOCALTZ']
__docformat__ = 'restructuredtext en'

def distinct(iterable):
    seen = set()
    for item in iter(iterable):
        if item not in seen:
            yield item
            seen.add(item)


PYTHON_MAGIC_COMMENT_re = re.compile('[ \\t\\f]* \\# .* coding[=:][ \\t]*([-\\w.]+)', re.VERBOSE)

def parse_encoding(fp):
    pos = fp.tell()
    fp.seek(0)
    try:
        line1 = fp.readline()
        has_bom = line1.startswith(codecs.BOM_UTF8)
        if has_bom:
            line1 = line1[len(codecs.BOM_UTF8):]
        m = PYTHON_MAGIC_COMMENT_re.match(line1)
        if not m:
            try:
                import parser
                parser.suite(line1)
            except (ImportError, SyntaxError):
                pass
            else:
                line2 = fp.readline()
                m = PYTHON_MAGIC_COMMENT_re.match(line2)

        if has_bom:
            if m:
                raise SyntaxError('python refuses to compile code with both a UTF8 byte-order-mark and a magic encoding comment')
            return 'utf_8'
        if m:
            return m.group(1)
        return
    finally:
        fp.seek(pos)


def pathmatch(pattern, filename):
    symbols = {'?': '[^/]',
     '?/': '[^/]/',
     '*': '[^/]+',
     '*/': '[^/]+/',
     '**/': '(?:.+/)*?',
     '**': '(?:.+/)*?[^/]+'}
    buf = []
    for idx, part in enumerate(re.split('([?*]+/?)', pattern)):
        if idx % 2:
            buf.append(symbols[part])
        elif part:
            buf.append(re.escape(part))

    match = re.match(''.join(buf) + '$', filename.replace(os.sep, '/'))
    return match is not None


class TextWrapper(textwrap.TextWrapper):
    wordsep_re = re.compile('(\\s+|(?<=[\\w\\!\\"\\\'\\&\\.\\,\\?])-{2,}(?=\\w))')


def wraptext(text, width = 70, initial_indent = '', subsequent_indent = ''):
    wrapper = TextWrapper(width=width, initial_indent=initial_indent, subsequent_indent=subsequent_indent, break_long_words=False)
    return wrapper.wrap(text)


class odict(dict):

    def __init__(self, data = None):
        dict.__init__(self, data or {})
        self._keys = dict.keys(self)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        if key not in self._keys:
            self._keys.append(key)

    def __iter__(self):
        return iter(self._keys)

    iterkeys = __iter__

    def clear(self):
        dict.clear(self)
        self._keys = []

    def copy(self):
        d = odict()
        d.update(self)
        return d

    def items(self):
        return zip(self._keys, self.values())

    def iteritems(self):
        return izip(self._keys, self.itervalues())

    def keys(self):
        return self._keys[:]

    def pop(self, key, default = missing):
        if default is missing:
            return dict.pop(self, key)
        if key not in self:
            return default
        self._keys.remove(key)
        return dict.pop(self, key, default)

    def popitem(self, key):
        self._keys.remove(key)
        return dict.popitem(key)

    def setdefault(self, key, failobj = None):
        dict.setdefault(self, key, failobj)
        if key not in self._keys:
            self._keys.append(key)

    def update(self, dict):
        for key, val in dict.items():
            self[key] = val

    def values(self):
        return map(self.get, self._keys)

    def itervalues(self):
        return imap(self.get, self._keys)


try:
    relpath = os.path.relpath
except AttributeError:

    def relpath(path, start = '.'):
        start_list = os.path.abspath(start).split(os.sep)
        path_list = os.path.abspath(path).split(os.sep)
        i = len(os.path.commonprefix([start_list, path_list]))
        rel_list = [os.path.pardir] * (len(start_list) - i) + path_list[i:]
        return os.path.join(*rel_list)


try:
    from operator import attrgetter, itemgetter
except ImportError:

    def itemgetter(name):

        def _getitem(obj):
            return obj[name]

        return _getitem


try:
    ''.rsplit

    def rsplit(a_string, sep = None, maxsplit = None):
        return a_string.rsplit(sep, maxsplit)


except AttributeError:

    def rsplit(a_string, sep = None, maxsplit = None):
        parts = a_string.split(sep)
        if maxsplit is None or len(parts) <= maxsplit:
            return parts
        maxsplit_index = len(parts) - maxsplit
        non_splitted_part = sep.join(parts[:maxsplit_index])
        splitted = parts[maxsplit_index:]
        return [non_splitted_part] + splitted


ZERO = timedelta(0)

class FixedOffsetTimezone(tzinfo):

    def __init__(self, offset, name = None):
        self._offset = timedelta(minutes=offset)
        if name is None:
            name = 'Etc/GMT+%d' % offset
        self.zone = name

    def __str__(self):
        return self.zone

    def __repr__(self):
        return '<FixedOffset "%s" %s>' % (self.zone, self._offset)

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return self.zone

    def dst(self, dt):
        return ZERO


try:
    from pytz import UTC
except ImportError:
    UTC = FixedOffsetTimezone(0, 'UTC')

STDOFFSET = timedelta(seconds=-time.timezone)
if time.daylight:
    DSTOFFSET = timedelta(seconds=-time.altzone)
else:
    DSTOFFSET = STDOFFSET
DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year,
         dt.month,
         dt.day,
         dt.hour,
         dt.minute,
         dt.second,
         dt.weekday(),
         0,
         -1)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0


LOCALTZ = LocalTimezone()
