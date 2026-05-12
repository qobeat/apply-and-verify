# Changelog

## v0.3 — 2026-05-12

- Bumped package version to `v0.3`.
- Rewrote `README.md` with human-readable goal, objectives, topology, usage instructions, and safe-change workflow.
- Added `UNITTEST.md` with detailed descriptions of the four base reproducibility tests.
- Added `UNITTEST.md` to static validator required-file checks.
- Updated `RESULTS_TEMPLATE.csv` to reference `v0.3`.

## 0.2.1-stage1 — 2026-05-12

- Synchronized `PROCESS.md` guarantee text exactly with `PROCESS.json.guarantees`.
- Clarified transition semantics with `event_owner_skill` and `next_skill` while retaining legacy `skill` for compatibility.
- Added `transition_field_semantics` to `PROCESS.json` and updated `schemas/process.schema.json`.
- Added schema-instance checks for examples and fixture acceptance files to `tools/av_validate.py` without third-party dependencies.
- Added fixture workability checks for required `input/target-package/` folders.
- Added `EVALUATION_PROTOCOL.md` and `RESULTS_TEMPLATE.csv`.
- Added four reproducible stdlib tests in `tests/test_static_contract.py`.

## 0.2.0-stage1 — 2026-05-12

- Introduced seven-skill minimum real-product process.
- Added `PROCESS.json` finite-state process contract.
- Added machine-readable authority matrix, guards, and guarantees.
- Added schemas for mutable state artifacts.
- Added F1-F6 behavioral fixtures.
- Added static package validator `tools/av_validate.py`.
- Kept essay/research manuscript materials out of the public code package.

## 0.1.0 — initial bootstrap

- Four-skill kernel: Plan / Apply / Verify / Reflect.
- Two-prompt package repair loop.
