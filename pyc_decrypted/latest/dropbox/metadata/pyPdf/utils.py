#Embedded file name: dropbox/metadata/pyPdf/utils.py
__author__ = 'Mathieu Fenniak'
__author_email__ = 'biziqe@mathieu.fenniak.net'

def readUntilWhitespace(stream, maxchars = None):
    txt = ''
    while True:
        tok = stream.read(1)
        if tok.isspace() or not tok:
            break
        txt += tok
        if len(txt) == maxchars:
            break

    return txt


def readNonWhitespace(stream):
    tok = ' '
    while tok == '\n' or tok == '\r' or tok == ' ' or tok == '\t':
        tok = stream.read(1)

    return tok


class ConvertFunctionsToVirtualList(object):

    def __init__(self, lengthFunction, getFunction):
        self.lengthFunction = lengthFunction
        self.getFunction = getFunction

    def __len__(self):
        return self.lengthFunction()

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError('sequence indices must be integers')
        len_self = len(self)
        if index < 0:
            index = len_self + index
        if index < 0 or index >= len_self:
            raise IndexError('sequence index out of range')
        return self.getFunction(index)


def RC4_encrypt(key, plaintext):
    S = [ i for i in range(256) ]
    j = 0
    for i in range(256):
        j = (j + S[i] + ord(key[i % len(key)])) % 256
        S[i], S[j] = S[j], S[i]

    i, j = (0, 0)
    retval = ''
    for x in range(len(plaintext)):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        t = S[(S[i] + S[j]) % 256]
        retval += chr(ord(plaintext[x]) ^ t)

    return retval


def matrixMultiply(a, b):
    return [ [ sum([ float(i) * float(j) for i, j in zip(row, col) ]) for col in zip(*b) ] for row in a ]


class PyPdfError(Exception):
    pass


class PdfReadError(PyPdfError):
    pass


class PageSizeNotDefinedError(PyPdfError):
    pass


if __name__ == '__main__':
    out = RC4_encrypt('Key', 'Plaintext')
    print repr(out)
    pt = RC4_encrypt('Key', out)
    print repr(pt)
