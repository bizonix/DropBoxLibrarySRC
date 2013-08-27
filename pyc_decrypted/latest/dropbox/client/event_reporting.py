#Embedded file name: dropbox/client/event_reporting.py
import collections
import itertools
import threading
import time
from Crypto.Random import random
from client_api.dropbox_connection import DropboxConnection
from dropbox.event import AGGREGATE_TIMEOUT, report, report_aggregate_event
from dropbox.gui import message_sender, spawn_thread_with_name
from dropbox.native_event import AutoResetEvent
from dropbox.threadutils import StoppableThread
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from dropbox.url_info import dropbox_url_info
import arch

class AggregateEvent(object):

    def __init__(self, data, ts, timeout):
        self.min_ts = ts
        self.max_ts = ts
        self.data = data.copy()
        self.timeout_ts = timeout + time.time()

    def update(self, data, ts):
        self.min_ts = min(self.min_ts, ts)
        self.max_ts = max(self.max_ts, ts)
        for k in data:
            self.data[k] = self.data.get(k, 0) + data[k]

    def is_ready_to_log(self):
        return time.time() > self.timeout_ts


class EventReporterThread(StoppableThread):
    DEFAULT_WAIT_PERIOD = 900

    def __init__(self, buildno, dropbox_app, *n, **kw):
        kw['name'] = 'EVENTREPORTER'
        super(EventReporterThread, self).__init__(*n, **kw)
        self.conn = None
        self.alarmer = AutoResetEvent()
        self.buildno = buildno
        self.dropbox_app = dropbox_app
        self.wait_period = self.DEFAULT_WAIT_PERIOD
        self.lock = threading.Lock()
        self.events = collections.deque()
        self.aggregate_events = {}
        self.timing_report_percent_url = {}
        self.timing_report_percent = 100
        report.pre.add_handler(self._handle_report)
        report_aggregate_event.pre.add_handler(self._handle_report_aggregate_event)

    def set_conn(self, value):
        self.conn = value

    @message_sender(spawn_thread_with_name('FLUSH_EVENTS'), block=False, dont_post=lambda : False)
    def flush_async(self):
        return self.flush_events(True)

    def flush_events(self, force = True):
        TRACE('Flushing events')
        conn = self.conn
        if force and not conn:
            TRACE('Forcing dropbox connection to report events')
            conn = DropboxConnection(hosts=dropbox_url_info.api_hosts, event_reporter=self.dropbox_app.event, user_agent_dict=arch.util.get_user_agent_dict())
            conn.set_host_id(self.dropbox_app.unlink_cookie['host_id'])
        self._send_events_to_server(conn)

    def report(self, data_name, data = None, ts = None, **info):
        if data:
            info['data'] = data
        if ts:
            info['ts'] = ts
        return report(data_name, **info)

    def report_aggregate_event(self, data_name, data, ts = None, approx_timeout = AGGREGATE_TIMEOUT):
        return report_aggregate_event(data_name, data=data, ts=ts, approx_timeout=approx_timeout)

    def _handle_report(self, data_name, **info):
        event = info.copy()
        event['ts'] = info.get('ts') or time.time()
        event['data_name'] = data_name
        with self.lock:
            self.events.append(event)

    def _handle_report_aggregate_event(self, data_name, data, ts = None, approx_timeout = AGGREGATE_TIMEOUT):
        if ts is None:
            ts = time.time()
        with self.lock:
            try:
                self.aggregate_events[data_name].update(data, ts)
            except KeyError:
                self.aggregate_events[data_name] = AggregateEvent(data, ts, approx_timeout)

    def _get_events(self):
        with self.lock:
            remove_me = []
            for name, ae in self.aggregate_events.iteritems():
                if ae.is_ready_to_log():
                    data = ae.data
                    data['min_ts'] = int(ae.min_ts)
                    data['max_ts'] = int(ae.max_ts)
                    self.events.append({'data_name': name,
                     'ts': time.time(),
                     'data': data})
                    remove_me.append(name)

            for name in remove_me:
                self.aggregate_events.pop(name)

            if self.events:
                events, self.events = self.events, collections.deque()
                return events

    def _put_back_events(self, events):
        with self.lock:
            events.extend(self.events)
            self.events = events

    def _send_events_to_server(self, conn = None):
        try:
            conn = conn or self.conn
            if not conn:
                return
            events = self._get_events()
            if not events:
                return
            self._send_these_events_to_server(events, conn=conn)
        except Exception:
            unhandled_exc_handler()

    def _send_these_events_to_server(self, events, conn = None):
        conn = conn or self.conn
        try:
            try:
                TRACE('Sending %r clogger events to server', len(events))
                ret = conn.report_events(self.buildno, list(events))
                if ret['ret'] != 'ok':
                    raise Exception(ret)
            except Exception:
                unhandled_exc_handler()
                self._put_back_events(events)
            else:
                self.wait_period = ret.get('wait_period', self.DEFAULT_WAIT_PERIOD)
                self.timing_report_percent = ret.get('timing_report_percent', self.timing_report_percent)
                self.timing_report_percent_url = ret.get('timing_report_percent_url', self.timing_report_percent_url)
                results = ret.get('results')
                if results is None:
                    return
                if len(results) > len(events):
                    report_bad_assumption('More results than events?!')
                elif len(events) > len(results):
                    results += ['fail'] * (len(events) - len(results))
                elif all((result == 'ok' for result in results)):
                    return
                failed = collections.deque()
                for event, result in itertools.izip(events, results):
                    if result == 'ok':
                        continue
                    if result == 'fail':
                        failed.append(event)
                    elif result == 'malformed':
                        report_bad_assumption('Malformed event request %r', event)
                    else:
                        report_bad_assumption('Unknown result from report_events %r', result)

                self._put_back_events(failed)

        except Exception:
            unhandled_exc_handler()

    def set_wakeup_event(self):
        self.alarmer.set()

    def run(self):
        TRACE('EventReporter thread starting.')
        while not self.stopped():
            if self.conn:
                self._send_events_to_server()
            wait_period = self.wait_period
            time_to_wait = random.randint(wait_period - wait_period / 4, wait_period + wait_period / 4)
            self.alarmer.wait(time_to_wait)

        TRACE('Stopping...')

    def report_client_timing(self, timing_report):
        url = timing_report['url'].split('?')[0]
        percent = min(self.timing_report_percent_url.get(url, 100), REPORT_PERCENT_URL.get(url, 100), self.timing_report_percent)
        if percent == 0:
            return
        if percent < 100:
            if random.randrange(10000) >= percent * 100:
                return
        if url in ('retrieve_batch', 'retrieve_batch_parallel', 'store_batch', 'store_batch_parallel'):
            for limit in ('download_hash_batch_max', 'download_hash_batch_max_size', 'download_hash_batch_parallel_connections', 'upload_hash_batch_max', 'upload_hash_batch_max_size', 'upload_hash_batch_parallel_connections'):
                timing_report[limit] = self.dropbox_app.sync_engine.server_limits.get(limit)

        report('timing', **timing_report)


REPORT_PERCENT_URL = {'subscribe': 0,
 'exception': 0,
 'send_trace': 0,
 'report_formatted_trace': 0,
 'report_events': 1,
 'gandalf_get_variants': 1}
