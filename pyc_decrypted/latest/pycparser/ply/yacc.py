#Embedded file name: pycparser/ply/yacc.py
__version__ = '3.4'
__tabversion__ = '3.2'
yaccdebug = 1
debug_file = 'parser.out'
tab_module = 'parsetab'
default_lr = 'LALR'
error_count = 3
yaccdevel = 0
resultlimit = 40
pickle_protocol = 0
import re, types, sys, os.path
if sys.version_info[0] < 3:

    def func_code(f):
        return f.func_code


else:

    def func_code(f):
        return f.__code__


try:
    MAXINT = sys.maxint
except AttributeError:
    MAXINT = sys.maxsize

def load_ply_lex():
    if sys.version_info[0] < 3:
        import lex
    else:
        import ply.lex as lex
    return lex


class PlyLogger(object):

    def __init__(self, f):
        self.f = f

    def debug(self, msg, *args, **kwargs):
        self.f.write(msg % args + '\n')

    info = debug

    def warning(self, msg, *args, **kwargs):
        self.f.write('WARNING: ' + msg % args + '\n')

    def error(self, msg, *args, **kwargs):
        self.f.write('ERROR: ' + msg % args + '\n')

    critical = debug


class NullLogger(object):

    def __getattribute__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self


class YaccError(Exception):
    pass


def format_result(r):
    repr_str = repr(r)
    if '\n' in repr_str:
        repr_str = repr(repr_str)
    if len(repr_str) > resultlimit:
        repr_str = repr_str[:resultlimit] + ' ...'
    result = '<%s @ 0x%x> (%s)' % (type(r).__name__, id(r), repr_str)
    return result


def format_stack_entry(r):
    repr_str = repr(r)
    if '\n' in repr_str:
        repr_str = repr(repr_str)
    if len(repr_str) < 16:
        return repr_str
    else:
        return '<%s @ 0x%x>' % (type(r).__name__, id(r))


class YaccSymbol():

    def __str__(self):
        return self.type

    def __repr__(self):
        return str(self)


class YaccProduction():

    def __init__(self, s, stack = None):
        self.slice = s
        self.stack = stack
        self.lexer = None
        self.parser = None

    def __getitem__(self, n):
        if n >= 0:
            return self.slice[n].value
        else:
            return self.stack[n].value

    def __setitem__(self, n, v):
        self.slice[n].value = v

    def __getslice__(self, i, j):
        return [ s.value for s in self.slice[i:j] ]

    def __len__(self):
        return len(self.slice)

    def lineno(self, n):
        return getattr(self.slice[n], 'lineno', 0)

    def set_lineno(self, n, lineno):
        self.slice[n].lineno = lineno

    def linespan(self, n):
        startline = getattr(self.slice[n], 'lineno', 0)
        endline = getattr(self.slice[n], 'endlineno', startline)
        return (startline, endline)

    def lexpos(self, n):
        return getattr(self.slice[n], 'lexpos', 0)

    def lexspan(self, n):
        startpos = getattr(self.slice[n], 'lexpos', 0)
        endpos = getattr(self.slice[n], 'endlexpos', startpos)
        return (startpos, endpos)

    def error(self):
        raise SyntaxError


class LRParser():

    def __init__(self, lrtab, errorf):
        self.productions = lrtab.lr_productions
        self.action = lrtab.lr_action
        self.goto = lrtab.lr_goto
        self.errorfunc = errorf

    def errok(self):
        self.errorok = 1

    def restart(self):
        del self.statestack[:]
        del self.symstack[:]
        sym = YaccSymbol()
        sym.type = '$end'
        self.symstack.append(sym)
        self.statestack.append(0)

    def parse(self, input = None, lexer = None, debug = 0, tracking = 0, tokenfunc = None):
        if debug or yaccdevel:
            if isinstance(debug, int):
                debug = PlyLogger(sys.stderr)
            return self.parsedebug(input, lexer, debug, tracking, tokenfunc)
        elif tracking:
            return self.parseopt(input, lexer, debug, tracking, tokenfunc)
        else:
            return self.parseopt_notrack(input, lexer, debug, tracking, tokenfunc)

    def parsedebug(self, input = None, lexer = None, debug = None, tracking = 0, tokenfunc = None):
        global token
        global errok
        global restart
        lookahead = None
        lookaheadstack = []
        actions = self.action
        goto = self.goto
        prod = self.productions
        pslice = YaccProduction(None)
        errorcount = 0
        debug.info('PLY: PARSE DEBUG START')
        if not lexer:
            lex = load_ply_lex()
            lexer = lex.lexer
        pslice.lexer = lexer
        pslice.parser = self
        if input is not None:
            lexer.input(input)
        if tokenfunc is None:
            get_token = lexer.token
        else:
            get_token = tokenfunc
        statestack = []
        self.statestack = statestack
        symstack = []
        self.symstack = symstack
        pslice.stack = symstack
        errtoken = None
        statestack.append(0)
        sym = YaccSymbol()
        sym.type = '$end'
        symstack.append(sym)
        state = 0
        while 1:
            debug.debug('')
            debug.debug('State  : %s', state)
            if not lookahead:
                if not lookaheadstack:
                    lookahead = get_token()
                else:
                    lookahead = lookaheadstack.pop()
                if not lookahead:
                    lookahead = YaccSymbol()
                    lookahead.type = '$end'
            debug.debug('Stack  : %s', ('%s . %s' % (' '.join([ xx.type for xx in symstack ][1:]), str(lookahead))).lstrip())
            ltype = lookahead.type
            t = actions[state].get(ltype)
            if t is not None:
                if t > 0:
                    statestack.append(t)
                    state = t
                    debug.debug('Action : Shift and goto state %s', t)
                    symstack.append(lookahead)
                    lookahead = None
                    if errorcount:
                        errorcount -= 1
                    continue
                if t < 0:
                    p = prod[-t]
                    pname = p.name
                    plen = p.len
                    sym = YaccSymbol()
                    sym.type = pname
                    sym.value = None
                    if plen:
                        debug.info('Action : Reduce rule [%s] with %s and goto state %d', p.str, '[' + ','.join([ format_stack_entry(_v.value) for _v in symstack[-plen:] ]) + ']', -t)
                    else:
                        debug.info('Action : Reduce rule [%s] with %s and goto state %d', p.str, [], -t)
                    if plen:
                        targ = symstack[-plen - 1:]
                        targ[0] = sym
                        if tracking:
                            t1 = targ[1]
                            sym.lineno = t1.lineno
                            sym.lexpos = t1.lexpos
                            t1 = targ[-1]
                            sym.endlineno = getattr(t1, 'endlineno', t1.lineno)
                            sym.endlexpos = getattr(t1, 'endlexpos', t1.lexpos)
                        pslice.slice = targ
                        try:
                            del symstack[-plen:]
                            del statestack[-plen:]
                            p.callable(pslice)
                            debug.info('Result : %s', format_result(pslice[0]))
                            symstack.append(sym)
                            state = goto[statestack[-1]][pname]
                            statestack.append(state)
                        except SyntaxError:
                            lookaheadstack.append(lookahead)
                            symstack.pop()
                            statestack.pop()
                            state = statestack[-1]
                            sym.type = 'error'
                            lookahead = sym
                            errorcount = error_count
                            self.errorok = 0

                        continue
                    else:
                        if tracking:
                            sym.lineno = lexer.lineno
                            sym.lexpos = lexer.lexpos
                        targ = [sym]
                        pslice.slice = targ
                        try:
                            p.callable(pslice)
                            debug.info('Result : %s', format_result(pslice[0]))
                            symstack.append(sym)
                            state = goto[statestack[-1]][pname]
                            statestack.append(state)
                        except SyntaxError:
                            lookaheadstack.append(lookahead)
                            symstack.pop()
                            statestack.pop()
                            state = statestack[-1]
                            sym.type = 'error'
                            lookahead = sym
                            errorcount = error_count
                            self.errorok = 0

                        continue
                if t == 0:
                    n = symstack[-1]
                    result = getattr(n, 'value', None)
                    debug.info('Done   : Returning %s', format_result(result))
                    debug.info('PLY: PARSE DEBUG END')
                    return result
            if t == None:
                debug.error('Error  : %s', ('%s . %s' % (' '.join([ xx.type for xx in symstack ][1:]), str(lookahead))).lstrip())
                if errorcount == 0 or self.errorok:
                    errorcount = error_count
                    self.errorok = 0
                    errtoken = lookahead
                    if errtoken.type == '$end':
                        errtoken = None
                    if self.errorfunc:
                        errok = self.errok
                        token = get_token
                        restart = self.restart
                        if errtoken and not hasattr(errtoken, 'lexer'):
                            errtoken.lexer = lexer
                        tok = self.errorfunc(errtoken)
                        del errok
                        del token
                        del restart
                        if self.errorok:
                            lookahead = tok
                            errtoken = None
                            continue
                    elif errtoken:
                        if hasattr(errtoken, 'lineno'):
                            lineno = lookahead.lineno
                        else:
                            lineno = 0
                        if lineno:
                            sys.stderr.write('yacc: Syntax error at line %d, token=%s\n' % (lineno, errtoken.type))
                        else:
                            sys.stderr.write('yacc: Syntax error, token=%s' % errtoken.type)
                    else:
                        sys.stderr.write('yacc: Parse error in input. EOF\n')
                        return
                else:
                    errorcount = error_count
                if len(statestack) <= 1 and lookahead.type != '$end':
                    lookahead = None
                    errtoken = None
                    state = 0
                    del lookaheadstack[:]
                    continue
                if lookahead.type == '$end':
                    return
                if lookahead.type != 'error':
                    sym = symstack[-1]
                    if sym.type == 'error':
                        lookahead = None
                        continue
                    t = YaccSymbol()
                    t.type = 'error'
                    if hasattr(lookahead, 'lineno'):
                        t.lineno = lookahead.lineno
                    t.value = lookahead
                    lookaheadstack.append(lookahead)
                    lookahead = t
                else:
                    symstack.pop()
                    statestack.pop()
                    state = statestack[-1]
                continue
            raise RuntimeError('yacc: internal parser error!!!\n')

    def parseopt(self, input = None, lexer = None, debug = 0, tracking = 0, tokenfunc = None):
        global token
        global errok
        global restart
        lookahead = None
        lookaheadstack = []
        actions = self.action
        goto = self.goto
        prod = self.productions
        pslice = YaccProduction(None)
        errorcount = 0
        if not lexer:
            lex = load_ply_lex()
            lexer = lex.lexer
        pslice.lexer = lexer
        pslice.parser = self
        if input is not None:
            lexer.input(input)
        if tokenfunc is None:
            get_token = lexer.token
        else:
            get_token = tokenfunc
        statestack = []
        self.statestack = statestack
        symstack = []
        self.symstack = symstack
        pslice.stack = symstack
        errtoken = None
        statestack.append(0)
        sym = YaccSymbol()
        sym.type = '$end'
        symstack.append(sym)
        state = 0
        while 1:
            if not lookahead:
                if not lookaheadstack:
                    lookahead = get_token()
                else:
                    lookahead = lookaheadstack.pop()
                if not lookahead:
                    lookahead = YaccSymbol()
                    lookahead.type = '$end'
            ltype = lookahead.type
            t = actions[state].get(ltype)
            if t is not None:
                if t > 0:
                    statestack.append(t)
                    state = t
                    symstack.append(lookahead)
                    lookahead = None
                    if errorcount:
                        errorcount -= 1
                    continue
                if t < 0:
                    p = prod[-t]
                    pname = p.name
                    plen = p.len
                    sym = YaccSymbol()
                    sym.type = pname
                    sym.value = None
                    if plen:
                        targ = symstack[-plen - 1:]
                        targ[0] = sym
                        if tracking:
                            t1 = targ[1]
                            sym.lineno = t1.lineno
                            sym.lexpos = t1.lexpos
                            t1 = targ[-1]
                            sym.endlineno = getattr(t1, 'endlineno', t1.lineno)
                            sym.endlexpos = getattr(t1, 'endlexpos', t1.lexpos)
                        pslice.slice = targ
                        try:
                            del symstack[-plen:]
                            del statestack[-plen:]
                            p.callable(pslice)
                            symstack.append(sym)
                            state = goto[statestack[-1]][pname]
                            statestack.append(state)
                        except SyntaxError:
                            lookaheadstack.append(lookahead)
                            symstack.pop()
                            statestack.pop()
                            state = statestack[-1]
                            sym.type = 'error'
                            lookahead = sym
                            errorcount = error_count
                            self.errorok = 0

                        continue
                    else:
                        if tracking:
                            sym.lineno = lexer.lineno
                            sym.lexpos = lexer.lexpos
                        targ = [sym]
                        pslice.slice = targ
                        try:
                            p.callable(pslice)
                            symstack.append(sym)
                            state = goto[statestack[-1]][pname]
                            statestack.append(state)
                        except SyntaxError:
                            lookaheadstack.append(lookahead)
                            symstack.pop()
                            statestack.pop()
                            state = statestack[-1]
                            sym.type = 'error'
                            lookahead = sym
                            errorcount = error_count
                            self.errorok = 0

                        continue
                if t == 0:
                    n = symstack[-1]
                    return getattr(n, 'value', None)
            if t == None:
                if errorcount == 0 or self.errorok:
                    errorcount = error_count
                    self.errorok = 0
                    errtoken = lookahead
                    if errtoken.type == '$end':
                        errtoken = None
                    if self.errorfunc:
                        errok = self.errok
                        token = get_token
                        restart = self.restart
                        if errtoken and not hasattr(errtoken, 'lexer'):
                            errtoken.lexer = lexer
                        tok = self.errorfunc(errtoken)
                        del errok
                        del token
                        del restart
                        if self.errorok:
                            lookahead = tok
                            errtoken = None
                            continue
                    elif errtoken:
                        if hasattr(errtoken, 'lineno'):
                            lineno = lookahead.lineno
                        else:
                            lineno = 0
                        if lineno:
                            sys.stderr.write('yacc: Syntax error at line %d, token=%s\n' % (lineno, errtoken.type))
                        else:
                            sys.stderr.write('yacc: Syntax error, token=%s' % errtoken.type)
                    else:
                        sys.stderr.write('yacc: Parse error in input. EOF\n')
                        return
                else:
                    errorcount = error_count
                if len(statestack) <= 1 and lookahead.type != '$end':
                    lookahead = None
                    errtoken = None
                    state = 0
                    del lookaheadstack[:]
                    continue
                if lookahead.type == '$end':
                    return
                if lookahead.type != 'error':
                    sym = symstack[-1]
                    if sym.type == 'error':
                        lookahead = None
                        continue
                    t = YaccSymbol()
                    t.type = 'error'
                    if hasattr(lookahead, 'lineno'):
                        t.lineno = lookahead.lineno
                    t.value = lookahead
                    lookaheadstack.append(lookahead)
                    lookahead = t
                else:
                    symstack.pop()
                    statestack.pop()
                    state = statestack[-1]
                continue
            raise RuntimeError('yacc: internal parser error!!!\n')

    def parseopt_notrack(self, input = None, lexer = None, debug = 0, tracking = 0, tokenfunc = None):
        global token
        global errok
        global restart
        lookahead = None
        lookaheadstack = []
        actions = self.action
        goto = self.goto
        prod = self.productions
        pslice = YaccProduction(None)
        errorcount = 0
        if not lexer:
            lex = load_ply_lex()
            lexer = lex.lexer
        pslice.lexer = lexer
        pslice.parser = self
        if input is not None:
            lexer.input(input)
        if tokenfunc is None:
            get_token = lexer.token
        else:
            get_token = tokenfunc
        statestack = []
        self.statestack = statestack
        symstack = []
        self.symstack = symstack
        pslice.stack = symstack
        errtoken = None
        statestack.append(0)
        sym = YaccSymbol()
        sym.type = '$end'
        symstack.append(sym)
        state = 0
        while 1:
            if not lookahead:
                if not lookaheadstack:
                    lookahead = get_token()
                else:
                    lookahead = lookaheadstack.pop()
                if not lookahead:
                    lookahead = YaccSymbol()
                    lookahead.type = '$end'
            ltype = lookahead.type
            t = actions[state].get(ltype)
            if t is not None:
                if t > 0:
                    statestack.append(t)
                    state = t
                    symstack.append(lookahead)
                    lookahead = None
                    if errorcount:
                        errorcount -= 1
                    continue
                if t < 0:
                    p = prod[-t]
                    pname = p.name
                    plen = p.len
                    sym = YaccSymbol()
                    sym.type = pname
                    sym.value = None
                    if plen:
                        targ = symstack[-plen - 1:]
                        targ[0] = sym
                        pslice.slice = targ
                        try:
                            del symstack[-plen:]
                            del statestack[-plen:]
                            p.callable(pslice)
                            symstack.append(sym)
                            state = goto[statestack[-1]][pname]
                            statestack.append(state)
                        except SyntaxError:
                            lookaheadstack.append(lookahead)
                            symstack.pop()
                            statestack.pop()
                            state = statestack[-1]
                            sym.type = 'error'
                            lookahead = sym
                            errorcount = error_count
                            self.errorok = 0

                        continue
                    else:
                        targ = [sym]
                        pslice.slice = targ
                        try:
                            p.callable(pslice)
                            symstack.append(sym)
                            state = goto[statestack[-1]][pname]
                            statestack.append(state)
                        except SyntaxError:
                            lookaheadstack.append(lookahead)
                            symstack.pop()
                            statestack.pop()
                            state = statestack[-1]
                            sym.type = 'error'
                            lookahead = sym
                            errorcount = error_count
                            self.errorok = 0

                        continue
                if t == 0:
                    n = symstack[-1]
                    return getattr(n, 'value', None)
            if t == None:
                if errorcount == 0 or self.errorok:
                    errorcount = error_count
                    self.errorok = 0
                    errtoken = lookahead
                    if errtoken.type == '$end':
                        errtoken = None
                    if self.errorfunc:
                        errok = self.errok
                        token = get_token
                        restart = self.restart
                        if errtoken and not hasattr(errtoken, 'lexer'):
                            errtoken.lexer = lexer
                        tok = self.errorfunc(errtoken)
                        del errok
                        del token
                        del restart
                        if self.errorok:
                            lookahead = tok
                            errtoken = None
                            continue
                    elif errtoken:
                        if hasattr(errtoken, 'lineno'):
                            lineno = lookahead.lineno
                        else:
                            lineno = 0
                        if lineno:
                            sys.stderr.write('yacc: Syntax error at line %d, token=%s\n' % (lineno, errtoken.type))
                        else:
                            sys.stderr.write('yacc: Syntax error, token=%s' % errtoken.type)
                    else:
                        sys.stderr.write('yacc: Parse error in input. EOF\n')
                        return
                else:
                    errorcount = error_count
                if len(statestack) <= 1 and lookahead.type != '$end':
                    lookahead = None
                    errtoken = None
                    state = 0
                    del lookaheadstack[:]
                    continue
                if lookahead.type == '$end':
                    return
                if lookahead.type != 'error':
                    sym = symstack[-1]
                    if sym.type == 'error':
                        lookahead = None
                        continue
                    t = YaccSymbol()
                    t.type = 'error'
                    if hasattr(lookahead, 'lineno'):
                        t.lineno = lookahead.lineno
                    t.value = lookahead
                    lookaheadstack.append(lookahead)
                    lookahead = t
                else:
                    symstack.pop()
                    statestack.pop()
                    state = statestack[-1]
                continue
            raise RuntimeError('yacc: internal parser error!!!\n')


import re
_is_identifier = re.compile('^[a-zA-Z0-9_-]+$')

class Production(object):
    reduced = 0

    def __init__(self, number, name, prod, precedence = ('right', 0), func = None, file = '', line = 0):
        self.name = name
        self.prod = tuple(prod)
        self.number = number
        self.func = func
        self.callable = None
        self.file = file
        self.line = line
        self.prec = precedence
        self.len = len(self.prod)
        self.usyms = []
        for s in self.prod:
            if s not in self.usyms:
                self.usyms.append(s)

        self.lr_items = []
        self.lr_next = None
        if self.prod:
            self.str = '%s -> %s' % (self.name, ' '.join(self.prod))
        else:
            self.str = '%s -> <empty>' % self.name

    def __str__(self):
        return self.str

    def __repr__(self):
        return 'Production(' + str(self) + ')'

    def __len__(self):
        return len(self.prod)

    def __nonzero__(self):
        return 1

    def __getitem__(self, index):
        return self.prod[index]

    def lr_item(self, n):
        if n > len(self.prod):
            return
        p = LRItem(self, n)
        try:
            p.lr_after = Prodnames[p.prod[n + 1]]
        except (IndexError, KeyError):
            p.lr_after = []

        try:
            p.lr_before = p.prod[n - 1]
        except IndexError:
            p.lr_before = None

        return p

    def bind(self, pdict):
        if self.func:
            self.callable = pdict[self.func]


class MiniProduction(object):

    def __init__(self, str, name, len, func, file, line):
        self.name = name
        self.len = len
        self.func = func
        self.callable = None
        self.file = file
        self.line = line
        self.str = str

    def __str__(self):
        return self.str

    def __repr__(self):
        return 'MiniProduction(%s)' % self.str

    def bind(self, pdict):
        if self.func:
            self.callable = pdict[self.func]


class LRItem(object):

    def __init__(self, p, n):
        self.name = p.name
        self.prod = list(p.prod)
        self.number = p.number
        self.lr_index = n
        self.lookaheads = {}
        self.prod.insert(n, '.')
        self.prod = tuple(self.prod)
        self.len = len(self.prod)
        self.usyms = p.usyms

    def __str__(self):
        if self.prod:
            s = '%s -> %s' % (self.name, ' '.join(self.prod))
        else:
            s = '%s -> <empty>' % self.name
        return s

    def __repr__(self):
        return 'LRItem(' + str(self) + ')'


def rightmost_terminal(symbols, terminals):
    i = len(symbols) - 1
    while i >= 0:
        if symbols[i] in terminals:
            return symbols[i]
        i -= 1


class GrammarError(YaccError):
    pass


class Grammar(object):

    def __init__(self, terminals):
        self.Productions = [None]
        self.Prodnames = {}
        self.Prodmap = {}
        self.Terminals = {}
        for term in terminals:
            self.Terminals[term] = []

        self.Terminals['error'] = []
        self.Nonterminals = {}
        self.First = {}
        self.Follow = {}
        self.Precedence = {}
        self.UsedPrecedence = {}
        self.Start = None

    def __len__(self):
        return len(self.Productions)

    def __getitem__(self, index):
        return self.Productions[index]

    def set_precedence(self, term, assoc, level):
        assert self.Productions == [None], 'Must call set_precedence() before add_production()'
        if term in self.Precedence:
            raise GrammarError("Precedence already specified for terminal '%s'" % term)
        if assoc not in ('left', 'right', 'nonassoc'):
            raise GrammarError("Associativity must be one of 'left','right', or 'nonassoc'")
        self.Precedence[term] = (assoc, level)

    def add_production(self, prodname, syms, func = None, file = '', line = 0):
        if prodname in self.Terminals:
            raise GrammarError("%s:%d: Illegal rule name '%s'. Already defined as a token" % (file, line, prodname))
        if prodname == 'error':
            raise GrammarError("%s:%d: Illegal rule name '%s'. error is a reserved word" % (file, line, prodname))
        if not _is_identifier.match(prodname):
            raise GrammarError("%s:%d: Illegal rule name '%s'" % (file, line, prodname))
        for n, s in enumerate(syms):
            if s[0] in '\'"':
                try:
                    c = eval(s)
                    if len(c) > 1:
                        raise GrammarError("%s:%d: Literal token %s in rule '%s' may only be a single character" % (file,
                         line,
                         s,
                         prodname))
                    if c not in self.Terminals:
                        self.Terminals[c] = []
                    syms[n] = c
                    continue
                except SyntaxError:
                    pass

            if not _is_identifier.match(s) and s != '%prec':
                raise GrammarError("%s:%d: Illegal name '%s' in rule '%s'" % (file,
                 line,
                 s,
                 prodname))

        if '%prec' in syms:
            if syms[-1] == '%prec':
                raise GrammarError('%s:%d: Syntax error. Nothing follows %%prec' % (file, line))
            if syms[-2] != '%prec':
                raise GrammarError('%s:%d: Syntax error. %%prec can only appear at the end of a grammar rule' % (file, line))
            precname = syms[-1]
            prodprec = self.Precedence.get(precname, None)
            if not prodprec:
                raise GrammarError("%s:%d: Nothing known about the precedence of '%s'" % (file, line, precname))
            else:
                self.UsedPrecedence[precname] = 1
            del syms[-2:]
        else:
            precname = rightmost_terminal(syms, self.Terminals)
            prodprec = self.Precedence.get(precname, ('right', 0))
        map = '%s -> %s' % (prodname, syms)
        if map in self.Prodmap:
            m = self.Prodmap[map]
            raise GrammarError('%s:%d: Duplicate rule %s. ' % (file, line, m) + 'Previous definition at %s:%d' % (m.file, m.line))
        pnumber = len(self.Productions)
        if prodname not in self.Nonterminals:
            self.Nonterminals[prodname] = []
        for t in syms:
            if t in self.Terminals:
                self.Terminals[t].append(pnumber)
            else:
                if t not in self.Nonterminals:
                    self.Nonterminals[t] = []
                self.Nonterminals[t].append(pnumber)

        p = Production(pnumber, prodname, syms, prodprec, func, file, line)
        self.Productions.append(p)
        self.Prodmap[map] = p
        try:
            self.Prodnames[prodname].append(p)
        except KeyError:
            self.Prodnames[prodname] = [p]

        return 0

    def set_start(self, start = None):
        if not start:
            start = self.Productions[1].name
        if start not in self.Nonterminals:
            raise GrammarError('start symbol %s undefined' % start)
        self.Productions[0] = Production(0, "S'", [start])
        self.Nonterminals[start].append(0)
        self.Start = start

    def find_unreachable(self):

        def mark_reachable_from(s):
            if reachable[s]:
                return
            reachable[s] = 1
            for p in self.Prodnames.get(s, []):
                for r in p.prod:
                    mark_reachable_from(r)

        reachable = {}
        for s in list(self.Terminals) + list(self.Nonterminals):
            reachable[s] = 0

        mark_reachable_from(self.Productions[0].prod[0])
        return [ s for s in list(self.Nonterminals) if not reachable[s] ]

    def infinite_cycles(self):
        terminates = {}
        for t in self.Terminals:
            terminates[t] = 1

        terminates['$end'] = 1
        for n in self.Nonterminals:
            terminates[n] = 0

        while 1:
            some_change = 0
            for n, pl in self.Prodnames.items():
                for p in pl:
                    for s in p.prod:
                        if not terminates[s]:
                            p_terminates = 0
                            break
                    else:
                        p_terminates = 1

                    if p_terminates:
                        if not terminates[n]:
                            terminates[n] = 1
                            some_change = 1
                        break

            if not some_change:
                break

        infinite = []
        for s, term in terminates.items():
            if not term:
                if s not in self.Prodnames and s not in self.Terminals and s != 'error':
                    pass
                else:
                    infinite.append(s)

        return infinite

    def undefined_symbols(self):
        result = []
        for p in self.Productions:
            if not p:
                continue
            for s in p.prod:
                if s not in self.Prodnames and s not in self.Terminals and s != 'error':
                    result.append((s, p))

        return result

    def unused_terminals(self):
        unused_tok = []
        for s, v in self.Terminals.items():
            if s != 'error' and not v:
                unused_tok.append(s)

        return unused_tok

    def unused_rules(self):
        unused_prod = []
        for s, v in self.Nonterminals.items():
            if not v:
                p = self.Prodnames[s][0]
                unused_prod.append(p)

        return unused_prod

    def unused_precedence(self):
        unused = []
        for termname in self.Precedence:
            if not (termname in self.Terminals or termname in self.UsedPrecedence):
                unused.append((termname, self.Precedence[termname][0]))

        return unused

    def _first(self, beta):
        result = []
        for x in beta:
            x_produces_empty = 0
            for f in self.First[x]:
                if f == '<empty>':
                    x_produces_empty = 1
                elif f not in result:
                    result.append(f)

            if x_produces_empty:
                pass
            else:
                break
        else:
            result.append('<empty>')

        return result

    def compute_first(self):
        if self.First:
            return self.First
        for t in self.Terminals:
            self.First[t] = [t]

        self.First['$end'] = ['$end']
        for n in self.Nonterminals:
            self.First[n] = []

        while 1:
            some_change = 0
            for n in self.Nonterminals:
                for p in self.Prodnames[n]:
                    for f in self._first(p.prod):
                        if f not in self.First[n]:
                            self.First[n].append(f)
                            some_change = 1

            if not some_change:
                break

        return self.First

    def compute_follow(self, start = None):
        if self.Follow:
            return self.Follow
        if not self.First:
            self.compute_first()
        for k in self.Nonterminals:
            self.Follow[k] = []

        if not start:
            start = self.Productions[1].name
        self.Follow[start] = ['$end']
        while 1:
            didadd = 0
            for p in self.Productions[1:]:
                for i in range(len(p.prod)):
                    B = p.prod[i]
                    if B in self.Nonterminals:
                        fst = self._first(p.prod[i + 1:])
                        hasempty = 0
                        for f in fst:
                            if f != '<empty>' and f not in self.Follow[B]:
                                self.Follow[B].append(f)
                                didadd = 1
                            if f == '<empty>':
                                hasempty = 1

                        if hasempty or i == len(p.prod) - 1:
                            for f in self.Follow[p.name]:
                                if f not in self.Follow[B]:
                                    self.Follow[B].append(f)
                                    didadd = 1

            if not didadd:
                break

        return self.Follow

    def build_lritems(self):
        for p in self.Productions:
            lastlri = p
            i = 0
            lr_items = []
            while 1:
                if i > len(p):
                    lri = None
                else:
                    lri = LRItem(p, i)
                    try:
                        lri.lr_after = self.Prodnames[lri.prod[i + 1]]
                    except (IndexError, KeyError):
                        lri.lr_after = []

                    try:
                        lri.lr_before = lri.prod[i - 1]
                    except IndexError:
                        lri.lr_before = None

                lastlri.lr_next = lri
                if not lri:
                    break
                lr_items.append(lri)
                lastlri = lri
                i += 1

            p.lr_items = lr_items


class VersionError(YaccError):
    pass


class LRTable(object):

    def __init__(self):
        self.lr_action = None
        self.lr_goto = None
        self.lr_productions = None
        self.lr_method = None

    def read_table(self, module):
        if isinstance(module, types.ModuleType):
            parsetab = module
        elif sys.version_info[0] < 3:
            exec 'import %s as parsetab' % module
        else:
            env = {}
            exec ('import %s as parsetab' % module, env, env)
            parsetab = env['parsetab']
        if parsetab._tabversion != __tabversion__:
            raise VersionError('yacc table file version is out of date')
        self.lr_action = parsetab._lr_action
        self.lr_goto = parsetab._lr_goto
        self.lr_productions = []
        for p in parsetab._lr_productions:
            self.lr_productions.append(MiniProduction(*p))

        self.lr_method = parsetab._lr_method
        return parsetab._lr_signature

    def read_pickle(self, filename):
        try:
            import cPickle as pickle
        except ImportError:
            import pickle

        in_f = open(filename, 'rb')
        tabversion = pickle.load(in_f)
        if tabversion != __tabversion__:
            raise VersionError('yacc table file version is out of date')
        self.lr_method = pickle.load(in_f)
        signature = pickle.load(in_f)
        self.lr_action = pickle.load(in_f)
        self.lr_goto = pickle.load(in_f)
        productions = pickle.load(in_f)
        self.lr_productions = []
        for p in productions:
            self.lr_productions.append(MiniProduction(*p))

        in_f.close()
        return signature

    def bind_callables(self, pdict):
        for p in self.lr_productions:
            p.bind(pdict)


def digraph(X, R, FP):
    N = {}
    for x in X:
        N[x] = 0

    stack = []
    F = {}
    for x in X:
        if N[x] == 0:
            traverse(x, N, stack, F, X, R, FP)

    return F


def traverse(x, N, stack, F, X, R, FP):
    stack.append(x)
    d = len(stack)
    N[x] = d
    F[x] = FP(x)
    rel = R(x)
    for y in rel:
        if N[y] == 0:
            traverse(y, N, stack, F, X, R, FP)
        N[x] = min(N[x], N[y])
        for a in F.get(y, []):
            if a not in F[x]:
                F[x].append(a)

    if N[x] == d:
        N[stack[-1]] = MAXINT
        F[stack[-1]] = F[x]
        element = stack.pop()
        while element != x:
            N[stack[-1]] = MAXINT
            F[stack[-1]] = F[x]
            element = stack.pop()


class LALRError(YaccError):
    pass


class LRGeneratedTable(LRTable):

    def __init__(self, grammar, method = 'LALR', log = None):
        if method not in ('SLR', 'LALR'):
            raise LALRError('Unsupported method %s' % method)
        self.grammar = grammar
        self.lr_method = method
        if not log:
            log = NullLogger()
        self.log = log
        self.lr_action = {}
        self.lr_goto = {}
        self.lr_productions = grammar.Productions
        self.lr_goto_cache = {}
        self.lr0_cidhash = {}
        self._add_count = 0
        self.sr_conflict = 0
        self.rr_conflict = 0
        self.conflicts = []
        self.sr_conflicts = []
        self.rr_conflicts = []
        self.grammar.build_lritems()
        self.grammar.compute_first()
        self.grammar.compute_follow()
        self.lr_parse_table()

    def lr0_closure(self, I):
        self._add_count += 1
        J = I[:]
        didadd = 1
        while didadd:
            didadd = 0
            for j in J:
                for x in j.lr_after:
                    if getattr(x, 'lr0_added', 0) == self._add_count:
                        continue
                    J.append(x.lr_next)
                    x.lr0_added = self._add_count
                    didadd = 1

        return J

    def lr0_goto(self, I, x):
        g = self.lr_goto_cache.get((id(I), x), None)
        if g:
            return g
        s = self.lr_goto_cache.get(x, None)
        if not s:
            s = {}
            self.lr_goto_cache[x] = s
        gs = []
        for p in I:
            n = p.lr_next
            if n and n.lr_before == x:
                s1 = s.get(id(n), None)
                if not s1:
                    s1 = {}
                    s[id(n)] = s1
                gs.append(n)
                s = s1

        g = s.get('$end', None)
        if not g:
            if gs:
                g = self.lr0_closure(gs)
                s['$end'] = g
            else:
                s['$end'] = gs
        self.lr_goto_cache[id(I), x] = g
        return g

    def lr0_items(self):
        C = [self.lr0_closure([self.grammar.Productions[0].lr_next])]
        i = 0
        for I in C:
            self.lr0_cidhash[id(I)] = i
            i += 1

        i = 0
        while i < len(C):
            I = C[i]
            i += 1
            asyms = {}
            for ii in I:
                for s in ii.usyms:
                    asyms[s] = None

            for x in asyms:
                g = self.lr0_goto(I, x)
                if not g:
                    continue
                if id(g) in self.lr0_cidhash:
                    continue
                self.lr0_cidhash[id(g)] = len(C)
                C.append(g)

        return C

    def compute_nullable_nonterminals(self):
        nullable = {}
        num_nullable = 0
        while 1:
            for p in self.grammar.Productions[1:]:
                if p.len == 0:
                    nullable[p.name] = 1
                    continue
                for t in p.prod:
                    if t not in nullable:
                        break
                else:
                    nullable[p.name] = 1

            if len(nullable) == num_nullable:
                break
            num_nullable = len(nullable)

        return nullable

    def find_nonterminal_transitions(self, C):
        trans = []
        for state in range(len(C)):
            for p in C[state]:
                if p.lr_index < p.len - 1:
                    t = (state, p.prod[p.lr_index + 1])
                    if t[1] in self.grammar.Nonterminals:
                        if t not in trans:
                            trans.append(t)

            state = state + 1

        return trans

    def dr_relation(self, C, trans, nullable):
        dr_set = {}
        state, N = trans
        terms = []
        g = self.lr0_goto(C[state], N)
        for p in g:
            if p.lr_index < p.len - 1:
                a = p.prod[p.lr_index + 1]
                if a in self.grammar.Terminals:
                    if a not in terms:
                        terms.append(a)

        if state == 0 and N == self.grammar.Productions[0].prod[0]:
            terms.append('$end')
        return terms

    def reads_relation(self, C, trans, empty):
        rel = []
        state, N = trans
        g = self.lr0_goto(C[state], N)
        j = self.lr0_cidhash.get(id(g), -1)
        for p in g:
            if p.lr_index < p.len - 1:
                a = p.prod[p.lr_index + 1]
                if a in empty:
                    rel.append((j, a))

        return rel

    def compute_lookback_includes(self, C, trans, nullable):
        lookdict = {}
        includedict = {}
        dtrans = {}
        for t in trans:
            dtrans[t] = 1

        for state, N in trans:
            lookb = []
            includes = []
            for p in C[state]:
                if p.name != N:
                    continue
                lr_index = p.lr_index
                j = state
                while lr_index < p.len - 1:
                    lr_index = lr_index + 1
                    t = p.prod[lr_index]
                    if (j, t) in dtrans:
                        li = lr_index + 1
                        while li < p.len:
                            if p.prod[li] in self.grammar.Terminals:
                                break
                            if p.prod[li] not in nullable:
                                break
                            li = li + 1
                        else:
                            includes.append((j, t))

                    g = self.lr0_goto(C[j], t)
                    j = self.lr0_cidhash.get(id(g), -1)

                for r in C[j]:
                    if r.name != p.name:
                        continue
                    if r.len != p.len:
                        continue
                    i = 0
                    while i < r.lr_index:
                        if r.prod[i] != p.prod[i + 1]:
                            break
                        i = i + 1
                    else:
                        lookb.append((j, r))

            for i in includes:
                if i not in includedict:
                    includedict[i] = []
                includedict[i].append((state, N))

            lookdict[state, N] = lookb

        return (lookdict, includedict)

    def compute_read_sets(self, C, ntrans, nullable):
        FP = lambda x: self.dr_relation(C, x, nullable)
        R = lambda x: self.reads_relation(C, x, nullable)
        F = digraph(ntrans, R, FP)
        return F

    def compute_follow_sets(self, ntrans, readsets, inclsets):
        FP = lambda x: readsets[x]
        R = lambda x: inclsets.get(x, [])
        F = digraph(ntrans, R, FP)
        return F

    def add_lookaheads(self, lookbacks, followset):
        for trans, lb in lookbacks.items():
            for state, p in lb:
                if state not in p.lookaheads:
                    p.lookaheads[state] = []
                f = followset.get(trans, [])
                for a in f:
                    if a not in p.lookaheads[state]:
                        p.lookaheads[state].append(a)

    def add_lalr_lookaheads(self, C):
        nullable = self.compute_nullable_nonterminals()
        trans = self.find_nonterminal_transitions(C)
        readsets = self.compute_read_sets(C, trans, nullable)
        lookd, included = self.compute_lookback_includes(C, trans, nullable)
        followsets = self.compute_follow_sets(trans, readsets, included)
        self.add_lookaheads(lookd, followsets)

    def lr_parse_table(self):
        Productions = self.grammar.Productions
        Precedence = self.grammar.Precedence
        goto = self.lr_goto
        action = self.lr_action
        log = self.log
        actionp = {}
        log.info('Parsing method: %s', self.lr_method)
        C = self.lr0_items()
        if self.lr_method == 'LALR':
            self.add_lalr_lookaheads(C)
        st = 0
        for I in C:
            actlist = []
            st_action = {}
            st_actionp = {}
            st_goto = {}
            log.info('')
            log.info('state %d', st)
            log.info('')
            for p in I:
                log.info('    (%d) %s', p.number, str(p))

            log.info('')
            for p in I:
                if p.len == p.lr_index + 1:
                    if p.name == "S'":
                        st_action['$end'] = 0
                        st_actionp['$end'] = p
                    else:
                        if self.lr_method == 'LALR':
                            laheads = p.lookaheads[st]
                        else:
                            laheads = self.grammar.Follow[p.name]
                        for a in laheads:
                            actlist.append((a, p, 'reduce using rule %d (%s)' % (p.number, p)))
                            r = st_action.get(a, None)
                            if r is not None:
                                if r > 0:
                                    sprec, slevel = Productions[st_actionp[a].number].prec
                                    rprec, rlevel = Precedence.get(a, ('right', 0))
                                    if slevel < rlevel or slevel == rlevel and rprec == 'left':
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        if not slevel and not rlevel:
                                            log.info('  ! shift/reduce conflict for %s resolved as reduce', a)
                                            self.sr_conflicts.append((st, a, 'reduce'))
                                        Productions[p.number].reduced += 1
                                    elif slevel == rlevel and rprec == 'nonassoc':
                                        st_action[a] = None
                                    elif not rlevel:
                                        log.info('  ! shift/reduce conflict for %s resolved as shift', a)
                                        self.sr_conflicts.append((st, a, 'shift'))
                                elif r < 0:
                                    oldp = Productions[-r]
                                    pp = Productions[p.number]
                                    if oldp.line > pp.line:
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        chosenp, rejectp = pp, oldp
                                        Productions[p.number].reduced += 1
                                        Productions[oldp.number].reduced -= 1
                                    else:
                                        chosenp, rejectp = oldp, pp
                                    self.rr_conflicts.append((st, chosenp, rejectp))
                                    log.info('  ! reduce/reduce conflict for %s resolved using rule %d (%s)', a, st_actionp[a].number, st_actionp[a])
                                else:
                                    raise LALRError('Unknown conflict in state %d' % st)
                            else:
                                st_action[a] = -p.number
                                st_actionp[a] = p
                                Productions[p.number].reduced += 1

                else:
                    i = p.lr_index
                    a = p.prod[i + 1]
                    if a in self.grammar.Terminals:
                        g = self.lr0_goto(I, a)
                        j = self.lr0_cidhash.get(id(g), -1)
                        if j >= 0:
                            actlist.append((a, p, 'shift and go to state %d' % j))
                            r = st_action.get(a, None)
                            if r is not None:
                                if r > 0:
                                    if r != j:
                                        raise LALRError('Shift/shift conflict in state %d' % st)
                                elif r < 0:
                                    rprec, rlevel = Productions[st_actionp[a].number].prec
                                    sprec, slevel = Precedence.get(a, ('right', 0))
                                    if slevel > rlevel or slevel == rlevel and rprec == 'right':
                                        Productions[st_actionp[a].number].reduced -= 1
                                        st_action[a] = j
                                        st_actionp[a] = p
                                        if not rlevel:
                                            log.info('  ! shift/reduce conflict for %s resolved as shift', a)
                                            self.sr_conflicts.append((st, a, 'shift'))
                                    elif slevel == rlevel and rprec == 'nonassoc':
                                        st_action[a] = None
                                    elif not slevel and not rlevel:
                                        log.info('  ! shift/reduce conflict for %s resolved as reduce', a)
                                        self.sr_conflicts.append((st, a, 'reduce'))
                                else:
                                    raise LALRError('Unknown conflict in state %d' % st)
                            else:
                                st_action[a] = j
                                st_actionp[a] = p

            _actprint = {}
            for a, p, m in actlist:
                if a in st_action:
                    if p is st_actionp[a]:
                        log.info('    %-15s %s', a, m)
                        _actprint[a, m] = 1

            log.info('')
            not_used = 0
            for a, p, m in actlist:
                if a in st_action:
                    if p is not st_actionp[a]:
                        if (a, m) not in _actprint:
                            log.debug('  ! %-15s [ %s ]', a, m)
                            not_used = 1
                            _actprint[a, m] = 1

            if not_used:
                log.debug('')
            nkeys = {}
            for ii in I:
                for s in ii.usyms:
                    if s in self.grammar.Nonterminals:
                        nkeys[s] = None

            for n in nkeys:
                g = self.lr0_goto(I, n)
                j = self.lr0_cidhash.get(id(g), -1)
                if j >= 0:
                    st_goto[n] = j
                    log.info('    %-30s shift and go to state %d', n, j)

            action[st] = st_action
            actionp[st] = st_actionp
            goto[st] = st_goto
            st += 1

    def write_table(self, modulename, outputdir = '', signature = ''):
        basemodulename = modulename.split('.')[-1]
        filename = os.path.join(outputdir, basemodulename) + '.py'
        try:
            f = open(filename, 'w')
            f.write('\n# %s\n# This file is automatically generated. Do not edit.\n_tabversion = %r\n\n_lr_method = %r\n\n_lr_signature = %r\n    ' % (filename,
             __tabversion__,
             self.lr_method,
             signature))
            smaller = 1
            if smaller:
                items = {}
                for s, nd in self.lr_action.items():
                    for name, v in nd.items():
                        i = items.get(name)
                        if not i:
                            i = ([], [])
                            items[name] = i
                        i[0].append(s)
                        i[1].append(v)

                f.write('\n_lr_action_items = {')
                for k, v in items.items():
                    f.write('%r:([' % k)
                    for i in v[0]:
                        f.write('%r,' % i)

                    f.write('],[')
                    for i in v[1]:
                        f.write('%r,' % i)

                    f.write(']),')

                f.write('}\n')
                f.write('\n_lr_action = { }\nfor _k, _v in _lr_action_items.items():\n   for _x,_y in zip(_v[0],_v[1]):\n      if not _x in _lr_action:  _lr_action[_x] = { }\n      _lr_action[_x][_k] = _y\ndel _lr_action_items\n')
            else:
                f.write('\n_lr_action = { ')
                for k, v in self.lr_action.items():
                    f.write('(%r,%r):%r,' % (k[0], k[1], v))

                f.write('}\n')
            if smaller:
                items = {}
                for s, nd in self.lr_goto.items():
                    for name, v in nd.items():
                        i = items.get(name)
                        if not i:
                            i = ([], [])
                            items[name] = i
                        i[0].append(s)
                        i[1].append(v)

                f.write('\n_lr_goto_items = {')
                for k, v in items.items():
                    f.write('%r:([' % k)
                    for i in v[0]:
                        f.write('%r,' % i)

                    f.write('],[')
                    for i in v[1]:
                        f.write('%r,' % i)

                    f.write(']),')

                f.write('}\n')
                f.write('\n_lr_goto = { }\nfor _k, _v in _lr_goto_items.items():\n   for _x,_y in zip(_v[0],_v[1]):\n       if not _x in _lr_goto: _lr_goto[_x] = { }\n       _lr_goto[_x][_k] = _y\ndel _lr_goto_items\n')
            else:
                f.write('\n_lr_goto = { ')
                for k, v in self.lr_goto.items():
                    f.write('(%r,%r):%r,' % (k[0], k[1], v))

                f.write('}\n')
            f.write('_lr_productions = [\n')
            for p in self.lr_productions:
                if p.func:
                    f.write('  (%r,%r,%d,%r,%r,%d),\n' % (p.str,
                     p.name,
                     p.len,
                     p.func,
                     p.file,
                     p.line))
                else:
                    f.write('  (%r,%r,%d,None,None,None),\n' % (str(p), p.name, p.len))

            f.write(']\n')
            f.close()
        except IOError:
            e = sys.exc_info()[1]
            sys.stderr.write("Unable to create '%s'\n" % filename)
            sys.stderr.write(str(e) + '\n')
            return

    def pickle_table(self, filename, signature = ''):
        try:
            import cPickle as pickle
        except ImportError:
            import pickle

        outf = open(filename, 'wb')
        pickle.dump(__tabversion__, outf, pickle_protocol)
        pickle.dump(self.lr_method, outf, pickle_protocol)
        pickle.dump(signature, outf, pickle_protocol)
        pickle.dump(self.lr_action, outf, pickle_protocol)
        pickle.dump(self.lr_goto, outf, pickle_protocol)
        outp = []
        for p in self.lr_productions:
            if p.func:
                outp.append((p.str,
                 p.name,
                 p.len,
                 p.func,
                 p.file,
                 p.line))
            else:
                outp.append((str(p),
                 p.name,
                 p.len,
                 None,
                 None,
                 None))

        pickle.dump(outp, outf, pickle_protocol)
        outf.close()


def get_caller_module_dict(levels):
    try:
        raise RuntimeError
    except RuntimeError:
        e, b, t = sys.exc_info()
        f = t.tb_frame
        while levels > 0:
            f = f.f_back
            levels -= 1

        ldict = f.f_globals.copy()
        if f.f_globals != f.f_locals:
            ldict.update(f.f_locals)
        return ldict


def parse_grammar(doc, file, line):
    grammar = []
    pstrings = doc.splitlines()
    lastp = None
    dline = line
    for ps in pstrings:
        dline += 1
        p = ps.split()
        if not p:
            continue
        try:
            if p[0] == '|':
                if not lastp:
                    raise SyntaxError("%s:%d: Misplaced '|'" % (file, dline))
                prodname = lastp
                syms = p[1:]
            else:
                prodname = p[0]
                lastp = prodname
                syms = p[2:]
                assign = p[1]
                if assign != ':' and assign != '::=':
                    raise SyntaxError("%s:%d: Syntax error. Expected ':'" % (file, dline))
            grammar.append((file,
             dline,
             prodname,
             syms))
        except SyntaxError:
            raise
        except Exception:
            raise SyntaxError("%s:%d: Syntax error in rule '%s'" % (file, dline, ps.strip()))

    return grammar


class ParserReflect(object):

    def __init__(self, pdict, log = None):
        self.pdict = pdict
        self.start = None
        self.error_func = None
        self.tokens = None
        self.files = {}
        self.grammar = []
        self.error = 0
        if log is None:
            self.log = PlyLogger(sys.stderr)
        else:
            self.log = log

    def get_all(self):
        self.get_start()
        self.get_error_func()
        self.get_tokens()
        self.get_precedence()
        self.get_pfunctions()

    def validate_all(self):
        self.validate_start()
        self.validate_error_func()
        self.validate_tokens()
        self.validate_precedence()
        self.validate_pfunctions()
        self.validate_files()
        return self.error

    def signature(self):
        try:
            from hashlib import md5
        except ImportError:
            from md5 import md5

        try:
            sig = md5()
            if self.start:
                sig.update(self.start.encode('latin-1'))
            if self.prec:
                sig.update(''.join([ ''.join(p) for p in self.prec ]).encode('latin-1'))
            if self.tokens:
                sig.update(' '.join(self.tokens).encode('latin-1'))
            for f in self.pfuncs:
                if f[3]:
                    sig.update(f[3].encode('latin-1'))

        except (TypeError, ValueError):
            pass

        return sig.digest()

    def validate_files(self):
        fre = re.compile('\\s*def\\s+(p_[a-zA-Z_0-9]*)\\(')
        for filename in self.files.keys():
            base, ext = os.path.splitext(filename)
            if ext != '.py':
                return 1
            try:
                f = open(filename)
                lines = f.readlines()
                f.close()
            except IOError:
                continue

            counthash = {}
            for linen, l in enumerate(lines):
                linen += 1
                m = fre.match(l)
                if m:
                    name = m.group(1)
                    prev = counthash.get(name)
                    if not prev:
                        counthash[name] = linen
                    else:
                        self.log.warning('%s:%d: Function %s redefined. Previously defined on line %d', filename, linen, name, prev)

    def get_start(self):
        self.start = self.pdict.get('start')

    def validate_start(self):
        if self.start is not None:
            if not isinstance(self.start, str):
                self.log.error("'start' must be a string")

    def get_error_func(self):
        self.error_func = self.pdict.get('p_error')

    def validate_error_func(self):
        if self.error_func:
            if isinstance(self.error_func, types.FunctionType):
                ismethod = 0
            elif isinstance(self.error_func, types.MethodType):
                ismethod = 1
            else:
                self.log.error("'p_error' defined, but is not a function or method")
                self.error = 1
                return
            eline = func_code(self.error_func).co_firstlineno
            efile = func_code(self.error_func).co_filename
            self.files[efile] = 1
            if func_code(self.error_func).co_argcount != 1 + ismethod:
                self.log.error('%s:%d: p_error() requires 1 argument', efile, eline)
                self.error = 1

    def get_tokens(self):
        tokens = self.pdict.get('tokens', None)
        if not tokens:
            self.log.error('No token list is defined')
            self.error = 1
            return
        if not isinstance(tokens, (list, tuple)):
            self.log.error('tokens must be a list or tuple')
            self.error = 1
            return
        if not tokens:
            self.log.error('tokens is empty')
            self.error = 1
            return
        self.tokens = tokens

    def validate_tokens(self):
        if 'error' in self.tokens:
            self.log.error("Illegal token name 'error'. Is a reserved word")
            self.error = 1
            return
        terminals = {}
        for n in self.tokens:
            if n in terminals:
                self.log.warning("Token '%s' multiply defined", n)
            terminals[n] = 1

    def get_precedence(self):
        self.prec = self.pdict.get('precedence', None)

    def validate_precedence(self):
        preclist = []
        if self.prec:
            if not isinstance(self.prec, (list, tuple)):
                self.log.error('precedence must be a list or tuple')
                self.error = 1
                return
            for level, p in enumerate(self.prec):
                if not isinstance(p, (list, tuple)):
                    self.log.error('Bad precedence table')
                    self.error = 1
                    return
                if len(p) < 2:
                    self.log.error('Malformed precedence entry %s. Must be (assoc, term, ..., term)', p)
                    self.error = 1
                    return
                assoc = p[0]
                if not isinstance(assoc, str):
                    self.log.error('precedence associativity must be a string')
                    self.error = 1
                    return
                for term in p[1:]:
                    if not isinstance(term, str):
                        self.log.error('precedence items must be strings')
                        self.error = 1
                        return
                    preclist.append((term, assoc, level + 1))

        self.preclist = preclist

    def get_pfunctions(self):
        p_functions = []
        for name, item in self.pdict.items():
            if name[:2] != 'p_':
                continue
            if name == 'p_error':
                continue
            if isinstance(item, (types.FunctionType, types.MethodType)):
                line = func_code(item).co_firstlineno
                file = func_code(item).co_filename
                p_functions.append((line,
                 file,
                 name,
                 item.__doc__))

        p_functions.sort()
        self.pfuncs = p_functions

    def validate_pfunctions(self):
        grammar = []
        if len(self.pfuncs) == 0:
            self.log.error('no rules of the form p_rulename are defined')
            self.error = 1
            return
        for line, file, name, doc in self.pfuncs:
            func = self.pdict[name]
            if isinstance(func, types.MethodType):
                reqargs = 2
            else:
                reqargs = 1
            if func_code(func).co_argcount > reqargs:
                self.log.error("%s:%d: Rule '%s' has too many arguments", file, line, func.__name__)
                self.error = 1
            elif func_code(func).co_argcount < reqargs:
                self.log.error("%s:%d: Rule '%s' requires an argument", file, line, func.__name__)
                self.error = 1
            elif not func.__doc__:
                self.log.warning("%s:%d: No documentation string specified in function '%s' (ignored)", file, line, func.__name__)
            else:
                try:
                    parsed_g = parse_grammar(doc, file, line)
                    for g in parsed_g:
                        grammar.append((name, g))

                except SyntaxError:
                    e = sys.exc_info()[1]
                    self.log.error(str(e))
                    self.error = 1

                self.files[file] = 1

        for n, v in self.pdict.items():
            if n[0:2] == 'p_' and isinstance(v, (types.FunctionType, types.MethodType)):
                continue
            if n[0:2] == 't_':
                continue
            if n[0:2] == 'p_' and n != 'p_error':
                self.log.warning("'%s' not defined as a function", n)
            if isinstance(v, types.FunctionType) and func_code(v).co_argcount == 1 or isinstance(v, types.MethodType) and func_code(v).co_argcount == 2:
                try:
                    doc = v.__doc__.split(' ')
                    if doc[1] == ':':
                        self.log.warning("%s:%d: Possible grammar rule '%s' defined without p_ prefix", func_code(v).co_filename, func_code(v).co_firstlineno, n)
                except Exception:
                    pass

        self.grammar = grammar


def yacc(method = 'LALR', debug = yaccdebug, module = None, tabmodule = tab_module, start = None, check_recursion = 1, optimize = 0, write_tables = 1, debugfile = debug_file, outputdir = '', debuglog = None, errorlog = None, picklefile = None):
    global parse
    if picklefile:
        write_tables = 0
    if errorlog is None:
        errorlog = PlyLogger(sys.stderr)
    if module:
        _items = [ (k, getattr(module, k)) for k in dir(module) ]
        pdict = dict(_items)
    else:
        pdict = get_caller_module_dict(2)
    pinfo = ParserReflect(pdict, log=errorlog)
    pinfo.get_all()
    if pinfo.error:
        raise YaccError('Unable to build parser')
    signature = pinfo.signature()
    try:
        lr = LRTable()
        if picklefile:
            read_signature = lr.read_pickle(picklefile)
        else:
            read_signature = lr.read_table(tabmodule)
        if optimize or read_signature == signature:
            try:
                lr.bind_callables(pinfo.pdict)
                parser = LRParser(lr, pinfo.error_func)
                parse = parser.parse
                return parser
            except Exception:
                e = sys.exc_info()[1]
                errorlog.warning('There was a problem loading the table file: %s', repr(e))

    except VersionError:
        e = sys.exc_info()
        errorlog.warning(str(e))
    except Exception:
        pass

    if debuglog is None:
        if debug:
            debuglog = PlyLogger(open(debugfile, 'w'))
        else:
            debuglog = NullLogger()
    debuglog.info('Created by PLY version %s (http://www.dabeaz.com/ply)', __version__)
    errors = 0
    if pinfo.validate_all():
        raise YaccError('Unable to build parser')
    if not pinfo.error_func:
        errorlog.warning('no p_error() function is defined')
    grammar = Grammar(pinfo.tokens)
    for term, assoc, level in pinfo.preclist:
        try:
            grammar.set_precedence(term, assoc, level)
        except GrammarError:
            e = sys.exc_info()[1]
            errorlog.warning('%s', str(e))

    for funcname, gram in pinfo.grammar:
        file, line, prodname, syms = gram
        try:
            grammar.add_production(prodname, syms, funcname, file, line)
        except GrammarError:
            e = sys.exc_info()[1]
            errorlog.error('%s', str(e))
            errors = 1

    try:
        if start is None:
            grammar.set_start(pinfo.start)
        else:
            grammar.set_start(start)
    except GrammarError:
        e = sys.exc_info()[1]
        errorlog.error(str(e))
        errors = 1

    if errors:
        raise YaccError('Unable to build parser')
    undefined_symbols = grammar.undefined_symbols()
    for sym, prod in undefined_symbols:
        errorlog.error("%s:%d: Symbol '%s' used, but not defined as a token or a rule", prod.file, prod.line, sym)
        errors = 1

    unused_terminals = grammar.unused_terminals()
    if unused_terminals:
        debuglog.info('')
        debuglog.info('Unused terminals:')
        debuglog.info('')
        for term in unused_terminals:
            errorlog.warning("Token '%s' defined, but not used", term)
            debuglog.info('    %s', term)

    if debug:
        debuglog.info('')
        debuglog.info('Grammar')
        debuglog.info('')
        for n, p in enumerate(grammar.Productions):
            debuglog.info('Rule %-5d %s', n, p)

    unused_rules = grammar.unused_rules()
    for prod in unused_rules:
        errorlog.warning("%s:%d: Rule '%s' defined, but not used", prod.file, prod.line, prod.name)

    if len(unused_terminals) == 1:
        errorlog.warning('There is 1 unused token')
    if len(unused_terminals) > 1:
        errorlog.warning('There are %d unused tokens', len(unused_terminals))
    if len(unused_rules) == 1:
        errorlog.warning('There is 1 unused rule')
    if len(unused_rules) > 1:
        errorlog.warning('There are %d unused rules', len(unused_rules))
    if debug:
        debuglog.info('')
        debuglog.info('Terminals, with rules where they appear')
        debuglog.info('')
        terms = list(grammar.Terminals)
        terms.sort()
        for term in terms:
            debuglog.info('%-20s : %s', term, ' '.join([ str(s) for s in grammar.Terminals[term] ]))

        debuglog.info('')
        debuglog.info('Nonterminals, with rules where they appear')
        debuglog.info('')
        nonterms = list(grammar.Nonterminals)
        nonterms.sort()
        for nonterm in nonterms:
            debuglog.info('%-20s : %s', nonterm, ' '.join([ str(s) for s in grammar.Nonterminals[nonterm] ]))

        debuglog.info('')
    if check_recursion:
        unreachable = grammar.find_unreachable()
        for u in unreachable:
            errorlog.warning("Symbol '%s' is unreachable", u)

        infinite = grammar.infinite_cycles()
        for inf in infinite:
            errorlog.error("Infinite recursion detected for symbol '%s'", inf)
            errors = 1

    unused_prec = grammar.unused_precedence()
    for term, assoc in unused_prec:
        errorlog.error("Precedence rule '%s' defined for unknown symbol '%s'", assoc, term)
        errors = 1

    if errors:
        raise YaccError('Unable to build parser')
    if debug:
        errorlog.debug('Generating %s tables', method)
    lr = LRGeneratedTable(grammar, method, debuglog)
    if debug:
        num_sr = len(lr.sr_conflicts)
        if num_sr == 1:
            errorlog.warning('1 shift/reduce conflict')
        elif num_sr > 1:
            errorlog.warning('%d shift/reduce conflicts', num_sr)
        num_rr = len(lr.rr_conflicts)
        if num_rr == 1:
            errorlog.warning('1 reduce/reduce conflict')
        elif num_rr > 1:
            errorlog.warning('%d reduce/reduce conflicts', num_rr)
    if debug and (lr.sr_conflicts or lr.rr_conflicts):
        debuglog.warning('')
        debuglog.warning('Conflicts:')
        debuglog.warning('')
        for state, tok, resolution in lr.sr_conflicts:
            debuglog.warning('shift/reduce conflict for %s in state %d resolved as %s', tok, state, resolution)

        already_reported = {}
        for state, rule, rejected in lr.rr_conflicts:
            if (state, id(rule), id(rejected)) in already_reported:
                continue
            debuglog.warning('reduce/reduce conflict in state %d resolved using rule (%s)', state, rule)
            debuglog.warning('rejected rule (%s) in state %d', rejected, state)
            errorlog.warning('reduce/reduce conflict in state %d resolved using rule (%s)', state, rule)
            errorlog.warning('rejected rule (%s) in state %d', rejected, state)
            already_reported[state, id(rule), id(rejected)] = 1

        warned_never = []
        for state, rule, rejected in lr.rr_conflicts:
            if not rejected.reduced and rejected not in warned_never:
                debuglog.warning('Rule (%s) is never reduced', rejected)
                errorlog.warning('Rule (%s) is never reduced', rejected)
                warned_never.append(rejected)

    if write_tables:
        lr.write_table(tabmodule, outputdir, signature)
    if picklefile:
        lr.pickle_table(picklefile, signature)
    lr.bind_callables(pinfo.pdict)
    parser = LRParser(lr, pinfo.error_func)
    parse = parser.parse
    return parser
