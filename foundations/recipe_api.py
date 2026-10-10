"""Closed typed recipe inputs. Data cannot choose an expression, head or space.

Only a generated variable in a declared pattern/projection slot becomes MeTTa
syntax. Literal identifiers are quoted data. These are recipes, not aliases for
engine primitives and not an admission mechanism for persistent spaces.
"""
import json
import re

RECIPES = frozenset({'branch-collect', 'branch-unique', 'pattern-join', 'pattern-count', 'local-space'})
IDENT = re.compile(r'[a-z][a-z0-9_-]{0,47}\Z')
RESERVED = frozenset({'eval', 'import', 'import!', 'py-call', 'call', 'self',
                      'add-atom', 'remove-atom', 'new-space', 'bind!', 'prolog'})


def identifier(value):
    if type(value) is not str or not IDENT.fullmatch(value) or value in RESERVED:
        raise ValueError('invalid-literal-or-variable')
    return value


def envelope(value):
    """Bound the tree before serialization, including pathological leaf values."""
    nodes = 0
    def visit(x, depth=0):
        nonlocal nodes
        nodes += 1
        if depth > 8 or nodes > 1024:
            raise ValueError('input-tree-limit')
        if type(x) is str:
            if len(x) > 64: raise ValueError('input-leaf-limit')
        elif type(x) is list:
            if len(x) > 64: raise ValueError('input-list-limit')
            for y in x: visit(y, depth + 1)
        elif type(x) is dict:
            if len(x) > 8: raise ValueError('input-object-limit')
            for k, y in x.items(): visit(k, depth + 1); visit(y, depth + 1)
        else:
            raise ValueError('unsupported-input-type')
    visit(value)
    if len(json.dumps(value).encode()) > 8192: raise ValueError('input-byte-limit')


def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError('closed-object-required')


def term(value, declared=(), pattern=False):
    if type(value) is not dict or len(value) != 1:
        raise ValueError('typed-term-required')
    if 'literal' in value:
        return json.dumps(identifier(value['literal']))
    if pattern and 'variable' in value and value['variable'] in declared:
        return '$v' + str(list(declared).index(value['variable']))
    raise ValueError('variable-outside-declared-pattern-slot')


def edges(value):
    if type(value) is not list or len(value) > 32:
        raise ValueError('edge-count-limit')
    for row in value:
        if type(row) is not list or len(row) != 2: raise ValueError('edge-pair-required')
        for t in row: term(t)
    return value


def validate(request):
    envelope(request)
    keys(request, ('schema', 'recipe', 'input'))
    if request['schema'] != 'omega-tools-foundation-request/v1' or request['recipe'] not in RECIPES:
        raise ValueError('unknown-recipe-or-schema')
    x = request['input']
    if request['recipe'] in ('branch-collect', 'branch-unique'):
        keys(x, ('values',))
        if type(x['values']) is not list or len(x['values']) > 32: raise ValueError('branch-count-limit')
        for t in x['values']: term(t)
    else:
        fields = ('edges', 'variables', 'patterns') if request['recipe'] == 'pattern-count' else ('edges', 'variables', 'patterns', 'project') if request['recipe'] == 'pattern-join' else ('edges', 'retract', 'variables', 'patterns', 'project')
        keys(x, fields); edges(x['edges'])
        if 'retract' in x: edges(x['retract'])
        declared = x['variables']
        if type(declared) is not list or len(declared) > 6 or len(set(declared)) != len(declared):
            raise ValueError('variable-declarations')
        for v in declared: identifier(v)
        patterns = x['patterns']
        cap = 1 if request['recipe'] == 'local-space' else 3
        if type(patterns) is not list or not 1 <= len(patterns) <= cap: raise ValueError('pattern-count-limit')
        used = set()
        for pair in patterns:
            if type(pair) is not list or len(pair) != 2: raise ValueError('pattern-pair-required')
            for t in pair:
                term(t, declared, True)
                if 'variable' in t: used.add(t['variable'])
        if used != set(declared): raise ValueError('unused-variable-declaration')
        if request['recipe'] != 'pattern-count':
            project = x['project']
            if type(project) is not list or not 1 <= len(project) <= 6: raise ValueError('projection-count-limit')
            for t in project: term(t, declared, True)
    return request


def compile_recipe(request):
    """Generate only known operations after closed input validation."""
    validate(request)
    x = request['input']
    if request['recipe'] in ('branch-collect', 'branch-unique'):
        values = ' '.join(term(t) for t in x['values'])
        # The pinned PeTTa translator rejects superpose (). Use the engine's
        # explicit empty generator for this recipe's zero-alternative case.
        branches = '(superpose (' + values + '))' if values else '(empty)'
        if request['recipe'] == 'branch-unique': branches = '(unique ' + branches + ')'
        return '!(FoundationResult (collapse ' + branches + '))\n'
    # PeTTa's spaces are named predicate namespaces, not Hyperon's new-space
    # objects. A fresh sandbox process owns this fixed initially empty name.
    code = []
    for row in x['edges']:
        code.append('!(add-atom &job (FoundationEdge ' + ' '.join(term(t) for t in row) + '))')
    def matches(result):
        for pair in reversed(x['patterns']):
            result = '(match &job (FoundationEdge ' + ' '.join(term(t, x['variables'], True) for t in pair) + ') ' + result + ')'
        return result
    def query():
        result = '(FoundationBinding ' + ' '.join(term(t, x['variables'], True) for t in x['project']) + ')'
        return '(collapse ' + matches(result) + ')'
    if request['recipe'] == 'local-space':
        body = '(FoundationResult (Before $before) (After ' + query() + '))'
        for row in reversed(x['retract']):
            body = '(let $ignored (remove-atom &job (FoundationEdge ' + ' '.join(term(t) for t in row) + ')) ' + body + ')'
        code.append('!(let $before ' + query() + ' ' + body + ')')
    elif request['recipe'] == 'pattern-count':
        # Fixed reducer and unit weight; no caller-supplied aggregator, expression
        # or materialized binding list. Duplicate matches count separately.
        code.append('!(FoundationResult (FoundationCount (foldall + ' + matches('1') + ' 0)))')
    else:
        code.append('!(FoundationResult ' + query() + ')')
    return '\n'.join(code) + '\n'


def decode_result(request, text, fixture=None):
    """Decode only the recipe's fixed result grammar; never evaluate output."""
    if type(text) is not str or len(text.encode()) > 8192: raise ValueError('result-byte-limit')
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()]|[A-Za-z][A-Za-z-]*|[0-9]+', text)
    # Tokenization may not silently discard an unknown operator or punctuation.
    if re.sub(r'\s+', '', ''.join(tokens)) != re.sub(r'\s+', '', text): raise ValueError('invalid-result-grammar')
    position = 0
    def read(depth=0):
        nonlocal position
        if depth > 8 or position >= len(tokens): raise ValueError('invalid-result-tree')
        t = tokens[position]; position += 1
        if t == '(':
            out = []
            while position < len(tokens) and tokens[position] != ')': out.append(read(depth+1))
            if position >= len(tokens): raise ValueError('invalid-result-tree')
            position += 1; return out
        if t.startswith('"'): return identifier(json.loads(t))
        if t.isdigit():
            if len(t)>5: raise ValueError('count-result-limit')
            return int(t)
        if t not in {'FoundationResult','FoundationBinding','FoundationCount','Before','After','FixtureBranch'}:
            raise ValueError('unknown-result-constructor')
        return t
    tree = read()
    if position != len(tokens) or type(tree) is not list or not tree or tree[0] != 'FoundationResult':
        raise ValueError('invalid-result-root')
    def rows(x, width, head='FoundationBinding'):
        if type(x) is not list or len(x) > 128: raise ValueError('result-count-limit')
        out = []
        for row in x:
            if type(row) is not list or len(row) != width+1 or row[0] != head: raise ValueError('invalid-result-binding')
            out.append([identifier(v) for v in row[1:]])
        return out
    if fixture == 'duplicate-definitions':
        if len(tree) != 2: raise ValueError('invalid-fixture-result')
        values = rows(tree[1], 1, 'FixtureBranch')
        return {'fixture':fixture,'definition_count':len(values),'branches':[r[0] for r in values]}
    validate(request)
    recipe = request['recipe']; x = request['input']
    if recipe in ('branch-collect', 'branch-unique'):
        if len(tree) != 2 or type(tree[1]) is not list or len(tree[1]) > 32: raise ValueError('invalid-branch-result')
        return {'recipe':recipe,'values':[identifier(v) for v in tree[1]]}
    if recipe == 'pattern-count':
        if len(tree)!=2 or type(tree[1]) is not list or len(tree[1])!=2 or tree[1][0]!='FoundationCount' or type(tree[1][1]) is not int:
            raise ValueError('invalid-count-result')
        count=tree[1][1]
        if not 0<=count<=len(x['edges'])**len(x['patterns']): raise ValueError('count-result-limit')
        return {'recipe':recipe,'count':count}
    columns = [v.get('variable', 'literal:'+v.get('literal','')) for v in x['project']]
    if recipe == 'pattern-join':
        if len(tree) != 2: raise ValueError('invalid-query-result')
        return {'recipe':recipe,'columns':columns,'bindings':rows(tree[1],len(columns))}
    if len(tree) != 3 or any(type(t) is not list or len(t) != 2 for t in tree[1:]) or tree[1][0] != 'Before' or tree[2][0] != 'After':
        raise ValueError('invalid-local-space-result')
    return {'recipe':recipe,'columns':columns,'before':rows(tree[1][1],len(columns)), 'after':rows(tree[2][1],len(columns))}
