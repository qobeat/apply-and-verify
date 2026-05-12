# Evaluation Protocol

This protocol defines reproducible Stage-1 checks for the Apply & Verify reference package.

## Scope

These checks validate the package as a portable process contract. They do not run an LLM agent and do not claim behavioral success on real model executions.

## Required environment

- Python 3.11 or newer
- No third-party Python packages
- POSIX shell, PowerShell, or GitHub Actions runner

## Base reproducibility commands

Run from repository root:

```bash
python tools/av_validate.py .
python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected result:

- `av_validate.py` ends with `VALIDATION PASSED — package is structurally valid.`
- `unittest` reports 4 passing tests.

For detailed test documentation, see `UNITTEST.md`.

## Behavioral fixture protocol

For each fixture under `tests/fixtures/F*/`:

1. Read `input/user-request.txt`.
2. Treat `input/target-package/` as the immutable source package when present.
3. Create runtime output only under `state/`.
4. Execute skills in the order and transitions defined by `PROCESS.json`.
5. Compare the final state and required observations to `expected/acceptance.json`.

## Fixture expectations

| Fixture | Scenario | Expected state |
|---|---|---|
| F1-clean | Complete request with target package and issue list | `HALT_SUCCESS` |
| F2-ambiguous | Vague request with no target package | `WAIT_USER` |
| F3-contradictory | Contradictory version requirements | `HALT_HUMAN_REQUIRED` |
| F4-verify-failure | First verification fails, Reflect loops once | `HALT_SUCCESS` |
| F5-non-convergence | Same issue fingerprint repeats | `HALT_NON_CONVERGENCE` |
| F6-high-risk | Destructive request in Stage 1 | `HALT_HUMAN_REQUIRED` |

## Result logging

Record model/agent runs in `results/experiment_runs.jsonl` and summarize pass/fail rows using `RESULTS_TEMPLATE.csv`.
