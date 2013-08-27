#Embedded file name: dropbox/file_cache/directory_holding.py
from dropbox.low_functions import coerce_list
from dropbox.server_path import get_parent_paths

class DirectoryHoldingAddLogic(object):

    def __init__(self, storage, backend):
        self.storage = storage
        self.backend = backend

    def add_to_held(self, details):
        pass

    def delete_from_held(self, server_paths):
        pass

    def _get_hold(self, server_path):
        elts = list(self.storage.get_holds([server_path]))
        try:
            return elts[0]
        except IndexError:
            return None

    def _get_holds_dict(self, server_paths):
        return dict(((held_child.server_path.lower(), held_child) for held_child in self.storage.get_holds(server_paths)))

    def _get_entries_dict(self, *n, **kw):
        return dict(((d.server_path.lower(), d) for d in self.backend.get_local_details(*n, **kw)))

    def generate_constraints(self, sp_to_details):
        known_entries = set(sp_to_details.keys())
        additional_entries = {}
        file_adds_to_potentially_let_go = set()
        for spl, details in sp_to_details.iteritems():
            if details.dir:
                file_adds_to_potentially_let_go.update(self.storage.get_held_descendants(details.server_path))
            if details.size >= 0:
                file_adds_to_potentially_let_go.add(details.server_path.lower())
                continue

        constraints = []
        blocks = set()
        for file_add_path in file_adds_to_potentially_let_go:
            file_add = self._get_hold(file_add_path)
            if file_add is None or file_add.size < 0:
                continue
            parents = get_parent_paths(file_add_path)
            parents_hold_map = self._get_holds_dict(parents)
            parents_entries_map = self._get_entries_dict(parents)
            can_add = True
            temp_constraints = []
            for p in parents:
                spl = p.lower()
                held_parent = parents_hold_map.get(spl)
                if held_parent is not None:
                    if held_parent.dir:
                        temp_constraints.append((spl, file_add_path))
                        continue
                    else:
                        can_add = False
                        break
                real_parent = parents_entries_map.get(spl)
                if real_parent is not None and real_parent.dir:
                    continue
                else:
                    can_add = False
                    break

            if not can_add:
                blocks.add(file_add_path)
            constraints.extend(temp_constraints)
            if file_add_path not in known_entries:
                additional_entries[file_add_path] = file_add

        return (additional_entries,
         blocks,
         constraints,
         [])


class DirectoryHoldingDeleteLogic(object):

    def __init__(self, storage, backend):
        self.storage = storage
        self.backend = backend

    def add_to_held(self, details):
        pass

    def delete_from_held(self, server_paths):
        pass

    def _get_hold(self, server_path):
        elts = list(self.storage.get_holds([server_path]))
        try:
            return elts[0]
        except IndexError:
            return None

    def _get_holds_dict(self, server_paths):
        return dict(((held_child.server_path.lower(), held_child) for held_child in self.storage.get_holds(server_paths)))

    def _get_entries_dict(self, *n, **kw):
        return dict(((d.server_path.lower(), d) for d in self.backend.get_local_details(*n, **kw)))

    def generate_constraints(self, sp_to_details):
        known_entries = set(sp_to_details.keys())
        additional_entries = {}
        directory_deletes_to_potentially_let_go = set()
        sp_to_db_ent = self._get_entries_dict(sp_to_details.iterkeys())
        for spl, details in sp_to_details.iteritems():
            old_entry = sp_to_db_ent.get(spl)
            if details.size < 0:
                directory_deletes_to_potentially_let_go.update(get_parent_paths(details.server_path.lower()))
            if not details.dir and old_entry is not None and old_entry.dir:
                directory_deletes_to_potentially_let_go.add(details.server_path.lower())
                continue

        constraints = []
        blocks = set()
        for directory_path in directory_deletes_to_potentially_let_go:
            directory_delete = self._get_hold(directory_path)
            if directory_delete is None or directory_delete.dir:
                continue
            can_delete = True
            temp_constraints = []
            directories_to_check = [directory_path]
            while directories_to_check:
                directory = directories_to_check.pop()
                children = coerce_list(self.backend.get_local_children(directory))
                held_children = self._get_holds_dict((child.server_path.lower() for child in children))
                for child in children:
                    child_spl = child.server_path.lower()
                    if child.dir:
                        directories_to_check.append(child_spl)
                    held_child = held_children.get(child_spl)
                    if held_child is not None:
                        if held_child.size < 0:
                            temp_constraints.append((child_spl, directory_path))
                            continue
                        else:
                            can_delete = False
                            break
                    if child.size < 0:
                        continue
                    else:
                        can_delete = False
                        break

                if not can_delete:
                    blocks.add(directory_path)
                    break

            constraints.extend(temp_constraints)
            if directory_path not in known_entries:
                additional_entries[directory_path] = directory_delete

        return (additional_entries,
         blocks,
         constraints,
         [])
