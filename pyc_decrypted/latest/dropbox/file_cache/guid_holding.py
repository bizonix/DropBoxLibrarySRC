#Embedded file name: dropbox/file_cache/guid_holding.py
from collections import defaultdict

class GUIDHoldingLogic(object):

    def __init__(self, storage, backend):
        self.storage = storage
        self.backend = backend

    def add_to_held(self, details):
        forward_entries = self.backend.entries_by_local_dropbox_guid_batch([ d.guid for d in details if hasattr(d, 'guid') ])
        guid_to_sp = dict(((row['local_guid'], row['server_path'].lower()) for row in forward_entries))
        self.storage.add_guid_references(details, guid_to_sp)

    def delete_from_held(self, server_paths):
        self.storage.delete_guid_references(server_paths)

    def _path_for_guid(self, guid):
        list_of_details = list(self.backend.entries_by_local_dropbox_guid_batch([guid]))
        if list_of_details:
            return list_of_details[0]['server_path'].lower()

    def backward_traverse(self, server_path, include_constraints = False):
        visited = set()
        stack = [server_path]
        constraints = []
        unique_constraints = []
        while stack:
            server_path = stack.pop()
            visited.add(server_path)
            ancestors = self.storage.get_backward_references(server_path)
            if include_constraints and len(ancestors) > 1:
                unique_constraints.append([ d.server_path.lower() for d in ancestors ])
            for d in ancestors:
                spl = d.server_path.lower()
                if include_constraints:
                    constraints.append((server_path, spl))
                if spl in visited:
                    continue
                stack.append(spl)

        if include_constraints:
            return (visited, constraints, unique_constraints)
        return visited

    def forward_traverse(self, details):
        cur_deets = details
        cur_sp = cur_deets.server_path.lower()
        visited = [cur_deets]
        visited_sp = [cur_sp]
        while True:
            dependent_path = self._path_for_guid(cur_deets.guid) if hasattr(cur_deets, 'guid') else None
            next_deets = self.storage.get_holds([dependent_path]) if dependent_path else None
            next_deets = next_deets[0] if next_deets else None
            if next_deets:
                next_sp = next_deets.server_path.lower()
                if next_sp in visited_sp:
                    return (next_deets, visited, visited_sp)
                visited_sp.append(next_sp)
                visited.append(next_deets)
                cur_deets = next_deets
                cur_sp = next_sp
            else:
                return (cur_deets, None, None)

    def generate_constraints(self, sp_to_details):
        known_entries = set(sp_to_details.keys())
        additional_entries = {}
        blocks = set()
        constraints = []
        edited_details_by_guid = defaultdict(set)
        for spl, details in sp_to_details.iteritems():
            if details.size >= 0 and hasattr(details, 'guid'):
                edited_details_by_guid[details.guid].add(details)

        unique_constraints = [ list((d.server_path for d in set_of_details)) for set_of_details in edited_details_by_guid.values() if len(set_of_details) > 1 ]

        def add_additional_entries(entries):
            for deets in entries:
                spl = deets.server_path.lower()
                if spl not in known_entries:
                    additional_entries[spl] = deets

        sp_to_deets_queue = dict(sp_to_details)
        while sp_to_deets_queue:

            def pop_from_queue(server_paths):
                for spl in server_paths:
                    sp_to_deets_queue.pop(spl, None)

            spl, details = sp_to_deets_queue.popitem()
            root_deets, cycle, cycle_sp = self.forward_traverse(details)
            root_sp = root_deets.server_path.lower()
            if not cycle:
                is_free = False
                next_path = self._path_for_guid(root_deets.guid) if hasattr(root_deets, 'guid') else None
                deets = self.storage.get_holds([next_path]) if next_path else None
                dep_guid = deets[0].guid if deets else None
                if dep_guid is None:
                    if next_path is None:
                        is_free = True
                    else:
                        is_free = False
                elif next_path == root_sp:
                    is_free = True
                if is_free:
                    visited, temp_constraints, temp_unique_constraints = self.backward_traverse(root_sp, include_constraints=True)
                    pop_from_queue(visited)
                    constraints.extend(temp_constraints)
                    unique_constraints.extend(temp_unique_constraints)
                    add_additional_entries(self.storage.get_holds(visited))
                else:
                    visited = self.backward_traverse(root_sp)
                    pop_from_queue(visited)
                    for spl in visited:
                        blocks.add(spl)

            else:
                visited = self.backward_traverse(root_sp)
                pop_from_queue(visited)
                for spl in visited:
                    if spl not in cycle_sp:
                        blocks.add(spl)

                for p1, p2 in zip(cycle_sp[0:-1], cycle_sp[1:]):
                    constraints.append((p1, p2))

                constraints.append((cycle_sp[-1], cycle_sp[0]))
                add_additional_entries(cycle)

        return (additional_entries,
         blocks,
         constraints,
         unique_constraints)
