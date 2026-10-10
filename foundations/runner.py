"""Reviewed closed protocol dispatch through the existing shared sandbox."""
import hashlib
import importlib.util
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent

async def execute(request, *, shared_runner, petta, steps=1000000, seconds=2, fixture=None):
    manifest = json.loads((HERE / 'manifest.json').read_text())
    for name, expected in manifest['source_pins'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise ValueError('foundation-source-drift')
    if type(request) is dict and request.get('schema') == 'omega-tools-concurrency-request/v1':
        if fixture is not None: raise ValueError('unknown-conformance-fixture')
        filename = HERE / 'concurrency/runner.py'
    else:
        filename = HERE / 'base_runner.py'
    spec = importlib.util.spec_from_file_location('reviewed_recipe_adapter', filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    kwargs = dict(shared_runner=shared_runner, petta=petta, steps=steps, seconds=seconds)
    if filename.name == 'base_runner.py': kwargs['fixture'] = fixture
    return await module.execute(request, **kwargs)
