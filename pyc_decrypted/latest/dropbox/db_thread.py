#Embedded file name: dropbox/db_thread.py
from __future__ import absolute_import
import os
from build_number import is_frozen
from dropbox.low_functions import identity
from dropbox.livetracer import make_traced_thread
from dropbox.profilers import make_profiled_thread, profiled, cpu_profiled, memory_profiled, cpu_mem_profiled, rss_profiled
from dropbox.trace import watched
watched_thread_wrapper = None

def _make_watched_thread(c):

    class WatchedThread(c):

        def __init__(self, *n, **kw):
            super(WatchedThread, self).__init__(*n, **kw)

        @watched
        def run(self):
            if watched_thread_wrapper is not None:
                watched_thread_wrapper(c.__name__, super(WatchedThread, self).run)()
            else:
                super(WatchedThread, self).run()

    return WatchedThread


def specified_profiler():
    null_profiler = (lambda x: identity, u'.' + unicode(os.path.sep))
    if is_frozen():
        return null_profiler
    DBPROFILE = os.getenv('DBPROFILE')
    DBRSSPROFILE = os.getenv('DBRSSPROFILE')
    DBCPUPROFILE = os.getenv('DBCPUPROFILE')
    DBMEMPROF = os.getenv('DBMEMPROF')
    DBCPUMEMPROF = os.getenv('DBCPUMEMPROF')
    if DBPROFILE:
        return (profiled, DBPROFILE)
    if DBCPUPROFILE:
        return (cpu_profiled, DBCPUPROFILE)
    if DBMEMPROF:
        return (memory_profiled, DBMEMPROF)
    if DBRSSPROFILE:
        return (rss_profiled, DBRSSPROFILE)
    if DBCPUMEMPROF:
        return (cpu_mem_profiled, DBCPUMEMPROF)
    return null_profiler


def live_tracer_is_enabled():
    return not is_frozen() and os.getenv('DBTRACE')


def db_thread(c):
    newc = _make_watched_thread(c)
    if live_tracer_is_enabled():
        newc = make_traced_thread(newc)
    return make_profiled_thread(newc, *specified_profiler())
