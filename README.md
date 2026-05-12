# Apply & Verify v0.3

Apply & Verify is a small, inspectable bootstrap package for **artifact-changing LLM-agent work**.

The project goal is to make an agent's work on files, code, configuration, and zip packages more controllable. Instead of relying on one long prompt, Apply & Verify gives the agent a process contract: skills, states, guards, schemas, fixtures, and tests. The language model may still reason probabilistically, but the package defines deterministic control over input binding, mutation authority, verification, evidence, and termination.

## Goal and objectives

**Goal:** provide a minimum sufficient process contract for tasks where an LLM agent must change an artifact and prove that the requested change was completed.

**Objectives:**

1. **Bind inputs before planning.** The agent must not create work items while mandatory inputs are missing, ambiguous, or contradictory.
2. **Separate planning, mutation, verification, and reflection.** A skill that changes files must not also certify success.
3. **Isolate mutation.** The agent must change only a candidate copy, not the original target package.
4. **Require evidence for completion.** `done=true` is valid only when `Verify` records evidence.
5. **Make failure observable.** Ambiguity, contradiction, unsupported requests, repeated failure, and high-risk requests must become explicit paused or terminal states.
6. **Keep the artifact portable.** The package uses Markdown, JSON, JSONL conventions, and Python stdlib tests so it can run in a plain container or GitHub Actions.

## What this project is not

Apply & Verify v0.3 is not a production workflow engine, not a universal agent framework, and not a claim that LLM inference becomes deterministic. It is a **reference process artifact**: a small repository that an agent, developer, or reviewer can inspect, run, test, and adapt.

## Process summary

The Stage-1 minimum real product uses seven skills:

| Skill | Role |
|---|---|
| `Intake` | Normalize the raw request and classify the intent. |
| `BindParameters` | Bind required inputs such as target package, issue source, mutation boundary, output target, and risk profile. |
| `AskQuestions` | Pause safely when required information is missing or ambiguous. |
| `Plan` | Convert a bound request into atomic work items in `state/works.json`. |
| `Apply` | Apply work items to a candidate copy only. |
| `Verify` | Check the candidate and set `done=true` only with evidence. |
| `Reflect` | Decide success, loop, human escalation, unsupported halt, or non-convergence halt. |

The four-skill loop `Plan / Apply / Verify / Reflect` is only the kernel. A real user-facing product also needs `Intake / BindParameters / AskQuestions` so the agent does not silently guess missing inputs.

## Topology

```text
apply-and-verify/
  README.md                         project overview and usage
  SKILLS.md                         human-readable skill contracts
  PROCESS.md                        human-readable process contract
  PROCESS.json                      canonical machine-readable process contract
  FixPrompt.txt                     operator prompt for Intake/Bind/Ask/Plan/Apply
  ReflectionPrompt.txt              operator prompt for Verify/Reflect
  CHANGELOG.md                      release history
  ARTIFACT.md                       artifact inventory and claim boundary
  CODE_AVAILABILITY.md              code availability statement template
  EVALUATION_PROTOCOL.md            fixture execution protocol
  RESULTS_TEMPLATE.csv              table template for behavioral runs
  UNITTEST.md                       detailed description of base tests
  schemas/                          JSON schemas for process and state artifacts
  examples/                         valid example inputs and state artifacts
  tests/
    test_static_contract.py         four Python stdlib reproducibility tests
    fixtures/F1-clean/              happy path fixture
    fixtures/F2-ambiguous/          missing target / clarification fixture
    fixtures/F3-contradictory/      contradictory input fixture
    fixtures/F4-verify-failure/     verify-failure then repair fixture
    fixtures/F5-non-convergence/    repeated failure fixture
    fixtures/F6-high-risk/          destructive/high-risk halt fixture
  tools/
    av_validate.py                  static contract validator
```

### Canonical sources

| Topic | Canonical file |
|---|---|
| States, transitions, guards, guarantees, authority matrix | `PROCESS.json` |
| Human explanation of process semantics | `PROCESS.md` |
| Skill contracts | `SKILLS.md` |
| Static validation rules | `tools/av_validate.py` |
| Base reproducibility tests | `tests/test_static_contract.py` and `UNITTEST.md` |
| Behavioral fixture protocol | `EVALUATION_PROTOCOL.md` |

When Markdown and JSON differ, treat `PROCESS.json` as the canonical process contract.

## How to validate and test

Run from the repository root:

```bash
python tools/av_validate.py .
python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected result:

```text
VALIDATION PASSED — package is structurally valid.
Ran 4 tests ... OK
```

These commands are intentionally stdlib-only. They test the package structure, process contract, examples, fixture preconditions, and documentation alignment. They do **not** execute an LLM agent and do **not** prove fixture behavioral success.

## How to use it with an LLM agent

Use this package as a working directory or as a bootstrap zip for another agent session.

1. Put the source package or files to be changed into a target input location.
2. Give the agent `README.md`, `SKILLS.md`, `PROCESS.json`, `PROCESS.md`, and the relevant prompt file.
3. Require the agent to create runtime output under `state/` only.
4. Require the agent to follow the seven-skill flow in `PROCESS.json`.
5. Require every completed work item in `state/works.json` to have an `evidence_refs` entry.
6. Run `python tools/av_validate.py .` before and after package-level changes.
7. Record behavioral runs using `RESULTS_TEMPLATE.csv` and the protocol in `EVALUATION_PROTOCOL.md`.

Typical runtime state files:

```text
state/run-state.json
state/intake-result.json
state/parameter-bindings.json
state/questions.json
state/works.json
state/issues.partN.jsonl
state/events.jsonl
state/candidate/vN/
state/verification-report.md
state/reflect-summary.iterN.md
```

`state/` is runtime output and is ignored by git.

## How to change the package safely

For small maintenance changes:

1. Edit only the files required by the change.
2. If process semantics change, update `PROCESS.json` first.
3. Update `PROCESS.md` only as a projection of `PROCESS.json`.
4. If a schema changes, update the matching example file and test/fixture data.
5. If a test changes, update `UNITTEST.md` in the same commit.
6. If a fixture changes, update `EVALUATION_PROTOCOL.md` or the fixture's `expected/acceptance.json`.
7. Update `CHANGELOG.md`.
8. Run:

```bash
python tools/av_validate.py .
python -m unittest discover -s tests -p 'test_*.py' -v
```

For larger process changes, use a new version branch and keep the old package reproducible until the new validator and tests pass.

## Base tests

`UNITTEST.md` documents the four reproducible base tests:

1. static validator pass;
2. guarantee alignment between `PROCESS.md` and `PROCESS.json`;
3. explicit transition semantics and deterministic transition pairs;
4. fixture input and acceptance-contract workability.

## Current version

Current package version: **v0.3**.
