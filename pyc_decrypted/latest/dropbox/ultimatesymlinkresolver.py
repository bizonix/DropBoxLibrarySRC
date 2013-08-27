#Embedded file name: dropbox/ultimatesymlinkresolver.py
from __future__ import absolute_import
import os
import stat
import collections
import itertools
import time
import socket
import errno
from dropbox.sync_engine_file_system.constants import FILE_TYPE_DIRECTORY, FILE_TYPE_POSIX_SYMLINK
from dropbox.trace import TRACE, unhandled_exc_handler
from dropbox.functions import absreadlink, desanitize
from dropbox.fastwalk_bridge import fastwalk
from dropbox.fileevents import FileEvents
import pprint

class UltimateSymlinkResolver(object):

    class FileNode(object):

        def __init__(self, abspath, inlinks = None):
            self.abspath = abspath
            self.inlinks = set() if inlinks is None else inlinks

        def __repr__(self):
            return 'FileNode(%r, inlinks=%r)' % (self.abspath, self.inlinks)

    class DirNode(object):

        def __init__(self, abspath, inlinks = None, child_symlinks = None):
            self.abspath = abspath
            self.inlinks = set() if inlinks is None else inlinks
            self.child_symlinks = set() if child_symlinks is None else child_symlinks

        def __repr__(self):
            return 'DirNode(%r, inlinks=%r, child_symlinks=%r)' % (self.abspath, self.inlinks, self.child_symlinks)

    class SymlinkNode(object):

        def __init__(self, abspath, abslink, outlinks = None, inlinks = None, parent_directories = None):
            self.abspath = abspath
            self.abslink = abslink
            self.outlinks = [] if outlinks is None else outlinks
            self.inlinks = set() if inlinks is None else inlinks
            self.parent_directories = set() if parent_directories is None else parent_directories

        def __repr__(self):
            return 'SymlinkNode(%r, %r, outlinks=%r, inlinks=%r, parent_directories=%r)' % (self.abspath,
             self.abslink,
             self.outlinks,
             self.inlinks,
             self.parent_directories)

    @staticmethod
    def test():
        serv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        oldtimeout = serv.gettimeout()
        serv.settimeout(0.2)
        start = time.time()
        while True:
            try:
                serv.connect('/.dbfseventsd')
            except:
                if time.time() - start > 1.0:
                    raise
            else:
                serv.settimeout(oldtimeout)
                break

        def realp(x):
            print x

        symlink_resolver = UltimateSymlinkResolver(log=realp)
        symlink_resolver.add_watch(u'/Applications')
        print pprint.pformat(symlink_resolver.nodes.values())
        linereader = serv.makefile()
        CREATE, RENAME, DELETE, UPDATE, STAT, EXCHANGE = range(6)
        while True:
            line = linereader.readline()
            if line == '':
                break
            line = line[:-1].decode('utf-8')
            print line
            if line == u'dropped':
                continue
            event, data = line.split('\t', 1)
            if event == u'update':
                ev = (UPDATE, desanitize(data))
            elif event == u'create':
                ev = (CREATE, desanitize(data))
            elif event == u'delete':
                ev = (DELETE, desanitize(data))
            elif event == u'stat':
                ev = (STAT, desanitize(data))
            elif event == 'rename':
                pathfrom, pathto = [ desanitize(a) for a in data.split('\t', 1) ]
                ev = (RENAME, pathfrom, pathto)
            elif event == 'exchange':
                pathfrom, pathto = [ desanitize(a) for a in data.split('\t', 1) ]
                ev = (EXCHANGE, pathfrom, pathto)
            if ev[0] == CREATE:
                symlink_resolver.file_created(ev[1])
            elif ev[0] == DELETE:
                symlink_resolver.file_deleted(ev[1])
            elif ev[0] == RENAME:
                if ev[1] != '':
                    symlink_resolver.file_deleted(ev[1])
                if ev[2] != '':
                    symlink_resolver.file_created(ev[2])
            print pprint.pformat(list(symlink_resolver.reverse_resolve_symlinks(ev[1])))
            try:
                print pprint.pformat(list(symlink_resolver.reverse_resolve_symlinks(ev[2])))
            except:
                pass

    def __init__(self, case_insensitive = True, debug = None, log = None):
        self.watchpoints = set()
        self.nodes = dict()
        self.symlink_roots = set()
        self.debug = debug
        self.log = log
        self.case_insensitive = case_insensitive

    def add_watch(self, path, recurse = FileEvents.RECURSE_ALL):
        if self.debug:
            assert path == os.path.normpath(path), 'Need normal path'
            assert os.path.isabs(path), 'Need absolute path'
        if self.case_insensitive:
            path = path.lower()
        self.watchpoints.add(path)
        self.recurse = recurse
        self.add_node(path)
        if self.debug:
            self.debug(pprint.pformat(self.nodes.values()))

    def get_watches(self):
        return frozenset(self.watchpoints)

    def remove_watch(self, dir):
        pass

    def add_node(self, abspath, parent_symlink = None):
        if self.debug:
            assert os.path.isabs(abspath)
            assert abspath == os.path.normpath(abspath)
            assert abspath not in self.nodes
        if os.path.islink(abspath):
            try:
                l = absreadlink(abspath)
                if self.case_insensitive:
                    l = l.lower()
            except (UnicodeDecodeError, OSError):
                pass
            else:
                self.add_symlink(abspath, l, parent_symlink=parent_symlink)

        else:
            if os.path.isdir(abspath):
                self.nodes[abspath] = UltimateSymlinkResolver.DirNode(abspath)
            else:
                self.nodes[abspath] = UltimateSymlinkResolver.FileNode(abspath)
            if parent_symlink is not None:
                parentnode, outlinkidx = parent_symlink
                assert type(self.nodes[parentnode]) is UltimateSymlinkResolver.SymlinkNode
                self.nodes[abspath].inlinks.add((outlinkidx, parentnode))
                self.nodes[parentnode].outlinks[outlinkidx] = (self.nodes[parentnode].outlinks[outlinkidx][0], abspath)
            if type(self.nodes[abspath]) is UltimateSymlinkResolver.DirNode and self.is_symlink_root(abspath):
                self.symlink_roots.add(abspath)
                self.add_children(abspath)

    def forward_resolve_symlink(self, symlinkpath):
        node = self.nodes[symlinkpath]
        seen = set()
        assert type(node) is UltimateSymlinkResolver.SymlinkNode
        while type(node) is UltimateSymlinkResolver.SymlinkNode:
            if node.abspath in seen:
                return
            seen.add(node.abspath)
            if node.outlinks[-1][1] is None:
                return
            node = self.nodes[node.outlinks[-1][1]]

        return node.abspath

    def is_symlink_root(self, dirpath):
        assert type(self.nodes[dirpath]) is UltimateSymlinkResolver.DirNode
        if dirpath in self.watchpoints:
            return True
        to_explore = collections.deque((parentnode for outlinkidx, parentnode in self.nodes[dirpath].inlinks if outlinkidx == len(self.nodes[parentnode].outlinks) - 1))
        while to_explore:
            toexp = to_explore.popleft()
            assert type(self.nodes[toexp]) is UltimateSymlinkResolver.SymlinkNode
            if self.nodes[toexp].parent_directories:
                return True
            for outlinkidx, parentnode in self.nodes[toexp].inlinks:
                if outlinkidx == len(self.nodes[parentnode].outlinks) - 1:
                    to_explore.append(parentnode)

        return False

    def add_children(self, abspath):
        if self.log:
            self.log('IN add_children(%r)' % abspath)
        assert type(self.nodes[abspath]) is UltimateSymlinkResolver.DirNode
        if abspath == u'/':
            return
        if self.recurse == FileEvents.RECURSE_NONE:
            return

        def tracer(dir_name):
            TRACE('Error in ultimate symlink resolver for dir: %r', dir_name)

        try:
            _iterator = fastwalk(abspath, follow_symlinks=False, on_explore_error=tracer)
            for dir, ents in _iterator:
                for dirent in ents:
                    try:
                        if dirent.type == FILE_TYPE_DIRECTORY and self.recurse == FileEvents.RECURSE_ONE:
                            continue
                        if dirent.type == FILE_TYPE_POSIX_SYMLINK:
                            fp = dirent.fullpath
                            if self.case_insensitive:
                                fp = fp.lower()
                            if fp not in self.nodes:
                                try:
                                    l = absreadlink(fp)
                                    if self.case_insensitive:
                                        l = l.lower()
                                except (UnicodeDecodeError, OSError):
                                    pass
                                else:
                                    self.add_symlink(fp, l, parent_directory=abspath)

                            else:
                                self.nodes[abspath].child_symlinks.add(fp)
                                self.nodes[fp].parent_directories.add(abspath)
                    except:
                        unhandled_exc_handler()

                if self.recurse == FileEvents.RECURSE_ONE:
                    break

        except Exception:
            unhandled_exc_handler()

        if self.log:
            self.log('OUT add_children(%r)' % abspath)

    def add_symlink(self, abspath, linkpath, parent_symlink = None, parent_directory = None):
        if self.log:
            self.log('IN add_symlink(%r, %r, parent_symlink=%r, parent_directory=%r)' % (abspath,
             linkpath,
             parent_symlink,
             parent_directory))
        if self.debug:
            assert os.path.isabs(abspath) and os.path.isabs(linkpath)
            assert abspath == os.path.normpath(abspath) and linkpath == os.path.normpath(linkpath)
            assert abspath not in self.nodes
        components = []
        op = linkpath
        while op != u'/':
            components.append(op)
            op = os.path.dirname(op)

        components.append(u'/')
        components.reverse()
        self.nodes[abspath] = UltimateSymlinkResolver.SymlinkNode(abspath, linkpath)
        self.nodes[abspath].outlinks = [ (comp, None) for comp in components ]
        if parent_symlink is not None:
            parentnode, outlinkidx = parent_symlink
            self.nodes[abspath].inlinks.add((outlinkidx, parentnode))
            self.nodes[parentnode].outlinks[outlinkidx] = (self.nodes[parentnode].outlinks[outlinkidx][0], abspath)
        if parent_directory is not None:
            self.nodes[abspath].parent_directories.add(parent_directory)
            self.nodes[parent_directory].child_symlinks.add(abspath)
        self.add_components(self.nodes[abspath])
        if callable(self.log):
            self.log('OUT add_symlink(%r, %r, parent_symlink=%r, parent_directory=%r)' % (abspath,
             linkpath,
             parent_symlink,
             parent_directory))

    def add_components(self, node, startat = 0):
        if self.log:
            self.log('IN add_components(%s, startat=%r)' % (node.abspath, startat))
        for i in range(startat, len(node.outlinks)):
            accessat = self.access_at(node, i)
            if not accessat:
                break
            if accessat not in self.nodes:
                self.add_node(accessat, parent_symlink=(node.abspath, i))
            else:
                self.nodes[accessat].inlinks.add((i, node.abspath))
                node.outlinks[i] = (node.outlinks[i][0], accessat)
                if type(self.nodes[accessat]) is UltimateSymlinkResolver.DirNode and accessat not in self.symlink_roots and self.is_symlink_root(accessat):
                    self.symlink_roots.add(accessat)
                    self.add_children(accessat)

        if self.log:
            self.log('OUT add_components(%s, startat=%r)' % (node.abspath, startat))

    def access_at(self, node, i):
        assert type(node) is UltimateSymlinkResolver.SymlinkNode
        if not i:
            accessat = node.outlinks[0][0]
        else:
            prev_node = self.nodes[node.outlinks[i - 1][1]]
            tizzipe = type(prev_node)
            if tizzipe is UltimateSymlinkResolver.SymlinkNode:
                accessat = self.forward_resolve_symlink(prev_node.abspath)
            elif tizzipe is UltimateSymlinkResolver.DirNode:
                accessat = prev_node.abspath
            else:
                accessat = prev_node.abspath
            if accessat:
                accessat = accessat + node.outlinks[i][0][len(node.outlinks[i - 1][0]):]
        if accessat and not os.path.lexists(accessat):
            accessat = None
        return accessat

    def is_under_watchpoint(self, path):
        if path in self.watchpoints:
            return True
        if self.recurse == FileEvents.RECURSE_ALL:
            return any((path.startswith(wp + u'/') for wp in self.watchpoints))
        if self.recurse == FileEvents.RECURSE_NONE:
            return any((path == wp + u'/' for wp in self.watchpoints))
        for wp in self.watchpoints:
            wp = wp + u'/'
            if path.startswith(wp):
                relpath = path[len(wp):]
                if os.path.dirname(relpath) == u'':
                    return True

        return False

    is_watched = is_under_watchpoint

    def discard_path(self, path):
        brokenset = set()
        while True:
            try:
                node = self.nodes[path]
            except KeyError:
                tocheck = path + '/'
                for node in self.nodes.itervalues():
                    if node.abspath.startswith(tocheck):
                        break
                else:
                    break

            tocheck = collections.deque()
            if type(node) is UltimateSymlinkResolver.SymlinkNode:
                for i, outlink in enumerate(node.outlinks):
                    if outlink[1] is None:
                        continue
                    self.nodes[outlink[1]].inlinks.remove((i, node.abspath))
                    tocheck.append(outlink[1])

                dest = node.outlinks[-1][1]
                if dest is not None and type(self.nodes[dest]) is UltimateSymlinkResolver.DirNode and dest in self.symlink_roots and not self.is_symlink_root(dest):
                    self.symlink_roots.remove(dest)
                    for child in self.nodes[dest].child_symlinks:
                        tocheck.append(child)
                        self.nodes[child].parent_directories.remove(dest)

                    self.nodes[dest].child_symlinks.clear()
                for pdir in node.parent_directories:
                    self.nodes[pdir].child_symlinks.remove(node.abspath)

            elif type(node) is UltimateSymlinkResolver.DirNode:
                for cdir in node.child_symlinks:
                    self.nodes[cdir].parent_directories.remove(node.abspath)
                    tocheck.append(cdir)

            for outlink_idx, node_abspath in node.inlinks:
                outlink = self.nodes[node_abspath].outlinks[outlink_idx]
                self.nodes[node_abspath].outlinks[outlink_idx] = (outlink[0], None)

            del self.nodes[node.abspath]
            self.watchpoints.discard(node.abspath)
            broken_outlinks = collections.deque(node.inlinks)
            while broken_outlinks:
                outlink_idx, node_abspath = broken_outlinks.popleft()
                brokenset.add(node_abspath)
                node = self.nodes[node_abspath]
                for i in range(outlink_idx + 1, len(node.outlinks)):
                    comp, outnode_abspath = node.outlinks[i]
                    if outnode_abspath is None:
                        continue
                    self.nodes[outnode_abspath].inlinks.remove((i, node_abspath))
                    tocheck.append(outnode_abspath)
                    node.outlinks[i] = (comp, None)

                broken_outlinks.extend(node.inlinks)

            while tocheck:
                try:
                    outnode = self.nodes[tocheck.popleft()]
                except KeyError:
                    continue

                if type(outnode) is UltimateSymlinkResolver.SymlinkNode:
                    if not outnode.inlinks and outnode.abspath not in self.watchpoints and not outnode.parent_directories:
                        tocheck2 = []
                        for i, outlink in enumerate(outnode.outlinks):
                            if outlink[1] is None:
                                continue
                            self.nodes[outlink[1]].inlinks.remove((i, outnode.abspath))
                            tocheck2.append(outlink[1])

                        dest = outnode.outlinks[-1][1]
                        if dest is not None and type(self.nodes[dest]) is UltimateSymlinkResolver.DirNode and dest in self.symlink_roots and not self.is_symlink_root(dest):
                            self.symlink_roots.remove(dest)
                            for child in self.nodes[dest].child_symlinks:
                                self.nodes[child].parent_directories.remove(dest)
                                tocheck2.append(child)

                            self.nodes[dest].child_symlinks.clear()
                        tocheck.extendleft(reversed(tocheck2))
                        del self.nodes[outnode.abspath]
                elif type(outnode) is UltimateSymlinkResolver.DirNode:
                    if not outnode.inlinks and outnode.abspath not in self.watchpoints:
                        tocheck2 = []
                        for cdir in outnode.child_symlinks:
                            self.nodes[cdir].parent_directories.remove(outnode.abspath)
                            tocheck2.append(cdir)

                        tocheck.extendleft(reversed(tocheck2))
                        del self.nodes[outnode.abspath]
                else:
                    assert type(outnode) is UltimateSymlinkResolver.FileNode
                    if not outnode.inlinks:
                        del self.nodes[outnode.abspath]
                        assert outnode.abspath not in self.watchpoints

        return brokenset

    def is_working_symlink(self, symlinkpath):
        assert type(self.nodes[symlinkpath]) is UltimateSymlinkResolver.SymlinkNode
        return all((outlink[1] is not None for outlink in self.nodes[symlinkpath].outlinks))

    def restore_link(self, path):
        torestore = collections.deque()
        for node in self.nodes.itervalues():
            if type(node) is not UltimateSymlinkResolver.SymlinkNode:
                continue
            for i, outlink in enumerate(node.outlinks):
                if not outlink[1]:
                    if self.access_at(node, i) == path:
                        torestore.append((node, i))
                    break

            continue

        fixedset = set()
        while torestore:
            node, i = torestore.popleft()
            assert type(node) is UltimateSymlinkResolver.SymlinkNode
            if self.debug:
                self.debug('Fixing symlink %s child %s' % (node.abspath, node.outlinks[i][0]))
            self.add_components(node, i)
            if self.is_working_symlink(node.abspath):
                fixedset.add(node.abspath)
            if all((outlink[1] for outlink in node.outlinks)):
                torestore.extend(((self.nodes[inlink[1]], inlink[0] + 1) for inlink in node.inlinks if inlink[0] + 1 < len(self.nodes[inlink[1]].outlinks)))

        return fixedset

    def file_deleted(self, path):
        if self.case_insensitive:
            path = path.lower()
        ret = self.discard_path(path)
        if self.debug:
            self.debug(pprint.pformat(self.nodes.values()))
        return ret

    def file_created(self, path):
        if self.case_insensitive:
            path = path.lower()
        toret = self.restore_link(path)
        if path not in self.nodes:
            numps = sum((1 for p in self.symlink_roots if len(path) > len(p) and path[len(p)] == u'/' and path.startswith(p)))
            if numps:
                try:
                    l = absreadlink(path)
                    if self.case_insensitive:
                        l = l.lower()
                except (UnicodeDecodeError, OSError):
                    pass
                else:
                    if numps != 1:
                        parents = iter([ p for p in self.symlink_roots if len(path) > len(p) and path[len(p)] == u'/' and path.startswith(p) ])
                        self.add_symlink(path, l, parent_directory=parents.next())
                        node = self.nodes[path]
                        for prent in parents:
                            self.nodes[prent].child_symlinks.add(node.abspath)
                            node.parent_directories.add(prent)

                    else:
                        for p in self.symlink_roots:
                            if len(path) > len(p) and path[len(p)] == u'/' and path.startswith(p):
                                self.add_symlink(path, l, parent_directory=p)
                                break

        if self.debug:
            self.debug(pprint.pformat(self.nodes.values()))
        return toret

    def reverse_resolve_symlinks(self, path):
        nodeq = collections.deque(((path, path.lower() if self.case_insensitive else path, set()),))
        while nodeq:
            path, cmppath, visited = nodeq.popleft()
            notcirc = True
            for node in self.nodes.itervalues():
                if type(node) is UltimateSymlinkResolver.DirNode:
                    if cmppath.startswith(node.abspath + '/'):
                        relpath = path[len(node.abspath):]
                    elif cmppath == node.abspath:
                        relpath = None
                    else:
                        continue
                elif type(node) is UltimateSymlinkResolver.FileNode and cmppath == node.abspath:
                    relpath = None
                else:
                    continue
                if node.abspath in visited:
                    notcirc = False
                    continue
                v_copy = visited.copy()
                v_copy.add(node.abspath)
                subnodeq = [node]
                count = 0
                while subnodeq:
                    node1 = subnodeq.pop(0)
                    if not node1.inlinks:
                        count += 1
                    else:
                        for outlinkidx, symlinkpath in node1.inlinks:
                            parentnode = self.nodes[symlinkpath]
                            if outlinkidx != len(parentnode.outlinks) - 1:
                                continue
                            nextp = parentnode.abspath if relpath is None else parentnode.abspath + relpath
                            nodeq.append((nextp, nextp.lower() if self.case_insensitive else nextp, v_copy if count == 0 else v_copy.copy()))
                            subnodeq.append(parentnode)

            if notcirc and self.is_watched(cmppath):
                yield path
