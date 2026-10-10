# Contributing to Omega Tools

Thanks for helping. This is short on purpose.

## Before you start

Set up with the exact versions in the README ("Requirements" and "Test"). If a step fails or needs a guess,
that is a bug in our docs; please open an issue.

## Branch and pull request

- Branch from `main`, one change per pull request.
- Keep commits focused. Say what changed, why, and how you tested it.

## Tests

- `python -m pytest -q tests` (see the README for the environment).
- The contract check: `python -m hive.programs_check ../omega-tools` from an OmegaHive checkout.
- A change to any pinned file must update the pins that cover it (`foundations/manifest.json`,
  `foundations/concurrency/manifest.json`, `release-data.lock.json`); `tests/` checks them.
- A change to a module's MeTTa sources or to `examples.json` makes the banked receipts in `evidence/` stale:
  rerun the isolated checks and bank a new receipt rather than editing the old one.

## Review: two reviewers

Every change needs **two independent reviews** before merge, and neither reviewer may be the author. Code
written with a language model must be read and understood by the person who submits it. A review is void if
the change is altered after it.

## Data and secrets

- Only synthetic data in tests, fixtures and examples: no real people, no private records, no personal paths.
- No secrets: no `.env` files, keys, tokens or sign-in files (see `SECURITY.md`).

## Versioning

The app is versioned on its own (`version` in `plugin.json`), with a `CHANGELOG.md` entry for every release.
`plugin.json` also states the program contract it implements. Deployments pin an exact release by digest
(`HIVE_APP_PINS` in OmegaHive), never by a version string.

## Licence

This repository is open source under Apache-2.0 (`LICENSE`). By submitting a contribution you confirm you
have the right to contribute it under that licence.

## Conduct

See `CODE_OF_CONDUCT.md`.
