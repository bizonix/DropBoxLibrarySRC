#Embedded file name: dropbox/client/multiaccount/controller.py


class MergedController(object):

    def __init__(self, app):
        self.app = app
        self.show_primary = self.show_secondary = True

    def update_merge_state(self, show_personal = None, show_business = None):
        merge_state = self.app.mbox.multiaccount_value(personal=show_personal, business=show_business)
        if merge_state.primary is not None:
            self.show_primary = merge_state.primary
        if merge_state.secondary is not None:
            self.show_secondary = merge_state.secondary

    def tag_and_merge(self, primary_method, secondary_method, **kwargs):
        roles = self.app.mbox.roles
        primary = primary_method(**kwargs) if self.show_primary else []
        secondary = secondary_method(**kwargs) if self.show_secondary else []
        for change in primary:
            change.primary = True
            change.role = roles.primary

        for change in secondary:
            change.primary = False
            change.role = roles.secondary

        return primary + secondary
