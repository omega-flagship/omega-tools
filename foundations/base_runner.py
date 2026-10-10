"""Owner/offline harness using the ONE platform sandbox runner.

Host/petta paths and fences are reviewer controls, never fields of recipe input.
No app activation, caller-selected executable or alternate process launcher.
"""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def api():
    spec = importlib.util.spec_from_file_location('foundation_api', HERE / 'recipe_api.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def native_answer(result):
    if result['exit'] or result['stdout_truncated'] or result['missing_outputs'] or len(result['stderr']) >= 16384:
        raise ValueError('shared-runner-failed-or-incomplete')
    payload = result['outputs']['result.json']
    if len(payload) > 8192: raise ValueError('result-byte-limit')
    value = json.loads(payload)
    if type(value) is not dict or set(value) != {'kind','limit','results','data','authority','state_scope','provider_calls','persistent_writes','step_unit'}:
        raise ValueError('invalid-native-result')
    if value['provider_calls'] != 0 or value['persistent_writes'] != 0 or value['step_unit'] != 'SWI-Prolog inferences':
        raise ValueError('invalid-native-result')
    if value.get('kind') not in ('FoundationResult', 'FoundationLimitExceeded') or value.get('authority') != 'none' or value.get('state_scope') != 'job-local':
        raise ValueError('invalid-native-result')
    if type(value.get('results')) is not list or not all(type(s) is str for s in value['results']): raise ValueError('invalid-native-result')
    if value['kind'] == 'FoundationLimitExceeded' and value['results']: raise ValueError('partial-limit-output')
    if value['kind'] == 'FoundationResult' and len(value['results']) != 1: raise ValueError('incomplete-native-result')
    if value['kind'] == 'FoundationResult' and value.get('limit') is not None: raise ValueError('invalid-native-result')
    if value['kind'] == 'FoundationLimitExceeded' and value.get('limit') not in ('time','inferences'): raise ValueError('invalid-native-result')
    if value['kind'] == 'FoundationLimitExceeded' and value.get('data') is not None: raise ValueError('partial-limit-output')
    return value


async def execute(request, *, shared_runner, petta, steps=1000000, seconds=2, fixture=None):
    if fixture is None: api().validate(request)
    elif fixture != 'duplicate-definitions' or request is not None: raise ValueError('unknown-conformance-fixture')
    if type(steps) is not int or not 1 <= steps <= 1000000 or type(seconds) not in (int, float) or not 0 < seconds <= 2:
        raise ValueError('reviewer-fence-outside-ceiling')
    manifest = json.loads((HERE/'manifest.json').read_text())
    for name, expected in manifest['source_pins'].items():
        if digest(HERE/name) != expected: raise ValueError('foundation-source-drift')
    petta = Path(petta).resolve()
    for name, expected in manifest['engine']['source_pins'].items():
        if digest(petta/name) != expected: raise ValueError('engine-source-drift')
    with tempfile.TemporaryDirectory(prefix='omega-foundation-owner-') as folder:
        app = Path(folder); bundle = app/'recipes'; bundle.mkdir()
        for name in ('recipe_api.py', 'worker.py', 'duplicate-a.metta', 'duplicate-b.metta'):
            (bundle/name).write_bytes((HERE/name).read_bytes())
            if digest(bundle/name) != manifest['source_pins'][name]: raise ValueError('snapshot-source-drift')
        (bundle/'bundle.lock.json').write_text(json.dumps({'files':{p.name:digest(p) for p in bundle.iterdir()}}))
        job = {'request':request, 'fixture':fixture, 'petta':str(petta), 'seconds':seconds, 'steps':steps}
        try:
            result = await shared_runner.run({'id':'omega-tools', 'path':str(app), 'capabilities':['sandbox:run']},
                 'worker.py', bundle='recipes', runtime='metta', inputs={'request.json':json.dumps(job).encode()},
                 outputs=['result.json'], cpu_seconds=5, file_bytes=16384, timeout=7)
        except asyncio.TimeoutError:
            return {'kind':'FoundationLimitExceeded','limit':'job-deadline','results':[], 'data':None,'authority':'none','state_scope':'job-local'}
        value = native_answer(result); value['shared_runner'] = True
        if value['kind'] == 'FoundationResult' and value.get('data') != api().decode_result(request,value['results'][0],fixture):
            raise ValueError('typed-native-result-mismatch')
        return value


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', type=Path, required=True, help='Reviewer-owned isolated platform checkout')
    ap.add_argument('--petta', type=Path, required=True, help='Operator-configured engine')
    ap.add_argument('--example', required=True, help='Named banked example, never an expression')
    args = ap.parse_args()
    cases = json.loads((HERE/'examples.json').read_text())['cases']
    case = next((c for c in cases if c['id']==args.example), None)
    if case is None: ap.error('unknown banked example')
    sys.path.insert(0,str(args.host.resolve()))
    from hive.core import sandbox_run
    value = asyncio.run(execute(case['request'], shared_runner=sandbox_run, petta=args.petta))
    print(json.dumps(value,indent=2))
    return 0 if value['kind']=='FoundationResult' and value['results']==case['expected'] else 1


if __name__ == '__main__': raise SystemExit(main())
