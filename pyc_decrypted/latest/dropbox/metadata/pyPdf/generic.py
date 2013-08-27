#Embedded file name: dropbox/metadata/pyPdf/generic.py
__author__ = 'Mathieu Fenniak'
__author_email__ = 'biziqe@mathieu.fenniak.net'
import re
from utils import readNonWhitespace, RC4_encrypt
import filters
import utils
import decimal
import codecs

def readObject(stream, pdf):
    tok = stream.read(1)
    stream.seek(-1, 1)
    if tok == 't' or tok == 'f':
        return BooleanObject.readFromStream(stream)
    if tok == '(':
        return readStringFromStream(stream)
    if tok == '/':
        return NameObject.readFromStream(stream)
    if tok == '[':
        return ArrayObject.readFromStream(stream, pdf)
    if tok == 'n':
        return NullObject.readFromStream(stream)
    if tok == '<':
        peek = stream.read(2)
        stream.seek(-2, 1)
        if peek == '<<':
            return DictionaryObject.readFromStream(stream, pdf)
        else:
            return readHexStringFromStream(stream)
    else:
        if tok == '%':
            while tok not in ('\r', '\n'):
                tok = stream.read(1)

            tok = readNonWhitespace(stream)
            stream.seek(-1, 1)
            return readObject(stream, pdf)
        if tok == '+' or tok == '-':
            return NumberObject.readFromStream(stream)
        peek = stream.read(20)
        stream.seek(-len(peek), 1)
        if re.match('(\\d+)\\s(\\d+)\\sR[^a-zA-Z]', peek) != None:
            return IndirectObject.readFromStream(stream, pdf)
        return NumberObject.readFromStream(stream)


class PdfObject(object):

    def getObject(self):
        return self


class NullObject(PdfObject):

    def writeToStream(self, stream, encryption_key):
        stream.write('null')

    def readFromStream(stream):
        nulltxt = stream.read(4)
        if nulltxt != 'null':
            raise utils.PdfReadError('error reading null object')
        return NullObject()

    readFromStream = staticmethod(readFromStream)


class BooleanObject(PdfObject):

    def __init__(self, value):
        self.value = value

    def writeToStream(self, stream, encryption_key):
        if self.value:
            stream.write('true')
        else:
            stream.write('false')

    def readFromStream(stream):
        word = stream.read(4)
        if word == 'true':
            return BooleanObject(True)
        if word == 'fals':
            stream.read(1)
            return BooleanObject(False)
        assert False

    readFromStream = staticmethod(readFromStream)


class ArrayObject(list, PdfObject):

    def writeToStream(self, stream, encryption_key):
        stream.write('[')
        for data in self:
            stream.write(' ')
            data.writeToStream(stream, encryption_key)

        stream.write(' ]')

    def readFromStream(stream, pdf):
        arr = ArrayObject()
        tmp = stream.read(1)
        if tmp != '[':
            raise utils.PdfReadError('error reading array')
        while True:
            tok = stream.read(1)
            while tok.isspace():
                tok = stream.read(1)

            stream.seek(-1, 1)
            peekahead = stream.read(1)
            if peekahead == ']':
                break
            stream.seek(-1, 1)
            arr.append(readObject(stream, pdf))

        return arr

    readFromStream = staticmethod(readFromStream)


class IndirectObject(PdfObject):

    def __init__(self, idnum, generation, pdf):
        self.idnum = idnum
        self.generation = generation
        self.pdf = pdf

    def getObject(self):
        return self.pdf.getObject(self).getObject()

    def __repr__(self):
        return 'IndirectObject(%r, %r)' % (self.idnum, self.generation)

    def __eq__(self, other):
        return other != None and isinstance(other, IndirectObject) and self.idnum == other.idnum and self.generation == other.generation and self.pdf is other.pdf

    def __ne__(self, other):
        return not self.__eq__(other)

    def writeToStream(self, stream, encryption_key):
        stream.write('%s %s R' % (self.idnum, self.generation))

    def readFromStream(stream, pdf):
        idnum = ''
        while True:
            tok = stream.read(1)
            if tok.isspace():
                break
            idnum += tok

        generation = ''
        while True:
            tok = stream.read(1)
            if tok.isspace():
                break
            generation += tok

        r = stream.read(1)
        if r != 'R':
            raise utils.PdfReadError('error reading indirect object reference')
        return IndirectObject(int(idnum), int(generation), pdf)

    readFromStream = staticmethod(readFromStream)


class FloatObject(decimal.Decimal, PdfObject):

    def __new__(cls, value = '0', context = None):
        return decimal.Decimal.__new__(cls, str(value), context)

    def __repr__(self):
        if self == self.to_integral():
            return str(self.quantize(decimal.Decimal(1)))
        else:
            return '%.5f' % self

    def writeToStream(self, stream, encryption_key):
        stream.write(repr(self))


class NumberObject(int, PdfObject):

    def __init__(self, value):
        int.__init__(value)

    def writeToStream(self, stream, encryption_key):
        stream.write(repr(self))

    def readFromStream(stream):
        name = ''
        while True:
            tok = stream.read(1)
            if tok != '+' and tok != '-' and tok != '.' and not tok.isdigit():
                stream.seek(-1, 1)
                break
            name += tok

        if name.find('.') != -1:
            return FloatObject(name)
        else:
            return NumberObject(name)

    readFromStream = staticmethod(readFromStream)


def createStringObject(string):
    if isinstance(string, unicode):
        return TextStringObject(string)
    if isinstance(string, str):
        if string.startswith(codecs.BOM_UTF16_BE):
            retval = TextStringObject(string.decode('utf-16'))
            retval.autodetect_utf16 = True
            return retval
        try:
            retval = TextStringObject(decode_pdfdocencoding(string))
            retval.autodetect_pdfdocencoding = True
            return retval
        except UnicodeDecodeError:
            return ByteStringObject(string)

    else:
        raise TypeError('createStringObject should have str or unicode arg')


def readHexStringFromStream(stream):
    stream.read(1)
    txt = ''
    x = ''
    while True:
        tok = readNonWhitespace(stream)
        if tok == '>':
            break
        x += tok
        if len(x) == 2:
            txt += chr(int(x, base=16))
            x = ''

    if len(x) == 1:
        x += '0'
    if len(x) == 2:
        txt += chr(int(x, base=16))
    return createStringObject(txt)


def readStringFromStream(stream):
    tok = stream.read(1)
    parens = 1
    txt = ''
    while True:
        tok = stream.read(1)
        if tok == '(':
            parens += 1
        elif tok == ')':
            parens -= 1
            if parens == 0:
                break
        elif tok == '\\':
            tok = stream.read(1)
            if tok == 'n':
                tok = '\n'
            elif tok == 'r':
                tok = '\r'
            elif tok == 't':
                tok = '\t'
            elif tok == 'b':
                tok = '\x08'
            elif tok == 'f':
                tok = '\x0c'
            elif tok == '(':
                tok = '('
            elif tok == ')':
                tok = ')'
            elif tok == '\\':
                tok = '\\'
            elif tok.isdigit():
                for i in range(2):
                    ntok = stream.read(1)
                    if ntok.isdigit():
                        tok += ntok
                    else:
                        break

                tok = chr(int(tok, base=8))
            elif tok in '\n\r':
                tok = stream.read(1)
                if tok not in '\n\r':
                    stream.seek(-1, 1)
                tok = ''
            else:
                raise utils.PdfReadError('Unexpected escaped string')
        txt += tok

    return createStringObject(txt)


class ByteStringObject(str, PdfObject):
    original_bytes = property(lambda self: self)

    def writeToStream(self, stream, encryption_key):
        bytearr = self
        if encryption_key:
            bytearr = RC4_encrypt(encryption_key, bytearr)
        stream.write('<')
        stream.write(bytearr.encode('hex'))
        stream.write('>')


class TextStringObject(unicode, PdfObject):
    autodetect_pdfdocencoding = False
    autodetect_utf16 = False
    original_bytes = property(lambda self: self.get_original_bytes())

    def get_original_bytes(self):
        if self.autodetect_utf16:
            return codecs.BOM_UTF16_BE + self.encode('utf-16be')
        if self.autodetect_pdfdocencoding:
            return encode_pdfdocencoding(self)
        raise Exception('no information about original bytes')

    def writeToStream(self, stream, encryption_key):
        try:
            bytearr = encode_pdfdocencoding(self)
        except UnicodeEncodeError:
            bytearr = codecs.BOM_UTF16_BE + self.encode('utf-16be')

        if encryption_key:
            bytearr = RC4_encrypt(encryption_key, bytearr)
            obj = ByteStringObject(bytearr)
            obj.writeToStream(stream, None)
        else:
            stream.write('(')
            for c in bytearr:
                if not c.isalnum() and c != ' ':
                    stream.write('\\%03o' % ord(c))
                else:
                    stream.write(c)

            stream.write(')')


class NameObject(str, PdfObject):
    delimiterCharacters = ('(', ')', '<', '>', '[', ']', '{', '}', '/', '%')

    def __init__(self, data):
        str.__init__(data)

    def writeToStream(self, stream, encryption_key):
        stream.write(self)

    def readFromStream(stream):
        name = stream.read(1)
        if name != '/':
            raise utils.PdfReadError('name read error')
        while True:
            tok = stream.read(1)
            if tok.isspace() or tok in NameObject.delimiterCharacters:
                stream.seek(-1, 1)
                break
            name += tok

        return NameObject(name)

    readFromStream = staticmethod(readFromStream)


class DictionaryObject(dict, PdfObject):

    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            self.update(kwargs)
        elif len(args) == 1:
            arr = args[0]
            if not hasattr(arr, 'iteritems'):
                newarr = {}
                for k, v in arr:
                    newarr[k] = v

                arr = newarr
            self.update(arr)
        else:
            raise TypeError('dict expected at most 1 argument, got 3')

    def update(self, arr):
        for k, v in arr.iteritems():
            self.__setitem__(k, v)

    def raw_get(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if not isinstance(key, PdfObject):
            raise ValueError('key must be PdfObject')
        if not isinstance(value, PdfObject):
            raise ValueError('value must be PdfObject')
        return dict.__setitem__(self, key, value)

    def setdefault(self, key, value = None):
        if not isinstance(key, PdfObject):
            raise ValueError('key must be PdfObject')
        if not isinstance(value, PdfObject):
            raise ValueError('value must be PdfObject')
        return dict.setdefault(self, key, value)

    def __getitem__(self, key):
        return dict.__getitem__(self, key).getObject()

    def getXmpMetadata(self):
        metadata = self.get('/Metadata', None)
        if metadata == None:
            return
        metadata = metadata.getObject()
        import xmp
        if not isinstance(metadata, xmp.XmpInformation):
            metadata = xmp.XmpInformation(metadata)
            self[NameObject('/Metadata')] = metadata
        return metadata

    xmpMetadata = property(lambda self: self.getXmpMetadata(), None, None)

    def writeToStream(self, stream, encryption_key):
        stream.write('<<\n')
        for key, value in self.items():
            key.writeToStream(stream, encryption_key)
            stream.write(' ')
            value.writeToStream(stream, encryption_key)
            stream.write('\n')

        stream.write('>>')

    def readFromStream(stream, pdf):
        tmp = stream.read(2)
        if tmp != '<<':
            raise utils.PdfReadError('dictionary read error')
        data = {}
        while True:
            tok = readNonWhitespace(stream)
            if tok == '>':
                stream.read(1)
                break
            stream.seek(-1, 1)
            key = readObject(stream, pdf)
            tok = readNonWhitespace(stream)
            stream.seek(-1, 1)
            value = readObject(stream, pdf)
            if data.has_key(key):
                raise utils.PdfReadError('multiple definitions in dictionary')
            data[key] = value

        pos = stream.tell()
        s = readNonWhitespace(stream)
        if s == 's' and stream.read(5) == 'tream':
            eol = stream.read(1)
            while eol == ' ':
                eol = stream.read(1)

            assert eol in ('\n', '\r')
            if eol == '\r':
                stream.read(1)
            assert data.has_key('/Length')
            length = data['/Length']
            if isinstance(length, IndirectObject):
                t = stream.tell()
                length = pdf.getObject(length)
                stream.seek(t, 0)
            data['__streamdata__'] = stream.read(length)
            e = readNonWhitespace(stream)
            ndstream = stream.read(8)
            if e + ndstream != 'endstream':
                pos = stream.tell()
                stream.seek(-10, 1)
                end = stream.read(9)
                if end == 'endstream':
                    data['__streamdata__'] = data['__streamdata__'][:-1]
                else:
                    stream.seek(pos, 0)
                    raise utils.PdfReadError("Unable to find 'endstream' marker after stream.")
        else:
            stream.seek(pos, 0)
        if data.has_key('__streamdata__'):
            return StreamObject.initializeFromDictionary(data)
        else:
            retval = DictionaryObject()
            retval.update(data)
            return retval

    readFromStream = staticmethod(readFromStream)


class StreamObject(DictionaryObject):

    def __init__(self):
        self._data = None
        self.decodedSelf = None

    def writeToStream(self, stream, encryption_key):
        self[NameObject('/Length')] = NumberObject(len(self._data))
        DictionaryObject.writeToStream(self, stream, encryption_key)
        del self['/Length']
        stream.write('\nstream\n')
        data = self._data
        if encryption_key:
            data = RC4_encrypt(encryption_key, data)
        stream.write(data)
        stream.write('\nendstream')

    def initializeFromDictionary(data):
        if data.has_key('/Filter'):
            retval = EncodedStreamObject()
        else:
            retval = DecodedStreamObject()
        retval._data = data['__streamdata__']
        del data['__streamdata__']
        del data['/Length']
        retval.update(data)
        return retval

    initializeFromDictionary = staticmethod(initializeFromDictionary)

    def flateEncode(self):
        if self.has_key('/Filter'):
            f = self['/Filter']
            if isinstance(f, ArrayObject):
                f.insert(0, NameObject('/FlateDecode'))
            else:
                newf = ArrayObject()
                newf.append(NameObject('/FlateDecode'))
                newf.append(f)
                f = newf
        else:
            f = NameObject('/FlateDecode')
        retval = EncodedStreamObject()
        retval[NameObject('/Filter')] = f
        retval._data = filters.FlateDecode.encode(self._data)
        return retval


class DecodedStreamObject(StreamObject):

    def getData(self):
        return self._data

    def setData(self, data):
        self._data = data


class EncodedStreamObject(StreamObject):

    def __init__(self):
        self.decodedSelf = None

    def getData(self):
        if self.decodedSelf:
            return self.decodedSelf.getData()
        else:
            decoded = DecodedStreamObject()
            decoded._data = filters.decodeStreamData(self)
            for key, value in self.items():
                if key not in ('/Length', '/Filter', '/DecodeParms'):
                    decoded[key] = value

            self.decodedSelf = decoded
            return decoded._data

    def setData(self, data):
        raise utils.PdfReadError('Creating EncodedStreamObject is not currently supported')


class RectangleObject(ArrayObject):

    def __init__(self, arr):
        assert len(arr) == 4
        ArrayObject.__init__(self, [ self.ensureIsNumber(x) for x in arr ])

    def ensureIsNumber(self, value):
        if not isinstance(value, (NumberObject, FloatObject)):
            value = FloatObject(value)
        return value

    def __repr__(self):
        return 'RectangleObject(%s)' % repr(list(self))

    def getLowerLeft_x(self):
        return self[0]

    def getLowerLeft_y(self):
        return self[1]

    def getUpperRight_x(self):
        return self[2]

    def getUpperRight_y(self):
        return self[3]

    def getUpperLeft_x(self):
        return self.getLowerLeft_x()

    def getUpperLeft_y(self):
        return self.getUpperRight_y()

    def getLowerRight_x(self):
        return self.getUpperRight_x()

    def getLowerRight_y(self):
        return self.getLowerLeft_y()

    def getLowerLeft(self):
        return (self.getLowerLeft_x(), self.getLowerLeft_y())

    def getLowerRight(self):
        return (self.getLowerRight_x(), self.getLowerRight_y())

    def getUpperLeft(self):
        return (self.getUpperLeft_x(), self.getUpperLeft_y())

    def getUpperRight(self):
        return (self.getUpperRight_x(), self.getUpperRight_y())

    def setLowerLeft(self, value):
        self[0], self[1] = [ self.ensureIsNumber(x) for x in value ]

    def setLowerRight(self, value):
        self[2], self[1] = [ self.ensureIsNumber(x) for x in value ]

    def setUpperLeft(self, value):
        self[0], self[3] = [ self.ensureIsNumber(x) for x in value ]

    def setUpperRight(self, value):
        self[2], self[3] = [ self.ensureIsNumber(x) for x in value ]

    def getWidth(self):
        return self.getUpperRight_x() - self.getLowerLeft_x()

    def getHeight(self):
        return self.getUpperRight_y() - self.getLowerLeft_x()

    lowerLeft = property(getLowerLeft, setLowerLeft, None, None)
    lowerRight = property(getLowerRight, setLowerRight, None, None)
    upperLeft = property(getUpperLeft, setUpperLeft, None, None)
    upperRight = property(getUpperRight, setUpperRight, None, None)


def encode_pdfdocencoding(unicode_string):
    retval = ''
    for c in unicode_string:
        try:
            retval += chr(_pdfDocEncoding_rev[c])
        except KeyError:
            raise UnicodeEncodeError('pdfdocencoding', c, -1, -1, 'does not exist in translation table')

    return retval


def decode_pdfdocencoding(byte_array):
    retval = u''
    for b in byte_array:
        c = _pdfDocEncoding[ord(b)]
        if c == u'\x00':
            raise UnicodeDecodeError('pdfdocencoding', b, -1, -1, 'does not exist in translation table')
        retval += c

    return retval


_pdfDocEncoding = (u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\x00', u'\u02d8', u'\u02c7', u'\u02c6', u'\u02d9', u'\u02dd', u'\u02db', u'\u02da', u'\u02dc', u' ', u'!', u'"', u'#', u'$', u'%', u'&', u"'", u'(', u')', u'*', u'+', u',', u'-', u'.', u'/', u'0', u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9', u':', u';', u'<', u'=', u'>', u'?', u'@', u'A', u'B', u'C', u'D', u'E', u'F', u'G', u'H', u'I', u'J', u'K', u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V', u'W', u'X', u'Y', u'Z', u'[', u'\\', u']', u'^', u'_', u'`', u'a', u'b', u'c', u'd', u'e', u'f', u'g', u'h', u'i', u'j', u'k', u'l', u'm', u'n', u'o', u'p', u'q', u'r', u's', u't', u'u', u'v', u'w', u'x', u'y', u'z', u'{', u'|', u'}', u'~', u'\x00', u'\u2022', u'\u2020', u'\u2021', u'\u2026', u'\u2014', u'\u2013', u'\u0192', u'\u2044', u'\u2039', u'\u203a', u'\u2212', u'\u2030', u'\u201e', u'\u201c', u'\u201d', u'\u2018', u'\u2019', u'\u201a', u'\u2122', u'\ufb01', u'\ufb02', u'\u0141', u'\u0152', u'\u0160', u'\u0178', u'\u017d', u'\u0131', u'\u0142', u'\u0153', u'\u0161', u'\u017e', u'\x00', u'\u20ac', u'\xa1', u'\xa2', u'\xa3', u'\xa4', u'\xa5', u'\xa6', u'\xa7', u'\xa8', u'\xa9', u'\xaa', u'\xab', u'\xac', u'\x00', u'\xae', u'\xaf', u'\xb0', u'\xb1', u'\xb2', u'\xb3', u'\xb4', u'\xb5', u'\xb6', u'\xb7', u'\xb8', u'\xb9', u'\xba', u'\xbb', u'\xbc', u'\xbd', u'\xbe', u'\xbf', u'\xc0', u'\xc1', u'\xc2', u'\xc3', u'\xc4', u'\xc5', u'\xc6', u'\xc7', u'\xc8', u'\xc9', u'\xca', u'\xcb', u'\xcc', u'\xcd', u'\xce', u'\xcf', u'\xd0', u'\xd1', u'\xd2', u'\xd3', u'\xd4', u'\xd5', u'\xd6', u'\xd7', u'\xd8', u'\xd9', u'\xda', u'\xdb', u'\xdc', u'\xdd', u'\xde', u'\xdf', u'\xe0', u'\xe1', u'\xe2', u'\xe3', u'\xe4', u'\xe5', u'\xe6', u'\xe7', u'\xe8', u'\xe9', u'\xea', u'\xeb', u'\xec', u'\xed', u'\xee', u'\xef', u'\xf0', u'\xf1', u'\xf2', u'\xf3', u'\xf4', u'\xf5', u'\xf6', u'\xf7', u'\xf8', u'\xf9', u'\xfa', u'\xfb', u'\xfc', u'\xfd', u'\xfe', u'\xff')
assert len(_pdfDocEncoding) == 256
_pdfDocEncoding_rev = {}
for i in xrange(256):
    char = _pdfDocEncoding[i]
    if char == u'\x00':
        continue
    assert char not in _pdfDocEncoding_rev
    _pdfDocEncoding_rev[char] = i
