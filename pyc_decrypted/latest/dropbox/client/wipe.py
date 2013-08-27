#Embedded file name: dropbox/client/wipe.py
import os
import stat
import time
import tempfile
import shutil
from collections import OrderedDict
import arch
from client_api.dropbox_connection import DropboxConnection, DropboxResponseServerError
from dropbox.client.databases import clear_appdata_for_unlink
from dropbox.client.unlink_cookie import write_unlink_cookie_no_sync_engine
from dropbox.i18n import trans
from dropbox.url_info import dropbox_url_info
from dropbox.trace import TRACE, unhandled_exc_handler

def attempt_to_move_dropbox(app, host_id, path):
    TRACE("The Dropbox folder isn't under temp. Attempt to move it there.")
    temp_dir = os.path.abspath(unicode(tempfile.gettempdir()))

    def find_mount_point(path):
        path = os.path.abspath(path)
        while not os.path.ismount(path):
            path = os.path.dirname(path)

        return path

    TRACE('Checking if temp and the Dropbox folder are on the same logical drive..')
    if find_mount_point(temp_dir).lower() == find_mount_point(path).lower():
        TRACE('Temp and Dropbox are on the same logical drive. Moving to temp')
        new_path = os.path.abspath(os.path.join(temp_dir, u'tmpdbfldr'))
    else:
        TRACE('Temp and Dropbox are on different logical drives. Renaming to Deleted Dropbox..')
        new_path = os.path.join(os.path.dirname(path), trans(u'Deleted Dropbox'))
    os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
    suffix_index = 0
    while True:
        new_path_with_suffix = new_path if suffix_index == 0 else new_path + u' ' + str(suffix_index)
        if not os.path.isdir(new_path_with_suffix) and not os.path.isfile(new_path_with_suffix) and not os.path.islink(new_path_with_suffix):
            break
        suffix_index += 1

    try:
        TRACE('Moving/renaming the Dropbox folder to %r', new_path_with_suffix)
        os.rename(path, new_path_with_suffix)
    except OSError as e:
        TRACE('An error occured while trying to move Dropbox to temp: %r', e)
    except Exception as e:
        TRACE('An unhandled exception raised while moving Dropbox to temp: %r!', e)
        unhandled_exc_handler()
    else:
        path = new_path_with_suffix
        os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
        save_delete_data_state(app, host_id=host_id, first_run=False, finished_indexing=False, dropbox_path=path, delete_data_on_restart=True, paths_to_delete=[])

    return path


def delete_data(app, path):
    path = os.path.abspath(unicode(path))
    TRACE('START TO DELETE DATA: %r', path)
    app.create_keystore_and_unlink_cookie()
    host_id = app.unlink_cookie['host_id']
    if 'dropbox_path' in app.unlink_cookie:
        path = app.unlink_cookie['dropbox_path']
    try:
        os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
    except OSError:
        pass

    first_run = 'first_run' not in app.unlink_cookie or app.unlink_cookie['first_run']
    if first_run and os.path.isdir(path):
        path = attempt_to_move_dropbox(app, host_id, path)

    def onerror(func, path, excinfo):
        try:
            os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
            if func is os.rmdir or func is os.listdir:
                os.rmdir(path)
            elif func is os.remove or func is os.path.islink:
                os.remove(path)
            else:
                raise Exception('func must be os.rmdir, os.remove, os.listdir or os.path.islink')
        except OSError:
            TRACE('Failed to delete %r with exception: %r', path, excinfo)
            paths_to_delete.append(path)
        except Exception:
            unhandled_exc_handler()

    finished_indexing = 'finished_indexing' in app.unlink_cookie and app.unlink_cookie['finished_indexing']
    delete_state = {'host_id': host_id,
     'dropbox_path': path,
     'delete_data_on_restart': True,
     'first_run': False,
     'finished_indexing': finished_indexing}
    if not finished_indexing:
        paths_to_delete = []
        delete_state['paths_to_delete'] = paths_to_delete
        save_delete_data_state(app, **delete_state)
        try:
            shutil.rmtree(path, ignore_errors=False, onerror=onerror)
        except Exception:
            delete_state['delete_data_on_restart'] = False
            save_delete_data_state(app, **delete_state)
            unhandled_exc_handler()
            arch.util.restart()
        else:
            delete_state['finished_indexing'] = True
            delete_state['paths_to_delete'] = paths_to_delete
            save_delete_data_state(app, **delete_state)

    else:
        paths_to_delete = app.unlink_cookie['paths_to_delete']
    while len(paths_to_delete) > 0:
        failures = []
        for path in paths_to_delete:
            if os.path.exists(path):
                try:
                    if os.path.isdir(path):
                        os.rmdir(path)
                    elif os.path.isfile(path) or os.path.islink(path):
                        os.remove(path)
                except Exception as e:
                    failures.append(path)
                    TRACE('Failed to delete %r because %r.', path, e)

        paths_to_delete = list(OrderedDict.fromkeys(failures))
        delete_state['paths_to_delete'] = paths_to_delete
        save_delete_data_state(app, **delete_state)
        if len(paths_to_delete) > 0:
            TRACE('Failures left %s' % len(paths_to_delete))
            time.sleep(300)

    TRACE('Successfully deleted all Dropbox data')
    clear_appdata_for_unlink(database_dir=app.appdata_path)
    TRACE('Successfully deleted appdata')
    DELETE_COMPLETED = 4
    while True:
        TRACE('Change the unlink_state of this host to DELETE_COMPLETED on the metaserver')
        conn = DropboxConnection(hosts=dropbox_url_info.api_hosts, user_agent_dict=arch.util.get_user_agent_dict())
        conn.set_host_id(host_id)
        try:
            result = conn.record_unlink_state(DELETE_COMPLETED)
        except (IOError, DropboxResponseServerError):
            TRACE('Could not report unlink_state to server; retrying in 60 seconds')
            time.sleep(60)
        except Exception:
            TRACE('Could not report unlink_state to server; giving up')
            break
        else:
            TRACE('Unlink state reported to server')
            break

    delete_state['delete_data_on_restart'] = False
    save_delete_data_state(app, **delete_state)
    arch.util.restart()


def save_delete_data_state(app, host_id, first_run, finished_indexing, dropbox_path, delete_data_on_restart, paths_to_delete = []):
    write_unlink_cookie_no_sync_engine(appdata_path=app.appdata_path, in_config=app.config, keystore=app.keystore, host_id=host_id, first_run=first_run, finished_indexing=finished_indexing, delete_data_on_restart=delete_data_on_restart, path=dropbox_path, paths_to_delete=paths_to_delete)
