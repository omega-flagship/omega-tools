"""Pure recipe preview. No imports, registration, persistence or execution grants."""
import json
import math
import re

ID = re.compile(r'^[a-z][a-z0-9_.-]{0,95}$')
VERSION = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')


def _bounded(value, depth=0, count=None):
    count = [0] if count is None else count
    count[0] += 1
    if count[0] > 2048 or depth > 12:
        raise ValueError('Recipe too large or deeply nested.')
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or len(key) > 128:
                raise ValueError('Invalid recipe key.')
            _bounded(item, depth + 1, count)
    elif type(value) is list:
        for item in value:
            _bounded(item, depth + 1, count)
    elif type(value) is str:
        if len(value) > 2048:
            raise ValueError('Recipe string too large.')
    elif type(value) in (int, float):
        if not (-1000000000 <= value <= 1000000000) or not math.isfinite(value):
            raise ValueError('Invalid recipe number.')
    elif type(value) not in (bool, type(None)):
        raise ValueError('Recipe must contain JSON data only.')


def _configuration(values, schema):
    if type(values) is not dict or schema.get('type') != 'object' or schema.get('additionalProperties') is not False:
        raise ValueError('Configuration requires a closed object schema.')
    props = schema.get('properties')
    if type(props) is not dict or len(props) > 16 or set(values) - set(props):
        raise ValueError('Unknown configuration option.')
    required = schema.get('required', [])
    if type(required) is not list or not all(type(k) is str and k in props for k in required) or not set(required) <= set(values):
        raise ValueError('Missing required configuration option.')
    for key, value in values.items():
        spec = props[key]
        if type(spec) is not dict or set(spec) - {'type', 'enum', 'minimum', 'maximum'}:
            raise ValueError('Unsupported configuration schema.')
        kind = spec.get('type')
        valid = ((kind == 'string' and type(value) is str)
                 or (kind == 'boolean' and type(value) is bool)
                 or (kind == 'integer' and type(value) is int)
                 or (kind == 'number' and type(value) in (int, float)))
        if not valid or ('enum' in spec and value not in spec['enum']):
            raise ValueError('Configuration type or enum mismatch.')
        if type(value) in (int, float) and not (spec.get('minimum', -1000000000) <= value <= spec.get('maximum', 1000000000)):
            raise ValueError('Configuration outside declared range.')


def compose(registry, recipe):
    _bounded(recipe)
    if len(json.dumps(recipe, allow_nan=False).encode()) > 65536:
        raise ValueError('Recipe byte limit exceeded.')
    if type(recipe) is not dict or set(recipe) - {'schema', 'sets', 'bindings', 'custom_implementations', 'configuration'}:
        raise ValueError('Unknown recipe fields.')
    if recipe.get('schema') != 'omega-tools-recipe/v1':
        raise ValueError('Unsupported recipe schema.')
    selected = recipe.get('sets')
    sets = {s['id']: s for s in registry['sets']}
    if type(selected) is not list or not 1 <= len(selected) <= 12 or not all(type(x) is str and x in sets for x in selected) or len(set(selected)) != len(selected):
        raise ValueError('Choose distinct known capability sets.')
    available = {(i['id'], i['version']): i for i in registry['implementations']}
    custom = recipe.get('custom_implementations', [])
    if type(custom) is not list or len(custom) > 32:
        raise ValueError('Invalid custom implementation list.')
    for item in custom:
        keys = {'id', 'version', 'role', 'state', 'effects', 'configuration_schema', 'scope'}
        if type(item) is not dict or set(item) != keys or not all(type(item[k]) is str for k in ('id', 'version', 'role', 'scope')):
            raise ValueError('Custom implementations are closed inert descriptors.')
        if not ID.fullmatch(item['id']) or not ID.fullmatch(item['role']) or not VERSION.fullmatch(item['version']):
            raise ValueError('Invalid custom implementation identity.')
        if item['id'].startswith('omegahive.tools.') or item['state'] != 'extension-proposal' or item['effects'] != []:
            raise ValueError('Custom descriptor cannot impersonate a reviewed module or grant effects.')
        key = (item['id'], item['version'])
        if key in available:
            raise ValueError('Duplicate implementation identity.')
        if type(item['configuration_schema']) is not dict:
            raise ValueError('Invalid configuration schema.')
        available[key] = item
    slots = {}
    for sid in selected:
        for slot in sets[sid]['slots']:
            previous = slots.get(slot['role'])
            if previous and previous['default'] != slot['default']:
                raise ValueError('Conflicting defaults require a versioned set revision.')
            slots[slot['role']] = slot
    bindings, configs = recipe.get('bindings', {}), recipe.get('configuration', {})
    if type(bindings) is not dict or type(configs) is not dict or (set(bindings) | set(configs)) - set(slots):
        raise ValueError('Binding/configuration references an unknown slot.')
    resolved, unresolved = [], []
    for role, slot in slots.items():
        binding = bindings.get(role, slot['default'])
        if binding is None:
            if role in configs:
                raise ValueError('Cannot configure an unbound slot.')
            unresolved.append(role)
            continue
        if type(binding) is not dict or set(binding) != {'id', 'version'} or not all(type(x) is str for x in binding.values()):
            raise ValueError('Bind an exact implementation id and version.')
        implementation = available.get((binding['id'], binding['version']))
        if implementation is None or implementation['role'] != role:
            raise ValueError('Unknown implementation version or incompatible role.')
        _configuration(configs.get(role, {}), implementation['configuration_schema'])
        resolved.append({'role': role, 'implementation': binding, 'configuration': configs.get(role, {}),
                         'state': implementation['state'], 'host_shadow': implementation.get('host_shadow', False)})
    return {'schema': 'omega-tools-composition-preview/v1', 'sets': selected,
            'components': resolved, 'unresolved_required_slots': unresolved,
            'status': 'incomplete' if unresolved else 'ready-for-review',
            'executed': False, 'registered': False, 'authority': 'none',
            'effects': [], 'activation': 'separate exact-component review and existing host policy required',
            'compatibility': 'descriptor role/configuration checks only; semantic adapter compatibility is unproven'}


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    import sys
    parser = argparse.ArgumentParser(description='Preview a local Tools recipe; does not register or run implementations.')
    parser.add_argument('recipe', help='JSON recipe file, or - for stdin')
    args = parser.parse_args()
    try:
        if args.recipe == '-':
            raw = sys.stdin.buffer.read(65537)
        else:
            with Path(args.recipe).open('rb') as source:
                raw = source.read(65537)
        if len(raw) > 65536:
            raise ValueError('Recipe byte limit exceeded.')
        registry = json.loads((Path(__file__).resolve().parents[1] / 'capability-sets.json').read_text())
        print(json.dumps(compose(registry, json.loads(raw)), indent=2))
    except (ValueError, TypeError, OSError) as exc:
        print('Recipe refused: ' + str(exc), file=sys.stderr)
        raise SystemExit(2)
