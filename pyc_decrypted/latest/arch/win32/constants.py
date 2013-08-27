#Embedded file name: arch/win32/constants.py
import os
from win32com.shell import shellcon
from .internal import get_user_folder_path
from build_number import BUILD_KEY
from dropbox.win32.version import VISTA, WINDOWS_VERSION

def path_from_name(dropbox_folder_name):
    user_folder_path = get_user_folder_path(shellcon.CSIDL_PERSONAL if WINDOWS_VERSION < VISTA else shellcon.CSIDL_PROFILE)
    return os.path.join(user_folder_path, dropbox_folder_name)


default_dropbox_folder_name = BUILD_KEY
default_dropbox_path = path_from_name(default_dropbox_folder_name)
default_desktop_dropbox_path = os.path.join(get_user_folder_path(shellcon.CSIDL_DESKTOP), default_dropbox_folder_name)
seven_default_dropbox_path = os.path.join(get_user_folder_path(shellcon.CSIDL_PERSONAL), 'My %s' % BUILD_KEY)
local_form = 'NFC'
assert not BUILD_KEY.endswith('Master'), 'BUILD_KEY (%s) cannot end with "Master"' % BUILD_KEY
instance_config_path = os.path.join(get_user_folder_path(shellcon.CSIDL_APPDATA), '%sMaster' % BUILD_KEY)
appdata_path = os.path.join(get_user_folder_path(shellcon.CSIDL_APPDATA), BUILD_KEY)
if type(appdata_path) is str:
    try:
        appdata_path = appdata_path.decode('mbcs')
    except UnicodeEncodeError:
        try:
            appdata_path = appdata_path.decode('utf-8')
        except UnicodeEncodeError:
            appdata_path = appdata_path.decode('utf-8', 'ignore')

elif type(appdata_path) is not unicode:
    raise Exception('Appdata path is not unicode!')
hash_wait_time = 0.4
platform = 'win'
photo_update_name = 'UpdateHelper'
ICON_INDEX_ROOT = 1
ICON_INDEX_LOGO = 101
ICON_INDEX_IDLE = 201
ICON_INDEX_BUSY = 301
ICON_INDEX_BUSY2 = 401
ICON_INDEX_X = 501
ICON_INDEX_BLANK = 601
ICON_INDEX_BLACK = 701
ICON_INDEX_CAM = 801
ICON_INDEX_CAM2 = 802
ICON_INDEX_ATTENTION = 901
ICON_INDEX_PAUSED = 902
ICON_PATHS = {ICON_INDEX_ROOT: 'images\\icons\\box%(suffix)s.ico',
 ICON_INDEX_LOGO: 'images\\status\\dropboxstatus-logo%(suffix)s.ico',
 ICON_INDEX_IDLE: 'images\\status\\dropboxstatus-idle%(suffix)s.ico',
 ICON_INDEX_BUSY: 'images\\status\\dropboxstatus-busy%(suffix)s.ico',
 ICON_INDEX_BUSY2: 'images\\status\\dropboxstatus-busy2%(suffix)s.ico',
 ICON_INDEX_X: 'images\\status\\dropboxstatus-x%(suffix)s.ico',
 ICON_INDEX_BLANK: 'images\\status\\dropboxstatus-blank.ico',
 ICON_INDEX_BLACK: 'images\\status\\dropboxstatus-black.ico',
 ICON_INDEX_CAM: 'images\\status\\dropboxstatus-cam.ico',
 ICON_INDEX_CAM2: 'images\\status\\dropboxstatus-cam2.ico',
 ICON_INDEX_ATTENTION: 'images\\status\\dropboxstatus-attention.ico',
 ICON_INDEX_PAUSED: 'images\\status\\dropboxstatus-pause.ico'}
