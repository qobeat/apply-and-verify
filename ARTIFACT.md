# Artifact Inventory

This repository is intended to be a public research/code artifact for the Apply & Verify process contract.

## Included

- process contract: `PROCESS.md`, `PROCESS.json`;
- skill contracts: `SKILLS.md`;
- operator prompts: `FixPrompt.txt`, `ReflectionPrompt.txt`;
- schemas: `schemas/*.schema.json`;
- fixtures: `tests/fixtures/F1-*` through `F6-*`;
- static validator: `tools/av_validate.py`;
- base reproducibility tests: `tests/test_static_contract.py`;
- evaluation protocol: `EVALUATION_PROTOCOL.md`;
- results template: `RESULTS_TEMPLATE.csv`;
- unittest documentation: `UNITTEST.md`.

## Excluded

- private essay drafts;
- publication manuscript drafts;
- unpublished experiment results;
- private target packages;
- user data or credentials.

## Artifact claim boundary

The artifact is structurally valid if `python tools/av_validate.py .` passes.

The base reproducibility tests are valid if `python -m unittest discover -s tests -p 'test_*.py' -v` reports four passing tests.

Structural validity does not imply that an LLM agent has successfully executed the behavioral fixtures. Fixture execution results should be published separately with run logs, model identifiers, prompts, final state directories, and evaluation summaries.
