#Embedded file name: dropbox/memory_tracker.py
import sys
import arch
from build_number import is_frozen, stable_build
from dropbox import memtrace
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.trace import TRACE, report_bad_assumption
DEFAULT_WAIT = 900

class MemoryTrackHandler(object):

    def __init__(self, memory_tracker, wait_secs = DEFAULT_WAIT):
        self.memory_tracker = memory_tracker
        self.wait_secs = wait_secs
        self.last_call = 0.0

    def __call__(self):
        cur_time = get_monotonic_time_seconds()
        if cur_time > self.last_call + self.wait_secs:
            if self.memory_tracker.run():
                self.last_call = cur_time


REPORT_TIME_THRESHOLD = 180
REPORT_MEMORY_THRESHOLD = 524288000
REPORT_MEMORY_DELTA_THRESHOLD = 262144000
IGNORED_TYPES = ()

class MemoryTracker(object):

    def __init__(self):
        self.first_run = True
        self.initial_list_done = False
        self.memory_used = 0
        self.snapshot_full = {}
        self.snapshot = {}
        self.sync_engine = None

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine
        if self.sync_engine.check_if_initial_list_is_done(self.set_initial_list_done):
            self.set_initial_list_done()

    def set_initial_list_done(self):
        self.initial_list_done = True

    def _trace_snapshot(self, to_trace):
        extra_ignore = set()
        extra_ignore.add(id(extra_ignore))
        extra_ignore.add(id(sys._getframe()))
        extra_ignore.add(id(self.snapshot))
        extra_ignore.add(id(self.snapshot_full))
        extra_ignore.update((id(s) for s in self.snapshot_full.values()))
        if not stable_build() or not is_frozen():
            snapshot = memtrace.snapshot(collect=True, extra_ignore=extra_ignore)
            if not self.first_run:
                new_counts = memtrace.get_extra_types(self.snapshot, snapshot)
                extra_ignore.add(id(snapshot))
                extra_ignore.add(id(new_counts))
                to_trace.append('')
                to_trace.append('Object Delta Counts:')
                to_trace.append('%s' % memtrace.format_extra_types(new_counts))
            self.snapshot = snapshot
        if not is_frozen():
            snapshot_full = memtrace.snapshot_full()
            if not self.first_run:
                new_objects = memtrace.get_extra_objects(self.snapshot_full, snapshot_full)
                extra_ignore.add(id(snapshot_full))
                extra_ignore.add(id(new_objects))
                to_trace.append('')
                to_trace.append('Object Referrers:')
                to_trace.append('%s' % memtrace.format_referrers_report(new_objects, expanded_per_type=3, ignored_types=IGNORED_TYPES, extra_ignore=extra_ignore))
            self.snapshot_full = snapshot_full

    def run(self):
        if self.sync_engine is None or not self.initial_list_done:
            return False
        trace_time = get_monotonic_time_seconds()
        try:
            to_trace = ['Memory Report:']
            counts = self.sync_engine.get_queue_counts()
            to_trace.append('Hash: %d, Upload: %d, Download: %d, UploadHash: %d, DownloadHash: %d' % counts)
            if sum(counts) != 0:
                return False
            cur_memory = arch.startup.get_rss()
            to_trace.append('Memory Usage (RSS): %f' % cur_memory)
            if not self.first_run:
                memory_usage_delta = cur_memory - self.memory_used
                to_trace.append('Memory Usage Delta: %f' % memory_usage_delta)
            self.memory_used = cur_memory
            TRACE('\n'.join(to_trace))
            if not self.first_run and self.memory_used > REPORT_MEMORY_THRESHOLD:
                report_bad_assumption('Memory usage very high: %f', self.memory_used)
            if not self.first_run and memory_usage_delta > REPORT_MEMORY_DELTA_THRESHOLD:
                report_bad_assumption('Memory usage increasing rapidly: +%f', memory_usage_delta)
            self.first_run = False
            return True
        finally:
            time_taken = get_monotonic_time_seconds() - trace_time
            TRACE('Time Taken: %f', time_taken)
            if time_taken > REPORT_TIME_THRESHOLD:
                report_bad_assumption('Memory reporting took a loong time: %f', time_taken)
