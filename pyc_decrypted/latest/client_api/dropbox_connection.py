#Embedded file name: client_api/dropbox_connection.py
from __future__ import absolute_import
import base64
import build_number
import contextlib
import httplib
import string
import errno
import zlib
import gzip
import time
import json
import socket
import ssl
import sys
import threading
import pprint
from cStringIO import StringIO
import struct
from functools import partial
from dropbox.build_common import get_build_number
from dropbox.callbacks import Handler
from dropbox.dbexceptions import RequestDataOversizeError
from dropbox.event import TimedEvent
from dropbox.functions import lenient_decode, safe_str
from dropbox.threadutils import ThreadPool
from dropbox.throttle import Throttle
from dropbox.trace import assert_, TRACE, unhandled_exc_handler
from .hashing import DROPBOX_HASH_LENGTH, DROPBOX_MAX_BLOCK_SIZE
from .connection_hub import HTTPConnectionHub, DropboxServerError, DropboxResponseServerError, HTTP404Error
MAX_DATA_SIZE = 4194304
_to_websafe = string.maketrans('+/=', '-_~')

def safe_str_dict(**kwargs):
    return dict(((k, safe_str(v)) for k, v in kwargs.iteritems()))


class ServerListHTTPConnectionHub(HTTPConnectionHub):

    class UnderlyingConn:

        def __init__(self, conn):
            self.conn = conn
            self.in_use = True

    def __init__(self, override_map, server_list, **kwargs):
        HTTPConnectionHub.__init__(self, server_list, **kwargs)
        self.override_map = override_map
        self.silock = threading.RLock()
        self.connection_map = {}
        self.nuked = False

    def connect(self, event):
        HTTPConnectionHub.connect(self, event)
        if self.threadingLocal.conn:
            curr_thr = threading.currentThread()
            with self.silock:
                if curr_thr in self.connection_map:
                    if self.connection_map[curr_thr].conn != self.threadingLocal.conn:
                        TRACE('BUG: The connection_map in ServerListHTTPConnectionHub has become out of date for thread %s. We likely closed a connection without using disconnect()', curr_thr.name)
                    self.connection_map[curr_thr].in_use = True
                else:
                    self.connection_map[curr_thr] = ServerListHTTPConnectionHub.UnderlyingConn(self.threadingLocal.conn)

    def disconnect(self):
        curr_thr = threading.currentThread()
        if not hasattr(self.threadingLocal, 'conn'):
            TRACE("BUG: calling disconnect() on thread %s which doesn't have a connection", curr_thr.name)
        elif curr_thr not in self.connection_map or self.connection_map[curr_thr].conn != self.threadingLocal.conn:
            poss = [ k.name for k, v in self.connection_map.iteritems() if v.conn == self.threadingLocal.conn ]
            if not poss:
                s = 'Connection map does not contain this conn. Has it been cut already?'
            else:
                s = 'connect() was called from one of %s. Its bad since both deal with threadingLocal' % poss
            TRACE('BUG: disconnect() in ServerListHTTPConnectionHub called from %s. %s', curr_thr.name, s)
        HTTPConnectionHub.disconnect(self)
        with self.silock:
            try:
                del self.connection_map[curr_thr]
            except KeyError:
                pass

    def disconnect_all_threads(self, force_kill = False):
        with self.silock:
            if self.nuked:
                TRACE('Unexpected condition! Called disconnect_all_threads from %s more than once', self.name)
                assert_(lambda : not self.nuked)
            self.nuked = True
            self.force_no_retries()
            for thr, underlying_conn in self.connection_map.iteritems():
                if force_kill or not underlying_conn.in_use:
                    try:
                        underlying_conn.conn.hard_close()
                    except Exception:
                        unhandled_exc_handler(False)

    def expire_all_threads(self):
        with self.silock:
            for underlying_conn in self.connection_map.itervalues():
                try:
                    underlying_conn.conn.expire()
                except Exception:
                    unhandled_exc_handler(False)

    def request(self, cmd, *n, **kw):
        if not self.override_map:
            conn = super(ServerListHTTPConnectionHub, self)
        else:
            try:
                conn = self.override_map[cmd.split('?')[0]]
            except KeyError:
                conn = super(ServerListHTTPConnectionHub, self)

        ret = conn.request(cmd, *n, **kw)
        with self.silock:
            if self.nuked and self.threadingLocal.conn is not None:
                HTTPConnectionHub.disconnect(self)
            elif threading.currentThread() in self.connection_map:
                self.connection_map[threading.currentThread()].in_use = False
        return ret


def to_host_port(url):
    if url.startswith('https://'):
        url = url[8:]
    port = 443
    if url.find(':') != -1:
        url, port = url.split(':')
    return (str(url), int(port))


class HashPiecesDownloader(object):
    HEADER_FORMAT = '!%dsIII' % DROPBOX_HASH_LENGTH
    HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)

    def __init__(self, handle_piece):
        self.payload_length = None
        self.current_acc = ''
        self.data_written = 0
        self.handle_pieces = handle_piece

    def handle_data(self, gzip_data):
        while True:
            if self.payload_length is None:
                to_shift = self.HEADER_LENGTH - len(self.current_acc)
                self.current_acc += gzip_data[:to_shift]
                gzip_data = buffer(gzip_data, to_shift)
                if len(self.current_acc) == self.HEADER_LENGTH:
                    _hash, offset, length, payload_length = struct.unpack(self.HEADER_FORMAT, self.current_acc)
                    self.handle_pieces.new_piece(_hash, offset, length, payload_length)
                    self.payload_length = payload_length
                else:
                    assert not gzip_data
                if not gzip_data:
                    return
            left = self.payload_length - self.data_written
            to_write = buffer(gzip_data, 0, left)
            self.handle_pieces.new_data(to_write)
            self.data_written += len(to_write)
            if self.data_written == self.payload_length:
                self.payload_length = None
                self.current_acc = ''
                self.data_written = 0
            gzip_data = buffer(gzip_data, left)
            if not gzip_data:
                return


class DropboxConnection(object):
    SERVER_MAP = [('blockserver', ['retrieve',
       'retrieve_thumbnail',
       'store',
       'retrieve_batch',
       'store_batch']),
     ('block1server', ['retrieve_pieces']),
     ('authserver', ['client_upgrade',
       'link_host_with_ret',
       'link_host_twofactor',
       'register_and_link_with_ret',
       'register_host',
       'send_twofactor_sms',
       'wizard_route']),
     ('metaserver', ['change_mount',
       'client_translation_suggest',
       'close_changeset',
       'commit',
       'commit_batch',
       'desktop_login_syncget_reachable_names',
       'get_shmodel_link',
       'list',
       'list_dirs',
       'list_xattrs',
       'pre_multi_url',
       'record_upgrade_step',
       'report_cu_hashes',
       'send_checksums',
       'send_text',
       'wizard_load_strings',
       'client/notifications/user/retrieve',
       'client/notifications/user/ack_by_nids',
       'client/shared_folder_accept',
       'client/shared_folder_decline']),
     ('metaexcserver', ['exception', 'report_hang', 'report_hang2']),
     ('blockexcserver', ['report_formatted_trace', 'send_trace']),
     ('statserver', ['report_stats']),
     ('notifyserver', ['subscribe'])]

    def __init__(self, host = None, port = None, hosts = None, set_status_label = None, throttle_settings = None, locale = None, meta_proxy_info = None, response_preprocessor = None, event_reporter = None, user_agent_dict = None):
        super(DropboxConnection, self).__init__()
        if host is None:
            assert port is None
            host, port = hosts[0]
        else:
            assert port is not None
            assert hosts is None
            hosts = [(host, port)]
        self.host = host
        self.port = port
        self.meta_proxy_info = meta_proxy_info
        self.override_map = {}
        self.set_status_label = set_status_label
        self.throttle_settings = throttle_settings
        self.locale = locale
        self.response_preprocessor = response_preprocessor
        self.list_argument_handler = Handler()
        self.max_data_size = MAX_DATA_SIZE
        self.user_agent_dict = user_agent_dict
        self.event_reporter = event_reporter
        kwargs = self._build_kw_args()
        kwargs.update({'secure': True,
         'timeout': 90,
         'event_reporter': self.event_reporter})
        self.servers_lock = threading.Lock()
        self.servers = {}
        self.servers['authserver'] = ServerListHTTPConnectionHub(self.override_map, hosts, **kwargs)
        self.servers['block1server'] = ServerListHTTPConnectionHub(self.override_map, [('dl-client1.dropbox.com', 443)], **kwargs)
        self.reqmap = {}
        for conn, reqs in self.SERVER_MAP:
            for req in reqs:
                self.reqmap[req] = conn

        self.host_id = None
        self.host_int = None
        self.current_server_map = {}
        self.reconnect_wakeups_lock = threading.Lock()
        self.reconnect_wakeups = set()
        self.batch_request_pool_lock = threading.Lock()
        self.retrieve_batch_request_pool = None
        self.store_batch_request_pool = None

    def _build_kw_args(self):
        kwargs = {}
        if self.set_status_label is not None:
            kwargs['set_status_label'] = self.set_status_label
        if self.throttle_settings is not None:
            kwargs['throttle_settings'] = self.throttle_settings
        if self.locale:
            kwargs['locale'] = self.locale
        if self.response_preprocessor:
            kwargs['response_preprocessor'] = self.response_preprocessor
        if self.meta_proxy_info:
            kwargs['meta_proxy_info'] = self.meta_proxy_info
        if self.user_agent_dict:
            kwargs['user_agent_dict'] = self.user_agent_dict
        return kwargs

    def is_transient_error(self, e):
        if isinstance(e, DropboxResponseServerError):
            return 'TRANSIENT_HTTP_500'
        if isinstance(e, socket.gaierror):
            return 'TRANSIENT_DNS_LOOKUP'
        if isinstance(e, httplib.BadStatusLine) or isinstance(e, ssl.SSLError) and len(e.args) > 0 and e.args[0] == ssl.SSL_ERROR_EOF:
            return 'TRANSIENT_CONNECTION_DROPPED'
        if isinstance(e, ssl.CertificateError) or isinstance(e, ssl.SSLError) and len(e.args) > 1 and e.args[0] == ssl.SSL_ERROR_SSL and e.args[1].endswith(':certificate verify failed'):
            return 'TRANSIENT_INVALID_SSL_CERT'
        if isinstance(e, ssl.SSLError) and len(e.args) > 1 and e.args[0] == ssl.SSL_ERROR_SSL and e.args[1].endswith(':sslv3 alert bad record mac') or isinstance(e, ssl.SSLError) and len(e.args) > 1 and e.args[0] == ssl.SSL_ERROR_SSL and e.args[1].endswith(':wrong version number'):
            return 'TRANSIENT_OTHER_SSL_ERROR'
        if isinstance(e, socket.error) and e.args and e.args[0] in (errno.ECONNREFUSED,
         errno.ECONNRESET,
         errno.EHOSTDOWN,
         errno.EHOSTUNREACH):
            return 'TRANSIENT_SOCKET_ERROR'

    def get_conn_for_url(self, url):
        try:
            conn_name = self.reqmap[url.split('?', 1)[0]]
        except Exception:
            conn_name = 'authserver'

        with self.servers_lock:
            try:
                conn = self.servers[conn_name]
            except KeyError:
                if conn_name in ('metaexcserver', 'blockexcserver'):
                    self.servers[conn_name] = conn = self.default_exc_connection()
                elif conn_name == 'statserver':
                    self.servers[conn_name] = conn = self.default_stat_connection()
                else:
                    unhandled_exc_handler()
                    conn = self.servers['authserver']

        return conn

    def request(self, url, *n, **kwargs):
        already_tried = []
        for conn_for_url_retries in range(3):
            conn = self.get_conn_for_url(url)
            if conn.server_list in already_tried:
                raise
            try:
                ret = conn.request(url, *n, **kwargs)
                break
            except Exception:
                if not conn.nuked:
                    raise
                already_tried.append(conn.server_list)

        else:
            raise

        if isinstance(ret, dict):
            if 'conn_chillout' in ret and type(ret['conn_chillout']) is dict:
                for server_name, chillout in ret['conn_chillout'].iteritems():
                    try:
                        self.servers[server_name].update_chillout(chillout)
                    except Exception:
                        unhandled_exc_handler()

                del ret['conn_chillout']
            if 'chillout' in ret and type(ret['chillout']) in (int, float, long):
                conn.update_chillout(ret['chillout'])
                del ret['chillout']
        return ret

    def default_exc_connection(self):
        return ServerListHTTPConnectionHub(self.override_map, [('d.' + self.host.split('.', 1)[1], 443)], throttle_settings=self.throttle_settings, secure=True, meta_proxy_info=self.meta_proxy_info, locale=self.locale, response_preprocessor=self.response_preprocessor, event_reporter=self.event_reporter)

    def default_stat_connection(self):
        return ServerListHTTPConnectionHub(self.override_map, [('client-stats.' + self.host.split('.', 1)[1], 443)], throttle_settings=self.throttle_settings, secure=True, meta_proxy_info=self.meta_proxy_info, locale=self.locale, response_preprocessor=self.response_preprocessor, event_reporter=self.event_reporter)

    def _form_pickle(self, s):
        return base64.encodestring(zlib.compress(s)).translate(_to_websafe, ' \n\t')

    def _cook(self, s):
        return base64.encodestring(s.encode('utf8')).replace('\n', '')

    def _encode_multipart_formdata(self, fields = None, files = (), already_compressed = False):
        BOUNDARY = '-----------------------------%d' % int(time.time() * 1000)
        CRLF = '\r\n'
        L = []
        if fields:
            for key, value in fields.iteritems():
                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="%s"' % key)
                L.append('')
                L.append(str(value))

        for key, filename, value in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: application/octet-stream')
            L.append('')
            if not already_compressed:
                value = zlib.compress(value)
            L.append(value)

        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        headers = {'Content-Type': 'multipart/form-data; boundary=%s' % BOUNDARY,
         'Content-Length': len(body)}
        return (body, headers)

    def set_host_id(self, host_id):
        self.host_id = host_id

    def set_host_int(self, host_int):
        self.host_int = host_int

    def set_overrides(self, ret):
        try:
            override_dict = ret['method_override']
        except KeyError:
            if self.override_map:
                TRACE('Removing all method overrides.')
                old_map = self.override_map.copy()
                self.override_map.clear()
                for oldconn in old_map.itervalues():
                    oldconn.disconnect_all_threads()

            return

        try:
            for method, server_info in override_dict.iteritems():
                try:
                    newlist = map(to_host_port, server_info['server_list'])
                    a = sorted(newlist)
                    b = None if self.override_map.get(method) is None else sorted(self.override_map.get(method).server_list)
                    if a == b:
                        continue
                    TRACE('Updating override for %r (%r)' % (method, a))
                    kwargs = self._build_kw_args()
                    if method in ('exception', 'report_hang', 'report_hang2', 'report_stats', 'send_trace'):
                        try:
                            del kwargs['set_status_label']
                        except KeyError:
                            pass

                    kwargs['event_reporter'] = self.event_reporter
                    oldconn = self.override_map.get(method)
                    self.override_map[method] = ServerListHTTPConnectionHub({}, newlist, secure=server_info.get('secure', True), timeout=server_info.get('timeout', 60), **kwargs)
                    if oldconn is not None:
                        oldconn.disconnect_all_threads()
                except Exception:
                    unhandled_exc_handler()

            for method in set(self.override_map) - set(override_dict):
                oldconn = self.override_map[method]
                del self.override_map[method]
                oldconn.disconnect_all_threads()

        except Exception:
            unhandled_exc_handler()

    DUPLICATE_CONN = object()

    def set_servers(self, ret):

        def set_server(ret, server_name, **kwargs):
            try:
                if server_name not in ret:
                    return False
                oldconn = self.servers.get(server_name)
                kwargs['event_reporter'] = self.event_reporter
                if ret[server_name] is self.DUPLICATE_CONN:
                    assert oldconn
                    host_port_pairs = oldconn.server_list
                else:
                    newlist = ret[server_name].split(',')
                    a = sorted(newlist)
                    b = None if self.current_server_map.get(server_name) is None else sorted(self.current_server_map.get(server_name).split(','))
                    if a == b:
                        return False
                    TRACE('Updating changed server connection %r (%r)' % (server_name, a))
                    host_port_pairs = [ to_host_port(url) for url in newlist ]
                self.servers[server_name] = ServerListHTTPConnectionHub(self.override_map, host_port_pairs, name=server_name, **kwargs)
                if oldconn is not None:
                    forcekill = server_name == 'notifyserver'
                    oldconn.disconnect_all_threads(force_kill=forcekill)
                if ret[server_name] is not self.DUPLICATE_CONN:
                    self.current_server_map[server_name] = ret[server_name]
                return True
            except Exception:
                unhandled_exc_handler()
                return False

        try:
            non_exc_kwargs = self._build_kw_args()
            exc_kwargs = dict(non_exc_kwargs)
            try:
                del exc_kwargs['set_status_label']
            except KeyError:
                pass

            with self.servers_lock:
                set_server(ret, 'blockserver', secure=True, timeout=60, **non_exc_kwargs)
                set_server(ret, 'metaserver', secure=True, timeout=90, **non_exc_kwargs)
                set_server(ret, 'metaexcserver', secure=True, timeout=90, **exc_kwargs)
                set_server(ret, 'blockexcserver', secure=True, timeout=90, **exc_kwargs)
                set_server(ret, 'statserver', secure=True, timeout=90, **exc_kwargs)
                if set_server(ret, 'notifyserver', secure=False, timeout=90, **non_exc_kwargs):
                    self.last_ns_set = None
        except Exception:
            unhandled_exc_handler()

    def add_reconnect_wakeup(self, f):
        with self.reconnect_wakeups_lock:
            self.reconnect_wakeups.add(f)

    def remove_reconnect_wakeup(self, f):
        with self.reconnect_wakeups_lock:
            self.reconnect_wakeups.remove(f)

    def kill_all_connections(self, all_threads = False):
        TRACE('Closing all connections for %s.', 'all threads' if all_threads else threading.currentThread().getName())
        with self.servers_lock:
            for conn in self.servers.values():
                try:
                    if all_threads:
                        conn.disconnect_all_threads()
                    else:
                        conn.disconnect()
                except Exception:
                    unhandled_exc_handler(False)

    def reconnect(self, *n):
        TRACE('Reconnecting (%r)' % self.current_server_map)
        with self.servers_lock:
            to_reconnect = {}
            for name, conn in self.servers.items():
                TRACE('About to disconnect %s_conn' % name)
                to_reconnect[name] = self.DUPLICATE_CONN

        try:
            self.set_servers(to_reconnect)
        except Exception:
            unhandled_exc_handler(False)

        for name, conn in self.override_map.iteritems():
            TRACE("Disconnecting servers for overriden method '%s'" % name)
            try:
                conn.disconnect_all_threads()
            except Exception:
                unhandled_exc_handler(False)

        with self.reconnect_wakeups_lock:
            wakeups = list(self.reconnect_wakeups)
        for callback in wakeups:
            try:
                callback()
            except Exception:
                unhandled_exc_handler(False)

    def register_host(self, host_id, hostname, buildno, tag = '', platform_info = None, uuid = '', upgrading_from = None):
        args = dict(host_id=host_id, hostname=hostname, buildno=buildno, tag=tag, uuid=str(uuid), un=json.dumps([ lenient_decode(i) for i in platform_info ] if platform_info else None), server_list='True')
        if upgrading_from:
            args['upgrading_from'] = upgrading_from
        TRACE('register_host(%s)', pprint.pformat(args))
        ret = self.request('register_host', args)
        self.max_data_size = ret.get('max_data_size', MAX_DATA_SIZE)
        self.set_servers(ret)
        self.set_overrides(ret)
        return ret

    def link_host_with_ret(self, host_id, email, password, display_name, is_sso_link, post_2fa_token):
        args = safe_str_dict(host_id=host_id, email=email, password=password, display_name=display_name, is_sso_link=is_sso_link, post_2fa_token=post_2fa_token)
        return self.request('link_host_with_ret', args, redact_data=True)

    def check_sso_user(self, host_id, email):
        args = safe_str_dict(host_id=host_id, email=email)
        return self.request('check_sso_user', args)

    def link_host_twofactor(self, host_id, checkpoint_tkey, display_name, twofactor_code):
        args = safe_str_dict(host_id=host_id, checkpoint_tkey=checkpoint_tkey, display_name=display_name, twofactor_code=twofactor_code)
        return self.request('link_host_twofactor', args)

    def send_twofactor_sms(self, checkpoint_tkey):
        args = safe_str_dict(checkpoint_tkey=checkpoint_tkey)
        return self.request('send_twofactor_sms', args)

    def register_and_link_with_ret(self, host_id, fname, lname, email, password, password2, display_name):
        args = safe_str_dict(host_id=host_id, fname=fname, lname=lname, email=email, password=password, password2=password2, display_name=display_name)
        return self.request('register_and_link_with_ret', args, redact_data=True)

    def client_upgrade(self, ccn, expmo, expyr, ccode, address, zipcode, city, state, country_code, plan, period, name, version_number = 0):
        args = dict(host_id=self.host_id, ccn=ccn, expmo=expmo, expyr=expyr, ccode=ccode, address=address, zip=zipcode, city=city, state=state, country_code=country_code, plan=plan, period=period, name=name, version=version_number)
        enc_args = dict(((k, safe_str(v)) for k, v in args.iteritems()))
        ret = self.request('client_upgrade', enc_args, redact_data=True)
        return ret

    def send_text(self, mobile_number, strategy):
        return self.request('send_text', dict(host_id=self.host_id, mobile_number=safe_str(mobile_number), strategy=safe_str(strategy)))

    def wizard_route(self, route, wizard_time, tour_time, mobile_text_panel):
        args = dict(host_id=self.host_id, route=route, wizard_time=wizard_time, tour_time=tour_time, mobile_text_panel=mobile_text_panel)
        enc_args = dict(((k, safe_str(v)) for k, v in args.iteritems()))
        return self.request('wizard_route', enc_args)

    def wizard_load_strings(self):
        args = dict(host_id=self.host_id, build_no=get_build_number())
        return self.request('wizard_load_strings', args)

    def retrieve(self, hash, parent = None, sig = None, cb = None, data_cb = None, stop_cb = None):
        request_dict = dict(hash=hash, host_id=self.host_id)
        if parent:
            request_dict['parent'] = parent
        if sig:
            request_dict['sig'] = sig
        return self.request('retrieve', request_dict, is_json=False, dl_datacb=cb, dl_datacb2=data_cb, stop_cb=stop_cb, backoff_period=15, max_backoff_period=300, max_tries=10, do_backoff=True)

    def retrieve_thumbnail(self, filename, blocklist, size = None, format = None):
        request_dict = dict(host_id=self.host_id, filename=filename.encode('utf-8'), blocklist=blocklist)
        if size is not None:
            request_dict['size'] = size
        if format is not None:
            request_dict['format'] = format
        return self.request('retrieve_thumbnail', request_dict, is_json=False, max_tries=1)

    def record_upgrade_step(self, step = None, from_build_no = None, to_build_no = None):
        if build_number.is_frozen():
            assert all((from_build_no, to_build_no, step)), 'Invalid argument to record_upgrade_step: (%r, %r, %r)' % (from_build_no, to_build_no, step)
            return self.request('record_upgrade_step', {'from_build_no': from_build_no,
             'to_build_no': to_build_no,
             'host_id': self.host_id,
             'step': step})
        TRACE('Record Upgrade Step (Nonfrozen Build) from %r to %r step %r', from_build_no, to_build_no, step)

    def retrieve_batch(self, hash2info, cb = None, stop_cb = None, num_streams = 1):
        hashes = [ (hash, getattr(info, 'parent', None), getattr(info, 'sig', None)) for hash, info in hash2info.items() ]
        request_dict = dict(hashes=json.dumps(hashes), host_id=self.host_id)
        return self.request('retrieve_batch', request_dict, is_json=False, dl_datacb=cb, stop_cb=stop_cb, backoff_period=15, max_backoff_period=300, max_tries=10, do_backoff=True, num_streams=num_streams)

    def retrieve_batch_parallel(self, hash2info, num_connections, batch_max_size, cb = None, stop_cb = None):
        event = TimedEvent(url='retrieve_batch_parallel')
        request_pool = self._init_batch_request_pool(num_connections, retrieve=True)
        hash_bins = self._split_hash_batch(hash2info, num_connections, batch_max_size / num_connections)
        response_lock = threading.Lock()
        response = []
        exceptions = []

        def retrieve_bin(bin, stream_cb, num_streams):
            try:
                res = self.retrieve_batch(bin, cb=stream_cb, stop_cb=stop_cb, num_streams=num_streams)
                with response_lock:
                    response.append(res)
            except:
                with response_lock:
                    exceptions.append(sys.exc_info())

        for i, bin in enumerate(hash_bins):
            stream_cb = partial(cb, stream=i)
            request_pool.add_work(retrieve_bin, bin, stream_cb, len(hash_bins))

        request_pool.wait_for_completion(shutdown=False)
        if exceptions:
            type, value, traceback = exceptions[0]
            raise type, value, traceback
        ret = ''.join(response)
        event.info('num_connections', len(hash_bins))
        event.info('response_bytes', len(ret))
        event.event('total')
        if self.event_reporter:
            self.event_reporter.report_client_timing(event.report)
        return ret

    def retrieve_pieces(self, to_download, handle_pieces):
        return self.request('retrieve_pieces', dict(hash_pieces=json.dumps(to_download), host_id=self.host_id), is_json=False, dl_datacb2=HashPiecesDownloader(handle_pieces).handle_data)

    def store(self, hash, data, parent = None, ns_id_to_blocklists = None, already_compressed = False, cb = None, stop_cb = None):
        fields = dict(host_id=self.host_id, hash=hash)
        if parent:
            fields['parent'] = parent
        if ns_id_to_blocklists:
            fields['ns_id_to_blocklists'] = ns_id_to_blocklists
        if not already_compressed:
            data = zlib.compress(data)
        files = (('upload_file', hash, data),)
        data, headers = self._encode_multipart_formdata(fields=fields, files=files, already_compressed=True)
        return self.request('store', data, headers, ul_datacb=cb, stop_cb=stop_cb, backoff_period=15, max_backoff_period=300, max_tries=10, do_backoff=True)

    def store_batch(self, hash2info, already_compressed = False, cb = None, stop_cb = None, num_streams = 1):

        def make_batch_info_dict(hash_, info):
            entry = {'hash': hash_}
            if info.parent:
                entry['parent'] = info.parent
            return entry

        batch_info = [ make_batch_info_dict(hash_, info) for hash_, info in hash2info.iteritems() ]
        fields = dict(host_id=self.host_id, batch_info=json.dumps(batch_info), batch_info_version=1)
        files = ((hash, hash, info.data) for hash, info in hash2info.iteritems())
        data, headers = self._encode_multipart_formdata(fields=fields, files=files, already_compressed=already_compressed)
        return self.request('store_batch', data, headers, ul_datacb=cb, stop_cb=stop_cb, backoff_period=15, max_backoff_period=300, max_tries=10, do_backoff=True, num_streams=num_streams)

    def store_batch_parallel(self, hash2info, num_connections, batch_max_size, already_compressed = False, cb = None, stop_cb = None):
        event = TimedEvent(url='store_batch_parallel')
        event.info('request_bytes', sum((len(getattr(info, 'data', '')) for info in hash2info.itervalues())))
        request_pool = self._init_batch_request_pool(num_connections, retrieve=False)
        hash_bins = self._split_hash_batch(hash2info, num_connections, batch_max_size / num_connections)
        response_lock = threading.Lock()
        response = []
        exceptions = []

        def store_bin(bin, stream_cb, num_streams):
            try:
                res = self.store_batch(bin, already_compressed=already_compressed, cb=stream_cb, stop_cb=stop_cb, num_streams=num_streams)
                with response_lock:
                    response.extend(res)
            except:
                with response_lock:
                    exceptions.append(sys.exc_info())

        for i, bin in enumerate(hash_bins):
            stream_cb = partial(cb, stream=i)
            request_pool.add_work(store_bin, bin, stream_cb, len(hash_bins))

        request_pool.wait_for_completion(shutdown=False)
        if exceptions:
            type, value, traceback = exceptions[0]
            raise type, value, traceback
        event.info('num_connections', len(hash_bins))
        event.event('total')
        if self.event_reporter:
            self.event_reporter.report_client_timing(event.report)
        return response

    def _init_batch_request_pool(self, num_connections, retrieve = True):
        with self.batch_request_pool_lock:
            pool = self.retrieve_batch_request_pool if retrieve else self.store_batch_request_pool
            if pool and len(pool.workers) != num_connections:
                pool.wait_for_completion(shutdown=True)
                pool = None
            if not pool:
                name = '%s_batch_request_pool' % ('retrieve' if retrieve else 'store')
                pool = ThreadPool(name, num_connections)
            if retrieve:
                self.retrieve_batch_request_pool = pool
            else:
                self.store_batch_request_pool = pool
            return pool

    def _split_hash_batch(self, hash2info, num_bins, bin_size):
        hash_sizes = []
        for hash, info in hash2info.iteritems():
            if hasattr(info, 'data'):
                size = len(info.data)
            else:
                size = min(getattr(info, 'size', 0), DROPBOX_MAX_BLOCK_SIZE)
            hash_sizes.append((hash, size))

        hash_sizes.sort(key=lambda hash_size_tuple: hash_size_tuple[1], reverse=True)
        hash_bins = []
        for i in xrange(num_bins):
            hash_bins.append({'hash2info': {},
             'bin_size': 0})

        for hash, hash_size in hash_sizes:
            found_space = False
            for bin in hash_bins:
                if bin['bin_size'] < bin_size:
                    bin['hash2info'][hash] = hash2info[hash]
                    bin['bin_size'] += hash_size
                    found_space = True
                    break

            if not found_space:
                bin['hash2info'][hash] = hash2info[hash]
                bin['bin_size'] += hash_size

        return [ bin['hash2info'] for bin in hash_bins if len(bin['hash2info']) > 0 ]

    def close_changeset(self, changeset_id, ns_id):
        self.request('close_changeset', dict(changeset_id=changeset_id, ns_id=ns_id, host_id=self.host_id))

    def subscribe(self, ns_map, user_map = None, timeout = None):
        ns_set = ns_map.keys()
        ns_set.sort()
        if ns_set != self.last_ns_set:
            if self.last_ns_set:
                TRACE('Namespace set has changed; forcing disconnect from notification server')
                self.get_conn_for_url('subscribe').disconnect()
            self.last_ns_set = ns_set
        ns_map = ','.join([ '%s_%s' % (k, v) for k, v in ns_map.iteritems() ])
        while True:
            try:
                if timeout is not None and timeout < 0:
                    return
                st = time.time()
                timestamp = int(st)
                user_query = ''
                if user_map is not None:
                    uid, nid = user_map
                    user_query = '&user_id=%d&nid=%d' % (uid, nid)
                query = 'subscribe?host_int=%d&ns_map=%s%s&ts=%d' % (self.host_int,
                 ns_map,
                 user_query,
                 timestamp)
                result = self.request(query, max_tries=2)
                if timeout is not None:
                    timeout -= time.time() - st
                legacy_ret = result.get('ret')
                refresh = result.get('refresh')
                if refresh is not None:
                    if len(refresh) > 0:
                        return refresh
                elif legacy_ret is not None:
                    if legacy_ret not in ('new', 'punt'):
                        raise Exception("Unrecognized notserver 'ret': %r" % legacy_ret)
                    if legacy_ret != 'punt':
                        return ('list',)
                else:
                    raise Exception('Unrecognized notserver response: %r' % result)
            except DropboxServerError as e:
                if int(e.args[1]) / 100 == 5:
                    raise
                unhandled_exc_handler()
                TRACE('Non-200 response from server; sleeping for 30 sec and listing')
                time.sleep(30)
                return

    def serialize_ns_map(self, ns_map):
        return ','.join([ '%s_%s' % (k, v) for k, v in ns_map.iteritems() ])

    def list(self, buildno, ns_map, last_resync = None, ns_p2p_key_map = None, need_sandboxes = False, dict_return = False, return_file_ids = False):
        ns_map = self.serialize_ns_map(ns_map)
        args = dict(buildno=buildno, host_id=self.host_id, ns_map=ns_map, xattrs=True, server_list='True', need_sandboxes='1' if need_sandboxes else '0')
        if ns_p2p_key_map is not None:
            args['ns_p2p_key_map'] = json.dumps(ns_p2p_key_map)
        if last_resync:
            args['last_resync'] = last_resync
        if dict_return:
            args['dict_return'] = '1'
        if return_file_ids:
            args['return_file_ids'] = '1'
        self.list_argument_handler.run_handlers(args)
        ret = self.request('list', args)
        if 'max_data_size' in ret:
            self.max_data_size = ret['max_data_size']
        if 'metaserver' in ret:
            self.set_servers(ret)
        self.set_overrides(ret)
        return ret

    def list_xattrs(self, ns_map):
        ns_map = self.serialize_ns_map(ns_map)
        args = dict(host_id=self.host_id, ns_map=ns_map)
        ret = self.request('list_xattrs', args)
        if 'metaserver' in ret:
            self.set_servers(ret)
        return ret

    def list_dirs(self, ns_map):
        ns_map = self.serialize_ns_map(ns_map)
        ret = self.request('list_dirs', dict(host_id=self.host_id, ns_map=ns_map))
        if 'metaserver' in ret:
            self.set_servers(ret)
        return ret

    def gandalf_get_variants(self):
        return self.request('gandalf_get_variants', dict(host_id=self.host_id), backoff_period=30, max_backoff_period=300, max_tries=4, do_backoff=True)

    def send_checksums(self, checksum_map):
        return self.request('send_checksums', dict(host_id=self.host_id, checksum_map=self._form_pickle(json.dumps(checksum_map))))

    def change_mount(self, target_ns, from_mount, to_mount):
        return self.request('change_mount', dict(target_ns=target_ns, from_mount=self._cook(from_mount) if from_mount else '', to_mount=self._cook(to_mount) if to_mount else '', host_id=self.host_id))

    def commit_batch(self, commit_info, changeset_map = None, autoclose = None, extended_ret = False, allow_guid_sjid_hack = True, return_file_ids = True):
        if isinstance(changeset_map, dict):
            changeset_map = ','.join([ '%s_%s' % (k, v) for k, v in changeset_map.iteritems() ])
        elif changeset_map is None:
            changeset_map = ''
        else:
            raise ValueError('Invalid changeset dictionary')
        try:
            data_item_count = len(commit_info)
        except TypeError:
            data_item_count = None

        pickled_commit_info = self._form_pickle(json.dumps(commit_info))
        if self.max_data_size and data_item_count > 1:
            data_size_estimate = len(safe_str(pickled_commit_info))
            if data_size_estimate > self.max_data_size:
                TRACE('commit_batch data size (%s items, %s bytes) exceeds maximum (%s bytes). Not sending request.', data_item_count, data_size_estimate, self.max_data_size)
                raise RequestDataOversizeError(data_size_estimate, self.max_data_size, data_item_count)
        req_dict = dict(commit_info=pickled_commit_info, changeset_map=changeset_map, extended_ret='True' if extended_ret else '', host_id=self.host_id, autoclose='yes' if autoclose else '')
        if return_file_ids:
            req_dict['return_file_ids'] = '1'
        if not allow_guid_sjid_hack:
            req_dict['allow_guid_sjid_hack'] = '0'
        return self.request('commit_batch', req_dict)

    def pre_multi_url(self, id, file_info):
        return self.request('pre_multi_url', dict(id=id, file_info=self._form_pickle(json.dumps(file_info)), host_id=self.host_id))

    def report_exception(self, report, hash, count = 1, tag = None):
        return self.request('exception', dict(hash=hash, report=report, count=str(count), host_id=self.host_id, hostname=socket.gethostname(), buildno=get_build_number() or '', tag='' if tag is None else str(tag)), backoff_period=15, max_backoff_period=300, max_tries=10, do_backoff=True)

    def report_hang(self, is_hung, hung_for, pending_count, updated_count, conflicted_count, high_cpu_minutes, hash_cant_sync, upload_cant_sync, over_quota, last_exception_hash, dbfsevents_broken):
        self.request('report_hang', dict(is_hung=bool(is_hung) and '1' or '0', hung_for=hung_for, pending_count=pending_count, updated_count=updated_count, conflicted_count=conflicted_count, high_cpu_minutes=high_cpu_minutes, host_id=self.host_id, hash_cant_sync=hash_cant_sync and '1' or '0', upload_cant_sync=upload_cant_sync and '1' or '0', over_quota=over_quota and '1' or '0', last_exception_hash=last_exception_hash or '', dbfsevents_broken='1' if dbfsevents_broken else '0'))

    def report_hang2(self, hang_dict):
        self.request('report_hang2', dict(host_id=self.host_id, report_dict=json.dumps(hang_dict)))

    def report_stats(self, client_time_now, stat_list, event_list, buildno, report_id):
        with contextlib.closing(StringIO()) as io:
            with contextlib.closing(gzip.GzipFile(mode='wb', compresslevel=9, fileobj=io)) as gz:
                gz.writelines(json.JSONEncoder(separators=(',', ':')).iterencode({'client_time_now': client_time_now,
                 'stat_list_tuple': stat_list,
                 'event_list_tuple': event_list,
                 'buildno': buildno,
                 'host_id': self.host_int,
                 'report_id': report_id}))
            payload = io.getvalue()
        TRACE('Reporting stats with a payload size of %d', len(payload))
        return self.request('report_stats', headers={'Content-type': 'application/json',
         'Content-encoding': 'gzip'}, data=payload)

    def report_formatted_trace(self, datas):
        url = 'report_formatted_trace'
        return self.request(url, dict(host_id=self.host_id, data=json.dumps(datas), buildno=get_build_number()))

    def send_trace(self, ts, contents, related_exception = None):
        fields = dict(host_id=self.host_id, ts=ts, buildno=get_build_number() or '')
        if related_exception:
            fields['exc'] = related_exception
        files = (('upload_file', str(ts), contents),)
        data, headers = self._encode_multipart_formdata(fields=fields, files=files, already_compressed=True)
        return self.request('send_trace', data, headers)

    def client_translation_suggest(self, location = None, bad_text = None, msg_id = None, suggested_text = None, explanation = None, from_server = None):
        args = dict(host_id=self.host_id, location=location, bad_text=bad_text, msg_id=msg_id, suggested_text=suggested_text, explanation=explanation, from_server=from_server)
        TRACE('client_translation_suggest(%s)', pprint.pformat(args))
        args = dict(((k, safe_str(v)) for k, v in args.iteritems()))
        return self.request('client_translation_suggest', args)

    def set_web_locale(self, locale):
        return self.request('set_web_locale', dict(host_id=self.host_id, locale=locale))

    def abort_subscribe(self):
        self.set_servers({'notifyserver': self.DUPLICATE_CONN})

    def get_reachable_names(self):
        args = dict(host_id=self.host_id)
        return self.request('get_reachable_names', args)

    def report_cu_hashes(self, hashes, sizes):
        args = dict(host_id=self.host_id, cu_hashes=json.dumps(hashes), cu_sizes=json.dumps(sizes))
        return self.request('report_cu_hashes', args)

    def record_unlink_state(self, unlink_state):
        args = dict(new_unlink_state=unlink_state, host_key=self.host_id)
        return self.request('record_unlink_state', args)

    def report_events(self, buildno, events):
        while True:
            with contextlib.closing(StringIO()) as io:
                with contextlib.closing(gzip.GzipFile(mode='wb', compresslevel=9, fileobj=io)) as gz:
                    gz.writelines(json.JSONEncoder(separators=(',', ':')).iterencode({'events': events,
                     'buildno': buildno}))
                payload = io.getvalue()
            data, headers = self._encode_multipart_formdata(fields=dict(host_id=self.host_id), files=[('events', 'events', payload)], already_compressed=True)
            if len(data) > self.max_data_size and len(events) > 1:
                events = events[:len(events) / 2]
                continue
            return self.request('report_events', data, headers)

    def expire_old_connections(self):
        for conn in self.override_map.itervalues():
            conn.expire_all_threads()

        with self.servers_lock:
            for conn in self.servers.itervalues():
                conn.expire_all_threads()

    def desktop_login_sync(self, to_expire, invalidate_all):
        return self.request('desktop_login_sync', dict(host_id=self.host_id, us=self._form_pickle(json.dumps(to_expire)), ia='1' if invalidate_all else '0'))

    def get_shmodel_link(self, server_path, is_dir = None):
        nsid, path = server_path.ns_rel()
        path = path.encode('utf-8')
        data = dict(path=path, nsid=nsid, host_id=self.host_id)
        if is_dir is not None:
            data['is_dir'] = bool(is_dir)
        return self.request('get_shmodel_link', data, chillout=False)

    def get_special_folder_name(self, folder_type):
        data = dict(folder_type=folder_type, host_id=self.host_id)
        return self.request('client/get_special_folder_name', data, chillout=False)

    def list_user_notifications(self, start_nid = None, limit = 100):
        return self.request('client/notifications/user/retrieve', dict(host_id=self.host_id, start_nid=start_nid, limit=limit))

    def ack_user_notifications(self, nid_list):
        formatted_list = '-'.join((str(i) for i in nid_list))
        return self.request('client/notifications/user/ack_by_nids', dict(host_id=self.host_id, nids=formatted_list))

    def shared_folder_accept(self, iid):
        return self.request('client/shared_folder_accept', dict(host_id=self.host_id, iid=iid))

    def shared_folder_decline(self, iid):
        return self.request('client/shared_folder_decline', dict(host_id=self.host_id, iid=iid))

    def list_guids(self, ns_map):
        ns_map_s = self.serialize_ns_map(ns_map)
        return self.request('client/list_guids', dict(host_id=self.host_id, ns_map=ns_map_s))

    def create_collections(self, collection_names):
        return self.request('client/create_collections', dict(host_id=self.host_id, collection_names=json.dumps(collection_names)))
