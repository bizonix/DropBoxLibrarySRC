#Embedded file name: dropbox/client/client_shmodel.py
from __future__ import absolute_import
import urlparse
from collections import namedtuple
from functools import partial
from threading import Lock, Thread
from dropbox.bubble import BubbleKind, Bubble
from dropbox.dispatch import ActionTask
from dropbox.functions import snippet, lrudict
from dropbox.gui import message_sender, spawn_thread_with_name
from dropbox.monotonic_time import get_monotonic_time_seconds
from dropbox.trace import TRACE, report_bad_assumption, unhandled_exc_handler
from dropbox.sync_engine.constants import FileSyncStatus
from ui.common.strings import UIStrings
CLIENT_SHMODEL_UI_TIMEOUT = 10.0
CLIENT_SHMODEL_CACHE_LIFETIME = 300.0

class ClientShmodelStrings(UIStrings):
    _strings = dict(shmodel_working_caption=(u"Sharing '%(file)s'", u'abbreviation for "We\'re creating a shareable link to \'file\'". SHORT'), screenshots_shmodel_working_caption=(u'Sharing Screenshot', u'Abbreviation for "We\'re creating a shareable link to your screenshot.". SHORT'), shmodel_browse_taking_long=(u"We'll open the link in your web browser in just a moment", u"where 'the link' refers to a shareable link that the user just created"), shmodel_clipboard_taking_long=(u"We'll copy the link to your clipboard in just a moment", u"where 'the link' refers to a shareable link that the user just created"), shmodel_clipboard_finished_passive=u"A link to '%(file)s' has been copied to your clipboard.", shmodel_clipboard_finished=u"A link to '%(file)s' has been copied to your clipboard (click to view).", screenshots_shmodel_clipboard_finished_passive=u'A link to your screenshot has been copied to your clipboard.', screenshots_shmodel_clipboard_finished=u'A link to your screenshot has been copied to your clipboard (click to view).', shmodel_error_caption=(u"Couldn't share '%(file)s'", u'abbreviation for "We couldn\'t create a shareable link to \'file\'". SHORT'), shmodel_error_generic=u"Something went wrong. We're working to fix it.", shmodel_error_timeout=u'The server took too long to respond.  Please try again later.', shmodel_error_connection=u'Dropbox is unable to connect to the Internet. Please check your connection.', shmodel_error_not_yet_uploaded=u"The file isn't uploaded yet", shmodel_error_deleted_or_moved=u'The file was deleted or moved', shmodel_error_links_disabled=u'Your shared links are disabled. Please contact Dropbox Support for assistance.', shmodel_error_over_quota=u"You're out of Dropbox space!")
    _platform_overrides = dict()


CacheEntry = namedtuple('CacheEntry', 'timestamp_mono shmodel_link')

class ClientShmodelOrigin(object):
    GENERAL = 1
    SCREENSHOTS = 2


class ClientShmodel(object):

    def __init__(self, app):
        self.app = app
        self._cached_links = lrudict(cache_size=3000)
        self._cached_links_lock = Lock()
        self._active_request = None
        self._active_request_lock = Lock()

    def shmodel_to_clipboard_async(self, server_path, is_dir, origin = ClientShmodelOrigin.GENERAL):
        self.app.ui_kit.copy_text_to_clipboard(u'')
        request_id = self._new_request()
        Thread(name='SHMODEL_HANDLER', target=ActionTask(lambda : self._shmodel_to_clipboard(request_id, server_path, is_dir, origin))).start()

    def _new_request(self):
        with self._active_request_lock:
            self._active_request = object()
            return self._active_request

    def _deactivate_request(self, request):
        with self._active_request_lock:
            if request is self._active_request:
                self._active_request = None
                return True
            return False

    def _get_cached_link(self, server_path):
        now = get_monotonic_time_seconds()
        with self._cached_links_lock:
            cache_entry = self._cached_links.get(server_path)
            if cache_entry and now - cache_entry.timestamp_mono > CLIENT_SHMODEL_CACHE_LIFETIME:
                del self._cached_links[server_path]
                expired = True
            else:
                expired = False
        if expired:
            TRACE('Shmodel cache entry expired: %r -> %r', unicode(server_path), cache_entry)
            return
        elif cache_entry:
            TRACE('Shmodel cache hit: %r -> %r', unicode(server_path), cache_entry)
            return cache_entry.shmodel_link
        else:
            TRACE('Shmodel cache miss: %r', unicode(server_path))
            return

    def _store_link_in_cache(self, server_path, link):
        cache_entry = CacheEntry(timestamp_mono=get_monotonic_time_seconds(), shmodel_link=link)
        with self._cached_links_lock:
            self._cached_links[server_path] = cache_entry
        TRACE('Shmodel link cached: %r -> %r', unicode(server_path), cache_entry)

    def _bubble_success(self, server_path, link, origin):
        if origin == ClientShmodelOrigin.SCREENSHOTS:
            msg = ClientShmodelStrings.screenshots_shmodel_clipboard_finished
            msg_passive = ClientShmodelStrings.screenshots_shmodel_clipboard_finished_passive
            caption = ClientShmodelStrings.screenshots_shmodel_working_caption
        else:
            fname = snippet(server_path.basename, maxchars=25)
            msg = ClientShmodelStrings.shmodel_clipboard_finished % dict(file=fname)
            msg_passive = ClientShmodelStrings.shmodel_clipboard_finished_passive % dict(file=fname)
            caption = ClientShmodelStrings.shmodel_working_caption % dict(file=fname)
        self.app.ui_kit.show_bubble(Bubble(BubbleKind.SHMODEL_COPIED_TO_CLIPBOARD, msg, caption, self.app.bubble_context, self.app.bubble_context.make_func_context_ref(partial(self._user_clicked_shmodel_bubble, link)), show_when_disabled=True, msg_passive=msg_passive))

    def _bubble_error(self, server_path, error):
        TRACE('shmodel error: %r -> %s', unicode(server_path), error)
        fname = snippet(server_path.basename)
        caption = ClientShmodelStrings.shmodel_error_caption % dict(file=fname)
        try:
            message = ClientShmodelStrings[error]
        except KeyError:
            report_bad_assumption('Got unrecognized error: %r', error, full_stack=True)
            message = ClientShmodelStrings.shmodel_error_generic

        bubble = None
        if error is 'shmodel_error_over_quota':
            bubble = Bubble(BubbleKind.SHMODEL_ERROR, message, caption, self.app.bubble_context, self.app.bubble_context.make_func_context_ref(partial(self.app.desktop_login.login_and_redirect, 'c/getspace')), show_when_disabled=True)
        else:
            bubble = Bubble(BubbleKind.SHMODEL_ERROR, message, caption, show_when_disabled=True)
        self.app.ui_kit.show_bubble(bubble)

    def _user_clicked_shmodel_bubble(self, link):
        url_toks = urlparse.urlsplit(link)
        link_rel = urlparse.urlunsplit((None, None) + url_toks[2:]).lstrip('/')
        self.app.desktop_login.login_and_redirect(link_rel)

    @message_sender(spawn_thread_with_name('SHMODEL_REQUEST'), dont_post=lambda : False)
    def _get_shmodel_link_async(self, *args, **kwargs):
        return self.app.conn.get_shmodel_link(*args, **kwargs)

    def _shmodel_to_clipboard(self, request_id, server_path, is_dir, origin):
        local_path = self.app.sync_engine.server_to_local(server_path)
        if self.app.sync_engine.is_changed(unicode(local_path)) != FileSyncStatus.UP_TO_DATE and self.app.quota < self.app.in_use:
            self._bubble_error(server_path, 'shmodel_error_over_quota')
            return
        try:
            self.app.sync_engine.add_priority_hint(server_path)
        except Exception:
            unhandled_exc_handler()

        try:
            link = self._get_cached_link(server_path)
            if link:
                error = None
            else:
                sv_request = self._get_shmodel_link_async(server_path, is_dir=is_dir)
                ret = sv_request.wait(CLIENT_SHMODEL_UI_TIMEOUT)
                if ret is None:
                    if self._deactivate_request(request_id):
                        self._bubble_error(server_path, 'shmodel_error_timeout')
                ret = sv_request.wait()
                error = ret.get('error', None)
                link = ret.get('shmodel_link', None)
                if not link and not error:
                    report_bad_assumption("get_shmodel_link request returned no shmodel_link without setting 'error': %r", ret)
                elif link:
                    self._store_link_in_cache(server_path, link)
            if self._deactivate_request(request_id):
                if error:
                    self._bubble_error(server_path, error)
                elif link:
                    self.app.ui_kit.copy_text_to_clipboard(link)
                    self._bubble_success(server_path, link, origin)
            else:
                TRACE('Not copying shmodel link to clipboard (inactive request): %r', link)
        except Exception as e:
            is_transient_error = self.app.conn.is_transient_error(e)
            if is_transient_error:
                TRACE('!! Failed to communicate with server: %r%r', type(e), e.args)
                error = 'shmodel_error_connection'
            else:
                unhandled_exc_handler()
                error = 'shmodel_error_generic'
            if self._deactivate_request(request_id):
                TRACE('shmodel error (active request): %r -> %s', unicode(server_path), error)
                self._bubble_error(server_path, error)
            else:
                TRACE('shmodel error (inactive request): %r -> %s', unicode(server_path), error)
