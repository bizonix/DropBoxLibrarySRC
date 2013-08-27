#Embedded file name: dropbox/metadata/pyPdf/xmp.py
import re
import datetime
import decimal
from generic import PdfObject
from xml.dom import getDOMImplementation
from xml.dom.minidom import parseString
RDF_NAMESPACE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
DC_NAMESPACE = 'http://purl.org/dc/elements/1.1/'
XMP_NAMESPACE = 'http://ns.adobe.com/xap/1.0/'
PDF_NAMESPACE = 'http://ns.adobe.com/pdf/1.3/'
XMPMM_NAMESPACE = 'http://ns.adobe.com/xap/1.0/mm/'
PDFX_NAMESPACE = 'http://ns.adobe.com/pdfx/1.3/'
iso8601 = re.compile('\n        (?P<year>[0-9]{4})\n        (-\n            (?P<month>[0-9]{2})\n            (-\n                (?P<day>[0-9]+)\n                (T\n                    (?P<hour>[0-9]{2}):\n                    (?P<minute>[0-9]{2})\n                    (:(?P<second>[0-9]{2}(.[0-9]+)?))?\n                    (?P<tzd>Z|[-+][0-9]{2}:[0-9]{2})\n                )?\n            )?\n        )?\n        ', re.VERBOSE)

class XmpInformation(PdfObject):

    def __init__(self, stream):
        self.stream = stream
        docRoot = parseString(self.stream.getData())
        self.rdfRoot = docRoot.getElementsByTagNameNS(RDF_NAMESPACE, 'RDF')[0]
        self.cache = {}

    def writeToStream(self, stream, encryption_key):
        self.stream.writeToStream(stream, encryption_key)

    def getElement(self, aboutUri, namespace, name):
        for desc in self.rdfRoot.getElementsByTagNameNS(RDF_NAMESPACE, 'Description'):
            if desc.getAttributeNS(RDF_NAMESPACE, 'about') == aboutUri:
                attr = desc.getAttributeNodeNS(namespace, name)
                if attr != None:
                    yield attr
                for element in desc.getElementsByTagNameNS(namespace, name):
                    yield element

    def getNodesInNamespace(self, aboutUri, namespace):
        for desc in self.rdfRoot.getElementsByTagNameNS(RDF_NAMESPACE, 'Description'):
            if desc.getAttributeNS(RDF_NAMESPACE, 'about') == aboutUri:
                for i in range(desc.attributes.length):
                    attr = desc.attributes.item(i)
                    if attr.namespaceURI == namespace:
                        yield attr

                for child in desc.childNodes:
                    if child.namespaceURI == namespace:
                        yield child

    def _getText(self, element):
        text = ''
        for child in element.childNodes:
            if child.nodeType == child.TEXT_NODE:
                text += child.data

        return text

    def _converter_string(value):
        return value

    def _converter_date(value):
        m = iso8601.match(value)
        year = int(m.group('year'))
        month = int(m.group('month') or '1')
        day = int(m.group('day') or '1')
        hour = int(m.group('hour') or '0')
        minute = int(m.group('minute') or '0')
        second = decimal.Decimal(m.group('second') or '0')
        seconds = second.to_integral(decimal.ROUND_FLOOR)
        milliseconds = (second - seconds) * 1000000
        tzd = m.group('tzd') or 'Z'
        dt = datetime.datetime(year, month, day, hour, minute, seconds, milliseconds)
        if tzd != 'Z':
            tzd_hours, tzd_minutes = [ int(x) for x in tzd.split(':') ]
            tzd_hours *= -1
            if tzd_hours < 0:
                tzd_minutes *= -1
            dt = dt + datetime.timedelta(hours=tzd_hours, minutes=tzd_minutes)
        return dt

    _test_converter_date = staticmethod(_converter_date)

    def _getter_bag(namespace, name, converter):

        def get(self):
            cached = self.cache.get(namespace, {}).get(name)
            if cached:
                return cached
            retval = []
            for element in self.getElement('', namespace, name):
                bags = element.getElementsByTagNameNS(RDF_NAMESPACE, 'Bag')
                if len(bags):
                    for bag in bags:
                        for item in bag.getElementsByTagNameNS(RDF_NAMESPACE, 'li'):
                            value = self._getText(item)
                            value = converter(value)
                            retval.append(value)

            ns_cache = self.cache.setdefault(namespace, {})
            ns_cache[name] = retval
            return retval

        return get

    def _getter_seq(namespace, name, converter):

        def get(self):
            cached = self.cache.get(namespace, {}).get(name)
            if cached:
                return cached
            retval = []
            for element in self.getElement('', namespace, name):
                seqs = element.getElementsByTagNameNS(RDF_NAMESPACE, 'Seq')
                if len(seqs):
                    for seq in seqs:
                        for item in seq.getElementsByTagNameNS(RDF_NAMESPACE, 'li'):
                            value = self._getText(item)
                            value = converter(value)
                            retval.append(value)

                else:
                    value = converter(self._getText(element))
                    retval.append(value)

            ns_cache = self.cache.setdefault(namespace, {})
            ns_cache[name] = retval
            return retval

        return get

    def _getter_langalt(namespace, name, converter):

        def get(self):
            cached = self.cache.get(namespace, {}).get(name)
            if cached:
                return cached
            retval = {}
            for element in self.getElement('', namespace, name):
                alts = element.getElementsByTagNameNS(RDF_NAMESPACE, 'Alt')
                if len(alts):
                    for alt in alts:
                        for item in alt.getElementsByTagNameNS(RDF_NAMESPACE, 'li'):
                            value = self._getText(item)
                            value = converter(value)
                            retval[item.getAttribute('xml:lang')] = value

                else:
                    retval['x-default'] = converter(self._getText(element))

            ns_cache = self.cache.setdefault(namespace, {})
            ns_cache[name] = retval
            return retval

        return get

    def _getter_single(namespace, name, converter):

        def get(self):
            cached = self.cache.get(namespace, {}).get(name)
            if cached:
                return cached
            value = None
            for element in self.getElement('', namespace, name):
                if element.nodeType == element.ATTRIBUTE_NODE:
                    value = element.nodeValue
                else:
                    value = self._getText(element)
                break

            if value != None:
                value = converter(value)
            ns_cache = self.cache.setdefault(namespace, {})
            ns_cache[name] = value
            return value

        return get

    dc_contributor = property(_getter_bag(DC_NAMESPACE, 'contributor', _converter_string))
    dc_coverage = property(_getter_single(DC_NAMESPACE, 'coverage', _converter_string))
    dc_creator = property(_getter_seq(DC_NAMESPACE, 'creator', _converter_string))
    dc_date = property(_getter_seq(DC_NAMESPACE, 'date', _converter_date))
    dc_description = property(_getter_langalt(DC_NAMESPACE, 'description', _converter_string))
    dc_format = property(_getter_single(DC_NAMESPACE, 'format', _converter_string))
    dc_identifier = property(_getter_single(DC_NAMESPACE, 'identifier', _converter_string))
    dc_language = property(_getter_bag(DC_NAMESPACE, 'language', _converter_string))
    dc_publisher = property(_getter_bag(DC_NAMESPACE, 'publisher', _converter_string))
    dc_relation = property(_getter_bag(DC_NAMESPACE, 'relation', _converter_string))
    dc_rights = property(_getter_langalt(DC_NAMESPACE, 'rights', _converter_string))
    dc_source = property(_getter_single(DC_NAMESPACE, 'source', _converter_string))
    dc_subject = property(_getter_bag(DC_NAMESPACE, 'subject', _converter_string))
    dc_title = property(_getter_langalt(DC_NAMESPACE, 'title', _converter_string))
    dc_type = property(_getter_bag(DC_NAMESPACE, 'type', _converter_string))
    pdf_keywords = property(_getter_single(PDF_NAMESPACE, 'Keywords', _converter_string))
    pdf_pdfversion = property(_getter_single(PDF_NAMESPACE, 'PDFVersion', _converter_string))
    pdf_producer = property(_getter_single(PDF_NAMESPACE, 'Producer', _converter_string))
    xmp_createDate = property(_getter_single(XMP_NAMESPACE, 'CreateDate', _converter_date))
    xmp_modifyDate = property(_getter_single(XMP_NAMESPACE, 'ModifyDate', _converter_date))
    xmp_metadataDate = property(_getter_single(XMP_NAMESPACE, 'MetadataDate', _converter_date))
    xmp_creatorTool = property(_getter_single(XMP_NAMESPACE, 'CreatorTool', _converter_string))
    xmpmm_documentId = property(_getter_single(XMPMM_NAMESPACE, 'DocumentID', _converter_string))
    xmpmm_instanceId = property(_getter_single(XMPMM_NAMESPACE, 'InstanceID', _converter_string))

    def custom_properties(self):
        if not hasattr(self, '_custom_properties'):
            self._custom_properties = {}
            for node in self.getNodesInNamespace('', PDFX_NAMESPACE):
                key = node.localName
                while True:
                    idx = key.find(u'\u2182')
                    if idx == -1:
                        break
                    key = key[:idx] + chr(int(key[idx + 1:idx + 5], base=16)) + key[idx + 5:]

                if node.nodeType == node.ATTRIBUTE_NODE:
                    value = node.nodeValue
                else:
                    value = self._getText(node)
                self._custom_properties[key] = value

        return self._custom_properties

    custom_properties = property(custom_properties)
