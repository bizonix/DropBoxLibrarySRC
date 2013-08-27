#Embedded file name: dropbox/throttle.py
from __future__ import absolute_import
import errno
import select
import socket
import ssl
import threading
import time
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.fd_leak_debugging import debug_fd_leak

class Throttle(object):
    THROTTLE_AUTOMATIC = 60001
    THROTTLE_MANUAL = 60002
    THROTTLE_NONE = 60003
    AUTO_PERCENT = 0.75
    AUTOMATIC_START_SPEED = 51200
    SSL_CHUNK = 512
    INTERVAL = 0.1
    RUN_LENGTH = int(180.0 / INTERVAL)
    MEASURE_SECONDS = 3.0
    MEASURE_WINDOW = int(MEASURE_SECONDS / INTERVAL)
    MAX_DETECT_RUNS = int(10.0 / INTERVAL)

    class ThrottleState(object):
        pass

    def __init__(self):
        self.ul_chunk_size = 1
        self.ul_max_speed_timeout = 30
        self.ul_time_set = 0.0
        self.ul_filter = 65536
        self.ul_minimum_connection_speed = 20480
        self.ul_compute_max = False
        self.ul_compute_max_start_time = None
        self.ul_compute_max_bytes = 0
        self.ul_direction_timeout = 0
        self.ul_throttle_type = Throttle.THROTTLE_NONE
        self.ul_throttle_percentage = Throttle.AUTO_PERCENT
        self.dl_filter = 65536
        self.dl_chunk_size = 16384
        self.dl_throttle_type = Throttle.THROTTLE_NONE
        self.state = Throttle.ThrottleState()
        self.state.throttler = None
        self.state_lock = threading.Lock()
        self.threadingLocal = threading.local()

    def get_upload_speed(self):
        if self.ul_throttle_type == Throttle.THROTTLE_AUTOMATIC:
            if self.state.throttler != Throttle.THROTTLE_AUTOMATIC:
                return None
            elif self.state.auto_state == 0:
                return None
            else:
                return self.state.throttled_speed / Throttle.INTERVAL
        else:
            if self.ul_throttle_type == Throttle.THROTTLE_NONE:
                return None
            return self.ul_speed

    def get_download_speed(self):
        if self.dl_throttle_type != Throttle.THROTTLE_NONE:
            return self.dl_speed
        else:
            return None

    def read(self, resp, cb = None, data_cb = None, stop_cb = None, num_streams = 1):
        headers = dict(resp.getheaders())
        content_length = headers.get('content-length', None)
        if content_length is not None:
            content_length = int(content_length)
        ret = []
        if not data_cb:
            data_cb = ret.append
        to_read = content_length
        try:
            loop_start = self.threadingLocal.request_sent
        except Exception:
            unhandled_exc_handler()
            loop_start = time.time()

        saved = None
        while True:
            if to_read is not None:
                if to_read == 0:
                    break
                chunk = resp.read(min(self.dl_chunk_size, to_read))
                chunk_length = len(chunk)
                to_read -= chunk_length
            else:
                chunk = resp.read(self.dl_chunk_size)
                chunk_length = len(chunk)
            if not chunk:
                break
            stop_cb and stop_cb()
            data_cb(chunk)
            if self.dl_throttle_type != Throttle.THROTTLE_NONE:
                sleep_time = chunk_length / float(self.dl_speed / num_streams) - (time.time() - loop_start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            if cb:
                saved = (chunk_length + saved[0], loop_start) if saved else (chunk_length, loop_start)
                elapsed = time.time() - saved[1]
                if elapsed >= 0.001:
                    cb(saved[0], elapsed)
                    saved = None
            loop_start = time.time()

        if cb and saved:
            elapsed = time.time() - saved[1]
            cb(saved[0], elapsed)
        resp.close()
        return ''.join(ret)

    def request(self, conn, url, data, headers, cb = None, stop_cb = None, num_streams = 1):
        if data:
            if headers is None:
                headers = {}
            if 'Content-Length' not in headers:
                headers['Content-Length'] = len(data)
        self.threadingLocal.request_sent = time.time()
        if not data or len(data) < self.ul_filter:
            conn.request('POST' if data else 'GET', '/' + url, data, headers)
        else:
            TRACE('THROTTLE: Starting a throttled connection %s', url)
            conn.request('POST', '/' + url, None, headers)
            data_length = len(data)
            oldtimeout = conn.sock.gettimeout()
            conn.sock.settimeout(0)
            is_ssl = hasattr(conn.sock, 'ssl_version')
            empty = []
            waiting = (conn.sock.fileno(),)
            empty_return = (empty, empty, empty)
            start_index = 0
            if self.ul_throttle_type == Throttle.THROTTLE_AUTOMATIC:
                with self.state_lock:
                    if self.state.throttler != Throttle.THROTTLE_AUTOMATIC:
                        self.state.throttler = Throttle.THROTTLE_AUTOMATIC
                        self.state.auto_state = 0
                        self.state.samps = [None] * Throttle.MEASURE_WINDOW
                        self.state.sampsall = [None] * Throttle.MAX_DETECT_RUNS
                        self.state.iter = 0
                        self.state.detect_runs = 0
                    if self.state.auto_state == 0:
                        end_index = data_length
                    else:
                        end_index = min(start_index + self.state.throttled_speed / num_streams, data_length)
                started = start_index
                TRACE('Throttle: Automatic')
            elif self.ul_throttle_type == Throttle.THROTTLE_NONE:
                self.state.throttler = Throttle.THROTTLE_NONE
                end_index = data_length
                TRACE('Throttle: None')
            else:
                self.state.throttler = Throttle.THROTTLE_MANUAL
                ul_speed = self.ul_speed / num_streams
                end_index = min(start_index + int(ul_speed * Throttle.INTERVAL), data_length)
                TRACE('Throttle: Manual %0.2f' % ul_speed)
            buf = None
            while start_index < data_length:
                wait = Throttle.INTERVAL
                stop_cb and stop_cb()
                afin = start_index
                st = time.time()
                while wait > 0:
                    start = time.time()
                    if end_index > start_index:
                        debug_fd_leak()
                        if select.select(waiting, waiting, empty, wait) != empty_return:
                            if is_ssl:
                                while end_index > start_index:
                                    try:
                                        if buf is None:
                                            tosend = min(Throttle.SSL_CHUNK, end_index - start_index)
                                            buf = data[start_index:start_index + tosend]
                                        sent = conn.send(buf)
                                        buf = None
                                        start_index += sent
                                    except ssl.SSLError as e:
                                        if e[0] == socket.SSL_ERROR_WANT_WRITE:
                                            break
                                        else:
                                            TRACE('Error happened, bufsize was: %d, data left: %d, data_length: %d, start_index: %d, end_index: %d' % (tosend,
                                             data_length - start_index,
                                             data_length,
                                             start_index,
                                             end_index))
                                            raise

                            else:
                                while end_index > start_index:
                                    try:
                                        TRACE('start_index: %r end_index %r', start_index, end_index)
                                        TRACE('conn: %r', conn)
                                        start_index += conn.send(data[start_index:start_index + end_index])
                                    except socket.error as e:
                                        if e[0] == errno.EAGAIN:
                                            break
                                        else:
                                            raise

                    else:
                        time.sleep(wait)
                    wait -= time.time() - start

                if cb:
                    cb(start_index - afin, Throttle.INTERVAL)
                if self.ul_throttle_type == Throttle.THROTTLE_AUTOMATIC:
                    with self.state_lock:
                        if self.state.throttler != Throttle.THROTTLE_AUTOMATIC:
                            self.state.iter = 0
                            self.state.detect_runs = 0
                            self.state.throttler = Throttle.THROTTLE_AUTOMATIC
                            self.state.auto_state = 0
                            self.state.samps = [None] * Throttle.MEASURE_WINDOW
                            self.state.sampsall = [None] * Throttle.MAX_DETECT_RUNS
                            end_index = data_length
                            started = start_index
                        else:
                            self.state.samps[self.state.iter] = start_index - started
                            self.state.iter = (self.state.iter + 1) % len(self.state.samps)
                            if self.state.samps[-1] is not None:
                                mes = [ samp for samp in self.state.samps if samp != 0 ]
                                if len(mes) < Throttle.MEASURE_SECONDS:
                                    change = False
                                else:
                                    change = True
                                    avg1 = float(sum(mes)) / len(mes)
                                    avg_dev = float(sum((abs(elt - avg1) for elt in mes))) / len(mes)
                                    stable = avg_dev <= 0.13 * avg1
                                    avg = float(sum(self.state.samps)) / len(self.state.samps)
                            else:
                                change = False
                            if self.state.auto_state == 0:
                                self.state.sampsall[self.state.detect_runs] = start_index - started
                                self.state.detect_runs += 1
                                if change and stable or self.state.detect_runs == Throttle.MAX_DETECT_RUNS:
                                    self.state.auto_state = 1
                                    self.state.samps = [None] * Throttle.MEASURE_WINDOW
                                    self.state.iter = 0
                                    self.state.runs = 0
                                    self.state.throttled_speed = sum(self.state.sampsall[1:]) / (len(self.state.sampsall) - 1) if self.state.detect_runs == Throttle.MAX_DETECT_RUNS else int(avg * self.ul_throttle_percentage)
                                    self.state.throttled_speed *= num_streams
                                    if self.state.throttled_speed == 0:
                                        TRACE('Throttled speed was computed to be 0 %s, resetting to at least 5kB/s', 'after MAX DETECT runs' if self.state.detect_runs == Throttle.MAX_DETECT_RUNS else '')
                                        self.state.throttled_speed = 512
                                    end_index = min(start_index + self.state.throttled_speed / num_streams, data_length)
                                else:
                                    end_index = data_length
                            else:
                                self.state.runs += 1
                                if self.state.runs == Throttle.RUN_LENGTH or change and not stable:
                                    self.state.auto_state = 0
                                    self.state.samps = [None] * Throttle.MEASURE_WINDOW
                                    self.state.sampsall = [None] * Throttle.MAX_DETECT_RUNS
                                    self.state.iter = 0
                                    self.state.detect_runs = 0
                                    end_index = data_length
                                else:
                                    end_index = min(start_index + self.state.throttled_speed / num_streams, data_length)
                        started = start_index
                elif self.ul_throttle_type == Throttle.THROTTLE_NONE:
                    self.state.throttler = Throttle.THROTTLE_NONE
                    end_index = data_length
                else:
                    self.state.throttler = Throttle.THROTTLE_MANUAL
                    end_index = min(start_index + int(self.ul_speed / num_streams * Throttle.INTERVAL), data_length)

            conn.sock.settimeout(oldtimeout)
