# SKILLS.md

This bootstrap package defines four operator skills.

## Skill table

| Skill | Purpose | Input | Output |
|---|---|---|---|
| Plan | Convert the newest outstanding-issues file into an executable work ledger | `list-of-outstanding-issues-partN.txt`, `package.zip` | `works.json` |
| Apply | Execute all apply directives against the input package | `works.json`, `package.zip` | `packageVNext.zip` and optional companion zips |
| Verify | Check the candidate package against every verify directive and update work status | `packageVNext.zip`, `works.json` | updated `works.json` |
| Reflect | Repair unresolved works on the same candidate package and rerun verification until closure | `packageVNext.zip`, `works.json`, newest outstanding issues file | updated `works.json`, next issue file, same-version repaired `packageVNext.zip` |

---

## 1. Plan

### Inputs
- newest `list-of-outstanding-issues-partN.txt`
- target `package.zip`
- optional companion trace/spec zips
- target package files after unzip

### Output
- `works.json`

### Required output shape

`works.json` must be a JSON array of objects with exactly these required fields:

- `work_id`
- `apply-directive`
- `verify-directive`
- `done`

### Plan rules
1. Read the issue file and split it into atomic works.
2. One work may cover one issue or a tightly coupled issue cluster, but the work must still have one clear owner surface.
3. Each `apply-directive` must:
   - identify the file or files to change;
   - identify the authority-owner surface;
   - state the concrete modification;
   - state any required consistency propagation.
4. Each `verify-directive` must:
   - identify the expected changed state;
   - identify the exact validation command, file check, or schema check;
   - define closure criteria.
5. Set every `done` value to `false` in the initial Plan output.

---

## 2. Apply

### Inputs
- `works.json`
- input `package.zip`
- optional companion trace/spec zips

### Output
- `packageVNext.zip`
- optional regenerated companion zips

### Apply rules
1. Unzip the input package into a clean workspace.
2. Execute every `apply-directive` from `works.json`.
3. Apply must act on all works in the initial pass.
4. Preserve the target package naming/versioning policy when obvious.
5. If versioning is not obvious, emit a generic candidate named `packageVNext.zip`.
6. Regenerate companion trace/spec artifacts if the target package uses them.
7. Do not mark works as done. Only `Verify` may update `done`.

---

## 3. Verify

### Inputs
- `packageVNext.zip`
- optional companion zips
- `works.json`

### Output
- updated `works.json`

### Verify rules
1. Unzip `packageVNext.zip` into a clean workspace.
2. Run every `verify-directive` in `works.json`.
3. Update `done=true` only when the work's verify directive fully passes.
4. Update `done=false` when:
   - the verify directive fails;
   - the target package self-checks fail in a way relevant to that work;
   - the fix created a new contradiction for that work.
5. When the target package provides deterministic self-checks, run them.
6. When a target self-check is absent, report it as unrun and continue with file-based verification.
7. Verification must also check package tracing and governance surfaces when the target package defines them.

---

## 4. Reflect

### Inputs
- `packageVNext.zip`
- optional companion zips
- `works.json`
- newest `list-of-outstanding-issues-partN.txt`
- previous issue files, if available

### Output
- updated `works.json`
- next `list-of-outstanding-issues-partN+1.txt`
- same-version repaired `packageVNext.zip`

### Reflect rules
1. Read the updated `works.json`.
2. Write the next outstanding-issues file containing only:
   - works still unresolved;
   - newly discovered issues found during Verify;
   - regressions reopened by recent changes.
3. If the newest issue file is not empty, run another repair pass on the same candidate package.
4. Reflect must apply fixes only for works with `done=false` or for new issues written in the newest issue file.
5. Reflect must not bump the version.
6. After the repair pass, Reflect must call Verify again.
7. Repeat until:
   - every work is `done=true`; and
   - the newest issue file is zero-byte.

---

## Minimal design intent

This package deliberately stays small:
- two prompts;
- one issue-list family;
- one work ledger;
- four skills.

It is meant to be copied into a container chat and used as a zip-local repair loop, not as a full agent framework.
