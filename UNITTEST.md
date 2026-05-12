# UNITTEST.md — Base Reproducibility Tests

This file documents the four base tests in `tests/test_static_contract.py`.

The tests are intentionally small and use only the Python standard library. Their purpose is to prove that the repository is structurally coherent and reproducible in a clean container or GitHub Actions runner. They do not run an LLM agent and do not claim that behavioral fixtures pass with a specific model.

## How to run

Run from the repository root:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

For the full local check, run the validator first:

```bash
python tools/av_validate.py .
python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected result:

```text
VALIDATION PASSED — package is structurally valid.
test_01_static_validator_passes ... ok
test_02_process_md_guarantees_match_process_json ... ok
test_03_transition_semantics_are_explicit_and_consistent ... ok
test_04_fixture_inputs_and_acceptance_contracts_are_workable ... ok
```

## Test 1 — `test_01_static_validator_passes`

**Purpose:** prove that the package-level static validator passes in a clean Python stdlib environment.

**What it runs:**

```bash
python tools/av_validate.py .
```

**Success condition:**

- exit code is `0`;
- stdout contains `VALIDATION PASSED`.

**Why it matters:** this is the broadest smoke test. It checks required files, skills, process structure, schemas, examples, fixtures, prompts, public repo hygiene, artifact docs, and `PROCESS.md` alignment.

**Failure usually means:** a required file was removed, JSON no longer parses, `PROCESS.json` drifted from expected structure, fixtures are incomplete, or docs no longer match the canonical process contract.

## Test 2 — `test_02_process_md_guarantees_match_process_json`

**Purpose:** prevent drift between the human-readable guarantee table and the canonical machine-readable guarantee definitions.

**Inputs:**

- `PROCESS.json`
- `PROCESS.md`

**Validation logic:** for every guarantee row `G1`–`G8` in `PROCESS.json.guarantees`, the test requires this exact Markdown row in `PROCESS.md`:

```text
| GID | guarantee text |
```

**Success condition:** every guarantee text in `PROCESS.md` exactly matches `PROCESS.json`.

**Why it matters:** the essay and README may summarize the process, but `PROCESS.json` is the canonical contract. This test makes sure the main human-readable process document does not define a parallel, divergent guarantee model.

**Failure usually means:** someone changed a guarantee in `PROCESS.json` without updating `PROCESS.md`, or changed the wording in `PROCESS.md` without changing the canonical JSON.

## Test 3 — `test_03_transition_semantics_are_explicit_and_consistent`

**Purpose:** ensure that process transitions are deterministic and that skill-related fields are not ambiguous.

**Input:**

- `PROCESS.json`

**Validation logic:** each transition must satisfy all of the following:

1. The `(from, event)` pair is unique.
2. `event_owner_skill` is one of the declared skills or an allowed actor such as `System` or `User`.
3. If the target state is active, `next_skill` is a declared skill.
4. If the target state is active, legacy field `skill` equals `next_skill`.
5. If the target state is paused or terminal, `next_skill` is `null`.
6. The transition target is a known state.

**Success condition:** no duplicate transition pairs exist and every transition exposes unambiguous event-owner and next-skill semantics.

**Why it matters:** earlier versions used a single `skill` field that could be read as either the source skill or the next skill. v0.3 keeps `skill` only as a compatibility alias and relies on `event_owner_skill` plus `next_skill` for precise semantics.

**Failure usually means:** a transition was added without the new fields, a target state was misspelled, or two transitions now compete for the same `(state, event)` pair.

## Test 4 — `test_04_fixture_inputs_and_acceptance_contracts_are_workable`

**Purpose:** prove that the six behavioral fixtures have enough local input and expected-output metadata to be reproducible.

**Inputs:**

- `tests/fixtures/F1-clean/`
- `tests/fixtures/F2-ambiguous/`
- `tests/fixtures/F3-contradictory/`
- `tests/fixtures/F4-verify-failure/`
- `tests/fixtures/F5-non-convergence/`
- `tests/fixtures/F6-high-risk/`

**Validation logic:** for every fixture, the test checks:

1. `input/user-request.txt` exists.
2. `expected/acceptance.json` exists and parses.
3. `acceptance.json.fixture_id` matches the folder name.
4. `acceptance.json.expected_state` matches the expected fixture outcome.
5. `expected_state_class` is one of `terminal`, `paused`, or `active`.
6. `acceptance_criteria` is an object.
7. `minimum_observations` is an object.
8. All fixtures except `F2-ambiguous` contain a non-empty `input/target-package/`.
9. `F2-ambiguous` intentionally has no `target-package`, because it tests halt-on-ambiguity / no-guess behavior.

**Success condition:** fixture directories are complete enough for an external model/agent runner to execute the behavioral protocol in `EVALUATION_PROTOCOL.md`.

**Why it matters:** static tests should not merely check that fixture names exist. They should confirm that each fixture has a request, an expected state, and a concrete target package whenever the scenario requires one.

**Failure usually means:** a fixture is missing its request, its acceptance contract is malformed, or a target package was accidentally removed.

## What these tests do not prove

The base tests do not prove that:

- an LLM agent will pass F1–F6;
- a specific model is reliable;
- the process is globally minimal;
- the package is a production workflow engine;
- runtime behavior is deterministic inside the LLM.

They prove only that the v0.3 package is a coherent, inspectable, locally testable process artifact.

## Maintenance rule

When a test is added, removed, or materially changed, update this file in the same commit. If `PROCESS.json` changes, run all tests and update `PROCESS.md` only as a readable projection of the JSON contract.
