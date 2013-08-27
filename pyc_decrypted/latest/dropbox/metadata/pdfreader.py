#Embedded file name: dropbox/metadata/pdfreader.py
from __future__ import absolute_import
from __future__ import with_statement
import time
from .pyPdf import PdfFileReader
from .pyPdf.utils import PdfReadError
dateformat = '%Y%m%d%H%M%S'

def parsePDFDate(data):
    date, timezone = str(data[:16]), data[16:]
    seconds_since_epoch = time.mktime(time.strptime(date[2:], dateformat[:len(date) - 2]))
    if timezone:
        hours = 0
        minutes = 0
        if timezone[0] != 'Z':
            if len(timezone) > 6:
                minutes = int(timezone[4:5])
            hours = int(timezone[1:2])
            if timezone[0] == '+':
                seconds_since_epoch += 3600 * hours + 60 * minutes
            elif timezone[0] == '-':
                seconds_since_epoch -= 3600 * hours + 60 * minutes
    return str(seconds_since_epoch)


def read_pdf(file_obj):
    try:
        data = PdfFileReader(file_obj)
        toret = {}
        for k, v in data.getDocumentInfo().iteritems():
            try:
                d = v.strip()
            except AttributeError:
                d = data.getObject(v)
            except Exception:
                continue

            toret[k[1:]] = decode_binary_data(d)

        return {'pdf': toret}
    except PdfReadError as e:
        raise ValueError(str(e))


def decode_binary_data(data):
    if data[:2] == 'D:':
        return parsePDFDate(data)
    else:
        return data


if __name__ == '__main__':
    import sys
    with open(sys.argv[1], 'rb') as f:
        for k, v in read_pdf(f).iteritems():
            print k, decode_binary_data(v)
