"""Tools catalogue plus default-denied, advisory agent action via shared sandbox.

Keep this directory within the candidate package: catalogue and source pins
are its only data. The host owns presentation and authorisation.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _foundations():
    return json.loads((ROOT / "foundations/catalogue.json").read_text())


def _data():
    cat_bytes = (ROOT / "catalogue.json").read_bytes()
    source_bytes = (ROOT / "sources.json").read_bytes()
    example_bytes = (ROOT / "examples.json").read_bytes()
    receipt_bytes = (ROOT / "evidence/all-tools-native-check.json").read_bytes()
    set_bytes = (ROOT / "capability-sets.json").read_bytes()
    foundation_bytes = b"".join(p.read_bytes() for p in sorted((ROOT / "foundations").iterdir()) if p.is_file())
    admission_bytes = b"".join((ROOT / name).read_bytes() for name in
                              ('admission.json', 'wire-examples.json', 'evidence/all-tools-pack-check.json')
                              if (ROOT / name).is_file())
    return (json.loads(cat_bytes)["tools"], json.loads(source_bytes)["sources"], json.loads(set_bytes),
            hashlib.sha256(cat_bytes + source_bytes + example_bytes + receipt_bytes
                           + set_bytes + foundation_bytes + admission_bytes + (ROOT / "tools/compose_sets.py").read_bytes()
                           + Path(__file__).read_bytes()).hexdigest())


def describe():
    descriptor = {"contract": "0.2", "kinds": [
        {"id": "tool", "label": "Skill candidate", "role": "other"},
        {"id": "set", "label": "Composable capability set", "role": "other"},
        {"id": "foundation", "label": "MeTTa / AtomSpace foundation", "role": "other"},
        {"id": "component", "label": "Owner component proposal", "role": "other"},
        {"id": "source", "label": "Historical source", "role": "evidence"}],
        "relations": [{"id": "derives-from", "label": "derived from", "polarity": "qualify"},
                      {"id": "contains", "label": "includes sample", "polarity": "qualify"}],
        "actions": [
            {"id": "inspect-component", "label": "Inspect component qualification and bindings", "applies_to": ["component"], "stage": "detail"},
            {"id": "inspect-foundation", "label": "Inspect primitive and recipe contract", "applies_to": ["foundation"], "stage": "detail"},
            {"id": "foundation-examples", "label": "See isolated recipe examples", "applies_to": ["foundation"], "stage": "detail"},
            {"id": "inspect-set", "label": "Inspect set and extension slots", "applies_to": ["set"], "stage": "detail"},
            {"id": "compose-set", "label": "Preview a custom composition", "applies_to": ["set"], "stage": "detail", "binding_params": ["recipe"]},
            {"id":"run-native", "label":"Run selected advisory skill", "applies_to":["tool"], "agents":True, "binding_params":["skill","arguments","review_receipt"]},
            {"id":"run-foundation", "label":"Run a typed transient MeTTa recipe", "applies_to":["foundation"], "agents":True, "binding_params":["request","review_receipt"]},
            {"id": "inspect-tool", "label": "Inspect skill", "applies_to": ["tool"], "stage": "detail"},
            {"id": "show-examples", "label": "See tested examples", "applies_to": ["tool"], "stage": "detail"},
            {"id": "inspect-source", "label": "Inspect provenance", "applies_to": ["tool", "source"], "stage": "detail"}]}
    for action in descriptor["actions"]:
        action.update(agents=True, effect="read")
    return descriptor



def _source(s):
    # Return technical provenance metadata, never the contents of arbitrary paths.
    return {"id": s["id"], "label": s["label"], "kind": "document",
            "status": "inspected", "local_ref": s["id"],
            "locator": "SHA-256 " + s["sha256"], "origin": "historical technical corpus"}


def view(ctx, focus, stage):
    tools, sources, registry, revision = _data()
    sets = registry["sets"]
    foundations = _foundations()["cards"]
    components = registry.get("owner_registrations", [])
    component_id = lambda c: "component:" + c["id"] + "@" + c["version"]
    smap = {s["id"]: s for s in sources}
    all_ids = {t["id"] for t in tools} | set(smap) | {"set:" + s["id"] for s in sets} | {"foundation:" + f["id"] for f in foundations} | {component_id(c) for c in components}
    focus = focus if focus in all_ids else None
    if stage == "detail" and focus:
        foundations = [f for f in foundations if "foundation:" + f["id"] == focus]
        chosen_set = next((s for s in sets if "set:" + s["id"] == focus), None)
        components = [c for c in components if component_id(c) == focus or (chosen_set and c["family"] == chosen_set["id"])]
        tools = [t for t in tools if t["id"] == focus or focus in t["source_ids"] or (chosen_set and t["id"] in chosen_set["members"])]
        sets = [s for s in sets if "set:" + s["id"] == focus or (not chosen_set and any(t["id"] in s["members"] for t in tools))]
        wanted = {sid for t in tools for sid in t["source_ids"]} | ({focus} if focus in smap else set())
        sources = [s for s in sources if s["id"] in wanted]
    else:
        wanted = {sid for t in tools for sid in t["source_ids"]}
        sources = [s for s in sources if s["id"] in wanted]
    items = [{"id": t["id"], "kind": "tool", "label": t["name"],
              "text": t["adds"] + "\n\nThis sample implements: " + t.get("sample_scope", t["adds"])
                      + "\n\nQualification: " + t["claim_ceiling"]
                      + "\nStage: " + t["stage"] + "\nEffect authority: none in this candidate.",
              "sources": [_source(smap[sid]) for sid in t["source_ids"]], "meta": t} for t in tools]
    items += [{"id": s["id"], "kind": "source", "label": s["label"],
               "text": s["basis"], "sources": [_source(s)]} for s in sources]
    items += [{"id": "set:" + s["id"], "kind": "set", "label": s["label"],
               "text": "Features: " + ", ".join(s["features"]) + "\n\n" + s["status"]
                       + "\nUnadmitted or unbound extension slots: " + ", ".join(x["role"] for x in s["slots"] if x["default"] is None)
                       + "\nMix sets and replace exact versioned components. Preview does not install or grant authority.",
               "meta": s, "sources": []} for s in sets]
    items += [{"id": "foundation:" + f["id"], "kind": "foundation", "label": f["label"],
               "text": "Operations: " + ", ".join(f["operations"]) + "\nOrigin: " + f["origin_kind"]
                       + "\nQualification: " + f["qualification"] + "\n" + f["note"],
               "meta": f, "sources": []} for f in foundations]
    items += [{"id": component_id(c), "kind": "component", "label": c["id"] + " " + c["version"],
               "text": "Family: " + c["family"] + "\nSlot: " + c["slot"] + "\nState: " + c["index_state"]
                       + "\nBlockers: " + "; ".join(c["blockers"])
                       + "\nRuntime admitted: false. Source bindings are an intake snapshot; revalidate before admission.",
               "meta": c, "sources": []} for c in components]
    return {"revision": revision, "title": "Tools — skills of thought and action", "focus": focus,
            "suggested_stage": stage, "items": items,
            "links": [{"id": t["id"] + "|" + sid, "from": t["id"], "to": sid,
                       "rel": "derives-from"} for t in tools for sid in t["source_ids"]]
                     + [{"id": "set:" + s["id"] + "|" + t["id"], "from": "set:" + s["id"], "to": t["id"],
                         "rel": "contains"} for s in sets for t in tools if t["id"] in s["members"]]
                     + [{"id": "set:" + s["id"] + "|" + component_id(c), "from": "set:" + s["id"], "to": component_id(c),
                         "rel": "contains"} for s in sets for c in components if c["family"] == s["id"]],
            "groups": [{"id": c, "label": "Skills of " + c,
                        "items": [t["id"] for t in tools if t["category"] == c]} for c in ["thought", "action"]]
                      + [{"id": "sets", "label": "Composable sets", "items": ["set:" + s["id"] for s in sets]},
                         {"id": "foundations", "label": "MeTTa / AtomSpace Foundations", "items": ["foundation:" + f["id"] for f in foundations]},
                         {"id": "components", "label": "Owner component proposals", "items": [component_id(c) for c in components]}],
            "notes": ["Historical examples are offline qualifications, not current runtime observations.",
                      "Native actions calculate advisory data in transient sandbox jobs. No provider, persistence or actuator authority."]}


def act(ctx, action, items, params):
    if action == "run-native":
        return _run_native(ctx, items, params)
    if action == "run-foundation":
        return _run_foundation(ctx, items, params)
    tools, sources, registry, revision = _data()
    if params.get("base_revision") != revision:
        return {"status": "stale", "message": "Refresh the catalogue before inspecting."}
    if action == "inspect-component":
        selected = [c for c in registry.get("owner_registrations", []) if "component:" + c["id"] + "@" + c["version"] in items]
        if not items or len(selected) != len(items): return {"status":"refused", "message":"Choose distinct known component proposals."}
        return {"status":"done", "detail":{"components":selected,"authority":"none","executed_now":False,"runtime_admitted":False}}
    if action in {"inspect-foundation", "foundation-examples"}:
        cards = [f for f in _foundations()["cards"] if "foundation:" + f["id"] in items]
        if not items or len(cards) != len(items):
            return {"status": "refused", "message": "Choose distinct known foundations."}
        detail = {"cards": cards, "manifest": json.loads((ROOT / "foundations/manifest.json").read_text()),
                  "authority": "none", "executed_now": False, "installation": "not installed"}
        if (ROOT / 'evidence/all-tools-pack-check.json').is_file():
            detail['execution_binding'] = {'program': 'omega-tools', 'action': 'run-foundation',
                'review_receipt': hashlib.sha256((ROOT / 'evidence/all-tools-pack-check.json').read_bytes()).hexdigest(),
                'request_schema': json.loads((ROOT / 'foundations/request.schema.json').read_text()),
                'requires': 'explicit host action grant and sandbox allowlist; fixed recipes, job-local state only'}
        if action == "foundation-examples":
            selected = {r for f in cards for r in f["recipes"]}
            detail["examples"] = [c for c in json.loads((ROOT / "foundations/examples.json").read_text())["cases"] if c["request"]["recipe"] in selected]
        return {"status": "done", "detail": detail}
    if action in {"inspect-set", "compose-set"}:
        selected = [s for s in registry["sets"] if "set:" + s["id"] in items]
        if not items or len(selected) != len(items):
            return {"status": "refused", "message": "Choose distinct known sets."}
        if action == "inspect-set":
            donors = {d for s in selected for d in s["historical_donor_ids"]}
            return {"status": "done", "detail": {"sets": selected,
                    "extension_contracts": registry["extension_contracts"],
                    "historical_donors": [d for d in registry["historical_donors"] if d["id"] in donors],
                    "authority": "none", "installation": "not installed"}}
        recipe = params.get("recipe", {"schema": "omega-tools-recipe/v1", "sets": [s["id"] for s in selected]})
        if type(recipe) is not dict or recipe.get("sets") != [s["id"] for s in selected]:
            return {"status": "refused", "message": "Recipe must match selected sets in catalogue order."}
        spec = importlib.util.spec_from_file_location("omega_tools_composition", ROOT / "tools/compose_sets.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            preview = module.compose(registry, recipe)
        except (ValueError, TypeError) as exc:
            return {"status": "refused", "message": str(exc)}
        return {"status": "done", "detail": preview}
    if action not in {"inspect-tool", "inspect-source", "show-examples"} or not items:
        return {"status": "refused", "message": "Choose a supported inspection and an item."}
    tmap, smap = {t["id"]: t for t in tools}, {s["id"]: s for s in sources}
    if any(i not in tmap and i not in smap for i in items):
        return {"status": "refused", "message": "Unknown item; no path is read."}
    if action in {"inspect-tool", "show-examples"} and any(i not in tmap for i in items):
        return {"status": "refused", "message": "Inspect skill requires skill items."}
    selected = [tmap[i] for i in items if i in tmap]
    if action == "inspect-tool" and (ROOT / 'admission.json').is_file():
        schema = json.loads((ROOT / 'admission.json').read_text())
        names = {name for t in selected for name in t['skills']}
        needed = set()
        def visit(spec):
            if isinstance(spec, str):
                if spec in needed: return
                needed.add(spec); visit(schema['types'][spec])
            elif isinstance(spec, dict):
                for key in ('fields', 'choices'):
                    for child in spec.get(key, []): visit(child)
                if 'item' in spec: visit(spec['item'])
        for name in names:
            for field in schema['skills'][name]['arguments']: visit(field)
        pack = ROOT / 'evidence/all-tools-pack-check.json'
        specs = [json.loads((ROOT / 'modules' / t['sample'] / 'spec.json').read_text()) for t in selected]
        detail = {'tools': selected, 'authority': 'none', 'executed_now': False,
                  'input_contract': {'schema': schema['version'], 'limits': schema['limits'],
                                     'skills': {name: schema['skills'][name] for name in sorted(names)},
                                     'types': {name: schema['types'][name] for name in sorted(needed)}},
                  'execution_binding': {'program': 'omega-tools', 'action': 'run-native',
                                        'review_receipt': hashlib.sha256(pack.read_bytes()).hexdigest(),
                                        'module_selection': [x['module_id'] + '@' + x['version'] for x in specs],
                                        'requires': 'host app grant plus exact selected module; sandbox allowlist; no provider calls'},
                  'sources': [_source(s) for s in sources if s['id'] in {sid for t in selected for sid in t['source_ids']}]}
        if (ROOT / 'wire-examples.json').is_file():
            detail['wire_examples'] = [c for c in json.loads((ROOT / 'wire-examples.json').read_text())['cases'] if c['skill'] in names]
        return {'status': 'done', 'detail': detail}
    if action == "show-examples":
        receipt = json.loads((ROOT / "evidence/all-tools-native-check.json").read_text())
        if not receipt["passed"]:
            return {"status": "refused", "message": "Banked checks are not passing."}
        if hashlib.sha256((ROOT / "examples.json").read_bytes()).hexdigest() != receipt["examples_sha256"]:
            return {"status": "stale", "message": "Example definitions changed; rerun isolated checks."}
        for tool in selected:
            if not any(r["tool"] == tool["id"] for r in receipt["results"]):
                return {"status": "refused", "message": "This tool has no banked examples."}
            prefix = "modules/" + tool["sample"] + "/"
            for relative, expected in receipt["native_sources"].items():
                if not relative.startswith(prefix):
                    continue
                file = (ROOT / relative).resolve()
                if not file.is_relative_to((ROOT / "modules" / tool["sample"]).resolve()):
                    return {"status": "refused", "message": "Invalid source binding."}
                if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                    return {"status": "stale", "message": "Sample bytes changed; rerun isolated checks."}
        return {"status": "done", "detail": {"scope": receipt["scope"],
                "recorded_at": receipt["recorded_at"], "executed_now": False,
                "examples": [r for r in receipt["results"] if r["tool"] in items],
                "authority": "none", "installation": "not installed"}}
    ids = set(i for i in items if i in smap) | {sid for t in selected for sid in t["source_ids"]}
    return {"status": "done", "detail": {"tools": selected,
            "sources": [_source(s) for s in sources if s["id"] in ids],
            "authority": "none", "installation": "not installed"}}


async def _run_native(ctx,items,params):
    if ctx is None or items:
        return {'status':'refused','message':'Authenticated mind action required; no item/path selection.'}
    from hive.core.tools import run_for_actor
    result=await run_for_actor(ctx,params)
    return {'status':'done' if result['kind'] in ('ToolResult','ToolLimitExceeded') else 'refused',
            'message':'Advisory data only; no persistence or effect authority.', 'detail':result}


async def _run_foundation(ctx, items, params):
    if ctx is None or items:
        return {'status':'refused', 'message':'Authenticated mind action required; no item/path selection.'}
    from hive.core.tools import run_for_actor
    result = await run_for_actor(ctx, params, foundation=True)
    return {'status':'done' if result['kind'] in ('FoundationResult', 'FoundationLimitExceeded', 'ConcurrencyResult', 'ConcurrencyLimitExceeded') else 'refused',
            'message':'Transient job results only; no persistent AtomSpace or effect authority.', 'detail':result}
