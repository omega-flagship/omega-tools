# Omega Tools

Tools is the OmegaHive app for modular skills of thought and action: 20 advisory modules, 12 capability sets and
eight typed, transient MeTTa recipes, each with declared provenance and synthetic, banked examples. People browse
the catalogue and examples; minds invoke a module or recipe only through an exact host grant and the hive's
sandbox (`sandbox:run`).

**Tier:** Open source, Apache-2.0 (`LICENSE`). Inherited and third-party notices (OmegaClaw Core, PeTTa) are in
`NOTICE`.

This repository is release **0.6.3** (program contract 0.2), the release installed on the organisation's hive,
with the handover changes listed in "Differences from the reviewed 0.6.3 bytes". Host source digest of this tree:
`sha256:1b699b67c07fcd08d5e9d7125094f47427cae92e7da93961a9923653928b569d`.

| Path | What |
|---|---|
| `plugin.json`, `program.py` | App identity and the host program (`describe` / `view` / `act`) |
| `catalogue.json`, `capability-sets.json`, `examples.json`, `wire-examples.json`, `admission.json`, `sources.json` | The catalogue, sets, examples, admission record and source pins |
| `modules/` | The 20 modules (MeTTa sources, `module.toml`, `spec.json`) |
| `foundations/` | Typed MeTTa recipes, schemas and the sandboxed runner |
| `tools/` | Set composition helper |
| `evidence/` | The banked review receipts for 0.6.3 (historical; hashes refer to the reviewed bytes) |
| `release-data.lock.json` | Per-file sha256 lock of this tree |
| `tests/` | Offline release-integrity and read-action tests |

## Requirements

- **OmegaHive** (the `omegahive` repository) and its Python **3.12** environment. The app imports only the
  standard library; the host provides the sandbox.
- **pytest** for the tests (tested with pytest 9.1.1).
- For the sandboxed actions and the maintainer conformance check: **PeTTa at commit `ae66fa8`** with
  **SWI-Prolog 10.1.14** and **janus-swi 1.5.3** built against the same Python 3.12, as described in the
  omegahive README ("Prerequisites"), and **jsonschema** (tested with 4.26.0).

## Quick start (mount in a hive)

1. Add this folder (the repository root) to `HIVE_PLUGIN_DIRS`.
2. Add `omega-tools` to `HIVE_SANDBOX_RUN_APPS` and give `HIVE_SANDBOX_RUNTIMES` a `metta` runtime whose Python
   can import PeTTa; set `PETTA_PATH`.
3. Optionally pin this exact tree with `HIVE_APP_PINS` (folder plus the digest above), and choose its home
   swarms with `HIVE_APP_HOMES`.
4. Restart the hive. People see the catalogue; a mind can run a module or recipe only through an exact host grant
   with the `run-native` / `run-foundation` actions.

## Test

From this folder, in a fresh Python 3.12 virtual environment:

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q tests                   # 8 tests, no host, PeTTa or network needed
```

They check that every pin matches its file (the recipe runners refuse to start on any mismatch), that the banked
examples still bind to the shipped bytes, and that the read-only actions answer for every tool and set.

Contract check (no PeTTa needed), with OmegaHive checked out next to this repository:

```sh
cd ../omegahive
python -m hive.programs_check ../omega-tools          # COMPATIBLE, 80 items
```

Maintainer conformance check of the concurrency recipes (needs PeTTa, the sandbox and a clean OmegaHive git
checkout; it writes `evidence/concurrency-r1-conformance.json`):

```sh
export PATH=$HOME/swipl-patched/bin:$PATH             # the SWI-Prolog 10.1.14 built for PeTTa
export PETTA_PATH=<PeTTa checkout> OMEGA_VENV=<the Python 3.12 venv that imports PeTTa>
export OMEGAHIVE_PATH=../omegahive                    # default: ../omegahive
python foundations/concurrency/check_conformance.py
```

On omegahive `7b1ce3f` this gives 44 of 45 checks passed. The one failure, `qualified-host-revision-unchanged`,
is expected: the check pins the platform commit the recipes were originally qualified on, which is not in the
published omegahive history.

## Differences from the reviewed 0.6.3 bytes

- `LICENSE`: Apache-2.0 (the original MIT notice is in `NOTICE`); the stray third-party appendix is removed.
- `NOTICE`: adds PeTTa.
- `modules/*/module.toml`: the `maker` credit names roles, not people.
- `sources.json`: one custody note reworded without personal history.
- `foundations/concurrency/check_conformance.py`: takes the host, PeTTa and venv from `OMEGAHIVE_PATH`,
  `PETTA_PATH` and `OMEGA_VENV` instead of owner paths, and writes its receipt into this repository.
- `foundations/manifest.json`, `foundations/concurrency/manifest.json`: source pins updated for the changed
  files, so the recipe runners' drift check passes (in the first handover snapshot it did not, and every
  `run-foundation` call would have been refused with `foundation-source-drift`).
- `release-data.lock.json`: updated for every changed file.
- Added `tests/`, `requirements-dev.txt` and the project documents.

- `modules/tools_standing_values/src/law.metta`, `examples.json`, `wire-examples.json`: the jurisdiction symbols
  `mind-self` and `owner-joint` replace the originals, which carried personal names. `modules/tools_goal_compass/src/law.metta`:
  one comment reworded. `program.py`: the source origin label reworded. The two modules' `exports.json` pins follow.

The receipts in `evidence/` are otherwise kept as recorded, so their entries for the earlier-changed files name the
reviewed originals. For the rename they were amended textually (`handover_amendment` field: calls, outputs and pins
of the renamed files), not re-run; re-bank the native check on real PeTTa before relying on it.

## How it plugs into OmegaHive

OmegaHive loads apps ("Dot programs") from the folders in `HIVE_PLUGIN_DIRS`. For Tools that folder is **this
repository's root**: it holds `plugin.json` and `program.py`, which implement program contract 0.2 (described in
`hive/PROGRAMS.md` in the omegahive repository).

- `view()` returns the catalogue: tools, sets, foundations, owner component proposals and their sources.
- Read actions (`inspect-tool`, `show-examples`, `inspect-set`, `compose-set`, `inspect-foundation`, ...) need the
  current view revision as `base_revision` and never execute anything.
- `run-native` and `run-foundation` run a selected module or recipe in the host sandbox through
  `hive.core.tools`, only for an authenticated mind with an exact grant, and only while the pins match.

## Licence

Apache-2.0 (`LICENSE`); inherited and third-party notices are in `NOTICE`.
