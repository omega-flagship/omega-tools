# Status: Omega Tools 0.6.3

Tier: Open (Apache-2.0). Checked on 2026-10-10.

## What works

- **Catalogue and read actions.** 20 modules, 12 capability sets and the foundation recipes are listed by `view()`;
  every tool shows its banked examples and every set can be inspected and composed (`tests/`).
- **Tests.** `python -m pytest -q tests` in a fresh Python 3.12.13 venv with `requirements-dev.txt`:
  **8 passed** (0.1 s, no host, PeTTa or network).
- **Contract check.** `python -m hive.programs_check ../omega-tools` on omegahive `7b1ce3f`: **COMPATIBLE**
  (views valid in every stage, ids stable, 80 items).
- **Concurrency recipes on real PeTTa.** `foundations/concurrency/check_conformance.py` against omegahive
  `7b1ce3f`, PeTTa `ae66fa8` and the shared OS sandbox: **44 of 45 checks passed**. The one failure,
  `qualified-host-revision-unchanged`, is the pin to the original qualifying platform commit, which is not in the
  published history.
- **Rerun after the rename (2026-10-10, omegahive `e4571e9`, PeTTa `ae66fa8`):** tests **8 passed**; contract check
  **COMPATIBLE** (80 items); concurrency conformance **44 of 45** (the same expected failure). The native check of
  the module examples was not rerun (see below).
- **Pins hold.** The foundation runners' source pins match the shipped files, so `run-foundation` is not refused
  for drift (this was broken in the first handover snapshot and is fixed here; `tests/` now guards it).

## Limited or known broken

- **Advisory only.** Modules and recipes return advisory data with `authority none`; nothing here performs an
  effect or writes persistent AtomSpace state.
- **Callers are not qualified.** Running `run-native` / `run-foundation` from a live mind needs a host with
  `sandbox:run`, a PeTTa runtime and an exact grant; that end-to-end path was not run for this handover.
- **Banked evidence is historical.** `evidence/*.json` records the reviewed 0.6.3 bytes; its entries for the
  files changed in this handover name the originals.
- **Version skew.** The organisation's cloud hive runs 0.6.3; the project lead's local test hive still ran 0.6.1
  at handover time.
- **Owner-workspace references in data.** `capability-sets.json` (owner component registrations) names files
  under the owner's private `coordination/` workspace with their sha256 values. They are provenance records,
  not links, and are not readable from this repository.
- **Personal names renamed (fixed in the handover copy, not yet in the owner's tree).** The standing-values
  jurisdiction symbols are now `mind-self` and `owner-joint` (were named after the mind and the owner) in
  `modules/tools_standing_values/src/law.metta:18`, `examples.json`, `wire-examples.json` and the banked receipts;
  the Goal Weaver comment (`modules/tools_goal_compass/src/law.metta:10`) and the source origin label in
  `program.py` no longer name the mind. The module `exports.json` pins, `release-data.lock.json` and the receipts'
  file pins were updated to the new bytes.
- **The banked native-check receipt predates the rename.** `evidence/all-tools-native-check.json` (and the pack
  check) record a run on the pre-rename bytes; they were amended textually (each carries a `handover_amendment`
  field) and were **not re-run** on real PeTTa. Re-run and re-bank the native check before relying on it for the
  renamed symbols.
