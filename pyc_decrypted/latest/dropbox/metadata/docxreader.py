#Embedded file name: dropbox/metadata/docxreader.py
from __future__ import absolute_import
from __future__ import with_statement
import zipfile
import contextlib
import cStringIO
from xml.etree.cElementTree import iterparse
NSMAP = {'extprop': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties',
 'opc': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
 'dc': 'http://purl.org/dc/terms/'}
RAW_TAGS = {'http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties': {'application': 'extprop',
                                                                                             'appversion': 'extprop',
                                                                                             'characters': 'extprop',
                                                                                             'characterswithspaces': 'extprop',
                                                                                             'company': 'extprop',
                                                                                             'docsecurity': 'extprop',
                                                                                             'hiddenslides': 'extprop',
                                                                                             'lines': 'extprop',
                                                                                             'manager': 'extprop',
                                                                                             'mmclips': 'extprop',
                                                                                             'notes': 'extprop',
                                                                                             'pages': 'extprop',
                                                                                             'paragraphs': 'extprop',
                                                                                             'presentationformat': 'extprop',
                                                                                             'scalecrop': 'extprop',
                                                                                             'shareddoc': 'extprop',
                                                                                             'template': 'extprop',
                                                                                             'totaltime': 'extprop',
                                                                                             'words': 'extprop'},
 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties': {'category': 'opc',
                                                                                           'contentstatus': 'opc',
                                                                                           'contenttype': 'opc',
                                                                                           'created': 'dc',
                                                                                           'creator': 'dc',
                                                                                           'description': 'dc',
                                                                                           'identifier': 'dc',
                                                                                           'keywords': 'opc',
                                                                                           'language': 'dc',
                                                                                           'lastmodifiedby': 'opc',
                                                                                           'lastprinted': 'opc',
                                                                                           'modified': 'dc',
                                                                                           'revision': 'opc',
                                                                                           'subject': 'dc',
                                                                                           'title': 'dc',
                                                                                           'version': 'opc'}}

def _make_full_tag(tag, ns):
    return '{%s}%s' % (NSMAP[ns].lower(), tag.lower())


TAGS = {}
for contenttype, tags in RAW_TAGS.iteritems():
    TAGS[contenttype] = {}
    for tag, ns in tags.iteritems():
        TAGS[contenttype][_make_full_tag(tag, ns)] = 1

def _wrapdata(data):
    out = cStringIO.StringIO(data)
    return out


def read_docx(file_obj):
    toret = {}
    try:
        with contextlib.closing(zipfile.ZipFile(file_obj, 'r')) as zipf:
            mappings = {}
            reldata = zipf.read('_rels/.rels')
            for event, elem in iterparse(_wrapdata(reldata)):
                if 'Type' in elem.attrib:
                    typename = elem.attrib['Type']
                    if typename in TAGS:
                        mappings[typename] = elem.attrib['Target']

            for typename, filename in mappings.iteritems():
                data = zipf.read(filename)
                toret.update(_parseTags(_wrapdata(data), TAGS[typename], RAW_TAGS[typename]))

    except (IOError, zipfile.BadZipfile):
        raise ValueError('Invalid zip file')

    return {'docx': toret}


def split_tag(tag):
    split = tag.rfind('}')
    return (tag[:split + 1], tag[split + 1:])


def _parseTags(f, tags, fallback_tags):
    toret = {}
    for event, elem in iterparse(f):
        tag = elem.tag.lower()
        if tag in tags and elem.text:
            toret[split_tag(elem.tag)[1].lower()] = elem.text
        else:
            tag = split_tag(elem.tag)[1].lower()
            if tag in fallback_tags and elem.text:
                toret[tag] = elem.text

    return toret


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as f:
        d = read_docx(f)
        for k, v in d.iteritems():
            print k, v

        print len(d)
