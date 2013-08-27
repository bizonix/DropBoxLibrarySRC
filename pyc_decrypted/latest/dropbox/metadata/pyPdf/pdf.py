#Embedded file name: dropbox/metadata/pyPdf/pdf.py
__author__ = 'Mathieu Fenniak'
__author_email__ = 'biziqe@mathieu.fenniak.net'
import math
import struct
from sys import version_info
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import filters
import utils
import warnings
from generic import *
from utils import readNonWhitespace, readUntilWhitespace, ConvertFunctionsToVirtualList
if version_info < (2, 4):
    from sets import ImmutableSet as frozenset
if version_info < (2, 5):
    from md5 import md5
else:
    from hashlib import md5

class PdfFileWriter(object):

    def __init__(self):
        self._header = '%PDF-1.3'
        self._objects = []
        pages = DictionaryObject()
        pages.update({NameObject('/Type'): NameObject('/Pages'),
         NameObject('/Count'): NumberObject(0),
         NameObject('/Kids'): ArrayObject()})
        self._pages = self._addObject(pages)
        info = DictionaryObject()
        info.update({NameObject('/Producer'): createStringObject(u'Python PDF Library - http://pybrary.net/pyPdf/')})
        self._info = self._addObject(info)
        root = DictionaryObject()
        root.update({NameObject('/Type'): NameObject('/Catalog'),
         NameObject('/Pages'): self._pages})
        self._root = self._addObject(root)

    def _addObject(self, obj):
        self._objects.append(obj)
        return IndirectObject(len(self._objects), 0, self)

    def getObject(self, ido):
        if ido.pdf != self:
            raise ValueError('pdf must be self')
        return self._objects[ido.idnum - 1]

    def _addPage(self, page, action):
        assert page['/Type'] == '/Page'
        page[NameObject('/Parent')] = self._pages
        page = self._addObject(page)
        pages = self.getObject(self._pages)
        action(pages['/Kids'], page)
        pages[NameObject('/Count')] = NumberObject(pages['/Count'] + 1)

    def addPage(self, page):
        self._addPage(page, list.append)

    def insertPage(self, page, index = 0):
        self._addPage(page, lambda l, p: l.insert(index, p))

    def getPage(self, pageNumber):
        pages = self.getObject(self._pages)
        return pages['/Kids'][pageNumber].getObject()

    def getNumPages(self):
        pages = self.getObject(self._pages)
        return int(pages[NameObject('/Count')])

    def addBlankPage(self, width = None, height = None):
        page = PageObject.createBlankPage(self, width, height)
        self.addPage(page)
        return page

    def insertBlankPage(self, width = None, height = None, index = 0):
        if width is None or height is None and self.getNumPages() - 1 >= index:
            oldpage = self.getPage(index)
            width = oldpage.mediaBox.getWidth()
            height = oldpage.mediaBox.getHeight()
        page = PageObject.createBlankPage(self, width, height)
        self.insertPage(page, index)
        return page

    def encrypt(self, user_pwd, owner_pwd = None, use_128bit = True):
        import time, random
        if owner_pwd == None:
            owner_pwd = user_pwd
        if use_128bit:
            V = 2
            rev = 3
            keylen = 128 / 8
        else:
            V = 1
            rev = 2
            keylen = 40 / 8
        P = -1
        O = ByteStringObject(_alg33(owner_pwd, user_pwd, rev, keylen))
        ID_1 = md5(repr(time.time())).digest()
        ID_2 = md5(repr(random.random())).digest()
        self._ID = ArrayObject((ByteStringObject(ID_1), ByteStringObject(ID_2)))
        if rev == 2:
            U, key = _alg34(user_pwd, O, P, ID_1)
        else:
            assert rev == 3
            U, key = _alg35(user_pwd, rev, keylen, O, P, ID_1, False)
        encrypt = DictionaryObject()
        encrypt[NameObject('/Filter')] = NameObject('/Standard')
        encrypt[NameObject('/V')] = NumberObject(V)
        if V == 2:
            encrypt[NameObject('/Length')] = NumberObject(keylen * 8)
        encrypt[NameObject('/R')] = NumberObject(rev)
        encrypt[NameObject('/O')] = ByteStringObject(O)
        encrypt[NameObject('/U')] = ByteStringObject(U)
        encrypt[NameObject('/P')] = NumberObject(P)
        self._encrypt = self._addObject(encrypt)
        self._encrypt_key = key

    def write(self, stream):
        import struct
        externalReferenceMap = {}
        for objIndex in xrange(len(self._objects)):
            obj = self._objects[objIndex]
            if isinstance(obj, PageObject) and obj.indirectRef != None:
                data = obj.indirectRef
                if not externalReferenceMap.has_key(data.pdf):
                    externalReferenceMap[data.pdf] = {}
                if not externalReferenceMap[data.pdf].has_key(data.generation):
                    externalReferenceMap[data.pdf][data.generation] = {}
                externalReferenceMap[data.pdf][data.generation][data.idnum] = IndirectObject(objIndex + 1, 0, self)

        self.stack = []
        self._sweepIndirectReferences(externalReferenceMap, self._root)
        del self.stack
        object_positions = []
        stream.write(self._header + '\n')
        for i in range(len(self._objects)):
            idnum = i + 1
            obj = self._objects[i]
            object_positions.append(stream.tell())
            stream.write(str(idnum) + ' 0 obj\n')
            key = None
            if hasattr(self, '_encrypt') and idnum != self._encrypt.idnum:
                pack1 = struct.pack('<i', i + 1)[:3]
                pack2 = struct.pack('<i', 0)[:2]
                key = self._encrypt_key + pack1 + pack2
                assert len(key) == len(self._encrypt_key) + 5
                md5_hash = md5(key).digest()
                key = md5_hash[:min(16, len(self._encrypt_key) + 5)]
            obj.writeToStream(stream, key)
            stream.write('\nendobj\n')

        xref_location = stream.tell()
        stream.write('xref\n')
        stream.write('0 %s\n' % (len(self._objects) + 1))
        stream.write('%010d %05d f \n' % (0, 65535))
        for offset in object_positions:
            stream.write('%010d %05d n \n' % (offset, 0))

        stream.write('trailer\n')
        trailer = DictionaryObject()
        trailer.update({NameObject('/Size'): NumberObject(len(self._objects) + 1),
         NameObject('/Root'): self._root,
         NameObject('/Info'): self._info})
        if hasattr(self, '_ID'):
            trailer[NameObject('/ID')] = self._ID
        if hasattr(self, '_encrypt'):
            trailer[NameObject('/Encrypt')] = self._encrypt
        trailer.writeToStream(stream, None)
        stream.write('\nstartxref\n%s\n%%%%EOF\n' % xref_location)

    def _sweepIndirectReferences(self, externMap, data):
        if isinstance(data, DictionaryObject):
            for key, value in data.items():
                origvalue = value
                value = self._sweepIndirectReferences(externMap, value)
                if isinstance(value, StreamObject):
                    value = self._addObject(value)
                data[key] = value

            return data
        if isinstance(data, ArrayObject):
            for i in range(len(data)):
                value = self._sweepIndirectReferences(externMap, data[i])
                if isinstance(value, StreamObject):
                    value = self._addObject(value)
                data[i] = value

            return data
        if isinstance(data, IndirectObject):
            if data.pdf == self:
                if data.idnum in self.stack:
                    return data
                else:
                    self.stack.append(data.idnum)
                    realdata = self.getObject(data)
                    self._sweepIndirectReferences(externMap, realdata)
                    self.stack.pop()
                    return data
            else:
                newobj = externMap.get(data.pdf, {}).get(data.generation, {}).get(data.idnum, None)
                if newobj == None:
                    newobj = data.pdf.getObject(data)
                    self._objects.append(None)
                    idnum = len(self._objects)
                    newobj_ido = IndirectObject(idnum, 0, self)
                    if not externMap.has_key(data.pdf):
                        externMap[data.pdf] = {}
                    if not externMap[data.pdf].has_key(data.generation):
                        externMap[data.pdf][data.generation] = {}
                    externMap[data.pdf][data.generation][data.idnum] = newobj_ido
                    newobj = self._sweepIndirectReferences(externMap, newobj)
                    self._objects[idnum - 1] = newobj
                    return newobj_ido
                else:
                    return newobj
        else:
            return data


class PdfFileReader(object):

    def __init__(self, stream):
        self.flattenedPages = None
        self.resolvedObjects = {}
        self.read(stream)
        self.stream = stream
        self._override_encryption = False

    def getDocumentInfo(self):
        if not self.trailer.has_key('/Info'):
            return None
        obj = self.trailer['/Info']
        retval = DocumentInformation()
        retval.update(obj)
        return retval

    documentInfo = property(lambda self: self.getDocumentInfo(), None, None)

    def getXmpMetadata(self):
        try:
            self._override_encryption = True
            return self.trailer['/Root'].getXmpMetadata()
        finally:
            self._override_encryption = False

    xmpMetadata = property(lambda self: self.getXmpMetadata(), None, None)

    def getNumPages(self):
        if self.flattenedPages == None:
            self._flatten()
        return len(self.flattenedPages)

    numPages = property(lambda self: self.getNumPages(), None, None)

    def getPage(self, pageNumber):
        if self.flattenedPages == None:
            self._flatten()
        return self.flattenedPages[pageNumber]

    namedDestinations = property(lambda self: self.getNamedDestinations(), None, None)

    def getNamedDestinations(self, tree = None, retval = None):
        if retval == None:
            retval = {}
            catalog = self.trailer['/Root']
            if catalog.has_key('/Dests'):
                tree = catalog['/Dests']
            elif catalog.has_key('/Names'):
                names = catalog['/Names']
                if names.has_key('/Dests'):
                    tree = names['/Dests']
        if tree == None:
            return retval
        if tree.has_key('/Kids'):
            for kid in tree['/Kids']:
                self.getNamedDestinations(kid.getObject(), retval)

        if tree.has_key('/Names'):
            names = tree['/Names']
            for i in range(0, len(names), 2):
                key = names[i].getObject()
                val = names[i + 1].getObject()
                if isinstance(val, DictionaryObject) and val.has_key('/D'):
                    val = val['/D']
                dest = self._buildDestination(key, val)
                if dest != None:
                    retval[key] = dest

        return retval

    outlines = property(lambda self: self.getOutlines(), None, None)

    def getOutlines(self, node = None, outlines = None):
        if outlines == None:
            outlines = []
            catalog = self.trailer['/Root']
            if catalog.has_key('/Outlines'):
                lines = catalog['/Outlines']
                if lines.has_key('/First'):
                    node = lines['/First']
            self._namedDests = self.getNamedDestinations()
        if node == None:
            return outlines
        while 1:
            outline = self._buildOutline(node)
            if outline:
                outlines.append(outline)
            if node.has_key('/First'):
                subOutlines = []
                self.getOutlines(node['/First'], subOutlines)
                if subOutlines:
                    outlines.append(subOutlines)
            if not node.has_key('/Next'):
                break
            node = node['/Next']

        return outlines

    def _buildDestination(self, title, array):
        page, typ = array[0:2]
        array = array[2:]
        return Destination(title, page, typ, *array)

    def _buildOutline(self, node):
        dest, title, outline = (None, None, None)
        if node.has_key('/A') and node.has_key('/Title'):
            title = node['/Title']
            action = node['/A']
            if action['/S'] == '/GoTo':
                dest = action['/D']
        elif node.has_key('/Dest') and node.has_key('/Title'):
            title = node['/Title']
            dest = node['/Dest']
        if dest:
            if isinstance(dest, ArrayObject):
                outline = self._buildDestination(title, dest)
            elif isinstance(dest, unicode) and self._namedDests.has_key(dest):
                outline = self._namedDests[dest]
                outline[NameObject('/Title')] = title
            else:
                raise utils.PdfReadError('Unexpected destination %r' % dest)
        return outline

    pages = property(lambda self: ConvertFunctionsToVirtualList(self.getNumPages, self.getPage), None, None)

    def _flatten(self, pages = None, inherit = None, indirectRef = None):
        inheritablePageAttributes = (NameObject('/Resources'),
         NameObject('/MediaBox'),
         NameObject('/CropBox'),
         NameObject('/Rotate'))
        if inherit == None:
            inherit = dict()
        if pages == None:
            self.flattenedPages = []
            catalog = self.trailer['/Root'].getObject()
            pages = catalog['/Pages'].getObject()
        t = pages['/Type']
        if t == '/Pages':
            for attr in inheritablePageAttributes:
                if pages.has_key(attr):
                    inherit[attr] = pages[attr]

            for page in pages['/Kids']:
                addt = {}
                if isinstance(page, IndirectObject):
                    addt['indirectRef'] = page
                self._flatten(page.getObject(), inherit, **addt)

        elif t == '/Page':
            for attr, value in inherit.items():
                if not pages.has_key(attr):
                    pages[attr] = value

            pageObj = PageObject(self, indirectRef)
            pageObj.update(pages)
            self.flattenedPages.append(pageObj)

    def getObject(self, indirectReference):
        retval = self.resolvedObjects.get(indirectReference.generation, {}).get(indirectReference.idnum, None)
        if retval != None:
            return retval
        if indirectReference.generation == 0 and self.xref_objStm.has_key(indirectReference.idnum):
            stmnum, idx = self.xref_objStm[indirectReference.idnum]
            objStm = IndirectObject(stmnum, 0, self).getObject()
            assert objStm['/Type'] == '/ObjStm'
            assert idx < objStm['/N']
            streamData = StringIO(objStm.getData())
            for i in range(objStm['/N']):
                objnum = NumberObject.readFromStream(streamData)
                readNonWhitespace(streamData)
                streamData.seek(-1, 1)
                offset = NumberObject.readFromStream(streamData)
                readNonWhitespace(streamData)
                streamData.seek(-1, 1)
                t = streamData.tell()
                streamData.seek(objStm['/First'] + offset, 0)
                obj = readObject(streamData, self)
                self.resolvedObjects[0][objnum] = obj
                streamData.seek(t, 0)

            return self.resolvedObjects[0][indirectReference.idnum]
        start = self.xref[indirectReference.generation][indirectReference.idnum]
        self.stream.seek(start, 0)
        idnum, generation = self.readObjectHeader(self.stream)
        assert idnum == indirectReference.idnum
        assert generation == indirectReference.generation
        retval = readObject(self.stream, self)
        if not self._override_encryption and self.isEncrypted:
            if not hasattr(self, '_decryption_key'):
                raise Exception('file has not been decrypted')
            import struct
            pack1 = struct.pack('<i', indirectReference.idnum)[:3]
            pack2 = struct.pack('<i', indirectReference.generation)[:2]
            key = self._decryption_key + pack1 + pack2
            assert len(key) == len(self._decryption_key) + 5
            md5_hash = md5(key).digest()
            key = md5_hash[:min(16, len(self._decryption_key) + 5)]
            retval = self._decryptObject(retval, key)
        self.cacheIndirectObject(generation, idnum, retval)
        return retval

    def _decryptObject(self, obj, key):
        if isinstance(obj, ByteStringObject) or isinstance(obj, TextStringObject):
            obj = createStringObject(utils.RC4_encrypt(key, obj.original_bytes))
        elif isinstance(obj, StreamObject):
            obj._data = utils.RC4_encrypt(key, obj._data)
        elif isinstance(obj, DictionaryObject):
            for dictkey, value in obj.items():
                obj[dictkey] = self._decryptObject(value, key)

        elif isinstance(obj, ArrayObject):
            for i in range(len(obj)):
                obj[i] = self._decryptObject(obj[i], key)

        return obj

    def readObjectHeader(self, stream):
        readNonWhitespace(stream)
        stream.seek(-1, 1)
        idnum = readUntilWhitespace(stream)
        generation = readUntilWhitespace(stream)
        obj = stream.read(3)
        readNonWhitespace(stream)
        stream.seek(-1, 1)
        return (int(idnum), int(generation))

    def cacheIndirectObject(self, generation, idnum, obj):
        if not self.resolvedObjects.has_key(generation):
            self.resolvedObjects[generation] = {}
        self.resolvedObjects[generation][idnum] = obj

    def read(self, stream):
        stream.seek(0, 2)
        if stream.tell() == 0:
            raise utils.PdfReadError('Empty file')
        stream.seek(-1, 2)
        line = ''
        while not line:
            line = self.readNextEndLine(stream)

        if line[:5] != '%%EOF':
            raise utils.PdfReadError('EOF marker not found')
        line = self.readNextEndLine(stream)
        startxref = int(line)
        line = self.readNextEndLine(stream)
        if line[:9] != 'startxref':
            raise utils.PdfReadError('startxref not found')
        self.xref = {}
        self.xref_objStm = {}
        self.trailer = DictionaryObject()
        while 1:
            stream.seek(startxref, 0)
            x = stream.read(1)
            if x == 'x':
                ref = stream.read(4)
                if ref[:3] != 'ref':
                    raise utils.PdfReadError('xref table read error')
                readNonWhitespace(stream)
                stream.seek(-1, 1)
                while 1:
                    num = readObject(stream, self)
                    readNonWhitespace(stream)
                    stream.seek(-1, 1)
                    size = readObject(stream, self)
                    readNonWhitespace(stream)
                    stream.seek(-1, 1)
                    cnt = 0
                    while cnt < size:
                        line = stream.read(20)
                        if line[-1] in '0123456789t':
                            stream.seek(-1, 1)
                        offset, generation = line[:16].split(' ')
                        offset, generation = int(offset), int(generation)
                        if not self.xref.has_key(generation):
                            self.xref[generation] = {}
                        if self.xref[generation].has_key(num):
                            pass
                        else:
                            self.xref[generation][num] = offset
                        cnt += 1
                        num += 1

                    readNonWhitespace(stream)
                    stream.seek(-1, 1)
                    trailertag = stream.read(7)
                    if trailertag != 'trailer':
                        stream.seek(-7, 1)
                    else:
                        break

                readNonWhitespace(stream)
                stream.seek(-1, 1)
                newTrailer = readObject(stream, self)
                for key, value in newTrailer.items():
                    if not self.trailer.has_key(key):
                        self.trailer[key] = value

                if newTrailer.has_key('/Prev'):
                    startxref = newTrailer['/Prev']
                else:
                    break
            elif x.isdigit():
                stream.seek(-1, 1)
                idnum, generation = self.readObjectHeader(stream)
                xrefstream = readObject(stream, self)
                assert xrefstream['/Type'] == '/XRef'
                self.cacheIndirectObject(generation, idnum, xrefstream)
                streamData = StringIO(xrefstream.getData())
                idx_pairs = xrefstream.get('/Index', [0, xrefstream.get('/Size')])
                entrySizes = xrefstream.get('/W')
                for num, size in self._pairs(idx_pairs):
                    cnt = 0
                    while cnt < size:
                        for i in range(len(entrySizes)):
                            d = streamData.read(entrySizes[i])
                            di = convertToInt(d, entrySizes[i])
                            if i == 0:
                                xref_type = di
                            elif i == 1:
                                if xref_type == 0:
                                    next_free_object = di
                                elif xref_type == 1:
                                    byte_offset = di
                                elif xref_type == 2:
                                    objstr_num = di
                            elif i == 2:
                                if xref_type == 0:
                                    next_generation = di
                                elif xref_type == 1:
                                    generation = di
                                elif xref_type == 2:
                                    obstr_idx = di

                        if xref_type == 0:
                            pass
                        elif xref_type == 1:
                            if not self.xref.has_key(generation):
                                self.xref[generation] = {}
                            if num not in self.xref[generation]:
                                self.xref[generation][num] = byte_offset
                        elif xref_type == 2:
                            if num not in self.xref_objStm:
                                self.xref_objStm[num] = [objstr_num, obstr_idx]
                        cnt += 1
                        num += 1

                trailerKeys = ('/Root', '/Encrypt', '/Info', '/ID')
                for key in trailerKeys:
                    if xrefstream.has_key(key) and not self.trailer.has_key(key):
                        self.trailer[NameObject(key)] = xrefstream.raw_get(key)

                if xrefstream.has_key('/Prev'):
                    startxref = xrefstream['/Prev']
                else:
                    break
            else:
                stream.seek(-11, 1)
                tmp = stream.read(20)
                xref_loc = tmp.find('xref')
                if xref_loc != -1:
                    startxref -= 10 - xref_loc
                    continue
                else:
                    assert False
                    break

    def _pairs(self, array):
        i = 0
        while True:
            yield (array[i], array[i + 1])
            i += 2
            if i + 1 >= len(array):
                break

    def readNextEndLine(self, stream):
        line = ''
        totalbytes = stream.tell()
        if totalbytes == 0:
            raise utils.PdfReadError('unexpected EOF')
        while totalbytes >= 0:
            x = stream.read(1)
            if x == '\n' or x == '\r':
                while (x == '\n' or x == '\r') and totalbytes:
                    stream.seek(-2, 1)
                    totalbytes -= 1
                    x = stream.read(1)

                stream.seek(-1, 1)
                break
            else:
                line = x + line
                if totalbytes:
                    stream.seek(-2, 1)
            totalbytes -= 1

        return line

    def decrypt(self, password):
        self._override_encryption = True
        try:
            return self._decrypt(password)
        finally:
            self._override_encryption = False

    def _decrypt(self, password):
        encrypt = self.trailer['/Encrypt'].getObject()
        if encrypt['/Filter'] != '/Standard':
            raise NotImplementedError('only Standard PDF encryption handler is available')
        if encrypt['/V'] not in (1, 2):
            raise NotImplementedError('only algorithm code 1 and 2 are supported')
        user_password, key = self._authenticateUserPassword(password)
        if user_password:
            self._decryption_key = key
            return 1
        rev = encrypt['/R'].getObject()
        if rev == 2:
            keylen = 5
        else:
            keylen = encrypt['/Length'].getObject() / 8
        key = _alg33_1(password, rev, keylen)
        real_O = encrypt['/O'].getObject()
        if rev == 2:
            userpass = utils.RC4_encrypt(key, real_O)
        else:
            val = real_O
            for i in range(19, -1, -1):
                new_key = ''
                for l in range(len(key)):
                    new_key += chr(ord(key[l]) ^ i)

                val = utils.RC4_encrypt(new_key, val)

            userpass = val
        owner_password, key = self._authenticateUserPassword(userpass)
        if owner_password:
            self._decryption_key = key
            return 2
        return 0

    def _authenticateUserPassword(self, password):
        encrypt = self.trailer['/Encrypt'].getObject()
        rev = encrypt['/R'].getObject()
        owner_entry = encrypt['/O'].getObject().original_bytes
        p_entry = encrypt['/P'].getObject()
        id_entry = self.trailer['/ID'].getObject()
        id1_entry = id_entry[0].getObject()
        if rev == 2:
            U, key = _alg34(password, owner_entry, p_entry, id1_entry)
        elif rev >= 3:
            U, key = _alg35(password, rev, encrypt['/Length'].getObject() / 8, owner_entry, p_entry, id1_entry, encrypt.get('/EncryptMetadata', BooleanObject(False)).getObject())
        real_U = encrypt['/U'].getObject().original_bytes
        return (U == real_U, key)

    def getIsEncrypted(self):
        return self.trailer.has_key('/Encrypt')

    isEncrypted = property(lambda self: self.getIsEncrypted(), None, None)


def getRectangle(self, name, defaults):
    retval = self.get(name)
    if isinstance(retval, RectangleObject):
        return retval
    if retval == None:
        for d in defaults:
            retval = self.get(d)
            if retval != None:
                break

    if isinstance(retval, IndirectObject):
        retval = self.pdf.getObject(retval)
    retval = RectangleObject(retval)
    setRectangle(self, name, retval)
    return retval


def setRectangle(self, name, value):
    if not isinstance(name, NameObject):
        name = NameObject(name)
    self[name] = value


def deleteRectangle(self, name):
    del self[name]


def createRectangleAccessor(name, fallback):
    return property(lambda self: getRectangle(self, name, fallback), lambda self, value: setRectangle(self, name, value), lambda self: deleteRectangle(self, name))


class PageObject(DictionaryObject):

    def __init__(self, pdf = None, indirectRef = None):
        DictionaryObject.__init__(self)
        self.pdf = pdf
        self.indirectRef = indirectRef

    def createBlankPage(pdf = None, width = None, height = None):
        page = PageObject(pdf)
        page.__setitem__(NameObject('/Type'), NameObject('/Page'))
        page.__setitem__(NameObject('/Parent'), NullObject())
        page.__setitem__(NameObject('/Resources'), DictionaryObject())
        if width is None or height is None:
            if pdf is not None and pdf.getNumPages() > 0:
                lastpage = pdf.getPage(pdf.getNumPages() - 1)
                width = lastpage.mediaBox.getWidth()
                height = lastpage.mediaBox.getHeight()
            else:
                raise utils.PageSizeNotDefinedError()
        page.__setitem__(NameObject('/MediaBox'), RectangleObject([0,
         0,
         width,
         height]))
        return page

    createBlankPage = staticmethod(createBlankPage)

    def rotateClockwise(self, angle):
        assert angle % 90 == 0
        self._rotate(angle)
        return self

    def rotateCounterClockwise(self, angle):
        assert angle % 90 == 0
        self._rotate(-angle)
        return self

    def _rotate(self, angle):
        currentAngle = self.get('/Rotate', 0)
        self[NameObject('/Rotate')] = NumberObject(currentAngle + angle)

    def _mergeResources(res1, res2, resource):
        newRes = DictionaryObject()
        newRes.update(res1.get(resource, DictionaryObject()).getObject())
        page2Res = res2.get(resource, DictionaryObject()).getObject()
        renameRes = {}
        for key in page2Res.keys():
            if newRes.has_key(key) and newRes[key] != page2Res[key]:
                newname = NameObject(key + 'renamed')
                renameRes[key] = newname
                newRes[newname] = page2Res[key]
            elif not newRes.has_key(key):
                newRes[key] = page2Res.raw_get(key)

        return (newRes, renameRes)

    _mergeResources = staticmethod(_mergeResources)

    def _contentStreamRename(stream, rename, pdf):
        if not rename:
            return stream
        stream = ContentStream(stream, pdf)
        for operands, operator in stream.operations:
            for i in range(len(operands)):
                op = operands[i]
                if isinstance(op, NameObject):
                    operands[i] = rename.get(op, op)

        return stream

    _contentStreamRename = staticmethod(_contentStreamRename)

    def _pushPopGS(contents, pdf):
        stream = ContentStream(contents, pdf)
        stream.operations.insert(0, [[], 'q'])
        stream.operations.append([[], 'Q'])
        return stream

    _pushPopGS = staticmethod(_pushPopGS)

    def _addTransformationMatrix(contents, pdf, ctm):
        a, b, c, d, e, f = ctm
        contents = ContentStream(contents, pdf)
        contents.operations.insert(0, [[FloatObject(a),
          FloatObject(b),
          FloatObject(c),
          FloatObject(d),
          FloatObject(e),
          FloatObject(f)], ' cm'])
        return contents

    _addTransformationMatrix = staticmethod(_addTransformationMatrix)

    def getContents(self):
        if self.has_key('/Contents'):
            return self['/Contents'].getObject()
        else:
            return None

    def mergePage(self, page2):
        self._mergePage(page2)

    def _mergePage(self, page2, page2transformation = None):
        newResources = DictionaryObject()
        rename = {}
        originalResources = self['/Resources'].getObject()
        page2Resources = page2['/Resources'].getObject()
        for res in ('/ExtGState', '/Font', '/XObject', '/ColorSpace', '/Pattern', '/Shading', '/Properties'):
            new, newrename = PageObject._mergeResources(originalResources, page2Resources, res)
            if new:
                newResources[NameObject(res)] = new
                rename.update(newrename)

        newResources[NameObject('/ProcSet')] = ArrayObject(frozenset(originalResources.get('/ProcSet', ArrayObject()).getObject()).union(frozenset(page2Resources.get('/ProcSet', ArrayObject()).getObject())))
        newContentArray = ArrayObject()
        originalContent = self.getContents()
        if originalContent is not None:
            newContentArray.append(PageObject._pushPopGS(originalContent, self.pdf))
        page2Content = page2.getContents()
        if page2Content is not None:
            if page2transformation is not None:
                page2Content = page2transformation(page2Content)
            page2Content = PageObject._contentStreamRename(page2Content, rename, self.pdf)
            page2Content = PageObject._pushPopGS(page2Content, self.pdf)
            newContentArray.append(page2Content)
        self[NameObject('/Contents')] = ContentStream(newContentArray, self.pdf)
        self[NameObject('/Resources')] = newResources

    def mergeTransformedPage(self, page2, ctm):
        self._mergePage(page2, lambda page2Content: PageObject._addTransformationMatrix(page2Content, page2.pdf, ctm))

    def mergeScaledPage(self, page2, factor):
        return self.mergeTransformedPage(page2, [factor,
         0,
         0,
         factor,
         0,
         0])

    def mergeRotatedPage(self, page2, rotation):
        rotation = math.radians(rotation)
        return self.mergeTransformedPage(page2, [math.cos(rotation),
         math.sin(rotation),
         -math.sin(rotation),
         math.cos(rotation),
         0,
         0])

    def mergeTranslatedPage(self, page2, tx, ty):
        return self.mergeTransformedPage(page2, [1,
         0,
         0,
         1,
         tx,
         ty])

    def mergeRotatedScaledPage(self, page2, rotation, scale):
        rotation = math.radians(rotation)
        rotating = [[math.cos(rotation), math.sin(rotation), 0], [-math.sin(rotation), math.cos(rotation), 0], [0, 0, 1]]
        scaling = [[scale, 0, 0], [0, scale, 0], [0, 0, 1]]
        ctm = utils.matrixMultiply(rotating, scaling)
        return self.mergeTransformedPage(page2, [ctm[0][0],
         ctm[0][1],
         ctm[1][0],
         ctm[1][1],
         ctm[2][0],
         ctm[2][1]])

    def mergeScaledTranslatedPage(self, page2, scale, tx, ty):
        translation = [[1, 0, 0], [0, 1, 0], [tx, ty, 1]]
        scaling = [[scale, 0, 0], [0, scale, 0], [0, 0, 1]]
        ctm = utils.matrixMultiply(scaling, translation)
        return self.mergeTransformedPage(page2, [ctm[0][0],
         ctm[0][1],
         ctm[1][0],
         ctm[1][1],
         ctm[2][0],
         ctm[2][1]])

    def mergeRotatedScaledTranslatedPage(self, page2, rotation, scale, tx, ty):
        translation = [[1, 0, 0], [0, 1, 0], [tx, ty, 1]]
        rotation = math.radians(rotation)
        rotating = [[math.cos(rotation), math.sin(rotation), 0], [-math.sin(rotation), math.cos(rotation), 0], [0, 0, 1]]
        scaling = [[scale, 0, 0], [0, scale, 0], [0, 0, 1]]
        ctm = utils.matrixMultiply(rotating, scaling)
        ctm = utils.matrixMultiply(ctm, translation)
        return self.mergeTransformedPage(page2, [ctm[0][0],
         ctm[0][1],
         ctm[1][0],
         ctm[1][1],
         ctm[2][0],
         ctm[2][1]])

    def addTransformation(self, ctm):
        originalContent = self.getContents()
        if originalContent is not None:
            newContent = PageObject._addTransformationMatrix(originalContent, self.pdf, ctm)
            newContent = PageObject._pushPopGS(newContent, self.pdf)
            self[NameObject('/Contents')] = newContent

    def scale(self, sx, sy):
        self.addTransformation([sx,
         0,
         0,
         sy,
         0,
         0])
        self.mediaBox = RectangleObject([float(self.mediaBox.getLowerLeft_x()) * sx,
         float(self.mediaBox.getLowerLeft_y()) * sy,
         float(self.mediaBox.getUpperRight_x()) * sx,
         float(self.mediaBox.getUpperRight_y()) * sy])

    def scaleBy(self, factor):
        self.scale(factor, factor)

    def scaleTo(self, width, height):
        sx = width / (self.mediaBox.getUpperRight_x() - self.mediaBox.getLowerLeft_x())
        sy = height / (self.mediaBox.getUpperRight_y() - self.mediaBox.getLowerLeft_x())
        self.scale(sx, sy)

    def compressContentStreams(self):
        content = self.getContents()
        if content is not None:
            if not isinstance(content, ContentStream):
                content = ContentStream(content, self.pdf)
            self[NameObject('/Contents')] = content.flateEncode()

    def extractText(self):
        text = u''
        content = self['/Contents'].getObject()
        if not isinstance(content, ContentStream):
            content = ContentStream(content, self.pdf)
        for operands, operator in content.operations:
            if operator == 'Tj':
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += _text
            elif operator == 'T*':
                text += '\n'
            elif operator == "'":
                text += '\n'
                _text = operands[0]
                if isinstance(_text, TextStringObject):
                    text += operands[0]
            elif operator == '"':
                _text = operands[2]
                if isinstance(_text, TextStringObject):
                    text += '\n'
                    text += _text
            elif operator == 'TJ':
                for i in operands[0]:
                    if isinstance(i, TextStringObject):
                        text += i

        return text

    mediaBox = createRectangleAccessor('/MediaBox', ())
    cropBox = createRectangleAccessor('/CropBox', ('/MediaBox',))
    bleedBox = createRectangleAccessor('/BleedBox', ('/CropBox', '/MediaBox'))
    trimBox = createRectangleAccessor('/TrimBox', ('/CropBox', '/MediaBox'))
    artBox = createRectangleAccessor('/ArtBox', ('/CropBox', '/MediaBox'))


class ContentStream(DecodedStreamObject):

    def __init__(self, stream, pdf):
        self.pdf = pdf
        self.operations = []
        stream = stream.getObject()
        if isinstance(stream, ArrayObject):
            data = ''
            for s in stream:
                data += s.getObject().getData()

            stream = StringIO(data)
        else:
            stream = StringIO(stream.getData())
        self.__parseContentStream(stream)

    def __parseContentStream(self, stream):
        stream.seek(0, 0)
        operands = []
        while True:
            peek = readNonWhitespace(stream)
            if peek == '':
                break
            stream.seek(-1, 1)
            if peek.isalpha() or peek == "'" or peek == '"':
                operator = ''
                while True:
                    tok = stream.read(1)
                    if tok.isspace() or tok in NameObject.delimiterCharacters:
                        stream.seek(-1, 1)
                        break
                    elif tok == '':
                        break
                    operator += tok

                if operator == 'BI':
                    assert operands == []
                    ii = self._readInlineImage(stream)
                    self.operations.append((ii, 'INLINE IMAGE'))
                else:
                    self.operations.append((operands, operator))
                    operands = []
            elif peek == '%':
                while peek not in ('\r', '\n'):
                    peek = stream.read(1)

            else:
                operands.append(readObject(stream, None))

    def _readInlineImage(self, stream):
        settings = DictionaryObject()
        while True:
            tok = readNonWhitespace(stream)
            stream.seek(-1, 1)
            if tok == 'I':
                break
            key = readObject(stream, self.pdf)
            tok = readNonWhitespace(stream)
            stream.seek(-1, 1)
            value = readObject(stream, self.pdf)
            settings[key] = value

        tmp = stream.read(3)
        assert tmp[:2] == 'ID'
        data = ''
        while True:
            tok = stream.read(1)
            if tok == 'E':
                next = stream.read(1)
                if next == 'I':
                    break
                else:
                    stream.seek(-1, 1)
                    data += tok
            else:
                data += tok

        x = readNonWhitespace(stream)
        stream.seek(-1, 1)
        return {'settings': settings,
         'data': data}

    def _getData(self):
        newdata = StringIO()
        for operands, operator in self.operations:
            if operator == 'INLINE IMAGE':
                newdata.write('BI')
                dicttext = StringIO()
                operands['settings'].writeToStream(dicttext, None)
                newdata.write(dicttext.getvalue()[2:-2])
                newdata.write('ID ')
                newdata.write(operands['data'])
                newdata.write('EI')
            else:
                for op in operands:
                    op.writeToStream(newdata, None)
                    newdata.write(' ')

                newdata.write(operator)
            newdata.write('\n')

        return newdata.getvalue()

    def _setData(self, value):
        self.__parseContentStream(StringIO(value))

    _data = property(_getData, _setData)


class DocumentInformation(DictionaryObject):

    def __init__(self):
        DictionaryObject.__init__(self)

    def getText(self, key):
        retval = self.get(key, None)
        if isinstance(retval, TextStringObject):
            return retval

    title = property(lambda self: self.getText('/Title'))
    title_raw = property(lambda self: self.get('/Title'))
    author = property(lambda self: self.getText('/Author'))
    author_raw = property(lambda self: self.get('/Author'))
    subject = property(lambda self: self.getText('/Subject'))
    subject_raw = property(lambda self: self.get('/Subject'))
    creator = property(lambda self: self.getText('/Creator'))
    creator_raw = property(lambda self: self.get('/Creator'))
    producer = property(lambda self: self.getText('/Producer'))
    producer_raw = property(lambda self: self.get('/Producer'))


class Destination(DictionaryObject):

    def __init__(self, title, page, typ, *args):
        DictionaryObject.__init__(self)
        self[NameObject('/Title')] = title
        self[NameObject('/Page')] = page
        self[NameObject('/Type')] = typ
        if typ == '/XYZ':
            self[NameObject('/Left')], self[NameObject('/Top')], self[NameObject('/Zoom')] = args
        elif typ == '/FitR':
            self[NameObject('/Left')], self[NameObject('/Bottom')], self[NameObject('/Right')], self[NameObject('/Top')] = args
        elif typ in ('/FitH', 'FitBH'):
            self[NameObject('/Top')], = args
        elif typ in ('/FitV', 'FitBV'):
            self[NameObject('/Left')], = args
        elif typ in ('/Fit', 'FitB'):
            pass
        else:
            raise utils.PdfReadError('Unknown Destination Type: %r' % typ)

    title = property(lambda self: self.get('/Title'))
    page = property(lambda self: self.get('/Page'))
    typ = property(lambda self: self.get('/Type'))
    zoom = property(lambda self: self.get('/Zoom', None))
    left = property(lambda self: self.get('/Left', None))
    right = property(lambda self: self.get('/Right', None))
    top = property(lambda self: self.get('/Top', None))
    bottom = property(lambda self: self.get('/Bottom', None))


def convertToInt(d, size):
    if size > 8:
        raise utils.PdfReadError('invalid size in convertToInt')
    d = '\x00\x00\x00\x00\x00\x00\x00\x00' + d
    d = d[-8:]
    return struct.unpack('>q', d)[0]


_encryption_padding = '(\xbfN^Nu\x8aAd\x00NV' + '\xff\xfa\x01\x08..\x00\xb6\xd0h>\x80/\x0c' + '\xa9\xfedSiz'

def _alg32(password, rev, keylen, owner_entry, p_entry, id1_entry, metadata_encrypt = True):
    password = (password + _encryption_padding)[:32]
    import struct
    m = md5(password)
    m.update(owner_entry)
    p_entry = struct.pack('<i', p_entry)
    m.update(p_entry)
    m.update(id1_entry)
    if rev >= 3 and not metadata_encrypt:
        m.update('\xff\xff\xff\xff')
    md5_hash = m.digest()
    if rev >= 3:
        for i in range(50):
            md5_hash = md5(md5_hash[:keylen]).digest()

    return md5_hash[:keylen]


def _alg33(owner_pwd, user_pwd, rev, keylen):
    key = _alg33_1(owner_pwd, rev, keylen)
    user_pwd = (user_pwd + _encryption_padding)[:32]
    val = utils.RC4_encrypt(key, user_pwd)
    if rev >= 3:
        for i in range(1, 20):
            new_key = ''
            for l in range(len(key)):
                new_key += chr(ord(key[l]) ^ i)

            val = utils.RC4_encrypt(new_key, val)

    return val


def _alg33_1(password, rev, keylen):
    password = (password + _encryption_padding)[:32]
    m = md5(password)
    md5_hash = m.digest()
    if rev >= 3:
        for i in range(50):
            md5_hash = md5(md5_hash).digest()

    key = md5_hash[:keylen]
    return key


def _alg34(password, owner_entry, p_entry, id1_entry):
    key = _alg32(password, 2, 5, owner_entry, p_entry, id1_entry)
    U = utils.RC4_encrypt(key, _encryption_padding)
    return (U, key)


def _alg35(password, rev, keylen, owner_entry, p_entry, id1_entry, metadata_encrypt):
    key = _alg32(password, rev, keylen, owner_entry, p_entry, id1_entry)
    m = md5()
    m.update(_encryption_padding)
    m.update(id1_entry)
    md5_hash = m.digest()
    val = utils.RC4_encrypt(key, md5_hash)
    for i in range(1, 20):
        new_key = ''
        for l in range(len(key)):
            new_key += chr(ord(key[l]) ^ i)

        val = utils.RC4_encrypt(new_key, val)

    return (val + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00', key)
