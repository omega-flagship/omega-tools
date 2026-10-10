"""Bind the actual loaded concurrency definition; no runtime path from input."""
import hashlib
from pathlib import Path

QUERY = ("predicate_property(concurrent_and(_, _), imported_from(Module)), "
         "predicate_property(thread:concurrent_and(_, _), file(File)), "
         "current_prolog_flag(version_data, swi(Major,Minor,Patch,_))")


def verify_definition(module, file, version, expected):
    if expected.keys() != {'module', 'predicate', 'source_sha256'}:
        raise ValueError('invalid-runtime-source-pin')
    if module != 'thread' or expected['module'] != module or expected['predicate'] != 'concurrent_and/2':
        raise ValueError('concurrency-provider-not-pinned-module')
    if type(file) is not str or Path(file).name != 'thread.pl' or not Path(file).is_file():
        raise ValueError('concurrency-definition-source-unavailable')
    if type(version) is not list or len(version) != 3 or not all(type(v) is int and v >= 0 for v in version):
        raise ValueError('invalid-runtime-version')
    actual = hashlib.sha256(Path(file).read_bytes()).hexdigest()
    if actual != expected['source_sha256']:
        raise ValueError('concurrency-definition-source-drift')
    return {'module': module, 'predicate': 'concurrent_and/2', 'source_sha256': actual, 'version': version}


def measure(janus, expected):
    value = janus.query_once(QUERY)
    if not value.get('truth'): raise ValueError('concurrency-definition-unavailable')
    return verify_definition(value['Module'], value['File'],
                             [value['Major'],value['Minor'],value['Patch']], expected)
