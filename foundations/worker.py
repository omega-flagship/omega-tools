"""One disposable native job; caller expressions and library paths are absent."""
import json
from pathlib import Path
import sys

FENCE = '''catch(call_with_time_limit(Seconds,
 call_with_inference_limit(run_metta_helper(false, load_metta_file, File, Results), Steps, Fuel)),
 time_limit_exceeded, Timed=true),
 (var(Results)->Results=[];true), (var(Fuel)->Fuel=unknown;true),
 (var(Timed)->Timed=false;true)'''


def main():
    from recipe_api import compile_recipe, decode_result
    p = Path('request.json')
    if p.stat().st_size > 16384: raise ValueError('request-bytes-limit')
    job = json.loads(p.read_text())
    sys.path.insert(0, str(Path(job['petta']) / 'python'))
    from petta import PeTTa
    import janus_swi as janus
    PeTTa(petta_path=job['petta'])
    if not janus.query_once('use_module(library(time)), current_predicate(call_with_time_limit/2), current_predicate(call_with_inference_limit/3)').get('truth'):
        raise RuntimeError('native-fences-unavailable')
    if job.get('fixture') == 'duplicate-definitions':
        # Fixed synthetic libraries, not imports selected by the request.
        source = '\n'.join('!(import! &self ' + json.dumps(str(Path(__file__).parent / f)) + ')' for f in ('duplicate-a.metta', 'duplicate-b.metta'))
        source += '\n!(FoundationResult (collapse (foundation-fixture-head "sample")))\n'
    else:
        source = compile_recipe(job['request'])
    Path('recipe.metta').write_text(source)
    r = janus.query_once(FENCE, {'Seconds':job['seconds'], 'Steps':job['steps'], 'File':str(Path('recipe.metta').resolve())})
    limit = 'time' if r.get('Timed') == 'true' else 'inferences' if r.get('Fuel') == 'inference_limit_exceeded' else None
    raw = [] if limit else r.get('Results', [])
    result = [s for s in raw if type(s) is str and s.startswith('(FoundationResult ')]
    if not limit and (len(result) != 1 or any('(Error ' in s for s in raw)):
        raise RuntimeError('incomplete-or-error-native-result')
    out = {'kind':'FoundationLimitExceeded' if limit else 'FoundationResult',
           'limit':limit, 'results':[] if limit else result, 'authority':'none',
           'data':None if limit else decode_result(job['request'], result[0], job.get('fixture')),
           'state_scope':'job-local', 'provider_calls':0, 'persistent_writes':0,
           'step_unit':'SWI-Prolog inferences'}
    data = json.dumps(out).encode()
    if len(data) > 8192: raise RuntimeError('result-byte-limit')
    Path('result.json').write_bytes(data)


if __name__ == '__main__': main()
