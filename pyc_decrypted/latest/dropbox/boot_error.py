#Embedded file name: dropbox/boot_error.py
from __future__ import absolute_import
import os
import sys
from dropbox.i18n import trans as trans_orig
from dropbox.i18n import safe_activate_translation
from dropbox.trace import TRACE, unhandled_exc_handler, report_bad_assumption
from dropbox.url_info import dropbox_url_info
__all__ = ['boot_error']

def trans(msgid):
    try:
        return trans_orig(msgid)
    except AssertionError:
        return msgid
    except Exception:
        unhandled_exc_handler()
        return msgid


def _common_title():
    return trans(u"Couldn't start Dropbox.")


def _common_message():
    return trans(u'This is usually because of a permissions error. Storing your home folder on a network share can also cause an error.') + '\n\n'


def _help_url(page = None):
    page = page or 'permissions_error'
    return dropbox_url_info.help_url(page)


def console_boot_error(extra_info = '', direct_message = '', page = None):
    message = direct_message + '\n\n' if direct_message else _common_message().encode('utf8')
    url = trans(u'Get more help at %(website_url)s').encode('utf8') % {'website_url': _help_url(page)}
    output = '%s\n%s%s' % (_common_title().encode('utf8'), message, url)
    if extra_info:
        output += '\n\n' + dump_extra_info_to_tempfile(extra_info).encode('utf8')
    sys.stderr.write(output + '\n')


def dump_extra_info_to_tempfile(extra_info):
    try:
        try:
            extra_info = str(extra_info)
        except UnicodeEncodeError:
            encodings = ['ascii', 'iso8859-1', 'utf8']
            if sys.platform.startswith('darwin'):
                encodings[1:1] = ['macroman']
            for encoding in encodings:
                try:
                    extra_info = unicode(extra_info).encode(encoding)
                    break
                except Exception:
                    pass

            else:
                extra_info = 'unencodable information'

        import tempfile
        import urllib
        fd, path = tempfile.mkstemp(prefix='dropbox_error', suffix='.txt', text=True)
        try:
            os.write(fd, extra_info)
        finally:
            os.close(fd)

        if sys.platform.startswith('win'):
            quoted_path = '/' + path[:2] + urllib.quote(path[2:].replace('\\', '/'))
        else:
            quoted_path = urllib.quote(path)
        try:
            path = path.decode(sys.getfilesystemencoding())
        except Exception:
            unhandled_exc_handler()
            try:
                path = path.decode('utf8')
            except Exception:
                unhandled_exc_handler()

        try:
            quoted_path = quoted_path.decode(sys.getfilesystemencoding())
        except Exception:
            unhandled_exc_handler()
            try:
                quoted_path = quoted_path.decode('utf8')
            except Exception:
                unhandled_exc_handler()

    except Exception:
        try:
            sys.stderr.write(extra_info + '\n')
        except Exception:
            unhandled_exc_handler()

        error_message = trans(u'Please check the system console for more details.')
    else:
        error_message = trans(u'Please contact Dropbox support with the following info for help:') + '\n\n%s'
        if sys.platform.startswith('linux'):
            error_message %= (path,)
        else:
            error_message %= (u'<a href="file://%s">%s</a>' % (quoted_path, path),)

    return error_message


def cocoa_boot_dialog(**kwargs):
    report_bad_assumption('No boot dialog in Cocoa.')


def cocoa_boot_error(extra_info = None, direct_message = '', page = None, caption = None, more_help = True):
    safe_activate_translation()
    from ui.cocoa.boot_error import BootErrorAlert
    if direct_message:
        message = direct_message + '\n\n'
    else:
        message = _common_message()
    message += trans(u'For more information, click the help button below.')
    text = dump_extra_info_to_tempfile(extra_info) if extra_info else ''
    BootErrorAlert.runModal(_common_title(), message, _help_url(page), text)


def wx_boot_dialog(**kwargs):
    try:
        safe_activate_translation()
        import wx
        import ui.images
        from ui.wxpython.dialogs import DropboxModalDialog
    except Exception:
        TRACE('!! No WX found to display boot dialog')
        return

    app = wx.GetApp()
    if app is not None and app.IsDisplayAvailable():
        dlg = DropboxModalDialog(None, **kwargs)
        return dlg.show_modal()
    else:
        return


def wx_boot_error(extra_info = None, direct_message = '', page = None, caption = None, more_help = True):
    try:
        safe_activate_translation()
        import wx
        import ui.images
        from ui.wxpython.dropbox_error_dialog import DropboxErrorDialog
    except Exception:
        TRACE('!! No WX found to display boot error')
        console_boot_error(extra_info=extra_info, direct_message=direct_message, page=page)
    else:
        if direct_message:
            message = direct_message + ('\n\n' if more_help else '')
        else:
            message = _common_message()
        if more_help:
            if sys.platform.startswith('win'):
                website_url = '<a href="%(path)s">%(text)s</a>' % dict(path=_help_url(page), text=_help_url(page))
                message += trans(u'Get more help at %(website_url)s') % {'website_url': website_url}
            else:
                message += trans(u'Get more help at %(website_url)s') % {'website_url': _help_url(page)}
        if extra_info:
            message += '\n\n' + dump_extra_info_to_tempfile(extra_info)
        caption = caption or _common_title()
        app = wx.GetApp()
        if app is None or not app.IsDisplayAvailable():
            try:
                TRACE('Displaying WX boot error dialog')
                ui.images.init(do_the_assert=False)
                app = wx.App(redirect=False)
                DropboxErrorDialog(None, caption=caption, message=message, ok_only=True, die_on_cancel=True)
                app.MainLoop()
            except Exception:
                TRACE('!! Error displaying WX boot error dialog')
                unhandled_exc_handler()
                console_boot_error(extra_info=extra_info, direct_message=direct_message, page=page)

        else:
            DropboxErrorDialog(None, caption=caption, message=message, ok_only=True, die_on_cancel=True).wait_for_cancel()


if sys.platform.startswith('darwin'):
    boot_error = cocoa_boot_error
    boot_dialog = cocoa_boot_dialog
else:
    boot_error = wx_boot_error
    boot_dialog = wx_boot_dialog
if __name__ == '__main__':
    boot_error()
