"""Offline checks of this release: every pin matches its file, and the read-only app actions answer.

No host, PeTTa or network is needed. The sandboxed actions (run-native, run-foundation) are not run here;
they need an OmegaHive host with sandbox:run (see the README).
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_program():
    spec = importlib.util.spec_from_file_location("omega_tools_program", ROOT / "program.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("manifest", ["foundations/manifest.json", "foundations/concurrency/manifest.json"])
def test_foundation_source_pins_match(manifest):
    # The recipe runners refuse with "foundation-source-drift" / "concurrency-source-drift" if any pin differs.
    path = ROOT / manifest
    pins = json.loads(path.read_text())["source_pins"]
    drift = [name for name, pin in pins.items() if sha256(path.parent / name) != pin]
    assert drift == []


def test_release_lock_matches_every_listed_file():
    lock = json.loads((ROOT / "release-data.lock.json").read_text())["files"]
    drift = [name for name, pin in lock.items() if sha256(ROOT / name) != pin]
    assert drift == []


def test_banked_examples_still_bind_to_the_shipped_bytes():
    receipt = json.loads((ROOT / "evidence/all-tools-native-check.json").read_text())
    assert receipt["passed"] is True
    assert sha256(ROOT / "examples.json") == receipt["examples_sha256"]
    drift = [name for name, pin in receipt["native_sources"].items() if sha256(ROOT / name) != pin]
    assert drift == []


def test_view_lists_the_catalogue():
    program = load_program()
    graph = program.view(None, None, "unfold")
    kinds = {}
    for item in graph["items"]:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    assert kinds.get("tool") == 20
    assert kinds.get("set") == 12
    assert kinds.get("foundation", 0) >= 1


def test_every_tool_shows_its_banked_examples():
    program = load_program()
    graph = program.view(None, None, "unfold")
    revision = graph["revision"]
    tools = [item["id"] for item in graph["items"] if item["kind"] == "tool"]
    results = {tool: program.act(None, "show-examples", [tool], {"base_revision": revision}) for tool in tools}
    assert {tool: r["status"] for tool, r in results.items() if r["status"] != "done"} == {}
    assert all(r["detail"]["executed_now"] is False for r in results.values())


def test_every_set_can_be_inspected_and_composed():
    program = load_program()
    graph = program.view(None, None, "unfold")
    revision = graph["revision"]
    sets = [item["id"] for item in graph["items"] if item["kind"] == "set"]
    for set_id in sets:
        assert program.act(None, "inspect-set", [set_id], {"base_revision": revision})["status"] == "done"
    preview = program.act(None, "compose-set", sets[:1], {"base_revision": revision})
    assert preview["status"] == "done"


def test_a_stale_revision_is_refused():
    program = load_program()
    assert program.act(None, "show-examples", ["atom-recall"], {"base_revision": "old"})["status"] == "stale"
