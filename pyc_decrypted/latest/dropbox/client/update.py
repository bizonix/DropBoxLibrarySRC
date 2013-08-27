#Embedded file name: dropbox/client/update.py
import build_number
import functools
import fnmatch
import os
import threading
import time
import urllib2
from client_api.hashing import DROPBOX_MAX_BLOCK_SIZE, DropboxHasher
from dropbox.bubble import BubbleKind, Bubble
from dropbox.trace import report_bad_assumption, unhandled_exc_handler, TRACE
from dropbox.sync_engine import BlockContentsNotFoundError, SyncEngineStoppedError, download_hash
IMPORTING_DELAY_TIME = 86400
updating = False

def download_from_block_server(blocklist, file_name, sync_engine, report_func):
    with sync_engine.fs.open(file_name, 'w') as f:
        bytes = 0
        for blockhash in blocklist.split(','):
            if not sync_engine.running:
                raise SyncEngineStoppedError
            s = None
            try:
                s = sync_engine.contents(blockhash)
            except BlockContentsNotFoundError:
                pass
            except Exception:
                unhandled_exc_handler()

            if s is None:
                s = download_hash(sync_engine, blockhash)
            if not (s != '' and s is not None):
                raise Exception("Couldn't download hash! %r", blockhash)
            f.write(s)
            bytes += len(s)

    TRACE('Wrote %d bytes to file %r', bytes, file_name)


def download_from_url(blocklist, url, file_name, sync_engine, report_func):
    TRACE('Download the updater from URL %s', url)
    response = urllib2.urlopen(url)
    if response.getcode() == 200:
        with sync_engine.fs.open(file_name, 'w') as f:
            for blockhash in blocklist.split(','):
                if not sync_engine.running:
                    raise SyncEngineStoppedError
                dbhash = DropboxHasher()
                while dbhash.total < DROPBOX_MAX_BLOCK_SIZE:
                    data = response.read(DROPBOX_MAX_BLOCK_SIZE - dbhash.total)
                    if data == '':
                        break
                    dbhash.update(data)
                    f.write(data)

                if blockhash != dbhash.digest():
                    raise Exception("Hash doesn't match! Expected: %r, Actual: %r", blockhash, dbhash.digest())

            if response.read(1):
                raise Exception("Number of blocks doesn't match!")
    else:
        raise Exception('Response code is not OK. Received Response Code: %r', response.getcode())
    TRACE('Finish validating block hashes of file %r', file_name)


def download_and_install_update(arch, version, blocklist, url, cache_path, sync_engine, report_func, host_id, dbkeyname, done_cb, flush_events):
    global updating
    try:
        report_func('started_upgrade')
    except Exception:
        unhandled_exc_handler()

    try:
        for fn in os.listdir(unicode(cache_path)):
            if fnmatch.fnmatch(fn, u'dropbox-upgrade-*'):
                try:
                    os.remove(unicode(cache_path.join(fn)))
                except (OSError, IOError):
                    unhandled_exc_handler(False)

    except Exception:
        unhandled_exc_handler()

    try:
        file_name = cache_path.join(u'dropbox-upgrade-%s%s' % (version, arch.EXTENSION))
        count = 1
        while sync_engine.is_exists(file_name):
            file_name = cache_path.join(u'dropbox-upgrade-%s-%d%s' % (version, count, arch.EXTENSION))
            count += 1

        try:
            report_func('started_upgrade_download')
        except Exception:
            unhandled_exc_handler()

        download_from_url_success = False
        if url is not None:
            try:
                download_from_url(blocklist, url, file_name, sync_engine, report_func)
                download_from_url_success = True
            except Exception:
                unhandled_exc_handler()

        if not download_from_url_success:
            download_from_block_server(blocklist, file_name, sync_engine, report_func)
        try:
            report_func('finished_upgrade_download')
        except Exception:
            unhandled_exc_handler()

        if not sync_engine.running:
            raise SyncEngineStoppedError
        start = time.time()
        while True:
            success = sync_engine.status.try_set_status_label('updating', True, fail_if_set=['importing'])
            if success:
                break
            if time.time() - start > IMPORTING_DELAY_TIME:
                TRACE("I can't wait any longer.  Force the update!")
                sync_engine.status.set_status_label('updating', True)
                break
            TRACE('Waiting for photo import to finish')
            time.sleep(1)

        try:
            if flush_events:
                flush_events(True)
        except Exception:
            unhandled_exc_handler()

        try:
            report_func('started_platform_upgrade')
        except Exception:
            unhandled_exc_handler()

        try:
            if build_number.is_frozen():
                arch.update_to(unicode(file_name), version, unicode(cache_path), report_func=report_func, host_id=host_id, dbkeyname=dbkeyname)
            else:
                sync_engine.ui_kit.show_bubble(Bubble(BubbleKind.DEBUG_BUBBLE_AUTOUPDATE, u'Updater has been successfully download to %s' % file_name, u'Updater Download Successful'))
        finally:
            sync_engine.status.set_status_label('updating', False)

    except Exception as e:
        print 'huh ', e
        unhandled_exc_handler(tag='upgrade')

    try:
        if done_cb:
            done_cb()
    except Exception:
        unhandled_exc_handler()

    updating = False


def update_to(arch, update_info, sync_engine, report_func, host_id, dbkeyname = None, synchronous = False, done_cb = None, flush_events = None):
    global updating
    version = update_info['version']
    blocklist = update_info['blocklist']
    url = update_info['url']
    cache_path = sync_engine.verify_cache_path()
    sync_engine.verify_disk_space(cache_path, (blocklist.count(',') + 1) * 4 * 1024 * 1024 * 3)
    arch.can_update()
    if not updating:
        updating = True
        to_update = functools.partial(download_and_install_update, arch, version, blocklist, url, cache_path, sync_engine, report_func, host_id, dbkeyname, done_cb, flush_events)
        if synchronous:
            to_update()
        else:
            threading.Thread(target=to_update, name='UPDATE').start()


class UpgradeLogic(object):
    DEFAULT_AUTO_UPGRADE_INTERVAL = 1800

    def __init__(self, arch, config, conn, from_build_no, new_version_prefix, dbkeyname = None, done_cb = None, flush_events = None):
        self.arch = arch
        self.config = config
        self.conn = conn
        self.from_build_no = from_build_no
        self.new_version_prefix = new_version_prefix
        self.done_cb = done_cb
        self.dbkeyname = dbkeyname
        self.flush_events = flush_events

    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine

    def handle_list(self, ret):
        try:
            next_upgrade_retry_interval = float(ret['upgrade_retry_interval'])
        except (KeyError, ValueError):
            pass
        except Exception:
            unhandled_exc_handler()
        else:
            try:
                with self.config as config:
                    if next_upgrade_retry_interval != config.get('auto_update_retry_interval', self.DEFAULT_AUTO_UPGRADE_INTERVAL):
                        TRACE('Resetting upgrade state, new upgrade retry interval: %r', next_upgrade_retry_interval)
                        config['last_update'] = None
                        config['auto_update_retry_interval'] = next_upgrade_retry_interval
            except Exception:
                unhandled_exc_handler()

        try:
            if 'update_to_dict' in ret:
                version = ret['update_to_dict']['version']
                blocklist = ret['update_to_dict']['blocklist']
                url = ret['update_to_dict']['url']
            else:
                version, blocklist = ret['update_to']
                url = None
        except KeyError:
            return

        TRACE('Received update_to command for version %s', version)
        from_build_no = self.from_build_no
        to_build_no = self.new_version_prefix + version
        report_func = functools.partial(self.conn.record_upgrade_step, from_build_no=from_build_no, to_build_no=to_build_no)
        try:
            report_func('received_upgrade_signal')
        except Exception:
            unhandled_exc_handler()

        try:
            with self.config as config:
                last_update = config.get('last_update')
                update_retry_interval = config.get('auto_update_retry_interval', self.DEFAULT_AUTO_UPGRADE_INTERVAL)
        except Exception:
            last_update = None
            update_retry_interval = self.DEFAULT_AUTO_UPGRADE_INTERVAL

        try:
            if last_update and time.time() < last_update[0] + update_retry_interval:
                TRACE('Skipping update_to version %s because it was tried too recently', version)
            elif not self.sync_engine.running:
                TRACE('Skipping update_to version %s because the sync engine is not running', version)
            else:
                if last_update and last_update[1] == (version, blocklist):
                    report_bad_assumption('This update to version %r has happened before', version)
                self.config['last_update'] = (time.time(),
                 (version, blocklist),
                 from_build_no,
                 to_build_no)
                try:
                    TRACE('Running update_to() for version %s', version)
                    update_info = {'version': version,
                     'blocklist': blocklist,
                     'url': url}
                    update_to(self.arch, update_info, self.sync_engine, report_func, self.conn.host_id, dbkeyname=self.dbkeyname, done_cb=self.done_cb, flush_events=self.flush_events)
                    TRACE('Completed update_to() for version %s', version)
                except Exception:
                    unhandled_exc_handler(tag='upgrade')
                    TRACE('Call was interrupted: update_to() for version %s', version)

        except Exception:
            unhandled_exc_handler()
