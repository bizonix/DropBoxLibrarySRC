#Embedded file name: dropbox/client/multiaccount/values.py
from collections import namedtuple
from dropbox.client.multiaccount.constants import Roles
from dropbox.i18n import trans
from dropbox.low_functions import undefined
from dropbox.trace import report_bad_assumption
MultiaccountValue = namedtuple('MultiaccountValue', ['personal',
 'business',
 'primary',
 'secondary'])

class MultiaccountValues(object):

    def multiaccount_value(self, personal = undefined, business = undefined, primary = undefined, secondary = undefined):
        if primary is not undefined and secondary is not undefined:
            if self.secondary_role == Roles.BUSINESS:
                personal, business = primary, secondary
            elif self.secondary_role == Roles.PERSONAL:
                personal, business = secondary, primary
        elif personal is not undefined and business is not undefined:
            if self.secondary_role == Roles.BUSINESS:
                primary, secondary = personal, business
            elif self.secondary_role == Roles.PERSONAL:
                primary, secondary = business, personal
        multiaccount_values = (personal,
         business,
         primary,
         secondary)
        if not all((v is not undefined for v in multiaccount_values)):
            report_bad_assumption('Incomplete data passed in to multiaccount_value: %s', multiaccount_values)
            return None
        return MultiaccountValue(*multiaccount_values)

    @property
    def roles(self):
        return self.multiaccount_value(personal=Roles.PERSONAL, business=Roles.BUSINESS)

    @property
    def dropbox_locations(self):
        return self.multiaccount_value(primary=self.app.get_dropbox_path(), secondary=self.get_dropbox_location())

    @property
    def account_labels_plain(self):
        return self.account_labels_plain_with_options()

    def account_labels_plain_with_options(self, lower_plain_names = False, use_team = False):
        personal = trans(u'Personal')
        business = trans(u'Business')
        if lower_plain_names:
            personal = personal.lower()
            business = business.lower()
        if use_team and self.team:
            business = self.team
        return self.multiaccount_value(personal=personal, business=business)

    @property
    def account_labels_plain_long(self):
        return self.multiaccount_value(personal=trans(u'Personal Account'), business=trans(u'Business Account'))

    @property
    def account_labels(self):
        return self.multiaccount_value(personal=trans(u'Personal:'), business=trans(u'Business:'))

    @property
    def unlink_labels(self):
        return self.multiaccount_value(personal=trans(u'Unlink Personal Account...'), business=trans(u'Unlink Business Account...'))

    @property
    def link_labels(self):
        return self.multiaccount_value(personal=trans(u'Link Personal Account...'), business=trans(u'Link Business Account...'))

    @property
    def email_addresses(self):
        return self.multiaccount_value(primary=self.app.config['email'], secondary=self.config['email'])

    @property
    def selective_sync_labels(self):
        return self.multiaccount_value(personal=trans(u'Personal Dropbox Selective Sync'), business=trans(u'Business Dropbox Selective Sync'))

    @property
    def location_changer_labels(self):
        return self.multiaccount_value(personal=trans(u'Personal Dropbox Location'), business=trans(u'Business Dropbox Location'))
