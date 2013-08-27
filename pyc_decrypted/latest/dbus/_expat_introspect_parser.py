#Embedded file name: dbus/_expat_introspect_parser.py
from xml.parsers.expat import ExpatError, ParserCreate
from dbus.exceptions import IntrospectionParserException

class _Parser(object):
    __slots__ = ('map', 'in_iface', 'in_method', 'sig')

    def __init__(self):
        self.map = {}
        self.in_iface = ''
        self.in_method = ''
        self.sig = ''

    def parse(self, data):
        parser = ParserCreate('UTF-8', ' ')
        parser.buffer_text = True
        parser.StartElementHandler = self.StartElementHandler
        parser.EndElementHandler = self.EndElementHandler
        parser.Parse(data)
        return self.map

    def StartElementHandler(self, name, attributes):
        if not self.in_iface:
            if not self.in_method and name == 'interface':
                self.in_iface = attributes['name']
        elif not self.in_method and name == 'method':
            self.in_method = attributes['name']
        elif self.in_method and name == 'arg':
            if attributes.get('direction', 'in') == 'in':
                self.sig += attributes['type']

    def EndElementHandler(self, name):
        if self.in_iface:
            if not self.in_method and name == 'interface':
                self.in_iface = ''
            elif self.in_method and name == 'method':
                self.map[self.in_iface + '.' + self.in_method] = self.sig
                self.in_method = ''
                self.sig = ''


def process_introspection_data(data):
    try:
        return _Parser().parse(data)
    except Exception as e:
        raise IntrospectionParserException('%s: %s' % (e.__class__, e))
