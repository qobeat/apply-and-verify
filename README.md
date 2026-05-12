# apply-and-verify bootstrap package

A minimal two-prompt bootstrap package for zip-local package repair loops.

This package intentionally keeps the control surface small:

- `FixPrompt.txt` owns **Plan + Apply**
- `ReflectionPrompt.txt` owns **Verify + Reflect**
- `list-of-outstanding-issues-part1.txt` is the mutable initial backlog
- `works.json` is the mutable execution ledger produced by `Plan`

The target package remains the authority for its own goal, objectives, glossary, topology, schemas, skills, and validation commands. These prompts must not restate or replace those authorities when the target package already defines them.

## Files

- `README.md` — package overview, usage, formats
- `SKILLS.md` — skill contracts for Plan / Apply / Verify / Reflect
- `FixPrompt.txt` — stable operator prompt for planning and applying fixes
- `ReflectionPrompt.txt` — stable operator prompt for verification and recursive reflection
- `list-of-outstanding-issues-part1.txt` — starter issue backlog template
- `works.json.example` — example Plan output ledger

## Design

This package uses a compact four-skill loop:

1. **Plan**  
   Read the newest outstanding-issues file and the target package.  
   Produce `works.json`.

2. **Apply**  
   Execute all `apply-directive` values from `works.json` against the input package zip.  
   Produce `packageVNext.zip`.  
   If the target package uses companion trace/spec zips, regenerate matching companions.

3. **Verify**  
   Unzip `packageVNext.zip`.  
   Run all `verify-directive` values from `works.json`.  
   Update the `done` field in `works.json`.  
   Also verify target-package self-checks, tracing, and governance-contract closure.

4. **Reflect**  
   If any work remains `done=false`, or if new defects are discovered, write the next
   `list-of-outstanding-issues-partN.txt`, call `FixPrompt.txt` again on the current
   candidate package, and rerun verification.  
   Reflect never bumps the version. It keeps repairing the same candidate package
   until all works are done and the newest issue list is empty.

## Input assumptions

The target package may be:
- one core zip only; or
- one core zip plus companion trace/spec zips.

The target package may expose helper commands or validators. Use them when present.
If a target validation command is absent, report it as unrun and continue with
file-based verification.

## Issue file format

`list-of-outstanding-issues-partN.txt` is plain text. Use one block per issue.

Required fields:

- `IssueID`
- `Severity`
- `Scope`
- `Problem`
- `Evidence`
- `RequiredFix`
- `Verify`

Recommended severity values:
- `critical`
- `high`
- `medium`
- `low`

The issue file should be atomic and operational. Each issue must be specific enough
for `Plan` to create one or more works with exact apply and verify directives.

## works.json format

`Plan` outputs `works.json`.

Minimum required format:

```json
[
  {
    "work_id": "W-001",
    "apply-directive": "Change the authority-owner file ...",
    "verify-directive": "Confirm the new field exists and target validations pass ...",
    "done": false
  }
]
```

Rules:
- `work_id` must be unique.
- `apply-directive` must tell the agent exactly what to change and where.
- `verify-directive` must state exact success criteria.
- `done` is boolean and is updated only by `Verify`.

## Usage

### First pass

Inputs:
- target `package.zip`
- optional `trace-package.zip`
- optional `spec-package.zip`
- `list-of-outstanding-issues-part1.txt`

Run `FixPrompt.txt`.

Outputs:
- `works.json`
- `packageVNext.zip`
- optional companion zips

Then run `ReflectionPrompt.txt` using:
- `packageVNext.zip`
- optional companion zips
- `works.json`
- the newest `list-of-outstanding-issues-partN.txt`

### Recursive passes

`ReflectionPrompt.txt` must:
1. verify all works;
2. write `list-of-outstanding-issues-partN+1.txt` containing only still-open or newly found issues;
3. call `FixPrompt.txt` again if any issue remains;
4. rerun itself until:
   - all `done` values are `true`; and
   - the newest issue file is zero-byte.

## Stop condition

Stop only when both are true:
1. `works.json` has no row with `done=false`;
2. the newest `list-of-outstanding-issues-partN.txt` is zero-byte.

## Design constraints

- Do not duplicate GOAL, OBJECTIVES, glossary, or schema rules already owned by the target package.
- Prefer changing the authority-owner file instead of patching dependent copies.
- Keep helper scripts mechanical if the target package has them.
- Do not promote generated evidence into normative package truth.
- Do not add unregistered static files to the target package.
- Preserve version naming used by the target package unless the target package itself requires a bump.
