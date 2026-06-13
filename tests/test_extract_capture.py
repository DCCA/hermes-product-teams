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


# A plausible split reply for fixture 101: four distinct topics. One keeps a real
# quote but also proposes a fabricated one (must be dropped within the topic); one
# topic has only a fabricated quote (whole topic must be reported as dropped, not
# silently merged away).
FAKE_SPLIT_REPLY = json.dumps(
    {
        "topics": [
            {
                "topic": "CSV export reliability",
                "type": "Support Ticket Cluster",
                "title": "Acme CSV export complaint",
                "evidence_quotes": [
                    "acme corp complain about the csv thing again",
                    "ticket from them this morning",
                ],
                "customer_insight": "Acme keeps hitting a recurring CSV export problem.",
                "implication": "Export reliability is a renewal risk for Acme.",
            },
            {
                "topic": "SSO before renewal",
                "type": "Customer Feedback / Roadmap Signal",
                "title": "Acme wants SSO before renewing",
                "evidence_quotes": [
                    "they want SSO before renewal",
                    "renewal will absolutely not happen without it",  # fabricated
                ],
            },
            {
                "topic": "Pricing comms confusion",
                "type": "Customer Feedback / Roadmap Signal",
                "title": "Starter-tier analytics confusion",
                "evidence_quotes": ["thought analytics was included in starter"],
            },
            {
                "topic": "Imaginary mobile request",
                "type": "Customer Feedback / Roadmap Signal",
                "title": "Mobile app ask",
                "evidence_quotes": ["customer asked for a native mobile app"],  # fabricated
            },
        ]
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


class SplitTests(unittest.TestCase):
    """UC-206: split a noisy multi-topic input into distinct, source-traced notes."""

    def test_split_prompt_asks_for_topics_and_verbatim_contract(self) -> None:
        prompt = extract_capture.build_split_prompt("101", "Slack #cust-feedback", SOURCE_101)
        self.assertIn('"topics"', prompt)
        self.assertIn("MULTI-TOPIC", prompt)
        self.assertIn("do NOT silently drop", prompt)
        self.assertIn("verbatim", prompt)
        self.assertIn("acme corp complain about the csv thing", prompt)  # input embedded

    def test_parse_split_handles_object_list_and_fence(self) -> None:
        self.assertEqual(
            extract_capture.parse_split_json('{"topics": [{"topic": "a"}, {"topic": "b"}]}'),
            [{"topic": "a"}, {"topic": "b"}],
        )
        self.assertEqual(
            extract_capture.parse_split_json('[{"topic": "a"}]'), [{"topic": "a"}]
        )
        fenced = "ok:\n```json\n{\"topics\": [{\"topic\": \"a\"}]}\n```\n"
        self.assertEqual(extract_capture.parse_split_json(fenced), [{"topic": "a"}])
        # A single object (model ignored the array) is tolerated as one topic.
        self.assertEqual(extract_capture.parse_split_json('{"topic": "solo"}'), [{"topic": "solo"}])

    def test_topic_slug_kebabs_and_falls_back(self) -> None:
        self.assertEqual(extract_capture.topic_slug("CSV export reliability!", 1), "csv-export-reliability")
        self.assertEqual(extract_capture.topic_slug("", 3), "topic-3")

    def test_extract_split_keeps_evidenced_topics_and_reports_dropped(self) -> None:
        with mock.patch("extract_capture.run_model", return_value=FAKE_SPLIT_REPLY):
            kept, dropped = extract_capture.extract_split(
                "101-noisy-slack-thread",
                "examples/inputs/adversarial/101-noisy-slack-thread.md",
                SOURCE_101,
                provider="auto",
                model="x",
                timeout=1,
                date="2026-06-13",
            )
        kept_topics = [e["topic"] for e in kept]
        self.assertEqual(len(kept), 3)
        self.assertIn("CSV export reliability", kept_topics)
        self.assertIn("SSO before renewal", kept_topics)
        self.assertIn("Pricing comms confusion", kept_topics)
        # Distinct slugs per topic so notes/blocks don't collide.
        self.assertEqual(len({e["topic_slug"] for e in kept}), 3)
        # The fabricated quote inside the kept SSO topic was dropped, real one kept.
        sso = next(e for e in kept if e["topic"] == "SSO before renewal")
        self.assertEqual(sso["verified"], ["they want SSO before renewal"])
        self.assertEqual(len(sso["fabricated"]), 1)
        # The all-fabricated topic is surfaced as dropped, not silently merged away.
        self.assertEqual([e["topic"] for e in dropped], ["Imaginary mobile request"])

    def test_extract_split_refuses_when_no_topic_verifies(self) -> None:
        reply = json.dumps({"topics": [{"topic": "x", "evidence_quotes": ["never said this"]}]})
        with mock.patch("extract_capture.run_model", return_value=reply):
            with self.assertRaises(extract_capture.ExtractionError):
                extract_capture.extract_split(
                    "101", "src", SOURCE_101,
                    provider="auto", model="x", timeout=1, date="2026-06-13",
                )

    def test_split_workspace_passes_trust_linter(self) -> None:
        with mock.patch("extract_capture.run_model", return_value=FAKE_SPLIT_REPLY):
            kept, dropped = extract_capture.extract_split(
                "101-noisy-slack-thread",
                "examples/inputs/adversarial/101-noisy-slack-thread.md",
                SOURCE_101,
                provider="auto", model="x", timeout=1, date="2026-06-13",
            )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            (workspace / "Weekly Briefs").mkdir(parents=True)
            rc = extract_capture._write_split(
                workspace, "101-noisy-slack-thread",
                "examples/inputs/adversarial/101-noisy-slack-thread.md",
                "2026-06-13", kept, dropped,
            )
            self.assertEqual(rc, 0)
            notes = list((workspace / "Discovery Notes").glob("*.generated.md"))
            self.assertEqual(len(notes), 3)  # one note per kept topic
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / "check_workspace.py"),
                    "--workspace", str(workspace),
                    "--inputs", str(ROOT / "examples" / "inputs"),
                ],
                capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


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

    def test_live_split_produces_multiple_verified_notes(self) -> None:
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
                    "--split",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            notes = list((workspace / "Discovery Notes").glob("*.generated.md"))
            # The whole point of UC-206: the noisy thread splits into >1 topic.
            self.assertGreater(len(notes), 1, result.stdout)
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

    def test_live_wave1_fixtures_capture_and_verify(self) -> None:
        # UC-201 (sales/CS call) and UC-202 (churn/exit feedback): each realistic
        # messy fixture must capture through the real engine with verbatim-verified
        # evidence and pass the trust linter.
        for fixture in ("201-sales-call-feedback", "202-churn-exit-feedback"):
            with self.subTest(fixture=fixture):
                with tempfile.TemporaryDirectory() as tmp:
                    workspace = Path(tmp) / "workspace"
                    (workspace / "Weekly Briefs").mkdir(parents=True)
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPTS / "extract_capture.py"),
                            "--input",
                            f"examples/inputs/{fixture}.md",
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
