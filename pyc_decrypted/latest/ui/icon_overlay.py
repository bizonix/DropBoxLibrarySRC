#Embedded file name: ui/icon_overlay.py
from __future__ import absolute_import
import collections
import time
import urllib
import urlparse
import stat
import errno
import re
import os
import fnmatch
import sys
from functools import partial
from threading import Thread
from dropbox.dispatch import ActionTask
from dropbox.features import feature_enabled
from dropbox.trace import unhandled_exc_handler, TRACE
from dropbox.dbexceptions import InterruptError
from dropbox.gui import message_sender, spawn_thread_with_name
from dropbox.i18n import format_bytes
from dropbox.url_info import dropbox_url_info
from dropbox.path import server_path_ns_rel
from dropbox.platform import platform
from dropbox.threadutils import StoppableThread
from dropbox.sync_engine.constants import FileSyncStatus
import arch
import build_number
from ui.common.icon_overlay import IconOverlayStrings
from ui.common.tray import TrayOptionStrings
if platform == 'mac':
    from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
STATE_TO_LABEL = {0: u'unwatched',
 1: u'up to date',
 2: u'syncing',
 3: u'unsyncable',
 4: u'selective sync'}

def weirdurlencode(item):
    return ''.join([ c in '%|~' and '%%%02X' % ord(c) or c for c in item ])


def encode_menu(items):
    return '|'.join([ encode_item(x) for x in items ])


def encode_item(item):
    if len(item) > 1 and isinstance(item[1], tuple):
        item = list(item)
        item[1] = encode_menu(item[1])
    return '~'.join([ weirdurlencode(x) for x in item ])


def add_matched(context_menu, verb, options, subs):
    menuitem = context_menu['menuitem']
    if len(menuitem) == 1:
        text = menuitem[0]
        options.append((text, text, verb))
        if platform == 'mac' and 'menualt' in context_menu:
            menuitem = context_menu['menualt']
            text = menuitem[0]
            options.append((text,
             text,
             verb,
             'alt'))
    else:
        curmenu = menuitem
        cursubs = subs
        while len(curmenu) > 1:
            name = curmenu[0]
            curmenu = curmenu[1:]
            cursubs = cursubs.setdefault(name, {})

        text = curmenu[0]
        cursubs[text] = verb


def tree_to_menu(tree, val):
    if isinstance(tree, unicode):
        return (val, val, tree)
    ops = []
    for k in tree.keys():
        ops.append(tree_to_menu(tree[k], k))

    return (val, encode_menu(ops), u'submenu')


def match_path(self, path, regex = None, glob = ()):
    if regex or glob:
        glob = tuple(glob)
        try:
            return bool(self.regex_dict[regex, glob].search(path))
        except KeyError:
            m = (['(?:%s)' % regex] if regex is not None else []) + [ '(?:%s)' % fnmatch.translate(g) for g in glob ]
            pat = '(?:%s)' % '|'.join(m)
            self.regex_dict[regex, glob] = re.compile(pat, re.I)
            return bool(self.regex_dict[regex, glob].search(path))

    return False


def is_context_menu_match(self, path, context_menu, is_dir, path_sp):
    local_path = self.se.fs.make_path(path)
    if path_sp is None:
        path_sp = self.se.local_to_server(local_path)
    path_rel = self.se.root_relative_server_path(path_sp).rel
    if match_path(self, path_rel, context_menu.get('exclude')):
        return False
    if is_dir is None:
        is_dir = self.se.is_directory(local_path)
    if is_dir:
        return context_menu.get('folder', False)
    return match_path(self, path_rel, context_menu.get('include'), context_menu.get('fnlist', ()))


def get_context_menus_options(self, pathlist, is_dir = None, path_sp = None):
    subs = {}
    options = []
    multi = len(pathlist) > 1
    assert is_dir is None or not multi
    for verb, context_menu in self.dropbox_app.ui_flags.get('context_menus', dict()).iteritems():
        if multi and not context_menu.get('multiurl', False):
            continue
        if len(pathlist) < context_menu.get('min_selected', 0):
            continue
        server_context_action = context_menu.get('action', None)
        if server_context_action and server_context_action not in server_context_actions:
            continue
        if all((is_context_menu_match(self, path, context_menu, is_dir, path_sp) for path in pathlist)):
            add_matched(context_menu, verb, options, subs)

    for k in subs.keys():
        options.append(tree_to_menu(subs[k], k))

    return options


def get_option_group(self, pathlist):
    options = []
    lowerdb = unicode(self.se.dropbox_folder).lower()
    lowerpath = pathlist[0].lower()
    is_in_dropbox = all((lowerpath.startswith(lowerdb) and (len(lowerdb) == len(lowerpath) or lowerpath[len(lowerdb)] == os.path.sep) for lowerpath in (path.lower() for path in pathlist)))
    if len(pathlist) == 1:
        TRACE('Getting option group for path: %r.', lowerpath)
        try:
            is_dir = stat.S_ISDIR(os.stat(pathlist[0]).st_mode)
        except Exception as e:
            if not isinstance(e, OSError) or e.errno != errno.ENOENT:
                unhandled_exc_handler()
            is_dir = None

        if is_in_dropbox:
            try:
                try:
                    local_path = self.se.arch.make_path(pathlist[0])
                    path_sp = self.se.local_to_server(local_path)
                    path = unicode(path_sp)
                except:
                    unhandled_exc_handler(False)
                    return options

                root_ns_path = u'%s:/' % self.se.main_root_ns
                is_dropbox_folder = path == root_ns_path
                is_in_shared_folder = path_sp.ns != self.se.main_root_ns
                if self.dropbox_app.ui_flags.get('support_public_folder', True):
                    public_folder = u'%d:/public' % (self.se.main_root_ns,)
                    is_in_public_folder = path.lower().startswith(public_folder + u'/') and path.lower() != public_folder
                else:
                    is_in_public_folder = False
                if is_in_public_folder:
                    if not is_dir:
                        options.append((IconOverlayStrings.copy_public_short, IconOverlayStrings.copy_public_long, u'copypublic'))
                elif not is_dropbox_folder:
                    options.append((IconOverlayStrings.shmodel_short, IconOverlayStrings.shmodel_long_folder if is_dir else IconOverlayStrings.shmodel_long_file, u'shmodel_to_clipboard'))
                options.append((IconOverlayStrings.browse_short, IconOverlayStrings.browse_long_folder if is_dir else IconOverlayStrings.browse_long_file, u'browse'))
                if not is_dir:
                    options.append((IconOverlayStrings.view_history_short, IconOverlayStrings.view_history_long, u'revisions'))
                else:
                    unshareable_folders = [root_ns_path]
                    if self.dropbox_app.ui_flags.get('support_public_folder', True):
                        unshareable_folders.append(root_ns_path + 'Public')
                    if not is_in_shared_folder and path not in unshareable_folders:
                        options.append((IconOverlayStrings.share_short, IconOverlayStrings.share_long, u'share'))
                if is_dir is not None:
                    try:
                        context_menu_options = get_context_menus_options(self, pathlist, is_dir=is_dir, path_sp=path_sp)
                        options.extend(context_menu_options)
                    except:
                        unhandled_exc_handler()

                if not is_dir and self.se.is_over_quota(path_sp) and self.dropbox_app.ui_flags.get('upgrade_prompt', False):
                    options.append((IconOverlayStrings.cant_sync_long, IconOverlayStrings.cant_sync_long, u'over_quota'))
            except:
                unhandled_exc_handler()

        elif feature_enabled('menu-move-to-dropbox'):
            move_blocked_count = arch.util.check_move_blocked(pathlist, unicode(self.se.dropbox_folder))
            if move_blocked_count == 0:
                longTxt = IconOverlayStrings.move_to_db_long_folder if is_dir else IconOverlayStrings.move_to_db_long_file
                options.append((IconOverlayStrings.move_to_db_short, longTxt, u'move'))
                if platform != 'linux':
                    self.dropbox_app.event.report('move_to_dropbox-context-menu', {'file_count': 1})
    elif len(pathlist) > 1:
        if is_in_dropbox:
            try:
                TRACE('Getting option group for paths: %r.', pathlist)
                context_menu_options = get_context_menus_options(self, pathlist)
                options.extend(context_menu_options)
            except:
                unhandled_exc_handler()

        elif feature_enabled('menu-move-to-dropbox'):
            move_blocked_count = arch.util.check_move_blocked(pathlist, unicode(self.se.dropbox_folder))
            if move_blocked_count < len(pathlist):
                options.append((IconOverlayStrings.move_to_db_short, IconOverlayStrings.move_to_db_long_multiple, u'move'))
                if platform != 'linux':
                    self.dropbox_app.event.report('move_to_dropbox-context-menu', {'file_count': len(pathlist)})
    if options and platform != 'linux':
        self.dropbox_app.event.report('view-context-menu')
    return options


def get_toolbar_option_group(self, pathlist):
    options = get_option_group(self, pathlist)
    if not options:
        options = [(TrayOptionStrings.open_dropbox, u'', u'opendropbox')]
    return options


def handle_server_context_action(self, pathlist, id):
    try:
        cm = self.dropbox_app.ui_flags['context_menus'][id]
        if 'action' in cm:
            action_verb = cm['action']
            try:
                handler = server_context_actions[action_verb]
            except KeyError:
                raise KeyError("Unknown client action '%s' for server-generated context menu item '%s'" % (action_verb, id))
            else:
                handler(self, pathlist)

        else:
            file_info = {}
            spaths = []
            for i, path in enumerate(pathlist):
                state = self.se.is_changed(path)
                spath = self.se.local_to_server(self.se.fs.make_path(path))
                nsid, rel_path = server_path_ns_rel(spath)
                lspath = spath.lower()
                spaths.append(lspath)
                file_info[lspath] = dict(nsid=nsid, path=rel_path.encode('utf-8'), state=state, sjid=0)

            try:
                for d in self.se.get_local_details_batch(spaths):
                    file_info[d.server_path.lower()]['sjid'] = d.sjid

            except:
                unhandled_exc_handler()

            if len(pathlist) == 1:
                url = cm['url']
                file_info[spaths[0]]['id'] = id
                client_params = urllib.urlencode(file_info[spaths[0]])
            elif len(pathlist) > 1:
                ret = self.dropbox_app.conn.pre_multi_url(id, file_info.values())
                url = cm['multiurl']
                client_params = dict(id=id, uuid=ret['uuid'])
            url_parts = urlparse.urlparse(url)
            server_params = urlparse.parse_qsl(url_parts.query)
            enc_params = urllib.urlencode(dict(server_params + client_params.items()))
            self.dropbox_app.desktop_login.login_and_redirect('%s?%s' % (url_parts.path, enc_params))
    except:
        TRACE(pathlist)
        unhandled_exc_handler()


def track_click(label, event):
    event.report('click-context', {'label': label})


def get_info(self, pathlist):
    extensions = collections.defaultdict(int)
    size = 0
    for path in pathlist:
        is_dir = self.se.is_directory(path)
        if is_dir:
            for dirpath, dirs, files in os.walk(path):
                for f in files:
                    extensions[os.path.splitext(f)[1].lower()] += 1
                    size += os.path.getsize(os.path.join(dirpath, f))

        else:
            ext = os.path.splitext(path)[1].lower()
            extensions[ext] += 1
            size += os.path.getsize(path)

    return (size, extensions)


@message_sender(spawn_thread_with_name('MOVE_TO_DROPBOX'))
def move_to_dropbox(self, pathlist):
    blocked_count = arch.util.check_move_blocked(pathlist, unicode(self.se.dropbox_folder))
    if blocked_count > 0:
        self.dropbox_app.event.report('move_to_dropbox_failed', {'disallowed_file_count': blocked_count})
        self.dropbox_app.ui_kit.show_dialog(caption=IconOverlayStrings.move_unable_heading, message=IconOverlayStrings.move_unable_message % dict(count=blocked_count), buttons=[IconOverlayStrings.cancel_button], cancel_button=0)
        return
    size, extensions = get_info(self, pathlist)
    if self.dropbox_app.quota < self.dropbox_app.in_use + size:
        over_quota_amount = self.dropbox_app.in_use + size - self.dropbox_app.quota
        self.dropbox_app.event.report('move_to_dropbox_failed', {'over_quota_amount': over_quota_amount})
        size = format_bytes(size)
        parent_dir = os.path.basename(os.path.dirname(pathlist[0]))
        msg = IconOverlayStrings.quota_message % dict(move_size=size, folder_name=parent_dir)
        ret = self.dropbox_app.ui_kit.show_dialog(caption=IconOverlayStrings.quota_heading, message=msg, buttons=[IconOverlayStrings.quota_more_space_button, IconOverlayStrings.cancel_button], default_button=0, cancel_button=1)
        if platform == 'win':
            ret = ret.wait()
        if ret == 0:
            self.dropbox_app.desktop_login.login_and_redirect('c/getspace')
        return
    try:
        self.dropbox_app.event.report('move_to_dropbox', extensions)
        arch.util.move_files(pathlist, unicode(self.se.dropbox_folder), self.se.fs)
    except:
        unhandled_exc_handler()


def do_context_action(self, pathlist, verb, uid, user_key):
    track_click(verb, self.dropbox_app.event)
    if verb == 'opendropbox':
        arch.util.launch_folder(unicode(self.se.dropbox_folder))
        return
    if verb == 'move':
        move_to_dropbox(self, pathlist)
        return
    local_path = self.se.fs.make_path(pathlist[0])
    server_path = self.se.local_to_server(local_path)
    if verb in ('browse', 'share', 'revisions'):
        try:
            ns_id, rel_path = server_path.ns_rel()
            self.dropbox_app.desktop_login.login_and_redirect('c/%s%s?ns_id=%s' % (verb, urllib.quote(rel_path.encode('utf-8')), ns_id))
        except:
            TRACE(server_path)
            unhandled_exc_handler()

    elif verb == 'over_quota':
        self.dropbox_app.desktop_login.login_and_redirect('plans')
    elif verb == 'copypublic':
        try:
            self.dropbox_app.ui_kit.copy_text_to_clipboard(dropbox_url_info.generate_public_link(server_path))
        except:
            unhandled_exc_handler()

    elif verb == 'shmodel_to_clipboard':
        try:
            is_dir = self.se.is_directory(local_path)
            self.dropbox_app.client_shmodel.shmodel_to_clipboard_async(server_path, is_dir=is_dir)
        except Exception:
            unhandled_exc_handler()

    elif verb in self.dropbox_app.ui_flags.get('context_menus', ()):
        try:
            work = partial(handle_server_context_action, self, pathlist, verb)
            Thread(name='SERVER_MENU_HANDLER', target=ActionTask(work)).start()
        except:
            unhandled_exc_handler()


server_context_actions = dict()
MSG_INIT, MSG_FILE_STATUS, MSG_RESERVED, MSG_CONTEXT_OPTIONS, MSG_CONTEXT_ACTION, MSG_REQUEST_CHAIN, MSG_TOOLBAR_OPTIONS, MSG_TOOLBAR_ACTION, MSG_TRACE, MSG_VERSION = range(10)

def status_thread(self):
    state_map = {}
    context = None
    first_chain_failure = None
    try:
        self.pipe = pipe = arch.util.NamedPipe(self.dropbox_app)
    except:
        unhandled_exc_handler()
        return

    if platform == 'win':
        try:
            from dropbox.sync_engine_arch.win._fschange import enable_fs_change_notifications
            enable_fs_change_notifications()
        except Exception:
            unhandled_exc_handler()

    elif platform == 'mac':
        try:
            self.se.arch.enable_fs_change_notifications(self.dropbox_app)
        except Exception:
            unhandled_exc_handler()

    firsttime = True
    while not self.stopped():
        if firsttime and platform == 'win':
            try:
                if hasattr(build_number, 'frozen'):
                    Thread(name='RECHECK_SHELLEXT', target=ActionTask(arch.win32.startup.recheck_shell_extensions)).start()
            except:
                unhandled_exc_handler()

        firsttime = False
        try:
            try:
                req_handled = False
                context, path, reqtype, extra = pipe.get_message()
            except InterruptError:
                continue

            ret = None
            if reqtype == MSG_INIT:
                ret = u'ok'
                TRACE('Initializing shell connection')
                if platform == 'mac' and MAC_VERSION >= SNOW_LEOPARD:
                    try:
                        self.se.arch.request_finder_bundle_version()
                    except Exception:
                        unhandled_exc_handler()

            elif reqtype == MSG_FILE_STATUS:
                try:
                    state = self.se.is_changed(path)
                except:
                    unhandled_exc_handler(False)
                    state = FileSyncStatus.UNWATCHED

                if state:
                    try:
                        self.dropbox_app.event.report_aggregate_event('render-icon-overlays', {STATE_TO_LABEL[state]: 1})
                    except Exception:
                        unhandled_exc_handler()

                ret = arch.util.icon_code(state)
                req_handled = state != FileSyncStatus.UNWATCHED
            elif reqtype == MSG_CONTEXT_OPTIONS:
                if context not in state_map or state_map[context][1]:
                    state_map[context] = [list(), False]
                state = state_map[context]
                if path.endswith('|'):
                    real_path = path[:-1]
                    more_paths = True
                else:
                    real_path = path
                    more_paths = False
                if more_paths:
                    state[0].append(real_path)
                    ret = u''
                    req_handled = True
                else:
                    state[0].append(path)
                    state[1] = True
                    ret = encode_menu(get_option_group(self, state[0])) or u''
                    if platform == 'win' and u'_dllver' in extra:
                        TRACE('DropboxExt DLL version detected: %r', extra[u'_dllver'])
                    elif platform == 'mac':
                        TRACE('Finder bundle version: %r', self.se.arch.finder_bundle_version)
                    if ret and platform == 'mac' and (2, 20) <= self.se.arch.finder_bundle_version < (2, 25):
                        ret = u'|'.join((u'\u200b' + item for item in ret.split(u'|')))
                    if ret:
                        req_handled = True
                    else:
                        del state_map[context]
            elif reqtype == MSG_CONTEXT_ACTION:
                state = state_map.get(context, None)
                if state is not None:
                    if state[1]:
                        TRACE('%s -> %s' % (path, state))
                        ret = u'ok'
                        req_handled = True
                    else:
                        ret = u''
                else:
                    ret = u'err'
            elif reqtype == MSG_REQUEST_CHAIN:
                if not pipe.chaining:
                    TRACE('Now passing messages through')
                    pipe.chaining = True

                    def update_chaining(chain):
                        if not chain:
                            pipe.chaining = False

                    self.dropbox_app.mbox.on_secondary_link.add_handler(update_chaining)
                ret = u'ok'
                req_handled = True
            elif reqtype == MSG_TOOLBAR_OPTIONS:
                if context not in state_map or state_map[context][1]:
                    state_map[context] = [list(), False]
                state = state_map[context]
                paths = path.split('|')
                if self.se.is_monitored(paths[0]):
                    state[0].extend(paths)
                    state[1] = True
                    ret = encode_menu(get_toolbar_option_group(self, state[0]))
                    if ret:
                        req_handled = True
                    else:
                        ret = '*'
                        del state_map[context]
                else:
                    ret = u''
            elif reqtype == MSG_TOOLBAR_ACTION:
                state = state_map.get(context, None)
                if state is not None:
                    if state[1]:
                        TRACE('%s -> %s' % (path, state))
                        ret = u'ok'
                        req_handled = True
                    else:
                        ret = u''
                else:
                    ret = u'err'
            elif reqtype == MSG_TRACE:
                TRACE('PIPETRACE: %s', path)
                ret = u'ok'
                req_handled = True
            elif reqtype == MSG_VERSION:
                try:
                    if platform == 'mac':
                        self.se.arch.set_finder_bundle_version(path)
                except Exception:
                    unhandled_exc_handler()

                ret = u'ok'
                if not getattr(pipe, 'chaining', None):
                    req_handled = True
            elif reqtype == 255:
                TRACE('MIGRATION MESSAGE')
                arch.update.update_with_archive(path)
                req_handled = True
            else:
                TRACE('Unknown Message!')
            if not req_handled and getattr(pipe, 'chaining', None) is True:
                try:
                    ret = pipe.chain_message(context, reqtype, path)
                    TRACE('Got %r from chain' % ret)
                    first_chain_failure = None
                except:
                    unhandled_exc_handler(False)
                    if not first_chain_failure:
                        TRACE('Failed to pass message through')
                        first_chain_failure = time.time()
                    elif time.time() - first_chain_failure >= 10:
                        TRACE('More than 10 seconds of failed chaining; giving up')
                        pipe.chaining = False

            if ret is not None:
                pipe.respond(context, ret)
            pipe.complete_request(context)
            context = None
            if reqtype in (MSG_CONTEXT_ACTION, MSG_TOOLBAR_ACTION) and state is not None:
                ret = do_context_action(self, state[0], path, self.uid, self.user_key)
        except:
            unhandled_exc_handler()
            if context is not None:
                try:
                    pipe.complete_request(context)
                except:
                    unhandled_exc_handler()


class StatusThread(StoppableThread):

    def __init__(self, sync_engine, dropbox_app, uid, user_key, *n, **kw):
        kw['name'] = 'STATUS'
        super(StatusThread, self).__init__(*n, **kw)
        self.se = sync_engine
        self.dropbox_app = dropbox_app
        self.uid = uid
        self.user_key = user_key
        self.pipe = None
        self.regex_dict = {}

    def set_wakeup_event(self):
        if self.pipe:
            self.pipe.break_block()

    def run(self):
        status_thread(self)
        TRACE('Stopping...')
