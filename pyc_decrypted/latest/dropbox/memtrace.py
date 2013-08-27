#Embedded file name: dropbox/memtrace.py
import gc
import inspect
import sys
import types
from collections import Counter, defaultdict

def _typename(obj):
    return type(obj).__name__


def _safe_repr(obj):
    try:
        return ' '.join([_typename(obj), _short_repr(obj), str(id(obj))])
    except Exception:
        return '(unrepresentable)'


def _short_repr(obj):
    if isinstance(obj, (type,
     types.ModuleType,
     types.BuiltinMethodType,
     types.BuiltinFunctionType)):
        return obj.__name__
    if isinstance(obj, types.MethodType):
        try:
            if obj.__self__ is not None:
                return obj.__func__.__name__ + ' (bound)'
            return obj.__func__.__name__
        except AttributeError:
            if obj.im_self is not None:
                return obj.im_func.__name__ + ' (bound)'
            else:
                return obj.im_func.__name__

    if isinstance(obj, types.FrameType):
        return '%s:%s' % (obj.f_code.co_filename, obj.f_lineno)
    if isinstance(obj, (tuple,
     list,
     dict,
     set)):
        return '%d items' % len(obj)
    return repr(obj)[:40]


def snapshot(collect = True, extra_ignore = ()):
    if collect:
        gc.collect()
    return Counter((_typename(o) for o in gc.get_objects() if id(o) not in extra_ignore))


def get_extra_types(old_snapshot, cur_snapshot = None):
    if cur_snapshot is None:
        cur_snapshot = snapshot()
    return cur_snapshot - old_snapshot


def format_extra_types(snapshot):
    return '\n'.join(('%s: %d' % (type_name, count) for type_name, count in snapshot.iteritems()))


def snapshot_full(collect = True):
    if collect:
        gc.collect()
    type_dict = defaultdict(set)
    for o in gc.get_objects():
        type_dict[_typename(o)].add(id(o))

    return type_dict


def get_extra_objects(old_snapshot, cur_snapshot = None):
    if cur_snapshot is None:
        cur_snapshot = snapshot_full()
    extra_entries = {}
    for type_name, ids in cur_snapshot.iteritems():
        delta = ids - old_snapshot[type_name]
        if delta:
            extra_entries[type_name] = delta

    return extra_entries


def get_reference_chain(obj, max_depth = 20, extra_ignore = ()):
    queue = [obj]
    depth = {id(obj): 0}
    parent = {id(obj): None}
    ignore = set(extra_ignore)
    ignore.add(id(queue))
    ignore.add(id(depth))
    ignore.add(id(parent))
    ignore.add(id(ignore))
    ignore.add(id(extra_ignore))
    ignore.add(id(sys._getframe()))
    gc.collect()
    while queue:
        target = queue.pop()
        if inspect.ismodule(target) or inspect.isclass(target):
            chain = [target]
            while parent[id(target)] is not None and parent[id(target)] not in chain:
                target = parent[id(target)]
                chain.append(target)

            return chain
        cur_depth = depth[id(target)]
        if cur_depth < max_depth:
            referrers = gc.get_referrers(target)
            ignore.add(id(referrers))
            for source in referrers:
                if id(source) in ignore:
                    continue
                if id(source) not in depth:
                    depth[id(source)] = cur_depth + 1
                    parent[id(source)] = target
                    queue.append(source)
                    if len(depth) > 1000:
                        break

        if len(depth) > 1000:
            break

    return [obj]


def format_reference_chain(chain):
    return '\n'.join((' ' * i + _safe_repr(obj) for i, obj in enumerate(chain)))


def at(addrs):
    addr_to_obj = {}
    for o in gc.get_objects():
        if id(o) in addrs:
            addr_to_obj[id(o)] = o

    return [ addr_to_obj.get(a, None) for a in addrs ]


def _format_helper(objs, format_func, expanded_per_type = 3, ignored_types = (), extra_ignore = (), **kw):
    ret = []
    ignored = set(ignored_types)
    extra_ignore = set(extra_ignore)
    extra_ignore.add(id(extra_ignore))
    extra_ignore.add(id(sys._getframe()))
    for type_name, object_ids in objs.iteritems():
        if type_name in ignored:
            continue
        object_ids = list(object_ids)
        added = 0
        idx = 0
        while added < expanded_per_type and idx < len(object_ids):
            try:
                if object_ids[idx] in extra_ignore:
                    continue
                real_object = at([object_ids[idx]])
                try:
                    if real_object[0] is None:
                        continue
                    extra_ignore.add(id(real_object))
                    ret.append(format_func(real_object[0], extra_ignore=extra_ignore, **kw))
                finally:
                    del real_object

                added += 1
            finally:
                idx += 1

        more = max(0, len(object_ids) - expanded_per_type)
        if more and added:
            ret.append('... %d more' % more)
        if added:
            ret.append('')

    return '\n'.join(ret)


def format_referrers_report(objs, expanded_per_type = 3, referrers = 6, ignored_types = (), extra_ignore = ()):
    extra_ignore = set(extra_ignore)
    extra_ignore.add(id(extra_ignore))
    extra_ignore.add(sys._getframe())
    return _format_helper(objs, format_referrers, expanded_per_type=expanded_per_type, referrers=referrers, ignored_types=ignored_types, extra_ignore=extra_ignore)


def format_reference_chain_report(objs, traces_per_type = 3, ignored_types = ()):

    def format_func(o, extra_ignore, **kw):
        return format_reference_chain(get_reference_chain(o, extra_ignore=extra_ignore))

    return _format_helper(objs, format_func, expanded_per_type=traces_per_type, ignored_types=ignored_types)


def format_referrers(obj, extra_ignore = (), referrers = 3):
    ret = [_safe_repr(obj)]
    extra_ignore = set(extra_ignore)
    extra_ignore.add(id(extra_ignore))
    extra_ignore.add(id(sys._getframe()))
    extra_ignore.add(id(ret))
    added = 0
    idx = 0
    candidates = gc.get_referrers(obj)
    extra_ignore.add(id(candidates))
    while added < referrers and idx < len(candidates):
        try:
            if id(candidates[idx]) in extra_ignore:
                continue
            ret.append(' ' + _safe_repr(candidates[idx]))
            added += 1
        finally:
            idx += 1

    return '\n'.join(ret)
