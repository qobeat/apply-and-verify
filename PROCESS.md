# Process Contract

Apply & Verify Stage 1 is a finite-state process contract for LLM-agent artifact modification.

`PROCESS.json` is the canonical machine-readable source for states, transitions, guards, guarantees, and authority. This document is a human-readable projection of that contract.

## State classes

- **Active states**: agent executes a skill or control transition.
- **Paused states**: process waits for user input and must not continue autonomously.
- **Terminal states**: process is closed and must not continue unless a new run starts.

## Minimum real-product process

```text
START
  → INTAKE
  → BIND_PARAMETERS
  ├─ missing_or_ambiguous → ASK_QUESTIONS → WAIT_USER
  ├─ contradictory       → HALT_HUMAN_REQUIRED
  ├─ unsupported         → HALT_UNSUPPORTED
  └─ bound               → PLAN
  → APPLY
  ├─ apply_failed        → REFLECT
  └─ apply_completed     → VERIFY
  → VERIFY
  → REFLECT
  ├─ all_done            → HALT_SUCCESS
  ├─ open_issues         → PLAN
  ├─ repeated_failure    → HALT_NON_CONVERGENCE
  └─ high_risk           → HALT_HUMAN_REQUIRED
```

The `apply_failed → REFLECT` branch is intentional. `Apply` may report failure, but only `Reflect` may decide whether to loop, halt, or escalate.

## Transition field semantics

Each transition row in `PROCESS.json.transitions` contains three skill-related fields:

| Field | Meaning |
|---|---|
| `event_owner_skill` | Skill or actor allowed to emit the transition event. Values are declared skills plus `System` or `User`. |
| `next_skill` | Next skill to execute after the transition. It is `null` when the target state is paused or terminal. |
| `skill` | Deprecated compatibility alias kept for existing readers. For active target states it equals `next_skill`; for paused or terminal targets it equals `event_owner_skill`. |

New tooling should read `event_owner_skill` and `next_skill`. The legacy `skill` field remains only to preserve Stage-1 compatibility.

## Guarantees

The following text must match `PROCESS.json.guarantees` exactly.

| ID | Guarantee |
|---|---|
| G1 | No works are created while mandatory inputs are unbound. |
| G2 | No target or candidate mutation occurs before Plan. |
| G3 | Apply mutates only the candidate copy. |
| G4 | Only Verify may set done=true. |
| G5 | Every done=true has evidence. |
| G6 | Verify and Reflect do not mutate the candidate. |
| G7 | The run ends only in explicit terminal states or pauses at explicit paused states. |
| G8 | Repeated unresolved issue fingerprints force non-convergence halt. |

## Minimality rationale

The process is not claimed to be globally minimal for all agentic systems. It is minimum sufficient for the defined Stage-1 product: a real user may provide a natural request and a target package, and the process must avoid hidden assumptions, isolate mutation, verify evidence, and terminate or pause explicitly.

The four-skill loop is the kernel. The seven-skill process is the minimum real product.
