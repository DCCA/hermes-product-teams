from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_eval_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_eval_harness", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EVAL = load_module()


class EvalHarnessTests(unittest.TestCase):
    def test_case_file_loads_five_golden_cases(self) -> None:
        cases = EVAL.load_cases(ROOT / "examples" / "evals" / "cases.json")
        self.assertEqual(5, len(cases))
        self.assertEqual("User Interview", cases[1].expected_type)
        self.assertIn("Interviewee role:", cases[1].required_note_strings)

    def test_clone_workspace_template_removes_generated_content_but_keeps_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            EVAL.clone_workspace_template(workspace)

            self.assertTrue((workspace / "Customer Insights.md").exists())
            self.assertTrue((workspace / "Decision Log.md").exists())
            self.assertTrue((workspace / "Open Questions.md").exists())
            self.assertTrue((workspace / "PRD Update Proposals.md").exists())
            self.assertTrue((workspace / "PRD.md").exists())
            self.assertTrue((workspace / "Discovery Notes").is_dir())
            self.assertTrue((workspace / "Weekly Briefs").is_dir())

            self.assertEqual([], list((workspace / "Discovery Notes").glob("*.generated.md")))
            self.assertEqual([], list((workspace / "Weekly Briefs").glob("*.generated.md")))

            customer_insights = (workspace / "Customer Insights.md").read_text(encoding="utf-8")
            self.assertIn("# Customer Insights", customer_insights)
            self.assertNotIn("<!-- generated:", customer_insights)

    def test_note_structure_check_requires_type_source_evidence_and_speculation(self) -> None:
        note = """# Example\n\nType: User Interview\nSource: sample\n\n## Evidence\n\n- Quote\n\n## Assumptions to validate\n\n- Unknown\n"""
        self.assertEqual(
            (True, True, True, True),
            EVAL.note_has_expected_structure(note, "User Interview"),
        )

    def test_markdown_report_includes_failure_output_for_failed_cases(self) -> None:
        failed_case = EVAL.CaseResult(
            case_id="failed-capture",
            input_path="examples/inputs/missing.md",
            command_ok=False,
            note_created=False,
            expected_type_found=False,
            source_line_found=False,
            evidence_section_found=False,
            speculative_section_found=False,
            required_note_strings_found=[],
            required_note_strings_missing=["Evidence:"],
            workspace_docs_touched=[],
            score=0,
            stdout_tail="stdout diagnostic",
            stderr_tail="hermes profile not found",
            note_path=None,
        )
        result = EVAL.HarnessResult(
            profile_name="product-teams-eval",
            hermes_home="/tmp/hermes-home",
            workspace="/tmp/workspace",
            model=None,
            provider=None,
            prompt_suffix=None,
            cases_passed=0,
            total_cases=1,
            weekly_brief_ok=False,
            workspace_check_ok=False,
            overall_score=0,
            weekly_brief_path=None,
            workspace_check_stdout="workspace diagnostic",
            workspace_check_stderr="workspace error",
            cases=[failed_case],
        )

        report = EVAL.format_markdown_report(result)

        self.assertIn("hermes profile not found", report)
        self.assertIn("stdout diagnostic", report)
        self.assertIn("workspace error", report)


if __name__ == "__main__":
    unittest.main()
