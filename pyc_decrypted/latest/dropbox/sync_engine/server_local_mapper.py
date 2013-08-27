#Embedded file name: dropbox/sync_engine/server_local_mapper.py
from dropbox.trace import DEVELOPER_WARNING
from dropbox.server_path import NsRelativePathFast
from dropbox.sync_engine.exceptions import UnmountedPathError

class ServerLocalMapper(object):

    def __init__(self, root_ns_to_local_path, file_cache, fs):
        self.root_ns_to_local_path = {}
        self.root_ns_to_local_path_lower = {}
        self.fs = fs
        for ns, lp in root_ns_to_local_path.iteritems():
            self.root_ns_to_local_path[ns] = lp
            self.root_ns_to_local_path_lower[ns] = lp.lower()

        self.cache = file_cache

    def convert_root_relative(self, root_relative, lowered = False):
        if lowered:
            root_ns_to_local = self.root_ns_to_local_path_lower
        else:
            root_ns_to_local = self.root_ns_to_local_path
        return root_ns_to_local[root_relative.ns].add_dropbox_ns_relative_path(root_relative.rel)

    def server_to_local(self, server_path, ignore_case = True, fast = True, local_case_only = False):
        return self.convert_root_relative(self.cache.root_relative_server_path(server_path, ignore_case=ignore_case, ctor=NsRelativePathFast if fast else None, local_case_only=local_case_only))

    def convert_local(self, local_path, ctor = None, warning = False):
        if not ctor:
            ctor = NsRelativePathFast
        lpl = local_path.lower()
        for ns, root_mount_point in self.root_ns_to_local_path_lower.iteritems():
            if lpl == root_mount_point:
                if warning:
                    DEVELOPER_WARNING('Calling local_to_server root_ns: %r', local_path)
                return ctor(ns, u'/')
            if root_mount_point.is_parent_of(lpl):
                return ctor(ns, local_path.to_dropbox_ns_relative(root_mount_point))

        raise UnmountedPathError(local_path)

    def local_to_server(self, local_path):
        root_relative = self.convert_local(local_path, ctor=NsRelativePathFast, warning=True)
        return self.cache.mount_relative_server_path(root_relative)
