#Embedded file name: dropbox/sync_engine/p2p/main.py
from __future__ import absolute_import
import hashlib
import dropsyncore as asyncore
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.native_event import AutoResetEvent
from dropbox.functions import frozendict
from dropbox.url_info import dropbox_url_info
from dropbox.fd_leak_debugging import debug_fd_leak
from .util import socketpair
from .discovery import DiscoveryEngine
from .protocol import P2PServer, ConnectionPool, set_force_tlsv1
VERSION = (1, 8)

class P2PState(object):

    def p2p_pref_callback(self, pref_state):
        self.p2p_enabled = pref_state['p2p_enabled']
        self.p2p_enabled_event.set()

    def __init__(self, config, status, pref_controller, host_int, sync_engine):
        self.config = config
        self.status = status
        self.host_int = host_int
        self.sync_engine = sync_engine
        self.status = status
        self._ns_p2p_key_map = {}
        try:
            with self.config as _config:
                try:
                    self._ns_p2p_key_map = dict(((ns, val[2]) for ns, val in (_config.get('ns_p2p_key_map') or frozendict()).iteritems()))
                except Exception:
                    unhandled_exc_handler()
                    try:
                        _config['ns_p2p_key_map'] = self._ns_p2p_key_map
                    except Exception:
                        unhandled_exc_handler()

        except:
            unhandled_exc_handler()

        self.xsock = None
        self.pool = None
        self.p2pserver = None
        self.mymap = {}
        self.p2p_loaded = False
        self.discovery = None
        self.reset_all_connections_event = AutoResetEvent()
        self.p2p_enabled_event = AutoResetEvent()
        try:
            self.p2p_enabled = pref_controller['p2p_enabled']
        except Exception as e:
            if not isinstance(e, KeyError):
                unhandled_exc_handler()
            self.p2p_enabled = False

        pref_controller.add_pref_callback('p2p_enabled', self.p2p_pref_callback)
        try:
            self.enable_p2p_from_preferences()
        except:
            unhandled_exc_handler()
            self.p2p_loaded = False
        else:
            self.p2p_loaded = True

    def pause(self):
        TRACE('Pausing P2P')
        try:
            if self.p2p_enabled:
                if self.p2pserver:
                    self.p2pserver.close()
                    self.p2pserver.want_die()
                if self.pool:
                    self.pool.closeAllConnections()
        except:
            unhandled_exc_handler()

    def unpause(self):
        TRACE('Unpausing P2P')
        try:
            self.p2p_enabled_event.set()
        except:
            unhandled_exc_handler()

    def enable_p2p_from_preferences(self):
        if self.p2p_enabled:
            TRACE('Enabling P2P')
            if not self.discovery:
                self.discovery = DiscoveryEngine()
                a, self.xsock = socketpair()
                self.xsock.setblocking(1)
                self.pool = ConnectionPool(status=self.status, discovery=self.discovery, sock=a, p2p_state=self, map=self.mymap, version=VERSION)
                self.discovery.set_announcement_data(version=self.pool.version, port=dropbox_url_info.p2p_port, host_int=dropbox_url_info.host_int, namespaces_callback=self.sync_engine.get_all_tracked_namespaces)
            if self.pool and not self.p2pserver:
                self.p2pserver = P2PServer(self, self.sync_engine, map=self.mymap, pool=self.pool)
        else:
            TRACE('Disabling P2P')
            if self.p2pserver:
                self.p2pserver.want_die()
            if self.pool:
                self.pool.closeAllConnections()

    def loop(self, stopped):
        while not stopped() and self.p2p_loaded:
            if self.pool:
                if self.p2p_enabled:
                    self.discovery.pulse()
                try:
                    want_fastwakeup = self.pool.pulse()
                except Exception as e:
                    TRACE('ERROR in p2p pulsing - disabling p2p code')
                    self.p2p_loaded = False
                    unhandled_exc_handler()
                    try:
                        assert False, 'p2p disabled: %s' % (e,)
                    except:
                        unhandled_exc_handler()

                    break

                if want_fastwakeup:
                    timeout = 0.2
                else:
                    timeout = 2
                debug_fd_leak()
                try:
                    asyncore.loop(timeout=timeout, count=1, map=self.mymap)
                except Exception as e:
                    TRACE('ERROR in p2p thread - disabling p2p code')
                    self.p2p_loaded = False
                    unhandled_exc_handler()
                    try:
                        assert False, 'p2p disabled: %s' % (e,)
                    except:
                        unhandled_exc_handler()

                    break

                if self.p2p_enabled_event.isSet():
                    self.p2p_enabled_event.clear()
                    self.enable_p2p_from_preferences()
                if self.p2pserver:
                    if self.p2pserver.check_death():
                        self.p2pserver = None
                if self.reset_all_connections_event.isSet():
                    self.reset_all_connections_event.clear()
                    if self.p2p_enabled:
                        TRACE('resetting all connections')
                        self.pause()
                        if self.p2pserver:
                            if self.p2pserver.check_death():
                                self.p2pserver = None
                        self.unpause()
            else:
                self.p2p_enabled_event.wait()
                self.enable_p2p_from_preferences()

    def update_active_namespaces(self, ns_set):
        ns_set = frozenset(ns_set)
        to_del = [ ns for ns in self._ns_p2p_key_map if ns not in ns_set ]
        try:
            with self.config as config:
                ns_p2p_key_map = config.get('ns_p2p_key_map') or {}
                for ns in to_del:
                    try:
                        del ns_p2p_key_map[ns]
                    except:
                        unhandled_exc_handler()

                config['ns_p2p_key_map'] = ns_p2p_key_map
        except:
            unhandled_exc_handler()
        else:
            for ns in to_del:
                del self._ns_p2p_key_map[ns]

    def ns_p2p_key_map_request(self, ns_list):
        return dict(((ns, self._ns_p2p_key_map.get(ns)) for ns in ns_list))

    def ns_p2p_key_map(self):
        try:
            return self.config.get('ns_p2p_key_map') or frozendict()
        except:
            unhandled_exc_handler()
            return frozendict()

    def _handle_list(self, ret):
        if 'p2p_force_tlsv1' in ret:
            if set_force_tlsv1(ret['p2p_force_tlsv1']):
                self.reset_all_connections_event.set()
        try:
            new_ns_p2p_key_map = ret['ns_p2p_key_map']
        except KeyError:
            pass
        else:
            rly_new = {}
            for ns, di in new_ns_p2p_key_map.iteritems():
                try:
                    ns = long(ns)
                    md = hashlib.md5(di['cert'] + di['pk']).hexdigest()
                    if md != di['md5']:
                        continue
                    rly_new[ns] = (di['cert'], di['pk'], md)
                except:
                    unhandled_exc_handler()

            try:
                with self.config as config:
                    a = config.get('ns_p2p_key_map') or {}
                    a.update(rly_new)
                    config['ns_p2p_key_map'] = a
            except:
                unhandled_exc_handler()
                try:
                    self.config['ns_p2p_key_map'] = {}
                except:
                    unhandled_exc_handler()
                else:
                    self._ns_p2p_key_map = {}

            else:
                self._ns_p2p_key_map.update(((ns, val[2]) for ns, val in rly_new.iteritems()))


class P2PThread(StoppableThread):

    def __init__(self, sync_engine, *n, **kw):
        kw['name'] = 'P2P'
        self.sync_engine = sync_engine
        self.p2p_state = sync_engine.p2p_state
        super(P2PThread, self).__init__(*n, **kw)

    def set_wakeup_event(self):
        self.p2p_state.p2p_enabled_event.set()

    def run(self):
        try:
            TRACE('Starting P2P Thread.')
            self.p2p_state.loop(self.stopped)
            TRACE('Stopping...')
        except:
            unhandled_exc_handler()
