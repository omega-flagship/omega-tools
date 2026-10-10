"""Offline candidate adapter to the existing sandbox_run, not another executor.

Reviewer controls host, engine and fences. Not installed, admitted or callable
by a live mind until the owner reviews a versioned Tools successor.
"""
import asyncio
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def api():
    spec = importlib.util.spec_from_file_location('concurrency_api', HERE/'recipe_api.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def limited(reason):
    return {'kind': 'ConcurrencyLimitExceeded', 'limit': reason, 'data': None, 'native': [],
            'authority': 'none', 'state_scope': 'job-local', 'provider_calls': 0,
            'persistent_writes': 0, 'shared_runner': True}


async def execute(request, *, shared_runner, petta, steps=1000000, seconds=2):
    api().validate(request)
    request = json.loads(json.dumps(request))
    if type(steps) is not int or not 1 <= steps <= 1000000 or type(seconds) not in (float, int) or not math.isfinite(seconds) or not 0 < seconds <= 2:
        raise ValueError('reviewer-fence-outside-ceiling')
    manifest = json.loads((HERE/'manifest.json').read_text())
    for name, pin in manifest['source_pins'].items():
        if digest(HERE/name) != pin: raise ValueError('concurrency-source-drift')
    petta = Path(petta).resolve()
    for name, pin in manifest['engine']['source_pins'].items():
        if digest(petta/name) != pin: raise ValueError('engine-source-drift')
    with tempfile.TemporaryDirectory(prefix='omega-concurrency-review-') as folder:
        app = Path(folder); bundle = app/'recipes'; bundle.mkdir()
        for name in ('recipe_api.py', 'worker.py', 'runtime_guard.py', 'runtime_pin.json'):
            (bundle/name).write_bytes((HERE/name).read_bytes())
            if digest(bundle/name) != manifest['source_pins'][name]: raise ValueError('snapshot-source-drift')
        (bundle/'bundle.lock.json').write_text(json.dumps({'files': {p.name: digest(p) for p in bundle.iterdir()}}))
        job = {'request': request, 'petta': str(petta), 'seconds': seconds, 'steps': steps}
        try:
            result = await shared_runner.run({'id': 'omega-tools', 'path': str(app), 'capabilities': ['sandbox:run']},
                'worker.py', bundle='recipes', runtime='metta', inputs={'request.json': json.dumps(job).encode()},
                outputs=['result.json'], cpu_seconds=5, file_bytes=16384, timeout=7)
        except asyncio.TimeoutError: return limited('job-deadline')
        if result['exit'] or result['stdout_truncated'] or result['missing_outputs'] or len(result['stderr']) >= 16384:
            raise ValueError('shared-runner-failed-or-incomplete')
        payload = result['outputs']['result.json']
        if len(payload) > 8192: raise ValueError('result-byte-limit')
        value = json.loads(payload)
        for name, pin in manifest['engine']['source_pins'].items():
            if digest(petta/name) != pin: raise ValueError('engine-source-drift-before-delivery')
        fields = {'kind','limit','data','native','authority','state_scope','provider_calls','persistent_writes','remaining_new_threads','runtime_definition'}
        if type(value) is not dict or set(value) != fields or value['authority'] != 'none' or value['state_scope'] != 'job-local' or type(value['provider_calls']) is not int or value['provider_calls'] != 0 or type(value['persistent_writes']) is not int or value['persistent_writes'] != 0 or value['remaining_new_threads'] != []:
            raise ValueError('invalid-native-envelope')
        if value['kind'] == 'ConcurrencyResult':
            if value['limit'] is not None or type(value['native']) is not list or len(value['native']) != 1 or value['data'] != api().decode_result(request, value['native'][0]):
                raise ValueError('invalid-native-success')
        elif value['kind'] == 'ConcurrencyLimitExceeded':
            if value['limit'] not in ('time', 'parent-inferences') or value['data'] is not None or value['native'] != []:
                raise ValueError('partial-or-invalid-exhaustion')
        else: raise ValueError('unknown-result-kind')
        binding = value['runtime_definition']
        expected = json.loads((HERE/'runtime_pin.json').read_text())
        if type(binding) is not dict or set(binding) != {'module','predicate','source_sha256','version'}:
            raise ValueError('invalid-runtime-definition-binding')
        if {k: binding[k] for k in expected} != expected or type(binding['version']) is not list or len(binding['version']) != 3 or not all(type(v) is int and v >= 0 for v in binding['version']):
            raise ValueError('runtime-definition-binding-mismatch')
        value['shared_runner'] = True
        return value


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--petta', type=Path, required=True)
    parser.add_argument('--example', required=True)
    args = parser.parse_args()
    case = next((c for c in json.loads((HERE/'examples.json').read_text())['cases'] if c['id'] == args.example), None)
    if case is None: parser.error('unknown banked example')
    sys.path.insert(0, str(args.host.resolve()))
    from hive.core import sandbox_run
    value = asyncio.run(execute(case['request'], shared_runner=sandbox_run, petta=args.petta))
    print(json.dumps(value, indent=2))
    raise SystemExit(0 if value.get('data') == case['expected'] else 1)
