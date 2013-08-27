#Embedded file name: dropbox/event.py
import time
from contextlib import contextmanager
from dropbox.callbacks import watchable
from dropbox.debugging import easy_repr
from dropbox.trace import TRACE
AGGREGATE_TIMEOUT = 3600

@watchable
def report(data_name, **info):
    TRACE('Event: %r -> %r', data_name, info)


@watchable
def report_aggregate_event(data_name, data, ts = None, approx_timeout = AGGREGATE_TIMEOUT):
    pass


class TimedEvent(object):
    __slots__ = ('start_time', 'report')

    def __init__(self, **info):
        self.start_time = time.time() * 1000
        self.report = {}
        self.update(**info)

    def info(self, name, value):
        self.report[name] = value

    def update(self, **info):
        self.report.update(info)

    def event(self, name):
        self.report[name + '_time'] = int(time.time() * 1000 - self.start_time)

    @contextmanager
    def timed_event(self, name):
        self.event(name + '_start')
        yield
        self.event(name + '_end')

    def __repr__(self):
        return easy_repr(self, *self.__slots__)
