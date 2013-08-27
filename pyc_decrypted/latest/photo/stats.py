#Embedded file name: photo/stats.py
from dropbox.trace import TRACE, unhandled_exc_handler
collectors = []

class PhotoStatCollector(object):

    def __init__(self, csr = None):
        self.ran = False
        self.csr = csr

    def __call__(self):
        if self.ran:
            return
        TRACE('Collecting stats on photo apps')
        for collector in collectors:
            collector(self.csr)

        self.ran = True


if __name__ == '__main__':

    def log(x):
        print 'TRACE:', x


    class FakeStat(object):

        def report_stat(self, key, value):
            print '%s: %r' % (key, value)


    import photo
    from dropbox.trace import add_trace_handler
    add_trace_handler(log)
    t = photo.PhotoStatCollector(FakeStat())
    t()
