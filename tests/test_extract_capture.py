from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

# Load the engine module directly (scripts/ is not a package).
spec = importlib.util.spec_from_file_location("extract_capture", SCRIPTS / "extract_capture.py")
assert spec and spec.loader
extract_capture = importlib.util.module_from_spec(spec)
sys.modules["extract_capture"] = extract_capture
spec.loader.exec_module(extract_capture)

SOURCE_101 = (ROOT / "examples" / "inputs" / "adversarial" / "101-noisy-slack-thread.md").read_text(
    encoding="utf-8"
)

# A plausible model reply for fixture 101: real verbatim spans plus one fabricated
# quote the engine must drop, and one paraphrase the linter would never accept.
FAKE_MODEL_REPLY = json.dumps(
    {
        "type": "Support Ticket Cluster",
        "title": "Export and pricing signals from #cust-feedback",
        "area": "Data Export / Pricing",
        "summary": "Several accounts surfaced export and pricing-clarity complaints in one thread.",
        "confidence": "medium",
        "facts": ["Acme has a recurring CSV complaint.", "A trial user churned over exports."],
        "assumptions": ["The CSV issue may be a reliability bug, not a format gap."],
        "evidence_quotes": [
            "they want SSO before renewal",
            "one wanted xlsx not csv",
            'exit survey said "couldn\'t get data out"',
            "Acme is definitely going to churn next quarter",  # fabricated, not in source
        ],
        "customer_signals": ["Acme (enterprise, renewal risk): recurring CSV complaint."],
        "decisions": [],
        "open_questions": ["Is this reliability, format, or pricing comms?"],
        "prd_suggestions": ["Propose XLSX export support."],
        "next_actions": ["Pull the Acme ticket and diagnose the CSV issue."],
        "priority": "High — enterprise renewal risk plus a churned trial.",
        "tags": ["#data-export", "#pricing"],
        "customer_insight": "Export reliability and format gaps are clustering across accounts.",
        "implication": "Export reliability likely outranks net-new format breadth.",
    }
)


class PromptTests(unittest.TestCase):
    def test_prompt_embeds_input_and_verbatim_contract(self) -> None:
        prompt = extract_capture.build_extraction_prompt("101", "Slack #cust-feedback", SOURCE_101)
        self.assertIn("acme corp complain about the csv thing", prompt)
        self.assertIn("NEVER invent customer evidence", prompt)
        self.assertIn("verbatim", prompt)
        self.assertIn("Support Ticket Cluster", prompt)  # taxonomy listed
        self.assertIn("BEGIN INPUT (101)", prompt)


class ParseTests(unittest.TestCase):
    def test_parses_bare_json(self) -> None:
        self.assertEqual(extract_capture.parse_model_json('{"a": 1}'), {"a": 1})

    def test_parses_fenced_json(self) -> None:
        raw = "Here you go:\n```json\n{\"a\": 1}\n```\nDone."
        self.assertEqual(extract_capture.parse_model_json(raw), {"a": 1})

    def test_parses_json_with_surrounding_prose(self) -> None:
        raw = 'Sure! {"a": 1, "b": [2]} hope that helps'
        self.assertEqual(extract_capture.parse_model_json(raw), {"a": 1, "b": [2]})

    def test_raises_on_non_json(self) -> None:
        with self.assertRaises(extract_capture.ExtractionError):
            extract_capture.parse_model_json("no json here")


class QuoteVerificationTests(unittest.TestCase):
    def test_keeps_verbatim_drops_fabricated(self) -> None:
        verified, fabricated = extract_capture.verify_quotes(
            ["one wanted xlsx not csv", "this was never said"], SOURCE_101
        )
        self.assertIn("one wanted xlsx not csv", verified)
        self.assertEqual(fabricated, ["this was never said"])

    def test_normalization_matches_curly_quotes_and_case(self) -> None:
        # Curly quotes / mixed case / collapsed whitespace still match verbatim source.
        source = 'The user said “Couldn\'t   get data out” today.'
        verified, fabricated = extract_capture.verify_quotes(['couldn\'t get data out'], source)
        self.assertEqual(len(verified), 1)
        self.assertEqual(fabricated, [])


class ProviderSelectionTests(unittest.TestCase):
    def test_explicit_provider_passes_through(self) -> None:
        self.assertEqual(extract_capture.select_provider("claude-cli"), "claude-cli")

    def test_auto_errors_when_nothing_available(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
            "extract_capture.shutil.which", return_value=None
        ):
            with self.assertRaises(extract_capture.ExtractionError):
                extract_capture.select_provider("auto")

    def test_auto_prefers_api_key(self) -> None:
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "x"}, clear=True):
            self.assertEqual(extract_capture.select_provider("auto"), "anthropic-api")


class EngineGuaranteeTests(unittest.TestCase):
    """The core guarantee: real engine output passes the trust linter, and the
    engine refuses to write fabricated/empty evidence."""

    def test_extract_drops_fabricated_quote(self) -> None:
        with mock.patch("extract_capture.run_model", return_value=FAKE_MODEL_REPLY):
            data, verified, fabricated = extract_capture.extract(
                "101-noisy-slack-thread",
                "examples/inputs/adversarial/101-noisy-slack-thread.md",
                SOURCE_101,
                provider="auto",
                model="x",
                timeout=1,
                date="2026-06-13",
            )
        self.assertEqual(data["type"], "Support Ticket Cluster")
        self.assertEqual(len(verified), 3)
        self.assertIn("Acme is definitely going to churn next quarter", fabricated)

    def test_extract_refuses_when_no_verbatim_evidence(self) -> None:
        reply = json.dumps({"type": "X", "evidence_quotes": ["entirely invented quote"]})
        with mock.patch("extract_capture.run_model", return_value=reply):
            with self.assertRaises(extract_capture.ExtractionError):
                extract_capture.extract(
                    "101-noisy-slack-thread",
                    "src",
                    SOURCE_101,
                    provider="auto",
                    model="x",
                    timeout=1,
                    date="2026-06-13",
                )

    def test_rendered_workspace_passes_trust_linter(self) -> None:
        with mock.patch("extract_capture.run_model", return_value=FAKE_MODEL_REPLY):
            data, verified, _ = extract_capture.extract(
                "101-noisy-slack-thread",
                "examples/inputs/adversarial/101-noisy-slack-thread.md",
                SOURCE_101,
                provider="auto",
                model="x",
                timeout=1,
                date="2026-06-13",
            )
        note = extract_capture.render_discovery_note(
            data, "101-noisy-slack-thread", "src", "2026-06-13", verified
        )
        blocks = extract_capture.render_shared_blocks(
            data, "101-noisy-slack-thread", "src", "2026-06-13", verified
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            (workspace / "Weekly Briefs").mkdir(parents=True)
            extract_capture.write_workspace(workspace, "101-noisy-slack-thread", note, blocks)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_workspace.py"),
                    "--workspace",
                    str(workspace),
                    "--inputs",
                    str(ROOT / "examples" / "inputs"),
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Evidence quotes verified against source inputs", result.stdout)


class DemoHonestyTests(unittest.TestCase):
    def test_deterministic_demo_refuses_adversarial_input(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "run_capture_demo.py"),
                "--input",
                "examples/inputs/adversarial/101-noisy-slack-thread.md",
                "--workspace",
                "/tmp/should-not-be-written",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot faithfully render", result.stderr)
        self.assertIn("extract_capture.py", result.stderr)


@unittest.skipUnless(
    os.environ.get("EXTRACT_CAPTURE_LIVE") == "1",
    "set EXTRACT_CAPTURE_LIVE=1 to run the real LLM end-to-end (needs a provider)",
)
class LiveEngineTests(unittest.TestCase):
    def test_live_engine_produces_verified_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            (workspace / "Weekly Briefs").mkdir(parents=True)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "extract_capture.py"),
                    "--input",
                    "examples/inputs/adversarial/101-noisy-slack-thread.md",
                    "--workspace",
                    str(workspace),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Verified", result.stdout)
            linter = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_workspace.py"),
                    "--workspace",
                    str(workspace),
                    "--inputs",
                    str(ROOT / "examples" / "inputs"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(linter.returncode, 0, linter.stdout + linter.stderr)


if __name__ == "__main__":
    unittest.main()
