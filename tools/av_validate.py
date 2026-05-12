#!/usr/bin/env python3
"""
av_validate.py — static contract validator for apply-and-verify Stage-1 packages.

This tool verifies structural consistency, example/schema coherence, and fixture
workability preconditions only. It does not run an LLM agent and it does not
prove that behavioral fixtures pass.

Usage:
    python tools/av_validate.py <package_dir>
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any, Dict, Iterable, List, Set, Tuple, Union

REQUIRED_SKILLS = [
    "Intake", "BindParameters", "AskQuestions", "Plan", "Apply", "Verify", "Reflect"
]

REQUIRED_SKILL_SECTIONS = [
    "Purpose", "Input contract", "Output contract", "Authority", "Instruction", "Success criteria"
]

REQUIRED_ROOT_FILES = [
    "README.md", "SKILLS.md", "FixPrompt.txt", "ReflectionPrompt.txt", "PROCESS.md", "PROCESS.json", "CHANGELOG.md", "EVALUATION_PROTOCOL.md", "RESULTS_TEMPLATE.csv", "UNITTEST.md"
]

REQUIRED_SCHEMAS = [
    "process.schema.json",
    "works.schema.json",
    "parameter-bindings.schema.json",
    "questions.schema.json",
    "issue.schema.json",
    "event.schema.json",
    "run-state.schema.json",
    "intake-result.schema.json",
    "fixture-acceptance.schema.json",
]

REQUIRED_FIXTURES = [
    "F1-clean", "F2-ambiguous", "F3-contradictory", "F4-verify-failure", "F5-non-convergence", "F6-high-risk"
]

REQUIRED_GUARDS = [
    "max_iterations",
    "repeat_issue_fingerprint_limit",
    "forbid_package_mutation_before_plan",
    "forbid_works_when_mandatory_inputs_unbound",
    "forbid_done_without_verification_evidence",
    "forbid_apply_mutation_outside_candidate",
    "forbid_done_set_by_non_verify_skill",
]

REQUIRED_GUARANTEES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
EXPECTED_TERMINALS = {"HALT_SUCCESS", "HALT_HUMAN_REQUIRED", "HALT_NON_CONVERGENCE", "HALT_UNSUPPORTED"}
EXPECTED_PAUSED = {"WAIT_USER"}


def load_json(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)




def json_type_ok(value: Any, expected: Union[str, List[str]]) -> bool:
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if t == "object" and isinstance(value, dict):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "string" and isinstance(value, str):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if t == "null" and value is None:
            return True
    return False


def validate_schema_subset(instance: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Validate a useful JSON Schema subset with stdlib only.

    Supported: type, required, additionalProperties=false, properties, items,
    enum, minLength, minItems, minimum, maximum, pattern. This intentionally
    avoids external dependencies so the validator is reproducible in a clean
    Python 3.11+ environment.
    """
    errors: List[str] = []
    expected_type = schema.get("type")
    if expected_type is not None and not json_type_ok(instance, expected_type):
        errors.append(f"{path}: expected type {expected_type}, got {type(instance).__name__}")
        return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: string does not match pattern {schema['pattern']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: number below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: number above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: array shorter than minItems {schema['minItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(instance):
                errors.extend(validate_schema_subset(item, item_schema, f"{path}[{i}]"))

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required key {key}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: unexpected key {key}")
        for key, subschema in props.items():
            if key in instance and isinstance(subschema, dict):
                errors.extend(validate_schema_subset(instance[key], subschema, f"{path}.{key}"))
    return errors


def check_schema_instance(label: str, instance_path: pathlib.Path, schema_path: pathlib.Path, errors: List[str]) -> None:
    try:
        instance = load_json(instance_path)
        schema = load_json(schema_path)
        validation_errors = validate_schema_subset(instance, schema)
        check(label, not validation_errors, errors, "; ".join(validation_errors[:5]))
    except Exception as e:
        check(label, False, errors, str(e))


def check(label: str, condition: bool, errors: List[str], detail: str = "") -> None:
    if condition:
        print(f"  [OK]   {label}")
    else:
        msg = label + (f" — {detail}" if detail else "")
        print(f"  [FAIL] {msg}")
        errors.append(msg)


def object_has_required_keys(obj: Dict[str, Any], keys: Iterable[str]) -> Tuple[bool, str]:
    missing = [k for k in keys if k not in obj]
    return (not missing, "missing: " + ", ".join(missing) if missing else "")


def extract_skill_block(text: str, skill: str) -> str:
    m = re.search(rf"^## Skill: {re.escape(skill)}\b(.*?)(?=^## Skill: |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def check_required_files(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[1/10] Required root files")
    for name in REQUIRED_ROOT_FILES:
        check(f"file exists: {name}", (pkg / name).is_file(), errors)


def check_skills(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[2/10] SKILLS.md")
    path = pkg / "SKILLS.md"
    if not path.exists():
        check("SKILLS.md exists", False, errors)
        return
    text = path.read_text(encoding="utf-8")
    for skill in REQUIRED_SKILLS:
        block = extract_skill_block(text, skill)
        check(f"skill declared: {skill}", bool(block), errors)
        if block:
            for section in REQUIRED_SKILL_SECTIONS:
                check(f"  {skill} section: {section}", f"**{section}.**" in block or f"**{section}**" in block, errors)


def check_process(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[3/10] PROCESS.json")
    path = pkg / "PROCESS.json"
    try:
        process = load_json(path)
        check("PROCESS.json parses", True, errors)
        check_schema_instance("PROCESS.json validates against schemas/process.schema.json", path, pkg / "schemas" / "process.schema.json", errors)
    except Exception as e:
        check("PROCESS.json parses", False, errors, str(e))
        return

    required = ["process_id", "version", "start_state", "states", "paused_states", "terminal_states", "skills", "guards", "guarantees", "authority_matrix", "transitions", "transition_field_semantics"]
    ok, detail = object_has_required_keys(process, required)
    check("PROCESS.json required top-level keys", ok, errors, detail)

    states: Set[str] = set(process.get("states", []))
    paused: Set[str] = set(process.get("paused_states", []))
    terminals: Set[str] = set(process.get("terminal_states", []))
    skills: Set[str] = set(process.get("skills", []))

    check("start_state == START", process.get("start_state") == "START", errors)
    check("START is declared in states", "START" in states, errors)
    check("terminal states equal expected", terminals == EXPECTED_TERMINALS, errors, f"got {sorted(terminals)}")
    check("paused states equal expected", paused == EXPECTED_PAUSED, errors, f"got {sorted(paused)}")
    check("paused and terminal states are disjoint", not (paused & terminals), errors, f"overlap {sorted(paused & terminals)}")
    check("skills equal expected", skills == set(REQUIRED_SKILLS), errors, f"got {sorted(skills)}")

    guards = process.get("guards", {})
    for guard in REQUIRED_GUARDS:
        check(f"guard declared: {guard}", guard in guards, errors)
    check("max_iterations positive integer", isinstance(guards.get("max_iterations"), int) and guards.get("max_iterations") >= 1, errors)
    check("repeat_issue_fingerprint_limit positive integer", isinstance(guards.get("repeat_issue_fingerprint_limit"), int) and guards.get("repeat_issue_fingerprint_limit") >= 1, errors)

    guarantees = process.get("guarantees", {})
    for gid in REQUIRED_GUARANTEES:
        check(f"guarantee declared: {gid}", gid in guarantees, errors)

    authority = process.get("authority_matrix", {})
    for skill in REQUIRED_SKILLS:
        check(f"authority declared: {skill}", skill in authority, errors)

    transitions = process.get("transitions", [])
    check("transitions is non-empty list", isinstance(transitions, list) and len(transitions) > 0, errors)
    seen_pairs = set()
    from_states = set()
    to_states = set()
    for idx, t in enumerate(transitions):
        ok, detail = object_has_required_keys(t, ["from", "event", "to", "skill", "event_owner_skill", "next_skill"])
        check(f"transition {idx} required keys", ok, errors, detail)
        if not ok:
            continue
        src, event, dst, skill = t["from"], t["event"], t["to"], t["skill"]
        owner = t.get("event_owner_skill")
        next_skill = t.get("next_skill")
        check(f"transition {idx} source declared", src in states, errors, src)
        check(f"transition {idx} target declared", dst in states, errors, dst)
        check(f"transition {idx} legacy skill declared", skill in skills, errors, skill)
        check(f"transition {idx} event_owner_skill declared", owner in skills or owner in {"System", "User"}, errors, str(owner))
        if dst in states - terminals - paused:
            check(f"transition {idx} next_skill declared for active target", next_skill in skills, errors, str(next_skill))
            check(f"transition {idx} legacy skill equals next_skill", skill == next_skill, errors, f"skill={skill}, next_skill={next_skill}")
        else:
            check(f"transition {idx} next_skill is null for paused/terminal target", next_skill is None, errors, str(next_skill))
        pair = (src, event)
        check(f"transition deterministic pair {src}/{event}", pair not in seen_pairs, errors)
        seen_pairs.add(pair)
        from_states.add(src)
        to_states.add(dst)

    check("terminal states have no outgoing transitions", not (terminals & from_states), errors, f"violators {sorted(terminals & from_states)}")
    active_nonterminal = states - terminals - paused
    missing_outgoing = active_nonterminal - from_states
    check("every active non-terminal has outgoing transition", not missing_outgoing, errors, f"missing {sorted(missing_outgoing)}")
    unreachable = states - to_states - {process.get("start_state")}
    check("every non-start state reachable", not unreachable, errors, f"unreachable {sorted(unreachable)}")


def check_schemas(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[4/10] schemas/")
    schema_dir = pkg / "schemas"
    check("schemas directory exists", schema_dir.is_dir(), errors)
    for name in REQUIRED_SCHEMAS:
        path = schema_dir / name
        check(f"schema present: {name}", path.is_file(), errors)
        if path.exists():
            try:
                data = load_json(path)
                check(f"  {name} parses", True, errors)
                check(f"  {name} has $schema", "$schema" in data, errors)
                check(f"  {name} has title", "title" in data, errors)
            except Exception as e:
                check(f"  {name} parses", False, errors, str(e))


def check_examples(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[5/10] examples/")
    examples = [
        "user-request.example.txt", "works.example.json", "parameter-bindings.example.json",
        "questions.example.json", "intake-result.example.json"
    ]
    edir = pkg / "examples"
    check("examples directory exists", edir.is_dir(), errors)
    for name in examples:
        path = edir / name
        check(f"example present: {name}", path.is_file(), errors)
        if path.suffix == ".json" and path.exists():
            try:
                load_json(path)
                check(f"  {name} parses", True, errors)
            except Exception as e:
                check(f"  {name} parses", False, errors, str(e))

    schema_map = {
        "works.example.json": "works.schema.json",
        "parameter-bindings.example.json": "parameter-bindings.schema.json",
        "questions.example.json": "questions.schema.json",
        "intake-result.example.json": "intake-result.schema.json",
    }
    for example_name, schema_name in schema_map.items():
        example_path = edir / example_name
        if example_path.exists():
            check_schema_instance(f"  {example_name} validates against {schema_name}", example_path, pkg / "schemas" / schema_name, errors)

    # Lightweight semantic checks for canonical examples.
    works = edir / "works.example.json"
    if works.exists():
        try:
            rows = load_json(works)
            check("works.example.json is list", isinstance(rows, list), errors)
            for row in rows if isinstance(rows, list) else []:
                ok, detail = object_has_required_keys(row, ["work_id", "owner_surface", "apply_directive", "verify_directive", "risk_level", "done", "evidence_refs"])
                check(f"  work row has required keys: {row.get('work_id', '?')}", ok, errors, detail)
        except Exception:
            pass


def check_fixtures(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[6/10] tests/fixtures/")
    fdir = pkg / "tests" / "fixtures"
    check("fixtures directory exists", fdir.is_dir(), errors)
    for fid in REQUIRED_FIXTURES:
        base = fdir / fid
        check(f"fixture present: {fid}", base.is_dir(), errors)
        check(f"  {fid}/input/user-request.txt exists", (base / "input" / "user-request.txt").is_file(), errors)
        accept_path = base / "expected" / "acceptance.json"
        check(f"  {fid}/expected/acceptance.json exists", accept_path.is_file(), errors)
        if accept_path.exists():
            try:
                acc = load_json(accept_path)
                check(f"  {fid}/acceptance parses", True, errors)
                check_schema_instance(f"  {fid}/acceptance validates against fixture-acceptance.schema.json", accept_path, pkg / "schemas" / "fixture-acceptance.schema.json", errors)
                ok, detail = object_has_required_keys(acc, ["fixture_id", "description", "expected_state", "expected_state_class", "acceptance_criteria", "minimum_observations"])
                check(f"  {fid}/acceptance required keys", ok, errors, detail)
                expected_state = acc.get("expected_state")
                state_class = acc.get("expected_state_class")
                if state_class == "terminal":
                    check(f"  {fid} terminal expected state is declared terminal", expected_state in EXPECTED_TERMINALS, errors, str(expected_state))
                if state_class == "paused":
                    check(f"  {fid} paused expected state is declared paused", expected_state in EXPECTED_PAUSED, errors, str(expected_state))
                target_dir = base / "input" / "target-package"
                if fid == "F2-ambiguous":
                    check(f"  {fid} intentionally has no target-package input", not target_dir.exists(), errors)
                else:
                    target_files = list(target_dir.rglob("*")) if target_dir.exists() else []
                    check(f"  {fid}/input/target-package has files", target_dir.is_dir() and any(x.is_file() for x in target_files), errors)
            except Exception as e:
                check(f"  {fid}/acceptance parses", False, errors, str(e))


def check_prompts(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[7/10] prompts")
    for name in ["FixPrompt.txt", "ReflectionPrompt.txt"]:
        path = pkg / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            check(f"{name} mentions PROCESS.json", "PROCESS.json" in text, errors)
            check(f"{name} mentions SKILLS.md", "SKILLS.md" in text, errors)
            check(f"{name} forbids target mutation or candidate mutation where appropriate", "MUST" in text or "must" in text, errors)


def check_no_private_essay(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[8/10] public repo hygiene")
    forbidden_patterns = ["essay", "рукоп", "эссе", "manuscript_v", "publication_pack"]
    offenders = []
    for path in pkg.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(pkg)).lower()
            if any(p in rel for p in forbidden_patterns):
                offenders.append(str(path.relative_to(pkg)))
    check("no essay/manuscript draft files included", not offenders, errors, ", ".join(offenders))



def check_process_md_alignment(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[10/10] PROCESS.md alignment")
    md_path = pkg / "PROCESS.md"
    process_path = pkg / "PROCESS.json"
    if not md_path.exists() or not process_path.exists():
        check("PROCESS.md and PROCESS.json exist for alignment check", False, errors)
        return
    text = md_path.read_text(encoding="utf-8")
    process = load_json(process_path)
    for gid, guarantee in process.get("guarantees", {}).items():
        check(f"PROCESS.md guarantee text matches {gid}", f"| {gid} | {guarantee} |" in text, errors)
    check("PROCESS.md documents transition field semantics", "event_owner_skill" in text and "next_skill" in text, errors)


def check_artifact_docs(pkg: pathlib.Path, errors: List[str]) -> None:
    print("\n[9/10] artifact docs")
    for name in ["ARTIFACT.md", "CODE_AVAILABILITY.md"]:
        check(f"{name} exists", (pkg / name).is_file(), errors)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: av_validate.py <package_dir>")
        return 2
    pkg = pathlib.Path(sys.argv[1]).resolve()
    if not pkg.is_dir():
        print(f"error: package directory not found: {pkg}")
        return 2

    print(f"Validating apply-and-verify Stage-1 package at: {pkg}")
    errors: List[str] = []

    check_required_files(pkg, errors)
    check_skills(pkg, errors)
    check_process(pkg, errors)
    check_schemas(pkg, errors)
    check_examples(pkg, errors)
    check_fixtures(pkg, errors)
    check_prompts(pkg, errors)
    check_no_private_essay(pkg, errors)
    check_artifact_docs(pkg, errors)
    check_process_md_alignment(pkg, errors)

    print()
    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("VALIDATION PASSED — package is structurally valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
