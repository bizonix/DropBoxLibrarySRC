#Embedded file name: dropbox/metadata/pyPdf/filters.py
__author__ = 'Mathieu Fenniak'
__author_email__ = 'biziqe@mathieu.fenniak.net'
from utils import PdfReadError
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import zlib

    def decompress(data):
        return zlib.decompress(data)


    def compress(data):
        return zlib.compress(data)


except ImportError:
    import System
    from System import IO, Collections, Array

    def _string_to_bytearr(buf):
        retval = Array.CreateInstance(System.Byte, len(buf))
        for i in range(len(buf)):
            retval[i] = ord(buf[i])

        return retval


    def _bytearr_to_string(bytes):
        retval = ''
        for i in range(bytes.Length):
            retval += chr(bytes[i])

        return retval


    def _read_bytes(stream):
        ms = IO.MemoryStream()
        buf = Array.CreateInstance(System.Byte, 2048)
        while True:
            bytes = stream.Read(buf, 0, buf.Length)
            if bytes == 0:
                break
            else:
                ms.Write(buf, 0, bytes)

        retval = ms.ToArray()
        ms.Close()
        return retval


    def decompress(data):
        bytes = _string_to_bytearr(data)
        ms = IO.MemoryStream()
        ms.Write(bytes, 0, bytes.Length)
        ms.Position = 0
        gz = IO.Compression.DeflateStream(ms, IO.Compression.CompressionMode.Decompress)
        bytes = _read_bytes(gz)
        retval = _bytearr_to_string(bytes)
        gz.Close()
        return retval


    def compress(data):
        bytes = _string_to_bytearr(data)
        ms = IO.MemoryStream()
        gz = IO.Compression.DeflateStream(ms, IO.Compression.CompressionMode.Compress, True)
        gz.Write(bytes, 0, bytes.Length)
        gz.Close()
        ms.Position = 0
        bytes = ms.ToArray()
        retval = _bytearr_to_string(bytes)
        ms.Close()
        return retval


class FlateDecode(object):

    def decode(data, decodeParms):
        data = decompress(data)
        predictor = 1
        if decodeParms:
            predictor = decodeParms.get('/Predictor', 1)
        if predictor != 1:
            columns = decodeParms['/Columns']
            if predictor >= 10 and predictor <= 15:
                output = StringIO()
                rowlength = columns + 1
                assert len(data) % rowlength == 0
                prev_rowdata = (0,) * rowlength
                for row in xrange(len(data) / rowlength):
                    rowdata = [ ord(x) for x in data[row * rowlength:(row + 1) * rowlength] ]
                    filterByte = rowdata[0]
                    if filterByte == 0:
                        pass
                    elif filterByte == 1:
                        for i in range(2, rowlength):
                            rowdata[i] = (rowdata[i] + rowdata[i - 1]) % 256

                    elif filterByte == 2:
                        for i in range(1, rowlength):
                            rowdata[i] = (rowdata[i] + prev_rowdata[i]) % 256

                    else:
                        raise PdfReadError('Unsupported PNG filter %r' % filterByte)
                    prev_rowdata = rowdata
                    output.write(''.join([ chr(x) for x in rowdata[1:] ]))

                data = output.getvalue()
            else:
                raise PdfReadError('Unsupported flatedecode predictor %r' % predictor)
        return data

    decode = staticmethod(decode)

    def encode(data):
        return compress(data)

    encode = staticmethod(encode)


class ASCIIHexDecode(object):

    def decode(data, decodeParms = None):
        retval = ''
        char = ''
        x = 0
        while True:
            c = data[x]
            if c == '>':
                break
            elif c.isspace():
                x += 1
                continue
            char += c
            if len(char) == 2:
                retval += chr(int(char, base=16))
                char = ''
            x += 1

        assert char == ''
        return retval

    decode = staticmethod(decode)


class ASCII85Decode(object):

    def decode(data, decodeParms = None):
        retval = ''
        group = []
        x = 0
        hitEod = False
        data = [ y for y in data if y not in ' \n\r\t' ]
        while not hitEod:
            c = data[x]
            if len(retval) == 0 and c == '<' and data[x + 1] == '~':
                x += 2
                continue
            elif c == 'z':
                assert len(group) == 0
                retval += '\x00\x00\x00\x00'
                continue
            elif c == '~' and data[x + 1] == '>':
                if len(group) != 0:
                    assert len(group) > 1
                    cnt = len(group) - 1
                    group += [85, 85, 85]
                    hitEod = cnt
                else:
                    break
            else:
                c = ord(c) - 33
                assert c >= 0 and c < 85
                group += [c]
            if len(group) >= 5:
                b = group[0] * 52200625 + group[1] * 614125 + group[2] * 7225 + group[3] * 85 + group[4]
                assert b < 4294967295L
                c4 = chr((b >> 0) % 256)
                c3 = chr((b >> 8) % 256)
                c2 = chr((b >> 16) % 256)
                c1 = chr(b >> 24)
                retval += c1 + c2 + c3 + c4
                if hitEod:
                    retval = retval[:-4 + hitEod]
                group = []
            x += 1

        return retval

    decode = staticmethod(decode)


def decodeStreamData(stream):
    from generic import NameObject
    filters = stream.get('/Filter', ())
    if len(filters) and not isinstance(filters[0], NameObject):
        filters = (filters,)
    data = stream._data
    for filterType in filters:
        if filterType == '/FlateDecode':
            data = FlateDecode.decode(data, stream.get('/DecodeParms'))
        elif filterType == '/ASCIIHexDecode':
            data = ASCIIHexDecode.decode(data)
        elif filterType == '/ASCII85Decode':
            data = ASCII85Decode.decode(data)
        elif filterType == '/Crypt':
            decodeParams = stream.get('/DecodeParams', {})
            if '/Name' not in decodeParams and '/Type' not in decodeParams:
                pass
            else:
                raise NotImplementedError('/Crypt filter with /Name or /Type not supported yet')
        else:
            raise NotImplementedError('unsupported filter %s' % filterType)

    return data


if __name__ == '__main__':
    assert 'abc' == ASCIIHexDecode.decode('61\n626\n3>')
    ascii85Test = '\n     <~9jqo^BlbD-BleB1DJ+*+F(f,q/0JhKF<GL>Cj@.4Gp$d7F!,L7@<6@)/0JDEF<G%<+EV:2F!,\n     O<DJ+*.@<*K0@<6L(Df-\\0Ec5e;DffZ(EZee.Bl.9pF"AGXBPCsi+DGm>@3BB/F*&OCAfu2/AKY\n     i(DIb:@FD,*)+C]U=@3BN#EcYf8ATD3s@q?d$AftVqCh[NqF<G:8+EV:.+Cf>-FD5W8ARlolDIa\n     l(DId<j@<?3r@:F%a+D58\'ATD4$Bl@l3De:,-DJs`8ARoFb/0JMK@qB4^F!,R<AKZ&-DfTqBG%G\n     >uD.RTpAKYo\'+CT/5+Cei#DII?(E,9)oF*2M7/c~>\n    '
    ascii85_originalText = 'Man is distinguished, not only by his reason, but by this singular passion from other animals, which is a lust of the mind, that by a perseverance of delight in the continued and indefatigable generation of knowledge, exceeds the short vehemence of any carnal pleasure.'
    assert ASCII85Decode.decode(ascii85Test) == ascii85_originalText
