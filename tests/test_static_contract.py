"""Base reproducibility tests for apply-and-verify Stage 1.

Run from repository root:
    python -m unittest discover -s tests -p 'test_*.py' -v

These tests use only Python stdlib. They intentionally test static contract
workability, not LLM behavioral performance.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROCESS = ROOT / "PROCESS.json"
PROCESS_MD = ROOT / "PROCESS.md"
FIXTURES = ROOT / "tests" / "fixtures"


class ApplyVerifyStaticContractTests(unittest.TestCase):
    def load_json(self, path: pathlib.Path):
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def test_01_static_validator_passes(self) -> None:
        """The package validator must pass in a clean Python stdlib environment."""
        result = subprocess.run(
            [sys.executable, "tools/av_validate.py", "."],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn("VALIDATION PASSED", result.stdout)

    def test_02_process_md_guarantees_match_process_json(self) -> None:
        """Human-readable guarantees must textually match the canonical JSON contract."""
        process = self.load_json(PROCESS)
        md = PROCESS_MD.read_text(encoding="utf-8")
        for gid, guarantee in process["guarantees"].items():
            self.assertIn(f"| {gid} | {guarantee} |", md)

    def test_03_transition_semantics_are_explicit_and_consistent(self) -> None:
        """Transitions must expose event owner and next-skill semantics without ambiguity."""
        process = self.load_json(PROCESS)
        skills = set(process["skills"])
        active = set(process["state_classes"]["active"])
        paused = set(process["paused_states"])
        terminal = set(process["terminal_states"])
        allowed_owners = skills | {"System", "User"}
        seen_pairs = set()

        for transition in process["transitions"]:
            pair = (transition["from"], transition["event"])
            self.assertNotIn(pair, seen_pairs)
            seen_pairs.add(pair)
            self.assertIn(transition["event_owner_skill"], allowed_owners)
            dst = transition["to"]
            if dst in active:
                self.assertIn(transition["next_skill"], skills)
                self.assertEqual(transition["skill"], transition["next_skill"])
            elif dst in paused or dst in terminal:
                self.assertIsNone(transition["next_skill"])
            else:
                self.fail(f"Unknown transition target: {dst}")

    def test_04_fixture_inputs_and_acceptance_contracts_are_workable(self) -> None:
        """Fixtures must have requests, acceptance contracts, and target packages when required."""
        expected_states = {
            "F1-clean": "HALT_SUCCESS",
            "F2-ambiguous": "WAIT_USER",
            "F3-contradictory": "HALT_HUMAN_REQUIRED",
            "F4-verify-failure": "HALT_SUCCESS",
            "F5-non-convergence": "HALT_NON_CONVERGENCE",
            "F6-high-risk": "HALT_HUMAN_REQUIRED",
        }
        for fixture_id, expected_state in expected_states.items():
            base = FIXTURES / fixture_id
            self.assertTrue((base / "input" / "user-request.txt").is_file(), fixture_id)
            acceptance = self.load_json(base / "expected" / "acceptance.json")
            self.assertEqual(acceptance["fixture_id"], fixture_id)
            self.assertEqual(acceptance["expected_state"], expected_state)
            self.assertIn(acceptance["expected_state_class"], {"terminal", "paused", "active"})
            self.assertIsInstance(acceptance["acceptance_criteria"], dict)
            self.assertIsInstance(acceptance["minimum_observations"], dict)

            target = base / "input" / "target-package"
            if fixture_id == "F2-ambiguous":
                self.assertFalse(target.exists(), "F2 must remain target-less to test no-guess behavior")
            else:
                self.assertTrue(target.is_dir(), f"{fixture_id} needs a target package")
                self.assertTrue(any(p.is_file() for p in target.rglob("*")), f"{fixture_id} target package is empty")


if __name__ == "__main__":
    unittest.main(verbosity=2)
