#Embedded file name: dropbox/sync_engine/case_filter.py
import itertools
from dropbox.low_functions import identity
from dropbox.trace import TRACE

def case_filter(get_db_state, local_path_iter, exists, dirname, key = identity, handle_conflict = None):
    cases_will_be_committed = {}
    for order, deets in enumerate(local_path_iter):
        lp = key(deets)
        server_lp, server_size = get_db_state(lp)
        try:
            entry = cases_will_be_committed[server_lp]
        except KeyError:
            entry = [server_size, None, []]
            cases_will_be_committed[server_lp] = entry

        if server_lp == lp:
            entry[1] = (order, deets, None)
        else:
            entry[2].append((order, deets, None))

    batch_list = []
    for server_lp, entry in cases_will_be_committed.iteritems():
        exist_map = {}
        for deets in list(itertools.chain(() if not entry[1] else (entry[1][1],), (a[1] for a in entry[2]))):
            exist_map[deets] = exists(key(deets))

        old_case_exists = entry[0] >= 0 and (not entry[1] or exist_map[entry[1][1]])
        ignore_children = set()
        if old_case_exists:
            for order, deets, basename in entry[2]:
                if exist_map[deets] and handle_conflict:
                    us, them = key(deets), server_lp
                    assert us != them
                    while us != them:
                        old_us, old_them = us, them
                        us, them = dirname(us), dirname(them)

                    handle_conflict(old_us, old_them)
                ignore_children.add(key(deets))
                yield ('ignored', deets)

            if entry[1]:
                batch_list.append((entry[1][0], entry[1][1]))
        else:
            new_case_exists = False
            for order, deets, basename in entry[2]:
                if new_case_exists:
                    if exist_map[deets] and handle_conflict:
                        us, them = key(deets), new_case_exists
                        assert us != them
                        while us != them:
                            old_us, old_them = us, them
                            us, them = dirname(us), dirname(them)

                        handle_conflict(old_us, old_them)
                    ignore_children.add(key(deets))
                    yield ('ignored', deets)
                elif exist_map[deets]:
                    batch_list.append((order, deets))
                    new_case_exists = key(deets)
                else:
                    ignore_children.add(key(deets))
                    yield ('ignored', deets)

            if entry[1]:
                if not new_case_exists:
                    batch_list.append((entry[1][0], entry[1][1]))
                else:
                    ignore_children.add(key(entry[1][1]))
                    yield ('ignored', entry[1][1])

    batch_list.sort()
    for ent in batch_list:
        lp = key(ent[1])
        yield_this = True
        while True:
            _dirname = dirname(lp)
            if _dirname == lp:
                break
            if _dirname in ignore_children:
                yield_this = False
                break
            lp = _dirname

        if yield_this:
            yield ('watched', ent[1])
        else:
            TRACE('Ignoring %r (parent is ignored)', ent[1])
            yield ('ignored', ent[1])
