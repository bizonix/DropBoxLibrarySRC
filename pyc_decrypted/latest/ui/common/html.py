#Embedded file name: ui/common/html.py
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

class HTMLTextConverter(HTMLParser):

    @classmethod
    def convert(cls, html):
        parser = cls()
        parser.feed(html)
        return ''.join(parser.text)

    def __init__(self):
        self.text = []
        HTMLParser.__init__(self)

    def handle_charref(self, name):
        if name.startswith('x') or name.startswith('X'):
            self.text.append(unichr(int(name[1:], 16)))
        else:
            self.text.append(unichr(int(name)))

    def handle_entityref(self, name):
        self.text.append(unichr(name2codepoint[name]))

    def handle_data(self, data):
        self.text.append(data)


if __name__ == '__main__':
    actual = HTMLTextConverter.convert(u"<p>Todd &amp; &#83;ujay are SICK&#x21;</p><img\nsrc='foo'><>")
    expected = u'Todd & Sujay are SICK!<>'
    assert expected == actual, (expected, actual)
