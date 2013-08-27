#Embedded file name: ui/cocoa/constants.py
from __future__ import absolute_import
import itertools
import os
from AppKit import NSColor
from dropbox.mac.version import MAC_VERSION, SNOW_LEOPARD
from ..common.constants import colors
from .util import get_image_dir, load_image
__all__ = ['Colors',
 'ENTER_KEY',
 'ESCAPE_KEY',
 'Images']
ENTER_KEY = '\r'
ESCAPE_KEY = '\x1b'

class MetaColors(type):

    def __getattr__(cls, attr):
        if attr not in colors:
            raise AttributeError("Color '%s' is not defined." % attr)
        r, g, b, a = colors[attr]
        return MetaColors.__makecolor(r, g, b, a)

    @classmethod
    def __makecolor(cls, r = 0, g = 0, b = 0, a = 0):
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(r / 255.0, g / 255.0, b / 255.0, a / 255.0)


class Colors(object):
    __metaclass__ = MetaColors


def _get_flag_paths(images_dict):
    flag_paths = []
    flag_dir = os.path.join(get_image_dir(), 'flags')
    for filename in os.listdir(flag_dir):
        if not filename.endswith('.png'):
            continue
        code = filename[:-4]
        full_path = 'flags/%s' % (filename,)
        images_dict['flag_%s' % (code,)] = full_path
        flag_paths.append(full_path)

    return flag_paths


class MetaImages(type):
    AllImages = dict(Amex=u'amex.gif', Box20=u'box_20.png', Box24=u'box_24.png', Box36=u'box_36.png', Box42=u'box_42.png', Box64=u'box_64.png', BoxGrowl=u'box_growl.png', Closebox=u'closebox.png', CloseboxPressed=u'closebox_pressed.png', IPhoto=u'iphoto_splash.png', Lock=u'lock.png', Mastercard=u'mastercard.gif', Mobile=u'setupwizard/mobile.png', PrefsAccount=u'preferences/account.tiff', PrefsAdvanced=u'preferences/advanced.tiff', PrefsMain=u'preferences/general.tiff', PrefsImport=u'preferences/import.tiff', PrefsNetwork=u'preferences/network.tiff', SetupWizardAdvancedIcon=u'setupwizard/advancedicon.png', SetupWizardBackground=u'setupwizard/mac/background.png', SetupWizardLogo=u'setupwizard/dropboxlogo.png', SetupWizardTypicalIcon=u'setupwizard/typicalicon.png', Transparent=u'transparent.png', TrayArrowDown=u'mac/tray_arrow_down.png', TrayArrowLeft=u'mac/tray_arrow_left.png', TrayArrowRight=u'mac/tray_arrow_right.png', TrayArrowUp=u'mac/tray_arrow_up.png', Visa=u'visa.gif', WorldBox=u'setupwizard/worldbox.png', CameraSplashDrawing=u'camera/CameraWelcomeDrawing.png', CameraQuotaSplash=u'camera/CameraOutOfSpace.png', CameraBackground=u'camera/CameraBackground.png', SplashGradientBackground=u'splash/gradient_background.png', ScreenshotsBox=u'Screenshots/box-and-arrows.png', boxstroked=u'about/box_stroked_150.png', arash3=u'about/arash3.jpg', david=u'about/david.jpg', drew=u'about/drew.jpg', dropboxlogo=u'about/dropboxlogo.png', jon=u'about/jon.png', mike=u'about/mike.jpg', rian=u'about/rian.jpg', tom=u'about/tom.jpg', martin=u'about/martin.jpg')
    LionScreenshots = dict(WebInterfaceShot=u'setupwizard/mac/10.7/web.png', MenuIconShot=u'setupwizard/mac/10.7/menu.png', ShareFoldersShot=u'setupwizard/mac/10.7/share.png', TourWelcomeShot=u'setupwizard/mac/10.7/welcome.png')
    IMAGES = dict(AllImages)
    screenshots_dict = LionScreenshots
    IMAGES.update(screenshots_dict)
    FLAG_PATHS = _get_flag_paths(IMAGES)
    LOADED_IMAGES = dict()

    def __init__(cls, classname, bases, class_dict):
        pass

    def paths(cls):
        return itertools.chain(MetaImages.AllImages.itervalues(), MetaImages.LionScreenshots.itervalues(), MetaImages.FLAG_PATHS)

    def __getattr__(cls, attr):
        if attr not in MetaImages.IMAGES:
            raise AttributeError("Image '%s' is not defined." % attr)
        if attr not in MetaImages.LOADED_IMAGES:
            MetaImages.LOADED_IMAGES[attr] = load_image(MetaImages.IMAGES[attr])
        return MetaImages.LOADED_IMAGES[attr]


class Images(object):
    __metaclass__ = MetaImages
