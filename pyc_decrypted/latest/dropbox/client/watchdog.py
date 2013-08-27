#Embedded file name: dropbox/client/watchdog.py
import hashlib
import os
import socket
import struct
import threading
import time
from Crypto.Random import random
from trace_report import make_report
from dropbox.build_common import get_build_number
from dropbox.callbacks import Handler
from dropbox.fileutils import safe_remove
from dropbox.globals import dropbox_globals
from dropbox.native_event import AutoResetEvent
from dropbox.native_queue import Queue
from dropbox.platform import platform
from dropbox.sqlite3_helpers import sqlite3_get_memory_statistics
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, unhandled_exc_handler, add_exception_handler, report_bad_assumption
import arch
from dropbox.client.high_trace import sample_process, send_ds_store, send_finder_crashes, send_trace_log
_ONE_WEEK = 604800

class Watchdog2(object):
    UNIT_REPORT_INTERVAL = 900
    HIGH_CPU_USAGE = 0.3

    def __init__(self, status_controller, conn, handler = None):
        self.status_controller = status_controller
        self.sync_engine = None
        self.conn = conn
        add_exception_handler(self.handle_exception)
        self.clear()
        if handler:
            handler.add_handler(self.update_counts)

    def clear(self):
        self.last_times = (time.time(), 0, 0)
        self.hung_since = None
        self.high_cpu_minutes = 0
        self.over_quota = False
        self.report_interval = self.UNIT_REPORT_INTERVAL
        self.last_cpu_minutes = 0
        self.last_dbfseventsd_broken = False
        self.last_counts = (0, 0, 0, 0)
        self.last_report = 0
        self.last_exception_hash = None
        self.last_upload_exception_hash = None
        self.last_reconstruct_exception_hash = None
        self.last_hash_exception_hash = None
        self.exc_lock = threading.Lock()

    def handle_exception(self, *exc_info, **kw):
        with self.exc_lock:
            self.last_exception_hash = make_report(exc_info)[1]
            thr_name = threading.currentThread().getName()
            if thr_name == 'UPLOAD':
                self.last_upload_exception_hash = self.last_exception_hash
            elif thr_name == 'RECONSTRUCT':
                self.last_reconstruct_exception_hash = self.last_exception_hash
            elif thr_name == 'HASH':
                self.last_hash_exception_hash = self.last_exception_hash

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine
        self.sync_engine.add_list_callback(self._handle_list)

    def _handle_list(self, ret):
        try:
            self.over_quota = ret['in_use'] > ret['quota']
        except KeyError:
            pass

    def update_counts(self):
        if not self.sync_engine:
            return
        if not self.sync_engine.running:
            self.clear()
            return
        ct = time.time()
        elapsed = ct - self.last_times[0]
        if elapsed >= 60:
            sys_time = ct, utime, stime = self.sync_engine.get_system_time_tuple()
            cpu_usage = (stime + utime - (self.last_times[1] + self.last_times[2])) / elapsed
            if cpu_usage > self.HIGH_CPU_USAGE:
                self.high_cpu_minutes += 1
                TRACE('!! Warning: high CPU usage (%d mins total; %.1f%% used)' % (self.high_cpu_minutes, cpu_usage * 100))
            self.last_times = sys_time
        if ct - self.last_report >= self.report_interval:
            queue_stats = self.sync_engine.get_queue_stats()
            counts = (queue_stats['hash']['total_count'],
             queue_stats['upload']['total_count'],
             queue_stats['reconstruct']['total_count'],
             queue_stats['conflicted']['total_count'])
            is_hung = self.last_counts == counts and sum(counts)
            cpu_minutes = self.high_cpu_minutes - self.last_cpu_minutes
            dbfseventsd_broken = dropbox_globals.get('dbfseventsd_is_broken', False)
            try:
                if is_hung or self.last_dbfseventsd_broken != dbfseventsd_broken and dbfseventsd_broken or cpu_minutes >= 5:
                    TRACE('!! Sync engine appears stalled: %r (%s high cpu mins) dbfseventsd_broken:%r' % (counts, cpu_minutes, dbfseventsd_broken))
                    if self.hung_since is None:
                        self.hung_since = time.time()
                        send_trace_log()
                    if cpu_minutes >= 5:
                        sample_process()
                    current_upload_speed = self.status_controller.upload_status.get_transfer_speed() or 0
                    current_download_speed = self.status_controller.download_status.get_transfer_speed() or 0
                    upload_bytecount, upload_hashcount = self.sync_engine.upload_queue_size()
                    download_bytecount, download_hashcount = self.sync_engine.download_queue_size()
                    unreconstructable_count = 0
                    self.conn.report_hang2(dict(is_hung=is_hung, dbfseventsd_broken=dbfseventsd_broken, cpu_minutes=cpu_minutes, cpu_minutesp=float(cpu_minutes) / self.report_interval, hung_for=time.time() - self.hung_since, queue_stats=queue_stats, conflicted_count=queue_stats['conflicted']['total_count'], over_quota=self.over_quota, current_upload_speed=current_upload_speed, current_download_speed=current_download_speed, low_disk_space=self.status_controller.is_true('low_disk_space'), upload_bytecount=upload_bytecount, download_bytecount=download_bytecount, upload_hashcount=upload_hashcount, download_hashcount=download_hashcount, unreconstructable_count=unreconstructable_count, exception_hashes=(self.last_exception_hash,
                     self.last_hash_exception_hash,
                     self.last_upload_exception_hash,
                     self.last_reconstruct_exception_hash)))
                elif self.hung_since:
                    TRACE('!! Sync engine no longer stalled: %r' % (counts,))
                    self.conn.report_hang2(None)
                    self.hung_since = None
            except Exception as e:
                if self.conn.is_transient_error(e):
                    TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                else:
                    unhandled_exc_handler()
                self.report_interval += self.UNIT_REPORT_INTERVAL
            else:
                self.last_counts = counts
                self.last_dbfseventsd_broken = dbfseventsd_broken
                self.last_cpu_minutes = self.high_cpu_minutes
                self.last_report = ct
                self.report_interval = self.UNIT_REPORT_INTERVAL


class StatReporter(object):
    DEFAULT_INTERVAL = 900

    def __init__(self, csr, buildno, status_controller, conn, config, handler = None):
        self.csr = csr
        self.config = config
        self.old_stats = {}
        self.last_report = 0
        self.buildno = buildno
        self.interval = self.DEFAULT_INTERVAL
        self.status_controller = status_controller
        self.conn = conn
        self.sync_engine = None
        self.failure_backoff = None
        try:
            with self.config as config:
                try:
                    last_stats_build = config['stats_build']
                except KeyError:
                    self.next_report_id = config.get('stats_next_report_id', 0)
                    self.next_report_time = config.get('stats_next_report_time')
                    self.dont_send_until_upgrade = config.get('stats_dont_send_until_upgrade')
                else:
                    if last_stats_build != get_build_number():
                        self.next_report_id = 0
                        self.next_report_time = None
                        self.dont_send_until_upgrade = False
                    else:
                        self.next_report_id = config.get('stats_next_report_id', 0)
                        self.next_report_time = config.get('stats_next_report_time')
                        self.dont_send_until_upgrade = config.get('stats_dont_send_until_upgrade')

        except Exception:
            unhandled_exc_handler()
            self.next_report_id = 0
            self.next_report_time = None
            self.dont_send_until_upgrade = False

        if self.next_report_time:
            TRACE('Client stats wants us to hit the server again at %s (%s seconds) (local: %s)' % (self.next_report_time, self.next_report_time - time.time(), time.ctime(self.next_report_time)))
        if handler:
            handler.add_handler(self.run)

    def set_reporting_interval(self, interval):
        self.interval = interval

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine

    def report_queryable_stats(self):
        us = self.status_controller.upload_status.get_transfer_speed()
        if us is not None:
            self.csr.report_stat('upload_speed', str(us))
        ds = self.status_controller.download_status.get_transfer_speed()
        if ds is not None:
            self.csr.report_stat('download_speed', str(ds))
        if self.sync_engine:
            queue_stats = self.sync_engine.get_queue_stats()
            self.csr.report_stat('pending_cache_count', str(queue_stats['upload']['total_count']))
            self.csr.report_stat('to_hash_cache_count', str(queue_stats['hash']['total_count']))
            self.csr.report_stat('updated_cache_count', str(queue_stats['reconstruct']['total_count']))
            self.csr.report_stat('conflicted_cache_count', str(queue_stats['conflicted']['total_count']))
            self.csr.report_stat('quota_pending_cache_count', str(queue_stats['upload']['failure_counts'].get('quota', 0)))
            self.csr.report_stat('invalid_path_pending_cache_count', str(queue_stats['upload']['failure_counts'].get('invalid_path', 0)))
            self.csr.report_stat('directory_not_empty_updated_cache_count', str(queue_stats['reconstruct']['failure_counts'].get('directory_not_empty', 0)))
            self.csr.report_stat('low_disk_space_updated_cache_count', str(queue_stats['reconstruct']['failure_counts'].get('low_disk_space', 0)))
            self.csr.report_stat('permission_denied_updated_cache_count', str(queue_stats['reconstruct']['failure_counts'].get('permission_denied', 0)))
        n = int(time.time())
        self.csr.report_stat('gui_backoff_factor', str(struct.unpack('<Q', hashlib.md5('Open %s Folder Launch %d Website Apple CarbonEventManager Windows %d' % (self.buildno, n, self.conn.host_int)).digest()[:struct.calcsize('<Q')])[0]), n)
        rss = arch.startup.get_rss()
        if rss is not None and rss != -1:
            self.csr.report_stat('rss', str(rss))
        try:
            mem_used, highwater = sqlite3_get_memory_statistics()
        except Exception:
            unhandled_exc_handler()
        else:
            self.csr.report_stat('sqlite3_memory_used', str(mem_used))
            self.csr.report_stat('sqlite3_memory_highwater', str(highwater))

        try:
            if self.sync_engine and self.sync_engine.p2p_state and self.sync_engine.p2p_state.pool:
                peer_dict = self.sync_engine.p2p_state.pool.getPeerAndConnCount()
                self.csr.report_stat('peer_count', str(peer_dict['peer_count']))
                self.csr.report_stat('peer_connections', str(peer_dict['total_connections']))
        except Exception:
            unhandled_exc_handler()

    def run(self):
        if self.dont_send_until_upgrade:
            return
        if self.failure_backoff:
            if time.time() < self.failure_backoff[1]:
                return
            if self.next_report_time is not None and time.time() < self.next_report_time:
                report_bad_assumption('Client-stats backoff was less than our next report time, %s < %s' % (self.next_report_time, self.failure_backoff[1]))
        elif self.next_report_time is not None and time.time() < self.next_report_time:
            return
        self.report_queryable_stats()
        self.csr.lock_updates()
        try:
            total_stats = self.csr.total_stats()
            total_events = self.csr.total_events()
            report_id = self.next_report_id
            divisor = 1
            done = False
            while not done:
                to_pull_from_stats = total_stats / divisor
                to_pull_from_events = total_events / divisor
                for i in xrange(divisor):
                    stat_batch = self.csr.iterate_n_stats(to_pull_from_stats)
                    event_batch = self.csr.iterate_n_events(to_pull_from_events)
                    stats_to_send = [ (stat, arg, ts) for stat, (arg, ts) in stat_batch ]
                    try:
                        event_ids_to_clear, events_to_send = zip(*event_batch)
                    except ValueError:
                        event_ids_to_clear, events_to_send = (), ()

                    if not (stats_to_send or events_to_send):
                        done = True
                        break
                    try:
                        ret = self.conn.report_stats(time.time(), stats_to_send, events_to_send, self.buildno, report_id)
                    except Exception as e:
                        unhandled_exc_handler()
                        if isinstance(e, socket.error) and e[0] == 32:
                            break
                        if self.failure_backoff:
                            self.failure_backoff = (self.failure_backoff[0] * 2, min(random.uniform(0, self.failure_backoff[0] * 4), _ONE_WEEK) + time.time())
                        else:
                            self.failure_backoff = (1, random.uniform(0, 2) + time.time())
                        TRACE('!! Client Stats failed, backing off until %s for (%s seconds) (local: %s)' % (self.failure_backoff[1], self.failure_backoff[1] - time.time(), time.ctime(self.failure_backoff[1])))
                        done = True
                    else:
                        self.failure_backoff = None
                        try:
                            self.dont_send_until_upgrade = ret['dont_send_until_upgrade']
                        except KeyError:
                            stats_backoff = float(ret['backoff'])
                            next_report_id = long(ret['report_id'])
                            self.next_report_time = stats_backoff + time.time()
                            self.next_report_id = next_report_id
                        else:
                            self.next_report_time = None
                            self.next_report_id = 0

                        try:
                            with self.config as config:
                                config['stats_dont_send_until_upgrade'] = self.dont_send_until_upgrade
                                config['stats_next_report_time'] = self.next_report_time
                                config['stats_next_report_id'] = self.next_report_id
                                config['stats_build'] = get_build_number()
                        except Exception:
                            unhandled_exc_handler()

                        TRACE('Client stats wants us to hit the server again at %s (%s seconds) (local: %s)', self.next_report_time, stats_backoff, time.ctime(self.next_report_time))
                        self.csr.clean_reported_stats_and_event_ids(stats_to_send, event_ids_to_clear)

                divisor *= 2

        finally:
            self.csr.unlock_updates()


def maybe_send_explorer_crash():
    if arch.util.unreported_explorer_crash():
        send_trace_log()


class WatchdogThread(StoppableThread):

    def __init__(self, app, *n, **kw):
        kw['name'] = 'WATCHDOG'
        super(WatchdogThread, self).__init__(*n, **kw)
        self.app = app
        self.bangp = AutoResetEvent()
        self.one_time_q = Queue(100)
        self.handler = Handler(handle_exc=unhandled_exc_handler)
        self.add_handler(self._one_time_handler)

    def set_wakeup_event(self, *n, **kw):
        self.bangp.set(*n, **kw)

    def add_handler(self, *n, **kw):
        self.handler.add_handler(*n, **kw)

    def remove_handler(self, *n, **kw):
        self.handler.remove_handler(*n, **kw)

    def add_one_time_handler(self, cb):
        try:
            self.one_time_q.put(cb)
        except Exception:
            unhandled_exc_handler()

    def _one_time_handler(self, *n, **kw):
        for fn in self.one_time_q.get_all_and_clear():
            try:
                fn(*n, **kw)
            except Exception:
                unhandled_exc_handler()

    def run(self):
        TRACE('Watchdog thread starting.')
        if platform == 'mac':

            def maybe_send_finder_crashes():
                sarch = self.app.sync_engine.arch
                if sarch.fschange and sarch.fschange.potential_finder_restart():
                    send_finder_crashes()

            self.add_handler(maybe_send_finder_crashes)
            self.add_handler(send_ds_store)
        if platform == 'win':
            self.add_handler(maybe_send_explorer_crash)
        send_finder_crashes()
        self.remove_installer_logs()
        while not self.stopped():
            self.handler.run_handlers()
            self.bangp.wait(60)

        TRACE('Stopping...')

    def remove_installer_logs(self):
        if platform != 'win':
            return
        try:
            installer_log_dir = os.path.join(self.app.appdata_path, 'installer', 'l')
            if not os.path.exists(installer_log_dir):
                return
            for x in os.listdir(installer_log_dir):
                full_path = os.path.join(installer_log_dir, x)
                safe_remove(full_path)

        except Exception:
            unhandled_exc_handler()
