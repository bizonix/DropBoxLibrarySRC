#Embedded file name: dropbox/client/multiaccount/multibox.py
import copy_reg
import arch
from dropbox.callbacks import Handler
from dropbox.client.multiaccount.callbacks import MultiBoxCallbacks
from dropbox.client.multiaccount.constants import Roles
from dropbox.client.multiaccount.proxy import MultiaccountProxies, StuffImporterMultiaccountProxy
from dropbox.client.multiaccount.manager import AUTHKEY, DropboxManager, other_client
from dropbox.client.multiaccount.values import MultiaccountValues
from dropbox.features import feature_enabled
from dropbox.globals import dropbox_globals
from dropbox.path import ServerPath
from dropbox.threadutils import StoppableThread
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler

def pickle_server_path(sp):
    return (ServerPath, (unicode(sp),))


copy_reg.pickle(ServerPath, pickle_server_path)

class MultiboxMixins(MultiaccountValues, MultiaccountProxies):
    pass


class MultiBoxServer(StoppableThread, MultiboxMixins):

    def __init__(self, app):
        super(MultiBoxServer, self).__init__(name='MULTIBOX_SERVER')
        self.app = app
        self.is_secondary = False
        self.has_secondary = False
        self.primary = None
        self.secondary = None
        self.primary_address = None
        self.team = None
        self.role = None
        self.on_secondary_link = Handler()
        self.secondary_email = None
        self.secondary_role = None
        self.folder_name = None
        self.commandline_flags = None
        self.server = None
        self.callbacks = MultiBoxCallbacks(app, self)
        self.registered_with_primary = False

    def initialize_handlers(self):
        self.app.on_quit.add_handler(lambda *n, **kw: self.other_client_exit())
        self.app.on_restart.add_handler(lambda *n, **kw: self.other_client_exit())

    def run(self):
        try:
            TRACE('Starting...')
            self.server.serve_forever()
        except Exception:
            unhandled_exc_handler()

        TRACE('Stopped.')

    def parse_commandline_flags(self, flags):
        try:
            secondary_email = flags.get('--secondary-email')
            secondary_role = flags.get('--secondary-role', '').lower()
            if secondary_email and secondary_role:
                self.secondary_email = secondary_email
                self.secondary_role = Roles.PERSONAL if secondary_role == 'personal' else (Roles.BUSINESS if secondary_role == 'business' else None)
                assert self.secondary_role is not None
                self.role = self.secondary_role if self.is_secondary else (Roles.PERSONAL if self.secondary_role == Roles.BUSINESS else Roles.BUSINESS)
                self.team = 'FAKERSON CO'
                TRACE('MULTIBOX: Parsed multibox commandline args! Secondary email: %s, secondary role: %s, role: %s', secondary_email, secondary_role, 'personal' if self.role == Roles.PERSONAL else 'business')
                self.commandline_flags = ['--secondary-email=%s' % secondary_email, '--secondary-role=%s' % secondary_role]
            self.folder_name = flags.get('--mbox-folder-prefix', None)
            if self.folder_name:
                if not self.commandline_flags:
                    self.commandline_flags = []
                self.commandline_flags.append('--mbox-folder-prefix=%s' % self.folder_name)
        except Exception:
            unhandled_exc_handler()
            self.secondary_email = self.secondary_role = self.team = self.folder_name = self.commandline_flags = None

    @property
    def is_primary(self):
        return not self.is_secondary

    @property
    def paired(self):
        return self.enabled or all([feature_enabled('multiaccount'), self.secondary_email is not None, self.secondary_role is not None]) or self.is_secondary

    @property
    def linked(self):
        try:
            return bool(feature_enabled('multiaccount') and (self.app.config.get('secondary_client_email') or self.is_secondary))
        except Exception:
            unhandled_exc_handler()
            return False

    @property
    def enabled(self):
        return feature_enabled('multiaccount') and self.is_primary and self.has_secondary

    @property
    def is_dfb_user(self):
        return bool(self.team and (self.role is None or self.role == Roles.BUSINESS))

    @property
    def is_dfb_user_without_linked_pair(self):
        return not self.linked and self.is_dfb_user

    def force_pair(self):
        report_bad_assumption('Forcing user to pair accounts for multiaccount!')
        title = 'Please pair your accounts'
        msg = 'Please pair your Dropbox accounts to continue running multiaccount.\n\nNote: This is a temporary error only for Dropboxers.'
        ret = self.app.ui_kit.show_alert_dialog(caption=title, message=msg, buttons=['More info', 'Exit'])
        ret = ret.wait()
        try:
            if ret == 0:
                url = 'https://docs.google.com/a/dropbox.com/document/d/1TPvqL6p_naDvuOR3gSrISMBtQGGau7VBDsytoN8dxQo/edit'
                self.app.dropbox_url_info.launch_full_url(url)
        except Exception:
            unhandled_exc_handler()
        finally:
            arch.util.hard_exit()

    def enable(self):
        if not self.server:
            self.server = DropboxManager(authkey=AUTHKEY).get_server()
            self.start()
        if self.has_secondary:
            return
        if self.is_secondary:
            if self.registered_with_primary:
                TRACE('Secondary already registered with primary.  Skipping registration.')
            elif self.primary_address:
                self.primary = other_client(self.primary_address.encode('utf8'))
                self.register_secondary(self.server.address)
                self.registered_with_primary = True
                TRACE('MULTIACCOUNT: Secondary successfully registered!')
            else:
                report_bad_assumption('Secondary client was launched with no server address!')
                arch.util.hard_exit(-1)
        else:
            slave_row = self.app.instance_config.get_slave_row(create_if_not_exists=True)
            current_email = self.app.config.get('secondary_client_email')
            if current_email and current_email != self.secondary_email:
                self.force_pair()
                TRACE('Unlinking secondary due to conflicting email')
                self.app.disable_multiaccount()
            else:
                args = ['--client=%d' % slave_row.id, '--server-address=%s' % self.server.address]
                if self.commandline_flags:
                    args.extend(self.commandline_flags)
                arch.util.launch_new_dropbox(args)
                TRACE('MULTIACCOUNT: Enabling multiaccount, launching secondary process!')

    def handle_register(self, ret):
        self.team = ret.get('org_name', None)
        if self.team:
            TRACE('MULTIACCOUNT: User %r is on team %r', ret.get('uid'), self.team)
        if self.role and self.secondary_email and self.secondary_role:
            TRACE('MULTIACCOUNT: Using role and email from command line flags!')
        else:
            role_str = ret.get('role', None)
            if role_str:
                if role_str not in {'PERSONAL', 'BUSINESS'}:
                    report_bad_assumption('Bad role from server: %s' % role_str)
                    TRACE('MULTIACCOUNT: bad role %r' % role_str)
                    self.role = self.secondary_email = self.secondary_role = self.team = None
                    return
                self.role = Roles.PERSONAL if role_str == 'PERSONAL' else Roles.BUSINESS
                TRACE('MULTIACCOUNT: setting role using role_str %r (role = %r, secondary_role = %r)' % (role_str, self.role, self.secondary_role))
            if self.is_primary:
                self.secondary_email = ret.get('secondary_email', self.secondary_email)
                self.secondary_role = Roles.PERSONAL if self.role == Roles.BUSINESS else Roles.BUSINESS
            else:
                self.secondary_role = self.role
        TRACE('MULTIACCOUNT: %s: paired: %s, linked : %s, DfB: %s', 'Primary' if self.is_primary else 'Secondary', self.paired, self.linked, self.is_dfb_user)
        TRACE('MULTIACCOUNT: %s: role: %s, secondary role : %s, secondary email: %s', 'Primary' if self.is_primary else 'Secondary', self.role, self.secondary_role, self.secondary_email)

    def unlink_secondary(self):
        try:
            self.other_client_exit()
        except EOFError:
            TRACE('Caught EOFError from multibox shutting down')
        except Exception:
            unhandled_exc_handler()

        slave_row = self.app.instance_config.get_slave_row()
        if slave_row is None:
            return
        arch.util.launch_new_dropbox(['--client=%d' % slave_row.id, '--server-address=%s' % self.server.address, '/killdata'])
        self.app.config['secondary_client_email'] = None
        self.has_secondary = False
        self.secondary = None
        self.on_secondary_link.run_handlers(False)
        self.app.ui_kit.disable_multiaccount()

    def derive_dropbox_name(self):
        folder = arch.constants.default_dropbox_folder_name
        if self.folder_name:
            TRACE('MULTIACCOUNT: Using folder name %r for testing' % self.folder_name)
            folder = self.folder_name
        if self.role == Roles.PERSONAL:
            return '%s (%s)' % (folder, self.account_labels_plain.personal)
        else:
            suffix = self.account_labels_plain.business
            if self.team:
                candidate = self.app.sync_engine_arch.sanitize_filename(self.team, ' ')
                if candidate:
                    suffix = candidate
            return '%s (%s)' % (folder, suffix)

    def derive_dropbox_name_and_path(self):
        current_path = self.app.sync_engine.fs.make_path(self.app.default_dropbox_path)
        dropbox_name = self.derive_dropbox_name()
        new_path = unicode(current_path.dirname.join(dropbox_name))
        return (dropbox_name, new_path)

    def update_dropbox_path_from_pref_controller(self, pref_controller):
        self.update_dropbox_path(pref_controller['dropbox_path'])

    def update_dropbox_path(self, dropbox_path, dropbox_name = None):
        if dropbox_path == self.app.default_dropbox_path:
            return
        if dropbox_name is None:
            dropbox_name = unicode(self.app.sync_engine.fs.make_path(dropbox_path).basename)
        TRACE('MULTIACCOUNT: updating dropbox_path to %r, %r' % (dropbox_path, dropbox_name))
        self.app.default_dropbox_folder_name = dropbox_name
        self.app.default_dropbox_path = dropbox_path
        self.app.config['dropbox_path'] = dropbox_path
        dropbox_globals['dropbox'] = dropbox_path
        self.app.instance_config.instance_db.update_dropbox_name(self.app.instance_id, dropbox_name, dropbox_path)

    def set_status_label(self, _clear_previous = False, **labels_and_states):
        if self.is_secondary:
            if self.primary:
                self.primary.set_secondary_status_label(_clear_previous=_clear_previous, **labels_and_states)
            else:
                TRACE('!! Not forwarding statuses %r on primary, no pipe yet!', labels_and_states)

    def get_stuff_importer(self):
        if not self.linked:
            return self.app.sync_engine.arch.StuffImporter(self.app)
        elif self.role == Roles.PERSONAL:
            TRACE('IPHOTOIMPORT: %s client, role is %r, using stuff_importer', 'Primary' if self.is_primary else 'Secondary', self.role)
            return self.app.sync_engine.arch.StuffImporter(self.app)
        else:
            TRACE('IPHOTOIMPORT: %s client, role is %r, returning stuff_importer_proxy', 'Primary' if self.is_primary else 'Secondary', self.role)
            return StuffImporterMultiaccountProxy(self.app)

    def __getattr__(self, name):
        if self.primary:
            return lambda *a, **k: getattr(self.primary, name)(*a, **k)._getvalue()
        if self.secondary:
            return lambda *a, **k: getattr(self.secondary, name)(*a, **k)._getvalue()
        raise AttributeError(name)
