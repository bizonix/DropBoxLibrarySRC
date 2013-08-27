#Embedded file name: ui/common/notifications.py
import hashlib
import string
import urllib
import urlparse
from xml.sax.saxutils import escape
import arch
from dropbox.client.multiaccount.constants import Roles
from dropbox.debugging import easy_repr
from dropbox.file_cache.exceptions import NamespaceNotMountedError
from dropbox.functions import snippet
from dropbox.i18n import ago, format_number, format_percent, trans, ungettext
from dropbox.path import ServerPath
from dropbox.trace import report_bad_assumption, TRACE, unhandled_exc_handler
from ui.common.strings import UIStrings
from ui.common.html import HTMLTextConverter

class IncompletePayloadException(Exception):
    pass


class MalformedPayloadException(Exception):
    pass


class UserNotificationStrings(UIStrings):
    _strings = dict(shared_folder_invite_bubble_title=u'Shared folder invitation', shared_folder_invite_bubble_message=u"%(inviter_name)s invited you to the shared folder '%(folder_name)s'.", shared_folder_invite_message=u'%(inviter_name)s invited you to the shared folder <strong>%(folder_name)s</strong>.', shared_folder_invite_message_accepted=u'You joined the shared folder <strong>%(folder_name)s</strong>.', shared_folder_invite_message_declined=u'You declined to join the shared folder <strong>%(folder_name)s</strong>.', shared_folder_invite_message_uninvited=u'You were uninvited by %(inviter_name)s to join <strong>%(folder_name)s</strong>.', shared_folder_invite_action_accept=u'Accept', shared_folder_invite_action_decline=u'Decline', shared_folder_invite_action_view=u'Open', shared_folder_joined_bubble_title=u'%(invitee_name)s joined your shared folder', shared_folder_joined_bubble_message=u"%(invitee_name)s joined your shared folder '%(folder_name)s'.", shared_folder_joined_message=u'%(invitee_name)s joined your shared folder <strong>%(folder_name)s</strong>.', shared_link_bubble_title=u'Shared Link', shared_link_bubble_message=u"%(sender_name)s shared '%(object_name)s' with you.", shared_link_message=u'%(sender_name)s shared <strong>%(object_name)s</strong> with you.', shared_link_action_view=u'View', unshared_link_message=u'%(sender_name)s unshared <strong>%(file_name)s</strong> with you.', shared_album_bubble_title=u'Shared Album', shared_album_bubble_message=u"%(sender_name)s shared the album '%(object_name)s' with you.", shared_album_message=u'%(sender_name)s shared the album <strong>%(object_name)s</strong> with you.', shared_album_action_view=u'View', unshared_album_message=u'%(sender_name)s unshared an album called <strong>%(file_name)s</strong>.', quota_full_bubble_title=u'Your Dropbox is full', quota_full_bubble_message=u'Upgrade or refer your friends to get more space.', quota_full_message=u'<strong>Your Dropbox is full!</strong> Upgrade or refer your friends to get more space.', quota_full_message_tag=u'<strong>Your Dropbox &#40;%(tag)s&#41; is full!</strong> Upgrade or refer your friends to get more space.', quota_full_action_upgrade=u'Upgrade', quota_full_action_refer=u'Refer friends', quota_low_bubble_title=u'Your Dropbox is almost full', quota_low_bubble_message=u'Uh-oh! Your Dropbox is %(percentage)s full. Upgrade or refer your friends to get more space.', quota_low_message=u'Uh-oh! Your Dropbox is %(percentage)s full. <strong>Upgrade or refer your friends</strong> to get more space.', referral_completed_bubble_title=u'You earned %(bump_amount)s of space', referral_completed_bubble_message=u'Congrats! You earned %(bump_amount)s of space because %(origin_user_name)s joined Dropbox.', referral_completed_message=u'Congrats! You earned %(bump_amount)s of space because %(origin_user_name)s joined Dropbox. <strong>Refer more friends</strong> to get more space.', referral_accepted_bubble_title=u'You earned %(bump_amount)s of space', referral_accepted_bubble_message=u'Congrats! You earned %(bump_amount)s of space for joining Dropbox.', referral_accepted_message=u'Congrats! You earned %(bump_amount)s of space for joining Dropbox. <strong>Refer your friends</strong> to get more space.', new_photos_action_share=(u'Share', 'This action will be visible in the notificationtray. Clicking it will take the user to the websitewhere they can share their photos or videos'), photo_gallery_title=u'Import Photo Gallery', photo_gallery_message=u'<strong>Keep your photos safe with Dropbox!</strong> Import %(num_photos)s photos from %(source)s.', photo_gallery_action_import=(u'Learn more', 'This action will be visible in the notificationtray. Clicking it will take the user to the a splash screenwhere they can choose to import photos from their iPhoto'), photo_gallery_action_never=(u'Never', 'This action will be visible in the notificationtray. Clicking it will cause the import notification tounstick from their tray popup and never come back.'), error_generic=(u'Sorry, an error occurred. Please try again later...', "This should be very rare, it's the message we display when something unexpected happened."), error_shared_folder_accept_verify=u'Please verify your email address.', error_shared_folder_accept_removed=u'This invitation was cancelled.', error_shared_folder_accept_forbidden=u"Sorry, you aren't allowed to accept this invitation.", error_shared_folder_accept_external=u'Your Dropbox admin restricts shared folders from outside your team.', error_shared_folder_decline_joined=u"You've already accepted this invitation.", error_shared_folder_decline_removed=u'This invitation was cancelled.', error_shared_folder_decline_forbidden=u"Sorry, you aren't allowed to decline this invitation.", error_shared_folder_view_not_mounted=u"This folder isn't synced.")
    _platform_overrides = dict(win=dict(photo_gallery_message=u'Move your pictures to Dropbox to make them safe and available anywhere!'))


class UserNotificationActionNotAvailableError(Exception):
    pass


class UserNotificationActionError(Exception):

    def __init__(self, identifier, wrapped = None):
        self.identifier = identifier
        self.wrapped = wrapped
        localized_message = getattr(UserNotificationStrings, identifier, None)
        if localized_message is None:
            report_bad_assumption('Missing message for error: %r' % identifier)
            localized_message = UserNotificationStrings.error_generic
        self.localized_message = localized_message

    def __str__(self):
        return '<%s(%r)%s>' % (self.__class__.__name__, self.identifier, ': %s' % self.wrapped if self.wrapped else '')


class MetaUserNotification(type):
    _notification_types = {}

    def __init__(cls, name, bases, cls_dict):
        if name == 'UserNotification':
            return
        for attr in ('_type_id', '_min_supported_version'):
            assert attr in cls_dict, "Classes deriving from MetaUserNotification must have a '%s' class attribute" % (attr,)

        _types = MetaUserNotification._notification_types
        _type_id = cls_dict['_type_id']
        assert _type_id not in _types, 'A notification class already declares it satisfies type id %r' % (_type_id,)
        _types[_type_id] = cls
        super(MetaUserNotification, cls).__init__(name, bases, cls_dict)

    @classmethod
    def _from_serialized(cls, notif_dict):
        _type_id = notif_dict.pop('_type_id')
        notif_class = cls._notification_types[_type_id]
        return notif_class._from_serialized(notif_dict)


class UserNotification(object):
    STATUS_UNREAD = 0
    STATUS_READ = 1
    STATUS_INVISIBLE = 2
    CLIENT_ALERT_VOLATILE = 0
    CLIENT_ALERT_VISIBLE = 1
    CLIENT_ALERT_BUZZ = 2
    CLIENT_ALERT_NO_BUBBLE = 3
    __metaclass__ = MetaUserNotification

    def __init__(self, nid, target_object_key, timestamp, payload, status, client_alert_level):
        self.nid = nid
        self.target_object_key = target_object_key
        self.timestamp = timestamp
        self.payload = payload
        self.status = status
        self.client_alert_level = client_alert_level
        _hash = hashlib.md5()
        _hash.update('%s_%s' % (self._type_id, target_object_key))
        self.key = _hash.hexdigest()
        self.message = None
        self.actions = ()
        self.local_icon = None
        self.remote_icon = None
        self.thumbnail = None
        self.default_action = None
        self.primary = None
        self.role = None

    def perform_action(self, app, target):
        if self.status == self.STATUS_INVISIBLE:
            raise UserNotificationActionNotAvailableError('Notification is not visible.')
        if not target:
            raise UserNotificationActionNotAvailableError('No action provided!')
        bundle = {'nid': self.nid,
         'type_id': self._type_id,
         'target_object_key': self.target_object_key,
         'status': self.status,
         'action_id': target}
        app.event.report('notification-action', **bundle)
        try:
            self._perform_action(app, target)
        except UserNotificationActionError as exc:
            error_bundle = bundle.copy()
            error_bundle['error_id'] = exc.identifier
            app.event.report('notification-action-error', **error_bundle)
            raise

    def get_bubble(self):
        return None

    def get_dict(self, now):
        result = {'nid': self.nid,
         'key': self.key,
         'extra_message': ago(self.timestamp, now),
         'message': self.message,
         'actions': self.actions,
         'status': self.status,
         'default_action': self.default_action,
         'local_icon': self.local_icon,
         'remote_icon': self.remote_icon,
         'thumbnail': self.thumbnail}
        if self.role == Roles.BUSINESS:
            result['multiaccount_subtitle'] = trans(u'Business')
        return result

    def _get_serialized(self):
        return {'nid': self.nid,
         'target_object_key': self.target_object_key,
         'timestamp': self.timestamp,
         'payload': self.payload,
         'status': self.status,
         'client_alert_level': self.client_alert_level,
         'key': self.key,
         '_type_id': self._type_id}

    def compare_payload(self, other):
        assert isinstance(other, UserNotification), 'Not supported!'
        return self.payload == other.payload

    def is_visible(self):
        return self.status != self.STATUS_INVISIBLE

    def __repr__(self):
        return easy_repr(self, 'nid', 'key', 'message', 'status')

    @classmethod
    def _from_serialized(cls, notif_dict):
        key = notif_dict.pop('key')
        instance = cls(**notif_dict)
        instance.key = key
        return instance


class SharedFolderInvitation(UserNotification):
    ACTION_VIEW = 'view'
    ACTION_ACCEPT = 'accept'
    ACTION_DECLINE = 'decline'
    ACTION_OPEN_TRAY = 'open_tray'
    STATUS_INVITED = 0
    STATUS_ACCEPTED = 1
    STATUS_DECLINED = 2
    STATUS_UNINVITED = 3
    NO_RESTRICTIONS = 0
    ACCEPT_FORBIDDEN = 1
    _type_id = 100
    _min_supported_version = 1

    def __init__(self, nid, target_object_key, timestamp, payload, status, client_alert_level):
        super(SharedFolderInvitation, self).__init__(nid, target_object_key, timestamp, payload, status, client_alert_level)
        self.local_icon = 'shared-folder'
        self.invite_status = payload['invite_status']
        self.iid = payload['invite_id']
        self.nsid = payload['ns_id']
        args = {'inviter_name': escape(payload['origin_user_display_name']),
         'folder_name': escape(snippet(payload['folder_name'], maxchars=32))}
        if self.invite_status == self.STATUS_INVITED:
            self.actions = ((self.ACTION_DECLINE, UserNotificationStrings.shared_folder_invite_action_decline, False), (self.ACTION_ACCEPT, UserNotificationStrings.shared_folder_invite_action_accept, True))
        if self.invite_status == self.STATUS_INVITED:
            self.message = UserNotificationStrings.shared_folder_invite_message % args
            self.bubble_title = UserNotificationStrings.shared_folder_invite_bubble_title
            self.bubble_message = UserNotificationStrings.shared_folder_invite_bubble_message % args
            self.bubble_action = self.ACTION_OPEN_TRAY
        elif self.invite_status == self.STATUS_ACCEPTED:
            self.message = UserNotificationStrings.shared_folder_invite_message_accepted % args
            self.default_action = self.ACTION_VIEW
        elif self.invite_status == self.STATUS_DECLINED:
            self.message = UserNotificationStrings.shared_folder_invite_message_declined % args
        elif self.invite_status == self.STATUS_UNINVITED:
            self.message = UserNotificationStrings.shared_folder_invite_message_uninvited % args
        else:
            raise MalformedPayloadException('Invite status is not recognized: %r', self.invite_status)

    def get_bubble(self):
        if self.invite_status != self.STATUS_INVITED:
            return None
        return (self.bubble_title, self.bubble_message, self.bubble_action)

    def is_visible(self):
        return True

    def _do_accept(self, app):
        TRACE('Accepting shared folder invitation: %r', self.iid)
        ret = app.conn.shared_folder_accept(self.iid)
        if ret['ret'] == 'ok':
            return
        err = ret.get('err')
        if err:
            raise UserNotificationActionError('error_shared_folder_accept_%s' % err)
        else:
            raise Exception('Call failed, but no error code')

    def _do_decline(self, app):
        TRACE('Declining shared folder invitation: %r', self.iid)
        ret = app.conn.shared_folder_decline(self.iid)
        if ret['ret'] == 'ok':
            return
        err = ret.get('err')
        if err:
            raise UserNotificationActionError('error_shared_folder_decline_%s' % err)
        else:
            raise Exception('Call failed, but no error code')

    def _do_view_mounted(self, app):
        mount_point = ServerPath.from_ns_rel(self.nsid, u'/')
        try:
            local_path = unicode(app.sync_engine.server_to_local(mount_point))
            arch.util.launch_folder(local_path)
        except NamespaceNotMountedError as e:
            raise UserNotificationActionError('error_shared_folder_view_not_mounted', e)

    def _do_view_web(self, app):
        app.desktop_login.login_and_redirect('share?inbox=1')

    def _do_open_tray(self, app):
        app.ui_kit.show_tray_popup()

    def _perform_action(self, app, target):
        if target == self.ACTION_VIEW and self.invite_status == self.STATUS_ACCEPTED:
            self._do_view_mounted(app)
        elif target == self.ACTION_ACCEPT:
            self._do_accept(app)
        elif target == self.ACTION_DECLINE:
            self._do_decline(app)
        elif target == self.ACTION_OPEN_TRAY:
            self._do_open_tray(app)
        else:
            raise UserNotificationActionNotAvailableError('Invalid action!')


class SharedFolderJoined(UserNotification):
    _type_id = 600
    _min_supported_version = 1
    ACTION_VIEW_OPTIONS = 'view_options'
    ACTION_OPEN = 'open'

    def __init__(self, nid, target_object_key, timestamp, payload, status, client_alert_level):
        super(SharedFolderJoined, self).__init__(nid, target_object_key, timestamp, payload, status, client_alert_level)
        self.local_icon = 'shared-folder-plus'
        self.ns_id = payload['ns_id']
        args = {'invitee_name': escape(payload['invitee_display_name']),
         'folder_name': escape(snippet(payload['folder_name'], maxchars=32))}
        self.bubble_title = UserNotificationStrings.shared_folder_joined_bubble_title % args
        self.bubble_message = UserNotificationStrings.shared_folder_joined_bubble_message % args
        self.message = UserNotificationStrings.shared_folder_joined_message % args
        self.default_action = self.ACTION_VIEW_OPTIONS

    def get_bubble(self):
        return (self.bubble_title, self.bubble_message, self.ACTION_OPEN)

    def _do_view_options(self, app):
        app.desktop_login.login_and_redirect('c/share/?ns_id=%s' % self.ns_id)

    def _do_view_mounted(self, app):
        mount_point = ServerPath.from_ns_rel(self.ns_id, u'/')
        try:
            local_path = unicode(app.sync_engine.server_to_local(mount_point))
            arch.util.launch_folder(local_path)
        except NamespaceNotMountedError as e:
            raise UserNotificationActionError('error_shared_folder_view_not_mounted', e)

    def _perform_action(self, app, target):
        if target == self.ACTION_VIEW_OPTIONS:
            self._do_view_options(app)
        elif target == self.ACTION_OPEN:
            self._do_view_mounted(app)
        else:
            raise UserNotificationActionNotAvailableError('Invalid action!')


class SharedLink(UserNotification):
    TOKEN_TYPE_BLOCKSERVER_FILE_VIEW = 5
    TOKEN_TYPE_BLOCKSERVER_FOLDER_VIEW = 6
    TOKEN_TYPE_BLOCKSERVER_TEMP_VIEW = 7
    TOKEN_TYPE_COLLECTION_VIEW = 10
    COLLECTION_TYPE_ANONYMOUS_PHOTO_AND_VIDEO = 3
    ACTION_VIEW = 'view'
    _type_id = 1
    _min_supported_version = 1

    def _set_strings(self, args):
        if self.status == UserNotification.STATUS_INVISIBLE:
            self.message = UserNotificationStrings.unshared_link_message % args
        else:
            self.message = UserNotificationStrings.shared_link_message % args
            self.has_bubble = True
            self.bubble_title = UserNotificationStrings.shared_link_bubble_title
            self.bubble_message = UserNotificationStrings.shared_link_bubble_message % args

    def _set_strings_albums(self, args):
        if self.status == UserNotification.STATUS_INVISIBLE:
            self.message = UserNotificationStrings.unshared_album_message % args
        else:
            self.message = UserNotificationStrings.shared_album_message % args
            self.has_bubble = True
            self.bubble_title = UserNotificationStrings.shared_album_bubble_title
            self.bubble_message = UserNotificationStrings.shared_album_bubble_message % args

    def _set_strings_counts(self, args, num_photos, num_videos):
        args['num_photos'] = num_photos
        args['num_videos'] = num_videos
        if self.status == UserNotification.STATUS_INVISIBLE:
            if num_photos and num_videos:
                self.message = trans(u'%(sender_name)s unshared <strong>%(num_photos)s photos and %(num_videos)s videos</strong> with you.') % args
            elif num_photos > 0:
                self.message = ungettext(u'%(sender_name)s unshared <strong>%(num_photos)s photo</strong> with you.', u'%(sender_name)s unshared <strong>%(num_photos)s photos</strong> with you.', num_photos) % args
            elif num_videos > 0:
                self.message = ungettext(u'%(sender_name)s unshared <strong>%(num_videos)s video</strong> with you.', u'%(sender_name)s unshared <strong>%(num_videos)s videos</strong> with you.', num_videos) % args
        else:
            self.has_bubble = True
            if num_photos and num_videos:
                self.message = trans(u'%(sender_name)s shared <strong>%(num_photos)s photos and %(num_videos)s videos</strong> with you.') % args
                self.bubble_title = trans(u'Shared photos and videos')
                self.bubble_message = trans(u'%(sender_name)s shared %(num_photos)s photos and %(num_videos)s videos with you.') % args
            elif num_photos > 0:
                self.message = ungettext(u'%(sender_name)s shared <strong>%(num_photos)s photo</strong> with you.', u'%(sender_name)s shared <strong>%(num_photos)s photos</strong> with you.', num_photos) % args
                self.bubble_title = trans(u'Shared photos')
                self.bubble_message = ungettext(u'%(sender_name)s shared %(num_photos)s photo with you.', u'%(sender_name)s shared %(num_photos)s photos with you.', num_photos) % args
            elif num_videos > 0:
                self.message = ungettext(u'%(sender_name)s shared <strong>%(num_videos)s video</strong> with you.', u'%(sender_name)s shared <strong>%(num_videos)s videos</strong> with you.', num_photos) % args
                self.bubble_title = trans(u'Shared videos')
                self.bubble_message = ungettext(u'%(sender_name)s shared %(num_videos)s video with you.', u'%(sender_name)s shared %(num_videos)s videos with you.', num_photos) % args

    def __init__(self, nid, target_object_key, timestamp, payload, status, client_alert_level):
        super(SharedLink, self).__init__(nid, target_object_key, timestamp, payload, status, client_alert_level)
        token_type = payload['token_type']
        token_name = payload['token_name']
        sender_name = payload['origin_user_i18n_name']
        link_parts = urlparse.urlparse(payload['shmodel_url'])
        self.link_url = link_parts.path.lstrip('/')
        is_thumbnail_placeholder = payload.get('is_thumbnail_placeholder')
        thumbnail_url = payload.get('thumbnail_url')
        collection_type = payload.get('collection_type')
        self.default_action = self.ACTION_VIEW
        self.has_bubble = False
        args = {'sender_name': escape(sender_name),
         'object_name': escape(snippet(token_name, maxchars=32))}
        if token_type == self.TOKEN_TYPE_COLLECTION_VIEW:
            if collection_type is not None and collection_type != self.COLLECTION_TYPE_ANONYMOUS_PHOTO_AND_VIDEO:
                self.local_icon = 'folder'
                self._set_strings_albums(args)
            else:
                self.local_icon = 'picture'
                num_photos, num_videos = payload.get('num_photos'), payload.get('num_videos')
                has_count_info = num_photos is not None and num_videos is not None
                if has_count_info:
                    self._set_strings_counts(args, num_photos, num_videos)
                else:
                    self._set_strings(args)
        else:
            if token_type == self.TOKEN_TYPE_BLOCKSERVER_FOLDER_VIEW:
                self.local_icon = 'folder'
            else:
                self.local_icon = 'file'
            self._set_strings(args)
        if is_thumbnail_placeholder and thumbnail_url is not None:
            try:
                self.remote_icon = urlparse.urlparse(thumbnail_url).path.split('/')[-1]
            except Exception:
                unhandled_exc_handler()

        elif thumbnail_url is not None:
            self.local_icon = 'picture'
            self.thumbnail = thumbnail_url

    def get_bubble(self):
        if not self.has_bubble:
            return None
        return (self.bubble_title, self.bubble_message, self.ACTION_VIEW)

    def is_visible(self):
        return True

    def _do_view_web(self, app):
        app.desktop_login.login_and_redirect(self.link_url)

    def _perform_action(self, app, target):
        if target == self.ACTION_VIEW:
            self._do_view_web(app)
        else:
            raise UserNotificationActionNotAvailableError()


class ReferralCompleted(UserNotification):
    _type_id = 500
    _min_supported_version = 1
    ACTION_OPEN_REFERRALS = 'refer'

    def __init__(self, nid, target_object_key, timestamp, payload, status, client_alert_level):
        super(ReferralCompleted, self).__init__(nid, target_object_key, timestamp, payload, status, client_alert_level)
        is_target_user_sender = payload['is_target_user_sender']
        args = {'origin_user_name': escape(payload['origin_user_i18n_name']),
         'bump_amount': escape(payload['bump_amount'])}
        self.default_action = self.ACTION_OPEN_REFERRALS
        if is_target_user_sender:
            self.bubble_title = UserNotificationStrings.referral_accepted_bubble_title % args
            self.bubble_message = UserNotificationStrings.referral_accepted_bubble_message % args
            self.message = UserNotificationStrings.referral_accepted_message % args
        else:
            self.bubble_title = UserNotificationStrings.referral_completed_bubble_title % args
            self.bubble_message = UserNotificationStrings.referral_completed_bubble_message % args
            self.message = UserNotificationStrings.referral_completed_message % args
        self.local_icon = 'gift'

    def get_bubble(self):
        return (self.bubble_title, self.bubble_message, None)

    def _do_open_referrals(self, app):
        app.desktop_login.login_and_redirect('referrals')

    def _perform_action(self, app, target):
        if target == self.ACTION_OPEN_REFERRALS:
            self._do_open_referrals(app)
        else:
            raise UserNotificationActionNotAvailableError()


class NewPhotos(UserNotification):
    ACTION_VIEW = 'view'
    ACTION_SHARE = 'share'
    _type_id = 200
    _min_supported_version = 1

    def __init__(self, nid, target_object_key, timestamp, payload, status, client_alert_level):
        super(NewPhotos, self).__init__(nid, target_object_key, timestamp, payload, status, client_alert_level)
        num_photos = payload.get('num_photos')
        num_videos = payload.get('num_videos')
        device_label = payload.get('device_label', '')
        self.link_url = string.lstrip(payload.get('view_url'), '/')
        self.local_icon = 'picture'
        self.thumbnail = payload.get('thumbnail_url')
        if payload.get('share'):
            self.actions = ((self.ACTION_SHARE, UserNotificationStrings.new_photos_action_share, False),)
        self.default_action = self.ACTION_VIEW
        self.bubble_title, self.bubble_message, self.message = self._get_strings(num_photos, num_videos, device_label)

    def _get_strings(self, num_photos, num_videos, device_label):
        device_label = device_label.split(':')
        if len(device_label) == 1:
            device_label.append('')
        category, model = device_label
        if category == 'phone' and model == 'iphone':
            strings = (trans(u'You added <strong>%(num_total)s new photos and videos</strong> from your iPhone.'), ungettext(u'You added <strong>%(num_photos)s new photo</strong> from your iPhone.', u'You added <strong>%(num_photos)s new photos</strong> from your iPhone.', num_photos), ungettext(u'You added <strong>%(num_videos)s new video</strong> from your iPhone.', u'You added <strong>%(num_videos)s new videos</strong> from your iPhone.', num_videos))
        elif category == 'tablet' and model == 'ipad':
            strings = (trans(u'You added <strong>%(num_total)s new photos and videos</strong> from your iPad.'), ungettext(u'You added <strong>%(num_photos)s new photo</strong> from your iPad.', u'You added <strong>%(num_photos)s new photos</strong> from your iPad.', num_photos), ungettext(u'You added <strong>%(num_videos)s new video</strong> from your iPad.', u'You added <strong>%(num_videos)s new videos</strong> from your iPad.', num_videos))
        elif category == 'phone':
            strings = (trans(u'You added <strong>%(num_total)s new photos and videos</strong> from your phone.'), ungettext(u'You added <strong>%(num_photos)s new photo</strong> from your phone.', u'You added <strong>%(num_photos)s new photos</strong> from your phone.', num_photos), ungettext(u'You added <strong>%(num_videos)s new video</strong> from your phone.', u'You added <strong>%(num_videos)s new videos</strong> from your phone.', num_videos))
        elif category == 'tablet':
            strings = (trans(u'You added <strong>%(num_total)s new photos and videos</strong> from your tablet.'), ungettext(u'You added <strong>%(num_photos)s new photo</strong> from your tablet.', u'You added <strong>%(num_photos)s new photos</strong> from your tablet.', num_photos), ungettext(u'You added <strong>%(num_videos)s new video</strong> from your tablet.', u'You added <strong>%(num_videos)s new videos</strong> from your tablet.', num_videos))
        elif category == 'camera':
            strings = (trans(u'You added <strong>%(num_total)s new photos and videos</strong> from your camera.'), ungettext(u'You added <strong>%(num_photos)s new photo</strong> from your camera.', u'You added <strong>%(num_photos)s new photos</strong> from your camera.', num_photos), ungettext(u'You added <strong>%(num_videos)s new video</strong> from your camera.', u'You added <strong>%(num_videos)s new videos</strong> from your camera.', num_videos))
        else:
            strings = (trans(u'You added <strong>%(num_total)s new photos and videos</strong>.'), ungettext(u'You added <strong>%(num_photos)s new photo</strong>.', u'You added <strong>%(num_photos)s new photos</strong>.', num_photos), ungettext(u'You added <strong>%(num_videos)s new video</strong>.', u'You added <strong>%(num_videos)s new videos</strong>.', num_videos))
        fill_dict = {'num_total': num_photos + num_videos,
         'num_photos': num_photos,
         'num_videos': num_videos}
        if num_photos and num_videos:
            title = trans(u'New Photos and Videos')
            message = strings[0] % fill_dict
        elif num_photos > 0:
            title = ungettext(u'New Photo', u'New Photos', num_photos)
            message = strings[1] % fill_dict
        else:
            title = ungettext(u'New Video', u'New Videos', num_videos)
            message = strings[2] % fill_dict
        bubble_message = HTMLTextConverter.convert(message)
        return (title, bubble_message, message)

    def get_bubble(self):
        return (self.bubble_title, self.bubble_message, self.ACTION_VIEW)

    def _do_view_web(self, app):
        app.desktop_login.login_and_redirect(self.link_url)

    def _do_share_web(self, app):
        url_parts = urlparse.urlparse(self.link_url)
        existing_params = dict(urlparse.parse_qsl(url_parts.query))
        existing_params['share'] = 1
        enc_params = urllib.urlencode(existing_params)
        app.desktop_login.login_and_redirect('%s?%s' % (url_parts.path, enc_params))

    def _perform_action(self, app, target):
        if target == self.ACTION_VIEW:
            self._do_view_web(app)
        elif target == self.ACTION_SHARE:
            self._do_share_web(app)
        else:
            raise UserNotificationActionNotAvailableError()


STICKY_PRIORITY_OUT_OF_QUOTA = 10
STICKY_PRIORITY_SYNC_ERROR = 20
STICKY_PRIORITY_PHOTO_GALLERY_IMPORT = 60

class MetaStickyNotification(type):
    _sticky_types = {}

    def __init__(cls, name, bases, cls_dict):
        if name == 'StickyNotification':
            return
        msg = "MetaStickyNotification subclasses must have the 'STICKY_KEY' class attribute"
        assert 'STICKY_KEY' in cls_dict, msg
        sticky_key = cls_dict['STICKY_KEY']
        msg = ("Duplicate 'STICKY_KEY': %s", sticky_key)
        assert sticky_key not in MetaStickyNotification._sticky_types, msg
        MetaStickyNotification._sticky_types[sticky_key] = cls
        super(MetaStickyNotification, cls).__init__(name, bases, cls_dict)

    @classmethod
    def _from_serialized(cls, sticky_dict):
        sticky_key = sticky_dict.pop('STICKY_KEY')
        sticky_cls = cls._sticky_types[sticky_key]
        return sticky_cls._from_serialized(sticky_dict)


class StickyNotification(object):
    __metaclass__ = MetaStickyNotification

    def __init__(self, key):
        assert self.STICKY_KEY and self._priority
        self.key = key
        self.local_icon = None
        self.thumbnail = None
        self.title = None
        self.message = None
        self.extra_message = None
        self.actions = ()

    def perform_action(self, app, target):
        bundle = {'key': self.key,
         'action_id': target}
        app.event.report('sticky-notification-action', **bundle)
        return self._perform_action(app, target)

    def get_dict(self):
        return {'key': self.key,
         'title': self.title,
         'message': self.message,
         'extra_message': self.extra_message,
         'actions': self.actions,
         'local_icon': self.local_icon,
         'thumbnail': self.thumbnail}

    def __repr__(self):
        return easy_repr(self, '_priority', 'key', 'message')


class PhotoGalleryStickyNotification(StickyNotification):
    STICKY_KEY = 'photo gallery'
    _priority = STICKY_PRIORITY_PHOTO_GALLERY_IMPORT
    ACTION_IMPORT = 'import'
    ACTION_NEVER = 'never'

    def __init__(self, num_photos, import_source, import_cb, never_cb):
        super(PhotoGalleryStickyNotification, self).__init__(key=self.STICKY_KEY)
        self.num_photos = num_photos
        self.import_source = import_source
        self.local_icon = 'import'
        self.thumbnail = None
        self.actions = ((self.ACTION_IMPORT, UserNotificationStrings.photo_gallery_action_import, True), (self.ACTION_NEVER, UserNotificationStrings.photo_gallery_action_never, False))
        self.title = UserNotificationStrings.photo_gallery_title
        fmt_dict = {'num_photos': format_number(num_photos, frac_precision=0),
         'source': import_source}
        self.message = UserNotificationStrings.photo_gallery_message % fmt_dict
        self.import_cb = import_cb
        self.never_cb = never_cb

    def _perform_action(self, app, target):
        if target == self.ACTION_IMPORT:
            return self.import_cb()
        if target == self.ACTION_NEVER:
            return self.never_cb()

    def _get_serialized(self):
        return {'num_photos': self.num_photos,
         'import_source': self.import_source,
         'STICKY_KEY': self.STICKY_KEY}

    @classmethod
    def _from_serialized(cls, sticky_dict):
        dummy_cb = lambda : None
        return cls(import_cb=dummy_cb, never_cb=dummy_cb, **sticky_dict)


class QuotaFullStickyNotification(StickyNotification):
    STICKY_KEY = 'out of quota'
    _priority = STICKY_PRIORITY_OUT_OF_QUOTA
    ACTION_UPGRADE = 'upgrade'
    ACTION_REFER = 'refer'

    def __init__(self, tag = None):
        super(QuotaFullStickyNotification, self).__init__(key=self.STICKY_KEY)
        self.tag = tag
        self.local_icon = 'warn'
        self.thumbnail = None
        self.actions = ((self.ACTION_UPGRADE, UserNotificationStrings.quota_full_action_upgrade, True), (self.ACTION_REFER, UserNotificationStrings.quota_full_action_refer, False))
        self.title = UserNotificationStrings.quota_full_bubble_title
        if self.tag:
            fmt_dict = {'tag': tag}
            self.message = UserNotificationStrings.quota_full_message_tag % fmt_dict
        else:
            self.message = UserNotificationStrings.quota_full_message

    def _perform_action(self, app, target):
        if not target:
            return self._do_open_page(app, 'upgrade?oqa=client_upnot')
        if target == self.ACTION_UPGRADE:
            return self._do_open_page(app, 'upgrade?oqa=client_upnotb')
        if target == self.ACTION_REFER:
            return self._do_open_page(app, 'referrals?oq=client_refnotb')

    def _do_open_page(self, app, page):
        app.desktop_login.login_and_redirect(page)

    def _get_serialized(self):
        return {'tag': self.tag,
         'STICKY_KEY': self.STICKY_KEY}

    @classmethod
    def _from_serialized(cls, sticky_dict):
        return cls(**sticky_dict)
