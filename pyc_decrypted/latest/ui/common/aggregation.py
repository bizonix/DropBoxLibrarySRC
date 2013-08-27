#Embedded file name: ui/common/aggregation.py
from __future__ import absolute_import
import os
from xml.sax.saxutils import escape
import arch
from dropbox.client.multiaccount.constants import Roles
from dropbox.i18n import ago, trans
from dropbox.trace import report_bad_assumption, unhandled_exc_handler
ICON_MAP = {'exe': 'page_white_gear',
 'dll': 'page_white_gear',
 'xls': 'page_white_excel',
 'xlsm': 'page_white_excel',
 'xlsx': 'page_white_excel',
 'ods': 'page_white_tux',
 'c': 'page_white_c',
 'h': 'page_white_c',
 'php': 'page_white_php',
 'mp3': 'page_white_sound',
 'wav': 'page_white_sound',
 'm4a': 'page_white_sound',
 'wma': 'page_white_sound',
 'aif': 'page_white_sound',
 'iff': 'page_white_sound',
 'm3u': 'page_white_sound',
 'mid': 'page_white_sound',
 'mpa': 'page_white_sound',
 'ra': 'page_white_sound',
 'aiff': 'page_white_sound',
 'au': 'page_white_sound',
 'amr': 'page_white_sound',
 'ogg': 'page_white_sound',
 '3ga': 'page_white_sound',
 'doc': 'page_white_word',
 'docx': 'page_white_word',
 'odt': 'page_white_tux',
 'ppt': 'page_white_powerpoint',
 'pptx': 'page_white_powerpoint',
 'pps': 'page_white_powerpoint',
 'ppsx': 'page_white_powerpoint',
 'odp': 'page_white_tux',
 'txt': 'page_white_text',
 'rtf': 'page_white_text',
 'log': 'page_white_text',
 'msg': 'page_white_text',
 'pages': 'page_white_text',
 'wpd': 'page_white_text',
 'wps': 'page_white_text',
 'sln': 'page_white_visualstudio',
 'vcproj': 'page_white_visualstudio',
 'html': 'page_white_code',
 'htm': 'page_white_code',
 'psd': 'page_white_paint',
 'pdf': 'page_white_acrobat',
 'fla': 'page_white_actionscript',
 'swf': 'page_white_flash',
 'gif': 'page_white_picture',
 'png': 'page_white_picture',
 'jpg': 'page_white_picture',
 'jpeg': 'page_white_picture',
 'tiff': 'page_white_picture',
 'tif': 'page_white_picture',
 'bmp': 'page_white_picture',
 'odg': 'page_white_picture',
 '3fr': 'page_white_picture',
 'ari': 'page_white_picture',
 'arw': 'page_white_picture',
 'srf': 'page_white_picture',
 'sr2': 'page_white_picture',
 'bay': 'page_white_picture',
 'crw': 'page_white_picture',
 'cr2': 'page_white_picture',
 'cap': 'page_white_picture',
 'eip': 'page_white_picture',
 'dcs': 'page_white_picture',
 'dcr': 'page_white_picture',
 'drf': 'page_white_picture',
 'k25': 'page_white_picture',
 'kdc': 'page_white_picture',
 'dng': 'page_white_picture',
 'erf': 'page_white_picture',
 'fff': 'page_white_picture',
 'iiq': 'page_white_picture',
 'mef': 'page_white_picture',
 'mos': 'page_white_picture',
 'mrw': 'page_white_picture',
 'nef': 'page_white_picture',
 'nrw': 'page_white_picture',
 'orf': 'page_white_picture',
 'pef': 'page_white_picture',
 'ptx': 'page_white_picture',
 'pxn': 'page_white_picture',
 'r3d': 'page_white_picture',
 'raf': 'page_white_picture',
 'rw2': 'page_white_picture',
 'raw': 'page_white_picture',
 'rwl': 'page_white_picture',
 'rwz': 'page_white_picture',
 'obm': 'page_white_picture',
 'srw': 'page_white_picture',
 'x3f': 'page_white_picture',
 'py': 'page_white_code',
 'jpeg': 'page_white_picture',
 'gz': 'page_white_compressed',
 'tar': 'page_white_compressed',
 'rar': 'page_white_compressed',
 'zip': 'page_white_compressed',
 'iso': 'page_white_dvd',
 'dmg': 'page_white_dvd',
 'css': 'page_white_code',
 'xml': 'page_white_code',
 'tgz': 'page_white_compressed',
 'bz2': 'page_white_compressed',
 'rb': 'page_white_ruby',
 'cpp': 'page_white_cplusplus',
 'java': 'page_white_cup',
 'js': 'page_white_code',
 'cs': 'page_white_csharp',
 'ai': 'page_white_vector',
 'avi': 'page_white_film',
 'mov': 'page_white_film',
 'mp4': 'page_white_film',
 'mkv': 'page_white_film',
 'wmv': 'page_white_film',
 'mpg': 'page_white_film',
 '3gp': 'page_white_film',
 '3gpp': 'page_white_film',
 'm4v': 'page_white_film',
 'vob': 'page_white_film',
 'ogv': 'page_white_film'}

class RecentlyChangedFile(object):
    ACTION_VIEW = 'view'
    ACTION_COPY_LINK = 'shmodel_to_clipboard'
    SUPPORTED_FILE_TYPES = {'jpg',
     'jpeg',
     'png',
     'bmp',
     'psd'}

    def __init__(self, server_path, timestamp, blocklist):
        self.display_name = escape(unicode(server_path.basename))
        self.name = unicode(server_path.basename)
        self.file_type = self.get_file_type(self.name)
        self.server_path = server_path
        self.timestamp = timestamp
        self.blocklist = blocklist
        self.primary = True
        self.role = None
        self.actions = ((self.ACTION_COPY_LINK, trans(u'Share Link'), False),)

    @staticmethod
    def get_file_type(file_name):
        try:
            return os.path.splitext(file_name)[1].lower()[1:]
        except Exception:
            unhandled_exc_handler()
            return None

    def get_dict(self, now):
        result = {'actions': self.actions,
         'name': self.display_name,
         'time': ago(self.timestamp, now)}
        if self.file_type in self.SUPPORTED_FILE_TYPES:
            result['thumbnail_available'] = True
        else:
            icon_name = ICON_MAP.get(self.file_type)
            if icon_name is not None:
                result['remote_icon'] = '%s.png' % icon_name
        if self.role == Roles.BUSINESS:
            result['multiaccount_subtitle'] = trans(u'Business')
        return result

    def perform_action(self, app, action):
        app.event.report('popup-file-action', action_id=action)
        self._perform_action(app, action)

    def _perform_action(self, app, action):
        if not action:
            action = self.ACTION_VIEW
        if action == self.ACTION_VIEW:
            self._do_view(app)
        elif action == self.ACTION_COPY_LINK:
            self._do_copy_link(app)
        else:
            report_bad_assumption('Unrecognized file action: key=%r, action=%r', self.key, action)

    def _do_view(self, app):
        sync_engine = app.sync_engine if self.primary else app.mbox
        if not sync_engine:
            return
        arch.util.highlight_file(unicode(sync_engine.server_to_local(self.server_path)))

    def _do_copy_link(self, app):
        sync_engine = app.sync_engine if self.primary else app.mbox
        local_path = sync_engine.server_to_local(self.server_path)
        is_dir = sync_engine.is_directory(local_path)
        app.client_shmodel.shmodel_to_clipboard_async(self.server_path, is_dir=is_dir)
