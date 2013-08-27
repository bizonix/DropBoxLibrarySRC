#Embedded file name: ui/common/strings.py
import sys
import types
from dropbox.i18n import trans
DONT_TRANSLATE = "DON'T TRANSLATE"

class UIStringsMeta(type):

    def __init__(cls, classname, bases, class_dict):
        if bases[0] is not object:
            for attr in ['_platform_overrides', '_strings']:
                assert attr in class_dict, "Classes deriving from UIStringsMeta must have a '%s' class attribute" % (attr,)

            for k, v in class_dict['_strings'].iteritems():
                if type(v) not in types.StringTypes:
                    assert len(v) == 2, "UIStrings tuples must have length two; '%s.%s' does not" % (classname, k)
                    v = v[0]
                assert isinstance(v, unicode), "All UI visible strings must be Unicode; '%s.%s' is not" % (classname, k)

            for platform, overrides in class_dict['_platform_overrides'].iteritems():
                for k, v in overrides.iteritems():
                    if type(v) not in types.StringTypes:
                        assert len(v) == 2, "UIStrings tuples must have length two; '%s._platform_overrides['%s']['%s']' does not" % (classname, platform, k)
                        v = v[0]
                    assert isinstance(v, unicode), "All UI visible strings must be Unicode; '%s._platform_overrides['%s']['%s']' is not" % (classname, platform, k)

    def __getitem__(cls, key):
        try:
            return getattr(cls, key)
        except AttributeError as e:
            raise KeyError(*e.args)

    def get(cls, key, default = None):
        try:
            return cls[key]
        except KeyError:
            return default

    def __getattr__(cls, attr):
        if attr not in cls._strings:
            raise AttributeError("String '%s' is not defined." % attr)
        try:
            choice = cls._platform_overrides[cls.platform()][attr]
        except KeyError:
            choice = cls._strings[attr]

        try:
            uistring = cls._server_overrides[attr]
        except KeyError:
            if type(choice) not in types.StringTypes:
                choice = choice[0]
            uistring = trans(choice)

        return uistring


class UIStrings(object):
    __metaclass__ = UIStringsMeta
    _server_overrides = {}

    @classmethod
    def platform(cls):
        if sys.platform.startswith('darwin'):
            return 'mac'
        elif sys.platform.startswith('win'):
            return 'win'
        else:
            return 'linux'
