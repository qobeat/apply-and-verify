# Skills

This file defines the seven skills required for the Stage-1 minimum real Apply & Verify product.

Each skill has a narrow authority boundary. Do not merge skills unless the merged skill preserves all authority constraints.

## Skill: Intake

**Purpose.** Normalize the raw user request into a stable, inspectable intake artifact.

**Input contract.**

- Raw user request text.
- Optional attached target package path or zip.
- Optional issue list path or inline issue list.

**Output contract.**

- `state/intake-result.json` matching `schemas/intake-result.schema.json`.
- One `events.jsonl` event with `event_type=intake_completed` or `event_type=unsupported_request`.

**Authority.**

- MAY create `state/intake-result.json`.
- MAY append to `state/events.jsonl`.
- MUST NOT create `state/works.json`.
- MUST NOT mutate the target package.
- MUST NOT mutate `state/candidate/`.

**Instruction.**

Read the raw request exactly. Normalize spelling and whitespace only when meaning is preserved. Extract intent type, action verbs, mentioned artifacts, and explicit constraints. Mark unsupported requests instead of forcing them into the package-repair flow.

**Success criteria.**

- Intake result exists and records the normalized request.
- Intent type is one of the schema enum values.
- No candidate or work registry is created by this skill.

## Skill: BindParameters

**Purpose.** Bind required execution parameters and detect missing, ambiguous, contradictory, or out-of-scope inputs before planning.

**Input contract.**

- `state/intake-result.json`.
- Raw request text.
- Available attachments or paths.
- Existing issue list if supplied.

**Output contract.**

- `state/parameter-bindings.json` matching `schemas/parameter-bindings.schema.json`.
- One event with one of: `parameters_bound`, `mandatory_inputs_unbound`, `contradictory_input`, `out_of_scope`.

**Authority.**

- MAY create/update `state/parameter-bindings.json`.
- MAY append to `state/events.jsonl`.
- MUST NOT create `state/works.json`.
- MUST NOT mutate the target package.
- MUST NOT mutate `state/candidate/`.

**Instruction.**

Bind at least these parameters: `target_package`, `requested_action`, `issue_source`, `mutation_boundary`, `output_package_name`, and `risk_policy`. Use explicit input first. Use context only when it is directly observable. Do not guess missing mandatory parameters. If inputs conflict, mark `contradictory`.

**Success criteria.**

- Every required parameter is present in the bindings list.
- Each required parameter has a status.
- Planning is allowed only when all mandatory parameters are `bound_explicit`, `bound_from_context`, `defaulted`, or `derived` with evidence.

## Skill: AskQuestions

**Purpose.** Ask the smallest set of user questions needed to unblock safe execution.

**Input contract.**

- `state/parameter-bindings.json` with at least one required parameter marked `missing`, `ambiguous`, or `contradictory`.

**Output contract.**

- `state/questions.json` matching `schemas/questions.schema.json`.
- `state/run-state.json` updated to `WAIT_USER`.
- One event with `event_type=questions_emitted`.

**Authority.**

- MAY create/update `state/questions.json`.
- MAY update `state/run-state.json` to `WAIT_USER`.
- MAY append to `state/events.jsonl`.
- MUST NOT create `state/works.json`.
- MUST NOT mutate the target package.
- MUST NOT mutate `state/candidate/`.

**Instruction.**

Ask only questions needed to bind mandatory parameters. Each question must name the parameter, expected answer format, and why it is required. Do not continue to `Plan` until the missing or ambiguous parameter is resolved.

**Success criteria.**

- Questions are specific and actionable.
- Run state is paused at `WAIT_USER`.
- No works or candidate are created.

## Skill: Plan

**Purpose.** Convert bound inputs and issue descriptions into atomic, verifiable work items.

**Input contract.**

- `state/intake-result.json`.
- `state/parameter-bindings.json` with all mandatory inputs bound.
- Issue list or review result.
- Target package inventory.

**Output contract.**

- `state/works.json` matching `schemas/works.schema.json`.
- One event with `event_type=works_planned`.

**Authority.**

- MAY create/update `state/works.json`.
- MAY append to `state/events.jsonl`.
- MUST NOT mutate candidate or target package.
- MUST NOT set `done=true` unless carrying forward a verified item from a previous run with evidence.

**Instruction.**

Create one or more work rows. Each row must include an exact `apply_directive`, exact `verify_directive`, `owner_surface`, `risk_level`, `done=false`, and empty `evidence_refs`. Split broad issues into atomic works. Mark high-risk changes but do not execute them.

**Success criteria.**

- Every work item is independently verifiable.
- Every work item has a concrete owner surface.
- No mutation occurs during planning.

## Skill: Apply

**Purpose.** Apply planned changes to an isolated candidate copy.

**Input contract.**

- `state/works.json` with at least one `done=false` row.
- Bound target package.
- Candidate path or permission to create `state/candidate/vN/`.

**Output contract.**

- Updated files under `state/candidate/vN/` only.
- One event per applied work with `event_type=work_applied` or `event_type=work_apply_failed`.

**Authority.**

- MAY create/update files under `state/candidate/vN/`.
- MAY append to `state/events.jsonl`.
- MUST NOT mutate the original target package.
- MUST NOT update `state/works.json` `done` field.
- MUST NOT write verification evidence as final truth.

**Instruction.**

Create a candidate copy before mutation. Execute each `apply_directive` literally. Keep changes minimal and limited to the owner surface unless the directive explicitly requires a dependent update. If a directive is unsafe or impossible, record failure and do not improvise.

**Success criteria.**

- Candidate exists when apply succeeds.
- Original target package remains unchanged.
- `done` fields remain unchanged after Apply.

## Skill: Verify

**Purpose.** Verify candidate changes against work-specific directives and collect evidence.

**Input contract.**

- `state/works.json`.
- `state/candidate/vN/`.
- Work-specific `verify_directive` values.
- Available package validation commands.

**Output contract.**

- Updated `state/works.json` with `done` and `evidence_refs` only.
- `state/verification-report.md`.
- One event per verified work with `event_type=work_verified` or `event_type=work_verification_failed`.

**Authority.**

- MAY update `state/works.json` fields `done` and `evidence_refs` only.
- MAY create/update `state/verification-report.md`.
- MAY append to `state/events.jsonl`.
- MUST NOT mutate the candidate.
- MUST NOT mutate the original target package.

**Instruction.**

Run each `verify_directive`. Use file checks, schema checks, command output, and package validators when available. A work item may be set `done=true` only when its verify directive passes and evidence is recorded.

**Success criteria.**

- Every `done=true` row has at least one evidence reference.
- Failed works remain `done=false`.
- Candidate content is unchanged by verification.

## Skill: Reflect

**Purpose.** Decide whether the run halts, loops, or requires human intervention.

**Input contract.**

- `state/works.json`.
- `state/verification-report.md`.
- `state/issues.partN.jsonl` if present.
- `state/events.jsonl`.
- `state/run-state.json`.

**Output contract.**

- Updated `state/run-state.json`.
- `state/issues.partN+1.jsonl` when new or still-open issues exist.
- `state/reflect-summary.iterN.md`.
- One event with one of: `halt_success`, `loop_required`, `non_converged`, `human_required`, `unsupported_halt`.

**Authority.**

- MAY update `state/run-state.json`.
- MAY create the next issue registry `state/issues.partN+1.jsonl`.
- MAY create `state/reflect-summary.iterN.md`.
- MAY append to `state/events.jsonl`.
- MUST NOT mutate the candidate.
- MUST NOT mutate the original target package.
- MUST NOT set `done=true`.

**Instruction.**

If all works are done and no open issues remain, halt success. If verification failed and iteration limits are not exceeded, create the next issue registry and loop to `Plan`. If the same issue fingerprint repeats beyond the limit, halt non-convergence. If risk exceeds the Stage-1 policy or input remains contradictory, halt human-required.

**Success criteria.**

- Run ends only in an explicit terminal state or pauses at `WAIT_USER`.
- Repeated issue fingerprints are detected.
- Reflect never mutates candidate content.
