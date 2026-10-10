# Changelog

## 0.6.3 (handover, 2026-10-10)

Prepared for the private SingularityNET handover. Module MeTTa sources, examples and the program are unchanged.

- Fixed: the foundation source pins (`foundations/manifest.json`, `foundations/concurrency/manifest.json`) did not
  match `foundations/concurrency/check_conformance.py` after its owner paths were removed, so every
  `run-foundation` call would have been refused with `foundation-source-drift`. The pins now match.
- `check_conformance.py`: host, PeTTa and venv come from `OMEGAHIVE_PATH`, `PETTA_PATH` and `OMEGA_VENV`; its
  receipt is written inside this repository.
- `module.toml` credits name roles, not people; one personal custody note in `sources.json` reworded.
- `LICENSE`: stray third-party appendix removed. `NOTICE`: PeTTa added.
- Added `tests/` (8 offline tests), `requirements-dev.txt`, STATUS, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY,
  this changelog and `.github/repo-description.txt`.
- `release-data.lock.json` updated for every changed file.

## 0.6.3

Installed release: 20 advisory modules, 12 capability sets and eight typed MeTTa recipes (contract 0.2).
