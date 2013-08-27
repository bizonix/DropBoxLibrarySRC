#Embedded file name: dropbox/profilers.py
from __future__ import absolute_import
import os
import sys
import functools
from cProfile import Profile
from profile import Profile as pyProfile
from dropbox.trace import TRACE

def memory_profiled(outputfile):

    def genfunc(eff):

        @functools.wraps(eff)
        def thenewfunc(*n, **kw):
            if not hasattr(sys, 'getmallocbytecount'):
                raise RuntimeError('Not a memory debug version of Python!')
            prof = Profile(timer=sys.getmallocbytecount)
            a = prof.runcall(eff, *n, **kw)
            prof.dump_stats(outputfile)
            TRACE('Allocated %d bytes' % sys.getmallocbytecount())
            return a

        return thenewfunc

    return genfunc


def cpu_mem_profiled(outputfile):

    class Bias(object):
        pass

    class MemoryStat(int):
        __slots__ = ('rss', 'thread_cpu', 'global_cpu', 'sum')

        def __new__(cls, rss, thread_cpu, global_cpu, sum):
            a = int.__new__(cls, 0)
            a.rss = rss
            a.thread_cpu = thread_cpu
            a.global_cpu = global_cpu
            a.sum = sum
            return a

        def __repr__(self):
            return 'MemoryStat(%f, %d, %f, %f)' % (self,
             self.rss,
             self.thread_cpu,
             self.global_cpu)

        def __sub__(self, other):
            if isinstance(other, MemoryStat):
                delta_global_cpu = self.global_cpu - other.global_cpu
                if delta_global_cpu:
                    new_val = (self.rss - other.rss) * float(self.thread_cpu - other.thread_cpu) / delta_global_cpu
                    if new_val > 0:
                        self.sum[0] += new_val
                        return MemoryStat(new_val, other.rss, other.thread_cpu, other.global_cpu, self.sum)
                return MemoryStat(0, other.rss, other.thread_cpu, other.global_cpu, self.sum)
            elif isinstance(other, Bias):
                return self
            else:
                return int(self) - other

    def genfunc(eff):

        @functools.wraps(eff)
        def intprofiled(*n, **kw):
            if sys.platform.startswith('linux'):
                import arch
                pid = os.getpid()
                tid = arch.util.thread_id()
                statfile = open('/proc/%d/task/%d/stat' % (pid, tid), 'r')
                sum = [0]

                def timer():
                    statfile.seek(0)
                    stats = statfile.read().split()
                    t = os.times()
                    try:
                        return MemoryStat(long(stats[23]), int(stats[13]) + int(stats[14]), int((t[0] + t[1]) * 100), sum)
                    except IndexError:
                        return MemoryStat(0, 0, int((t[0] + t[1]) * 100), sum)

                prof = pyProfile(timer=timer, bias=Bias())
            else:
                raise RuntimeError('RSS/Cpu profiling not supported on this platform')
            a = prof.runcall(eff, *n, **kw)
            TRACE('Dumping stats to: %r' % (outputfile,))
            prof.dump_stats(outputfile)
            if statfile is not None:
                TRACE('Total CPU Jifs %d' % timer().thread_cpu)
                statfile.close()
            TRACE('Memory Allocated = %d' % sum[0])
            return a

        return intprofiled

    return genfunc


def rss_profiled(outputfile):

    def genfunc(eff):

        @functools.wraps(eff)
        def intprofiled(*n, **kw):
            import arch
            prof = Profile(timer=arch.startup.get_rss)
            a = prof.runcall(eff, *n, **kw)
            TRACE('Dumping stats to: %r' % (outputfile,))
            prof.dump_stats(outputfile)
            TRACE('Final RSS = %d' % arch.startup.get_rss())
            return a

        return intprofiled

    return genfunc


def cpu_profiled(outputfile):

    def genfunc(eff):

        @functools.wraps(eff)
        def intprofiled(*n, **kw):
            import arch
            timer = arch.util.get_cpu_timer()
            prof = Profile(timer=timer)
            a = prof.runcall(eff, *n, **kw)
            TRACE('Dumping stats to: %r' % (outputfile,))
            prof.dump_stats(outputfile)
            TRACE('Total CPU time (maybe in jiffies) %.4f' % timer(close=True))
            return a

        return intprofiled

    return genfunc


def profiled(outputfile):

    def genfunc(eff):

        @functools.wraps(eff)
        def intprofiled(*n, **kw):
            prof = Profile()
            a = prof.runcall(eff, *n, **kw)
            prof.dump_stats(outputfile)
            return a

        return intprofiled

    return genfunc


def timer_profiled(timer):

    def profiler(outputfile):

        def genfunc(eff):

            @functools.wraps(eff)
            def intprofiled(*n, **kw):
                prof = Profile(timer=timer)
                a = prof.runcall(eff, *n, **kw)
                TRACE('Dumping profile stats to: %r' % (outputfile,))
                prof.dump_stats(outputfile)
                TRACE('Profile run: %d' % timer())
                return a

            return intprofiled

        return genfunc

    return profiler


def make_profiled_thread(c, profiler, rootdir = None):
    if rootdir is None:
        rootdir = u'.' + os.path.sep

    class ProfiledThread(c):

        def __init__(self, *n, **kw):
            super(ProfiledThread, self).__init__(*n, **kw)

        def run(self):
            profiler(os.path.join(rootdir, self.getName().decode('utf8') + u'.prof'))(super(ProfiledThread, self).run)()

    return ProfiledThread
