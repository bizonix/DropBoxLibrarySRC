#Embedded file name: arch/win32/photouploader/constants.py
from build_number import BUILD_KEY
from dropbox.win32.version import WINDOWS_VERSION, WIN7, WIN8, VISTA, WINXP
USE_PHOTOUPLOADER = WINDOWS_VERSION >= WINXP and WINDOWS_VERSION <= WIN8
USE_WIA = WINDOWS_VERSION >= WINXP and WINDOWS_VERSION < VISTA
USE_PROXY = WINDOWS_VERSION >= WINXP and WINDOWS_VERSION <= VISTA
AUTOPLAY_DEFAULTS_SUPPORTED = WINDOWS_VERSION in (WIN7, WIN8)
DROPBOX_AUTOPLAY_HANDLER_NAME = u'DropboxAutoplay'
DROPBOX_AUTOPLAY_PROGID = BUILD_KEY + u'.AutoplayEventHandler'
DROPBOX_AUTOPLAY_VERNO = 4
DROPBOX_AUTOPLAY_CLSID = u'{005A3A96-BAC4-4B0A-94EA-C0CE100EA736}'
DROPBOX_AUTOPLAY_PROXY_HANDLER_NAME = u'DropboxAutoplayProxy'
DROPBOX_AUTOPLAY_PROXY_PROGID = BUILD_KEY + u'.AutoplayEventHandlerProxy'
DROPBOX_AUTOPLAY_PROXY_VERNO = 5
DROPBOX_AUTOPLAY_PROXY_CLSID = u'{F38F335B-BC2E-450E-8FC6-0E13E17FC8FE}'
DROPBOX_DATA_CALLBACK_PROGID = BUILD_KEY + u'.DropboxWiaDataCallback'
DROPBOX_DATA_CALLBACK_VERNO = 2
DROPBOX_DATA_CALLBACK_CLSID = u'{E69341A3-E6D2-4175-B60C-C9D3D6FA40F6}'
DROPBOX_DATA_CALLBACK_DESC = u'Dropbox WIA Data Callback'
VOLUME_EVENTS = (u'CameraMemoryOnArrival', u'ShowPicturesOnArrival', u'MixedContentOnArrival', u'PlayVideoFilesOnArrival', u'UnknownContentOnArrival')
VOLUME_EVENT_DEFAULTS = (u'ShowPicturesOnArrival', u'MixedContentOnArrival', u'PlayVideoFilesOnArrival')
AUTOPLAY_KEY = u'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\AutoplayHandlers'