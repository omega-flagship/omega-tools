"""Fixed finite native tasks. Parent inference fence is NOT a child fuel budget."""
import json
from pathlib import Path
import sys
import uuid

FENCE = '''catch(call_with_time_limit(Seconds,
 call_with_inference_limit(run_metta_helper(false, load_metta_file, File, Results), Steps, Fuel)),
 time_limit_exceeded, Timed=true),
 (var(Results)->Results=[];true), (var(Fuel)->Fuel=unknown;true),
 (var(Timed)->Timed=false;true)'''


def main():
    from recipe_api import compile_recipe, decode_result
    path = Path('request.json')
    if path.stat().st_size > 16384: raise ValueError('request-byte-limit')
    job = json.loads(path.read_text())
    sys.path.insert(0, str(Path(job['petta'])/'python'))
    from petta import PeTTa
    import janus_swi as janus
    PeTTa(petta_path=job['petta'])
    from runtime_guard import measure
    pin = json.loads((Path(__file__).parent/'runtime_pin.json').read_text())
    runtime = measure(janus, pin)
    if not janus.query_once('use_module(library(time)), current_predicate(call_with_time_limit/2), current_predicate(call_with_inference_limit/3)').get('truth'):
        raise RuntimeError('native-fences-unavailable')
    baseline = set(map(str, janus.query_once('findall(Name, (thread_property(Id,status(_)), term_string(Id,Name)), Threads), Id=0, Name=0')['Threads']))
    namespace = 'wave_job_' + uuid.uuid4().hex
    Path('recipe.metta').write_text(compile_recipe(job['request'], namespace=namespace))
    r = janus.query_once(FENCE, {'Seconds': job['seconds'], 'Steps': job['steps'], 'File': str(Path('recipe.metta').resolve())})
    limit = 'time' if r.get('Timed') == 'true' else 'parent-inferences' if r.get('Fuel') == 'inference_limit_exceeded' else None
    raw = [] if limit else r.get('Results', [])
    result = [s for s in raw if type(s) is str and s.startswith('(WaveResult ')]
    if not limit and (len(result) != 1 or any('(Error ' in s for s in raw)):
        raise RuntimeError('incomplete-or-error-native-result')
    out = {'kind': 'ConcurrencyLimitExceeded' if limit else 'ConcurrencyResult', 'limit': limit,
           'data': None if limit else decode_result(job['request'], result[0]),
           'native': [] if limit else result, 'authority': 'none', 'state_scope': 'job-local',
           'provider_calls': 0, 'persistent_writes': 0}
    after = set(map(str, janus.query_once('findall(Name, (thread_property(Id,status(_)), term_string(Id,Name)), Threads), Id=0, Name=0')['Threads']))
    out['remaining_new_threads'] = sorted(after - baseline)
    if measure(janus, pin) != runtime: raise ValueError('concurrency-runtime-drift-during-job')
    out['runtime_definition'] = runtime
    data = json.dumps(out).encode()
    if len(data) > 8192: raise ValueError('result-byte-limit')
    Path('result.json').write_bytes(data)


if __name__ == '__main__': main()
