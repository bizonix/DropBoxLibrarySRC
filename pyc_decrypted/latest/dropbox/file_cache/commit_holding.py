#Embedded file name: dropbox/file_cache/commit_holding.py
from collections import defaultdict, deque

class CommitHoldingLogic(object):

    def __init__(self, storage, holding_logics):
        self.storage = storage
        self.logics = holding_logics
        self.logics_to_notify = {}
        for i, logic in enumerate(self.logics):
            self.logics_to_notify[logic] = self.logics[:i] + self.logics[i + 1:]

    def filter(self, details):
        self.storage.add_to_held(details)
        for logic in self.logics:
            logic.add_to_held(details)

        commits = dict(((d.server_path.lower(), d) for d in details))
        blocks = set()
        constraints = set()
        unique_constraints = []
        to_process = deque(((logic, commits) for logic in self.logics))
        while to_process:
            logic, sp_to_deets = to_process.popleft()
            cm, bl, cn, uniq = logic.generate_constraints(sp_to_deets)
            if cm:
                commits.update(cm)
                to_process.extend(((l, cm) for l in self.logics_to_notify[logic]))
            blocks.update(bl)
            constraints.update(cn)
            unique_constraints.extend(uniq)

        results = self._release_from_holding(commits, blocks, constraints, unique_constraints)
        for logic in self.logics:
            logic.delete_from_held(results.keys())

        self.storage.delete_from_held(results.keys())
        return results.values()

    def _release_from_holding(self, commits, blocks, constraints, unique_constraints):
        to_hold = []
        to_process = []
        precondition_to_holds = defaultdict(set)
        for precondition, hold in constraints:
            precondition_to_holds[precondition].add(hold)

        to_process = list(blocks)
        while to_process:
            hold = to_process.pop()
            to_hold.append(hold)
            to_process.extend((x for x in precondition_to_holds.get(hold, []) if x not in to_hold))

        for spl in to_hold:
            commits.pop(spl, None)

        best_size = [len(commits) + 1]
        best_holds = [None]

        def evaluate_unique_constraints(remaining_constraints, soln_so_far, holds_so_far):
            if len(holds_so_far) > best_size:
                return
            if len(soln_so_far) == len(unique_constraints):
                if len(holds_so_far) < best_size[0]:
                    best_size[0] = len(holds_so_far)
                    best_holds[0] = list(holds_so_far)
                return
            cur_constraint = remaining_constraints[0]
            for i in range(len(cur_constraint)):
                new_holds = []
                to_process = cur_constraint[:i] + cur_constraint[i + 1:]
                while to_process:
                    new_hold = to_process.pop()
                    new_holds.append(new_hold)
                    to_process.extend((x for x in precondition_to_holds.get(new_hold, []) if x not in new_holds))

                evaluate_unique_constraints(remaining_constraints[1:], soln_so_far + [i], holds_so_far + new_holds)

        evaluate_unique_constraints(unique_constraints, [], [])
        if best_holds[0]:
            for spl in best_holds[0]:
                commits.pop(spl, None)

        return commits
