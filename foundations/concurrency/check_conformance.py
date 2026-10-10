"""Focused synthetic offline acceptance through the owner's shared OS sandbox."""
import asyncio
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[1]  # the omega-tools repository root
# An OmegaHive git checkout; default: one named "omegahive" next to this repository.
HOST = Path(os.environ.get('OMEGAHIVE_PATH') or PACKAGE.parent/'omegahive').resolve()
PETTA = Path(os.environ.get('PETTA_PATH', 'PeTTa'))
VENV = Path(os.environ.get('OMEGA_VENV', '.venv'))
sys.path.insert(0, str(HOST))
from hive.core import sandbox_run
from jsonschema import Draft202012Validator

spec = importlib.util.spec_from_file_location('concurrency_runner', HERE/'runner.py')
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
api = runner.api()
checks, native, diagnostics = [], [], []
started_at = time.monotonic()
cases = json.loads((HERE/'examples.json').read_text())['cases']
schema = json.loads((HERE/'request.schema.json').read_text())
Draft202012Validator.check_schema(schema)
result_schema = json.loads((HERE/'result.schema.json').read_text())
Draft202012Validator.check_schema(result_schema)


def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})
    print(('PASS ' if value else 'FAIL ') + name, flush=True)


def refuse(name, request):
    try: api.validate(request); passed = False
    except (ValueError, TypeError): passed = True
    check(name, passed)


for case in cases:
    api.validate(case['request']); Draft202012Validator(schema).validate(case['request'])
    check(case['id']+'-closed-schema', api.expected(case['request']) == case['expected'])

base = copy.deepcopy(cases[0]['request'])
for name, change in [
    ('free-expression', lambda x: x['input'].update(expression='(eval private)')),
    ('caller-space', lambda x: x['input'].update(space='&self')),
    ('caller-executor', lambda x: x.update(executor='shell')),
    ('undeclared-variable', lambda x: x['input']['tasks'][0].update(value='$x')),
    ('boolean-is-not-integer', lambda x: x['input']['tasks'][0].update(value=True)),
    ('huge-integer', lambda x: x['input']['tasks'][0].update(value=10**10000)),
    ('oversize-label', lambda x: x['input']['tasks'][0].update(id='x'*1000000)),
    ('quote-breakout', lambda x: x['input']['tasks'][0].update(id='a") (py-call bad)')),
    ('duplicate-task-id', lambda x: x['input']['tasks'][1].update(id='north')),
    ('branch-ceiling', lambda x: x['input'].update(tasks=x['input']['tasks']*5)),
    ('unknown-recipe', lambda x: x.update(recipe='unrestricted-hyperpose')),
]:
    bad = copy.deepcopy(base); change(bad); refuse(name+'-refused', bad)
bad = copy.deepcopy(cases[-1]['request']); bad['input']['commit'] = 'yes'; refuse('boolean-decision-only', bad)
bad = copy.deepcopy(cases[2]['request']); bad['input']['increments'] = []; refuse('empty-updates-refused', bad)

for name, raw in [('partial', '(WaveResult ((WaveBranch "north" 20)))'),
                  ('duplicate', '(WaveResult ((WaveBranch "north" 20) (WaveBranch "north" 20)))'),
                  ('wrong-value', '(WaveResult ((WaveBranch "north" 21) (WaveBranch "south" 20)))'),
                  ('injection', '(WaveResult ((WaveBranch "north" 20) (WaveBranch "south" 20))) (eval bad)'),
                  ('negative-mismatch', '(WaveResult ((WaveBranch "north" -20) (WaveBranch "south" 20)))')]:
    try: api.decode_result(base, raw); ok = False
    except ValueError: ok = True
    check('decode-'+name+'-refused', ok)
reverse = '(WaveResult ((WaveBranch "south" 20) (WaveBranch "north" 20)))'
check('projection-order-independent-of-completion', api.decode_result(base, reverse) == cases[0]['expected'])


class ObservedRunner:
    @staticmethod
    async def run(*args, **kw):
        value = await sandbox_run.run(*args, **kw)
        if value['exit'] or value['missing_outputs']:
            diagnostics.append({'exit': value['exit'], 'stderr': value['stderr'].decode(errors='replace')[-2000:], 'missing_outputs': value['missing_outputs']})
        return value


async def main():
    env = {'HIVE_SANDBOX_RUN_APPS': 'omega-tools', 'HIVE_SANDBOX_RUNTIMES': json.dumps({'metta': {'exe': str(VENV/'bin/python'), 'reads': [str(VENV), str(PETTA)]}})}
    with patch.dict(os.environ, env):
        for case in cases:
            try:
                actual = await runner.execute(case['request'], shared_runner=ObservedRunner, petta=PETTA)
                native.append({'id': case['id'], 'actual': actual})
                check(case['id']+'-actual-native-result', actual['kind'] == 'ConcurrencyResult' and actual['data'] == case['expected'] and actual['remaining_new_threads'] == [])
            except Exception as error:
                native.append({'id': case['id'], 'error': str(error)}); check(case['id']+'-actual-native-result', False)
        maximum = copy.deepcopy(base)
        maximum['input']['tasks'] = [{'id': 'job'+str(i), 'value': -10000+i, 'increment': -100} for i in range(8)]
        actual = await runner.execute(maximum, shared_runner=ObservedRunner, petta=PETTA)
        check('eight-branches-negative-numeric-boundary', actual['data'] == api.expected(maximum))
        native.append({'id': 'eight-branches-negative-boundary', 'actual': actual})
        # Two disposable jobs use the same fixed name but must not share state.
        request = cases[2]['request']
        results = await asyncio.gather(*(runner.execute(request, shared_runner=ObservedRunner, petta=PETTA) for _ in range(2)))
        check('two-jobs-independent-space-and-mutex', all(v['data'] == cases[2]['expected'] for v in results))
        native.append({'id': 'two-independent-jobs', 'actual': results})
        for name, fence in [('parent-inferences', {'steps': 1}), ('time', {'seconds': 0.000001})]:
            actual = await runner.execute(base, shared_runner=ObservedRunner, petta=PETTA, **fence)
            check(name+'-exhaustion-no-partial-answer', actual['kind'] == 'ConcurrencyLimitExceeded' and actual['data'] is None and actual['native'] == [] and actual['limit'] == name)
            native.append({'id': name+'-exhaustion', 'actual': actual})
        for name, fence in [('nan', {'seconds': float('nan')}), ('boolean', {'steps': True}), ('over-ceiling', {'seconds': 3})]:
            try: await runner.execute(base, shared_runner=ObservedRunner, petta=PETTA, **fence); ok = False
            except ValueError as error: ok = str(error) == 'reviewer-fence-outside-ceiling'
            check(name+'-fence-refused', ok)
        class Deadline:
            @staticmethod
            async def run(*args, **kw): raise asyncio.TimeoutError()
        deadline = await runner.execute(base, shared_runner=Deadline, petta=PETTA)
        check('shared-deadline-maps-to-no-partial-answer', deadline['kind'] == 'ConcurrencyLimitExceeded' and deadline['limit'] == 'job-deadline' and deadline['data'] is None and deadline['native'] == [])
        class CorruptResult:
            @staticmethod
            async def run(*args, **kw):
                value = await sandbox_run.run(*args, **kw)
                payload = json.loads(value['outputs']['result.json'])
                payload['data']['rows'].pop()
                value['outputs']['result.json'] = json.dumps(payload).encode()
                return value
        try: await runner.execute(base, shared_runner=CorruptResult, petta=PETTA); ok = False
        except ValueError as error: ok = str(error) == 'invalid-native-success'
        check('native-envelope-structured-data-mismatch-refused', ok)
        with tempfile.TemporaryDirectory(prefix='omega-concurrency-drift-') as folder:
            altered = Path(folder)/'candidate'; shutil.copytree(HERE, altered)
            (altered/'worker.py').write_text('# altered\n')
            with patch.object(runner, 'HERE', altered):
                try: await runner.execute(base, shared_runner=ObservedRunner, petta=PETTA); ok = False
                except ValueError as error: ok = str(error) == 'concurrency-source-drift'
                check('worker-drift-before-dispatch-refused', ok)
        event = asyncio.Event(); processes = []
        original = sandbox_run.asyncio.create_subprocess_exec
        async def record_spawn(*args, **kw):
            process = await original(*args, **kw); processes.append(process); event.set(); return process
        with patch.object(sandbox_run.asyncio, 'create_subprocess_exec', record_spawn):
            task = asyncio.create_task(runner.execute(base, shared_runner=ObservedRunner, petta=PETTA))
            await asyncio.wait_for(event.wait(), 2)
            task.cancel()
            try: await task; cancelled = False
            except asyncio.CancelledError: cancelled = True
            check('cancel-started-worker-reaped', cancelled and processes and all(p.returncode is not None for p in processes))


asyncio.run(main())
for row in native:
    if 'actual' in row:
        for result in row['actual'] if type(row['actual']) is list else [row['actual']]:
            Draft202012Validator(result_schema).validate(result)
check('all-native-result-envelopes-match-closed-schema', True)
head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=HOST, capture_output=True, text=True, check=True).stdout.strip()
check('qualified-host-revision-unchanged', head == '430795fd1d8e43fabe0df4cf503469f419362d4a')
check('host-worktree-remains-clean', not subprocess.run(['git','status','--porcelain'],cwd=HOST,capture_output=True,text=True,check=True).stdout.strip())
receipt = {'suite_id': 'omega-tools-concurrency-r1', 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'qualification': 'offline L0 recipes through real PeTTa and shared OS sandbox; not host admission or native mind',
    'passed': all(c['passed'] for c in checks), 'duration_seconds': round(time.monotonic()-started_at, 3),
    'checks': checks, 'native': native, 'diagnostics': diagnostics, 'host_revision': head,
    'source_pins': {p.name: runner.digest(p) for p in HERE.iterdir() if p.is_file()},
    'shared_runner_sha256': runner.digest(HOST/'hive/core/sandbox_run.py'),
    'initial_failures_retained': [
        {'stage': 'thread-diagnostics', 'observed': 'Janus query returned unbound local query variables; Prolog instantiation error. Corrected by binding locals after findall; opaque thread IDs converted in Prolog.'},
        {'stage': 'counter-native-output', 'observed': 'Un-evaluated nested (+ ...) was stored as an atom. Corrected by evaluating arithmetic through let before insertion. No success accepted from symbolic output.'}],
    'limits': {'child_inference_budget': False, 'tasks_max': 8, 'native_parent_seconds': 2, 'shared_job_seconds': 7, 'process_cpu_seconds': 5},
    'cancellation_scope': 'Started OS worker killed/reaped; does not establish cancellation during native reduction',
    'non_claims': ['speedup or overlap benchmark', 'cross-mind scheduler', 'external effect rollback', 'live admission/install', 'general-purpose parallel expression evaluation'],
    'publication': 'private candidate; no upload', 'provider_calls': 0, 'persistent_space_access': False,
    'cleanup': 'All owned snapshots and sandbox jobs temporary; completed native jobs report no new surviving SWI threads'}
(PACKAGE/'evidence/concurrency-r1-conformance.json').write_text(json.dumps(receipt, indent=2)+'\n')
raise SystemExit(0 if receipt['passed'] else 1)
