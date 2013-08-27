#Embedded file name: dropbox/sync_engine/p2p/faststr.py
from __future__ import absolute_import
from collections import deque
from dropbox.trace import TRACE, unhandled_exc_handler
import time
totalAppendStringTime1 = 0
totalAppendStringTime2 = 0
totalAppendStringTime3 = 0
totalAppendStringTime4 = 0
totalAppendStringTime5 = 0
totalAppendStringTime6 = 0
totalAppendStringTime7 = 0

class AppendString:

    def __init__(self, input = None):
        self.buf = deque()
        self.blen = 0
        self.totalBlen = 0
        self.outLen = 0
        self.curpos = 0
        if input:
            self.append(input)

    def append(self, input):
        self.buf.append(input)
        self.blen += len(input)
        self.totalBlen += len(input)

    def appendleft(self, input):
        self.buf.appendleft(input)
        self.blen += len(input)
        self.totalBlen += len(input)

    def getoutputpart(self, amount):
        out = buffer(self.buf[0], self.curpos, amount)
        while len(out) < 1:
            self.buf.popleft()
            self.curpos = 0
            if len(self.buf) < 1:
                return ''
            out = buffer(self.buf[0], self.curpos, amount)

        return out

    def consume(self, amount):
        self.curpos += amount
        self.blen -= amount
        self.outLen += amount
        if self.blen == 0:
            assert self.outLen == self.totalBlen

    def getblock(self):
        buf = self.buf.popleft()
        self.blen -= len(buf)
        self.outLen += len(buf)
        if self.blen == 0:
            assert self.outLen == self.totalBlen
        return buf

    def getbuf(self, bytes = -1, keep = False):
        global totalAppendStringTime1
        global totalAppendStringTime2
        global totalAppendStringTime3
        global totalAppendStringTime4
        global totalAppendStringTime5
        global totalAppendStringTime6
        global totalAppendStringTime7
        stime3 = time.time()
        outlst = []
        outlen = 0
        if bytes == -1:
            override = True
        else:
            override = False
        while self.blen > 0 and (override or outlen < bytes):
            tmp = self.buf.popleft()
            if not override:
                stime1 = time.time()
                data = tmp[:bytes - outlen]
                rest = tmp[bytes - outlen:]
                restlen = len(rest)
                totalAppendStringTime1 += time.time() - stime1
            else:
                stime6 = time.time()
                data = tmp
                rest = ''
                restlen = 0
                totalAppendStringTime6 += time.time() - stime6
            stime7 = time.time()
            dlen = len(data)
            totalAppendStringTime7 += time.time() - stime7
            stime2 = time.time()
            outlst.append(data)
            outlen += dlen
            self.blen -= len(data)
            if restlen > 0:
                self.buf.appendleft(rest)
            totalAppendStringTime2 += time.time() - stime2

        stime4 = time.time()
        if keep:
            keepList = list(outlst)
            keepList.reverse()
            for x in keepList:
                self.appendleft(x)

        totalAppendStringTime4 += time.time() - stime4
        stime5 = time.time()
        out = ''.join(outlst)
        totalAppendStringTime5 += time.time() - stime5
        totalAppendStringTime3 += time.time() - stime3
        self.outLen += len(out)
        if self.blen == 0:
            assert self.outLen == self.totalBlen
        return out

    def __len__(self):
        return self.blen

    def __add__(self, other):
        self.append(other)
        return self


if __name__ == '__main__':
    x = AppendString()
    x.append('HELLO WORLD 12345')
    x.append('THIS IS JUST ANOTHER TEST')
    x.append('ASDFGHJKLASDFGHJK')
    x.append('THIS IS JUST ANOTHER TEST')
    x.append("THIS IS WHY WE CAN'T HAVE NICE THINGS")
    lenbef = len(x)
    y = x.getoutputpart(16384)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(16384)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(12)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    lenbef = len(x)
    y = x.getoutputpart(5)
    print y, '--', len(y), lenbef, len(x), lenbef - len(y), lenbef - len(x)
    print x.buf
