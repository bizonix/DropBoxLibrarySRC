#Embedded file name: arch/linux/dropboxcommands.py
from __future__ import absolute_import
import os
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.globals import dropbox_globals
from dropbox.threadutils import stop_all_threads
from dropbox.path import ServerPath
from dropbox.preferences import OPT_P2P
from .util import named_pipe_inqueue, named_pipe_outqueue
from .internal import get_contents_root
from .startup import wx_preconditions_cond_var
from .commandserver import IllegalArgumentException
import ui.icon_overlay
from build_number import VERSION

def add_commands(fn):
    g = globals()
    for k, v in ((name.decode('utf8'), g[name]) for name in g if callable(g[name]) and not getattr(g[name], 'dont_add_to_command_server', False)):
        fn(k, v)


def _get_server_path(se, path):
    return se.local_to_server(se.arch.make_path(path))


_get_server_path.dont_add_to_command_server = True

def _get_tag_info(se, path):
    server_path = _get_server_path(se, path)
    tag_info = se.get_tag_info(server_path=server_path)
    if tag_info:
        tag, ns = tag_info
        return tag


_get_tag_info.dont_add_to_command_server = True

def get_folder_tag(cs, conn, args):
    if u'path' not in args:
        raise IllegalArgumentException(u"Missing 'path' argument")
    if len(args[u'path']) != 1:
        raise IllegalArgumentException(u"The 'path' parameter requires single argument")
    path = args[u'path'][0]
    if not os.path.isdir(path):
        raise IllegalArgumentException(u"The 'path' argument is not a directory")
    ret = {u'tag': [u'']}
    try:
        if cs.app.sync_engine:
            if cs.app.sync_engine.is_monitored(path):
                tag = _get_tag_info(cs.app.sync_engine, os.path.normpath(path))
                if tag:
                    ret['tag'] = [unicode(tag)]
    except:
        unhandled_exc_handler()

    return ret


def on_x_server(cs, conn, args):
    if u'display' not in args:
        raise IllegalArgumentException(u"Missing 'display' argument")
    if len(args[u'display']) != 1:
        raise IllegalArgumentException(u"The 'display' parameter requires single argument")
    display = args[u'display'][0]
    TRACE(u'display: ' + display)
    if os.environ.get('DISPLAY', '') == '':
        os.environ['DISPLAY'] = display
        with wx_preconditions_cond_var:
            wx_preconditions_cond_var.notify()
    return {}


def is_out_of_date(cs, conn, args):
    if u'version' not in args:
        raise IllegalArgumentException(u"Missing 'version' argument")
    if len(args[u'version']) != 1:
        raise IllegalArgumentException(u"The 'version' parameter requires single argument")
    version = args[u'version'][0]
    vers = version.split(u'.', 3)
    if len(vers) != 3:
        raise IllegalArgumentException(u"The 'version' parameter isn't valid")
    cs.app.ui_kit.tray_icon.disable()
    return {u'outofdate': [u'true']}


def nautilus_dropbox_version(cs, conn, args):
    if u'version' not in args:
        raise IllegalArgumentException(u"Missing 'version' argument")
    if len(args[u'version']) != 1:
        raise IllegalArgumentException(u"The 'version' parameter requires single argument")
    version = args[u'version'][0]
    vers = version.split(u'.', 3)
    if len(vers) != 3:
        raise IllegalArgumentException(u"The 'version' parameter isn't valid")
    return {}


def icon_overlay_init(cs, conn, args):
    named_pipe_inqueue.put((None, ui.icon_overlay.MSG_INIT))
    named_pipe_outqueue.get()
    return {}


def icon_overlay_file_status(cs, conn, args):
    if u'path' not in args:
        raise IllegalArgumentException(u"Missing 'path' argument")
    if len(args[u'path']) != 1:
        raise IllegalArgumentException(u"The 'path' parameter requires single argument")
    path = args[u'path'][0]
    if not os.path.exists(path):
        raise IllegalArgumentException(u"The 'path' argument does not exist")
    named_pipe_inqueue.put((path, ui.icon_overlay.MSG_FILE_STATUS))
    status = named_pipe_outqueue.get()
    return {u'status': [status]}


def icon_overlay_context_options(cs, conn, args):
    if u'paths' not in args:
        raise IllegalArgumentException(u"Missin 'paths' argument")
    paths = args[u'paths']
    for path in paths:
        if not os.path.exists(path):
            raise IllegalArgumentException(u'The path "%s" does not exist' % (path,))

    for path in paths[0:-1]:
        named_pipe_inqueue.put((path + u'|', ui.icon_overlay.MSG_CONTEXT_OPTIONS))
        named_pipe_outqueue.get()

    named_pipe_inqueue.put((paths[len(paths) - 1], ui.icon_overlay.MSG_CONTEXT_OPTIONS))
    options = named_pipe_outqueue.get()
    return {u'options': options.split(u'|')}


def icon_overlay_context_action(cs, conn, args):
    if u'verb' not in args:
        raise IllegalArgumentException(u"Missing 'verb' argument")
    if u'paths' not in args:
        raise IllegalArgumentException(u"Missing 'paths' argument")
    if len(args[u'verb']) != 1:
        raise IllegalArgumentException(u"'verb' parameter requires single argument ")
    verb = args[u'verb'][0]
    paths = args[u'paths']
    for path in paths:
        if not os.path.exists(path):
            raise IllegalArgumentException(u'The path "%s" does not exist' % (path,))

    for path in paths[0:-1]:
        named_pipe_inqueue.put((path + u'|', ui.icon_overlay.MSG_CONTEXT_OPTIONS))
        named_pipe_outqueue.get()

    named_pipe_inqueue.put((paths[len(paths) - 1], ui.icon_overlay.MSG_CONTEXT_OPTIONS))
    named_pipe_outqueue.get()
    named_pipe_inqueue.put((verb, ui.icon_overlay.MSG_CONTEXT_ACTION))
    named_pipe_outqueue.get()
    return {}


def get_public_link(cs, conn, args):
    if u'path' not in args:
        raise IllegalArgumentException(u"Missing 'path' argument")
    if len(args[u'path']) != 1:
        raise IllegalArgumentException(u"'path' parameter requires single argument")
    upath = args[u'path'][0]
    if not os.path.exists(upath):
        raise IllegalArgumentException(u'The path "%s" does not exist' % (upath,))
    return {u'link': [cs.app.dropbox_url_info.generate_public_link(_get_server_path(cs.app.sync_engine, upath))]}


def get_dropbox_status(cs, conn, args):
    if args:
        raise IllegalArgumentException(u'get_dropbox_status takes no arguments')
    return {u'status': cs.app.status_controller.get_labels().values()}


def soft_exit(cs, conn, args):
    stop_all_threads()
    return {}


def tray_action_open_dropbox(cs, conn, args):
    cs.app.tray_controller.open_dropbox()
    return {}


def tray_action_open_tray_login(cs, conn, args):
    cs.app.tray_controller.open_tray_login()
    return {}


def tray_action_open_discussion_forum(cs, conn, args):
    cs.app.tray_controller.open_discussion_forum()
    return {}


def tray_action_hard_exit(cs, conn, args):
    cs.app.tray_controller.hard_exit()
    return {}


def tray_action_soft_resync(cs, conn, args):
    cs.app.tray_controller.soft_resync()
    return {}


def tray_action_launch_auth_page(cs, conn, args):
    cs.app.tray_controller.launch_auth_page()
    return {}


def tray_action_open_prefs(cs, conn, args):
    cs.app.ui_kit.enter_preferences()
    return {}


def tray_action_open_shell(cs, conn, args):
    try:
        raise Exception('not uh uh')
    except:
        unhandled_exc_handler()

    return {}


def get_dropbox_globals(cs, conn, args):
    if u'keys' not in args:
        raise IllegalArgumentException(u"Missing 'keys' argument")
    ret = []
    for var in args[u'keys']:
        if var in (u'email', u'active', u'icon_state'):
            val = dropbox_globals.get(var, '')
            ret.append(unicode(val))
        elif var == u'version':
            ret.append(unicode(VERSION))

    return {u'values': ret}


def needs_link(cs, conn, args):
    try:
        return {u'link_url': (cs.app.dropbox_url_info.cli_link_url().decode('ascii'),)}
    except:
        raise IllegalArgumentException(u'No client link url available yet!')


tag2emblem = {u'public': [u'web'],
 u'shared': [u'people'],
 u'sandbox': [u'dropbox-app'],
 u'camerauploads': []}
status2emblem = {u'up to date': [u'dropbox-uptodate'],
 u'syncing': [u'dropbox-syncing'],
 u'unsyncable': [u'dropbox-unsyncable'],
 u'selsync': [u'dropbox-selsync'],
 u'unwatched': []}

def get_emblem_paths(cs, conn, args):
    return {u'path': (os.path.join(get_contents_root(), u'images/emblems'),)}


def get_emblems(cs, conn, args):
    if u'path' not in args:
        raise IllegalArgumentException(u"Missing 'path' argument")
    if len(args[u'path']) != 1:
        raise IllegalArgumentException(u"The 'path' parameter requires single argument")
    path = args[u'path'][0]
    status = []
    tag = []
    named_pipe_inqueue.put((path, ui.icon_overlay.MSG_FILE_STATUS))
    try:
        status = status2emblem[named_pipe_outqueue.get()]
    except:
        unhandled_exc_handler()

    if status and os.path.isdir(path):
        try:
            if cs.app.sync_engine:
                tag_info = _get_tag_info(cs.app.sync_engine, os.path.normpath(path))
                if tag_info:
                    tag = tag2emblem[tag_info]
        except:
            unhandled_exc_handler()

    return {u'emblems': tag + status or [u'']}


def test_update(cs, conn, args):
    if u'path' not in args:
        raise IllegalArgumentException("Missing 'path' argument")
    if len(args[u'path']) != 1:
        raise IllegalArgumentException(u"The 'path' parameter requires single argument")
    path = args['path'][0]
    if not os.path.exists(path):
        raise IllegalArgumentException(u"The 'path' parameter must exit")
    named_pipe_inqueue.put((path, 255))
    return {}


def get_ignore_set(cs, conn, args):
    result = [u'']
    if cs.app.sync_engine:
        result = [ unicode(cs.app.sync_engine.server_to_local(path)) for path in cs.app.sync_engine.get_directory_ignore_set() ]
    return {u'ignore_set': result}


def ignore_set_remove(cs, conn, args):
    result = {u'removed': [],
     u'unrecognized': []}
    if u'paths' not in args:
        raise IllegalArgumentException(u"Missing 'paths' argument.")
    if len(args[u'paths']) < 1:
        raise IllegalArgumentException(u'This command requires at least one argument.')
    paths = args[u'paths']
    remove_set = set()
    for path in paths:
        try:
            remove_set.add(cs.app.sync_engine.root_relative_server_path(_get_server_path(cs.app.sync_engine, path)).lower())
        except Exception:
            result[u'unrecognized'].append(path)

    ignore_set = set((ServerPath(s).lower() for s in cs.app.sync_engine.get_directory_ignore_set()))
    candidate_set = ignore_set - remove_set
    cs.app.sync_engine.change_directory_ignore_set([ unicode(a) for a in candidate_set ])
    resulting_set = set((ServerPath(s).lower() for s in cs.app.sync_engine.get_directory_ignore_set()))
    removed_paths = [ unicode(cs.app.sync_engine.server_to_local(path)) for path in ignore_set - resulting_set ]
    result[u'removed'] = removed_paths
    return result


def ignore_set_add(cs, conn, args):
    result = {u'ignored': [],
     u'unrecognized': []}
    if u'paths' not in args:
        raise IllegalArgumentException(u"Missing 'paths' argument.")
    if len(args[u'paths']) < 1:
        raise IllegalArgumentException(u'This command requires at least one argument.')
    paths = args[u'paths']
    add_set = set()
    for path in paths:
        try:
            server_path = cs.app.sync_engine.root_relative_server_path(_get_server_path(cs.app.sync_engine, path)).lower()
            if not server_path.is_root:
                add_set.add(server_path)
        except Exception:
            result[u'unrecognized'].append(path)

    ignore_set = set((ServerPath(s).lower() for s in cs.app.sync_engine.get_directory_ignore_set()))
    new_set = ignore_set | add_set
    cs.app.sync_engine.change_directory_ignore_set([ unicode(a) for a in new_set ])
    resulting_set = set((ServerPath(s).lower() for s in cs.app.sync_engine.get_directory_ignore_set()))
    added_paths = [ unicode(cs.app.sync_engine.server_to_local(path)) for path in resulting_set - ignore_set ]
    result[u'ignored'] = added_paths
    return result


def set_lan_sync(cs, conn, args):
    if u'lansync' not in args:
        raise IllegalArgumentException(u"Missing 'lansync' argument.")
    if len(args[u'lansync']) != 1:
        raise IllegalArgumentException(u'This command requires must have one argument.')
    try:
        new_state = {'enabled': True,
         'disabled': False}[args['lansync'][0]]
    except KeyError:
        raise IllegalArgumentException(u"Only 'enabled' or 'disabled' is allowed as an argument")

    if cs.app:
        try:
            cs.app.pref_controller.update({OPT_P2P: new_state})
        except Exception:
            unhandled_exc_handler()

    return {}
