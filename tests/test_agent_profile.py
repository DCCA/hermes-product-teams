from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "hermes" / "profile"


class AgentProfileTests(unittest.TestCase):
    def test_profile_package_contains_required_runtime_files(self) -> None:
        required_files = [
            "distribution.yaml",
            "README.md",
            "SOUL.md",
            "config.example.yaml",
            "workflows/capture-input.md",
            "workflows/weekly-brief.md",
            "workflows/review-prd-proposals.md",
            "workspace.example.yaml",
        ]
        for relative_path in required_files:
            self.assertTrue((PROFILE / relative_path).exists(), relative_path)

    def test_profile_artifact_contract_matches_workspace_scaffold(self) -> None:
        config = (PROFILE / "config.example.yaml").read_text(encoding="utf-8")
        workspace_contract = (PROFILE / "workspace.example.yaml").read_text(encoding="utf-8")
        skill = (ROOT / "hermes" / "skills" / "product-team-memory" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for artifact in [
            "Product Brief.md",
            "Discovery Notes",
            "Customer Insights.md",
            "Decision Log.md",
            "Open Questions.md",
            "PRD Update Proposals.md",
            "PRD.md",
            "Weekly Briefs",
        ]:
            self.assertIn(artifact, config)
            self.assertIn(artifact, workspace_contract)
            self.assertIn(artifact, skill)

    def test_profile_soul_defines_actual_agent_behavior(self) -> None:
        soul = (PROFILE / "SOUL.md").read_text(encoding="utf-8")

        required_phrases = [
            "Hermes Product Teams",
            "Discovery + Living Docs Agent",
            "source-linked evidence",
            "facts from assumptions",
            "PRD update proposals",
            "human approval",
            "Never silently edit source-of-truth docs",
            "Do not create tickets, send stakeholder messages, or change external systems",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, soul)

    def test_profile_install_script_copies_profile_and_skill_without_credentials(self) -> None:
        script = ROOT / "scripts" / "install_profile.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir) / "hermes-home"
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--hermes-home",
                    str(hermes_home),
                    "--workspace",
                    str(ROOT / "examples" / "workspace"),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            profile_root = hermes_home / "profiles" / "product-teams"
            self.assertTrue((profile_root / "config.yaml").exists())
            self.assertTrue((profile_root / "SOUL.md").exists())
            self.assertTrue((profile_root / "distribution.yaml").exists())
            self.assertFalse((profile_root / "system.md").exists())
            self.assertTrue((profile_root / "workflows" / "capture-input.md").exists())
            self.assertTrue(
                (profile_root / "skills" / "product-team-memory" / "SKILL.md").exists()
            )
            self.assertTrue((profile_root / "scripts" / "run_agent_capture.py").exists())
            self.assertTrue((profile_root / "scripts" / "run_weekly_brief.py").exists())

            config = (profile_root / "config.yaml").read_text(encoding="utf-8")
            self.assertIn(str(ROOT / "examples" / "workspace"), config)
            self.assertNotIn("API_KEY", config)
            self.assertNotIn("token:", config.lower())

            capture_result = subprocess.run(
                [
                    sys.executable,
                    str(profile_root / "scripts" / "run_agent_capture.py"),
                    "--input",
                    str(ROOT / "examples" / "inputs" / "001-customer-feedback-thread.md"),
                    "--dry-run",
                ],
                cwd=profile_root,
                check=True,
                text=True,
                capture_output=True,
            )
            weekly_result = subprocess.run(
                [
                    sys.executable,
                    str(profile_root / "scripts" / "run_weekly_brief.py"),
                    "--dry-run",
                ],
                cwd=profile_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn(str(ROOT / "examples" / "workspace"), capture_result.stdout)
            self.assertIn("Weekly Briefs", weekly_result.stdout)

            interview_result = subprocess.run(
                [
                    sys.executable,
                    str(profile_root / "scripts" / "run_agent_capture.py"),
                    "--input",
                    str(ROOT / "examples" / "inputs" / "002-user-interview-notes.md"),
                    "--dry-run",
                ],
                cwd=profile_root,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("Detected input class: User Interview", interview_result.stdout)
            self.assertIn("Interviewee role:", interview_result.stdout)
            self.assertIn("Goals:", interview_result.stdout)

    def test_custom_profile_install_renders_profile_name_into_config_and_runners(self) -> None:
        script = ROOT / "scripts" / "install_profile.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir) / "hermes-home"
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--hermes-home",
                    str(hermes_home),
                    "--workspace",
                    str(ROOT / "examples" / "workspace"),
                    "--profile-name",
                    "acme-product-memory",
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            profile_root = hermes_home / "profiles" / "acme-product-memory"
            config = (profile_root / "config.yaml").read_text(encoding="utf-8")
            self.assertIn('name: "acme-product-memory"', config)
            self.assertNotIn("name: product-teams", config)

            capture_result = subprocess.run(
                [
                    sys.executable,
                    str(profile_root / "scripts" / "run_agent_capture.py"),
                    "--input",
                    str(ROOT / "examples" / "inputs" / "001-customer-feedback-thread.md"),
                    "--dry-run",
                ],
                cwd=profile_root,
                check=True,
                text=True,
                capture_output=True,
            )
            weekly_result = subprocess.run(
                [
                    sys.executable,
                    str(profile_root / "scripts" / "run_weekly_brief.py"),
                    "--dry-run",
                ],
                cwd=profile_root,
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("--profile acme-product-memory", capture_result.stdout)
            self.assertNotIn("--profile product-teams", capture_result.stdout)
            self.assertIn("--profile acme-product-memory", weekly_result.stdout)

    def test_install_can_initialize_a_new_workspace_without_overwriting_existing_artifacts(self) -> None:
        script = ROOT / "scripts" / "install_profile.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            hermes_home = Path(tmpdir) / "hermes-home"
            workspace = Path(tmpdir) / "new-product-workspace"
            workspace.mkdir()
            existing_prd = workspace / "PRD.md"
            existing_prd.write_text("# Existing PRD\n\nKeep this content.\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--hermes-home",
                    str(hermes_home),
                    "--workspace",
                    str(workspace),
                    "--init-workspace",
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )

            self.assertIn("Initialized workspace scaffold", result.stdout)
            self.assertTrue((workspace / "Discovery Notes").is_dir())
            self.assertTrue((workspace / "Weekly Briefs").is_dir())
            for artifact in [
                "Product Brief.md",
                "Customer Insights.md",
                "Decision Log.md",
                "Open Questions.md",
                "PRD Update Proposals.md",
            ]:
                self.assertTrue((workspace / artifact).exists(), artifact)
            self.assertEqual(
                "# Existing PRD\n\nKeep this content.\n",
                existing_prd.read_text(encoding="utf-8"),
            )
            self.assertIn("Status: Proposed, not applied to `PRD.md`", (workspace / "PRD Update Proposals.md").read_text(encoding="utf-8"))

            second_result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--hermes-home",
                    str(hermes_home),
                    "--workspace",
                    str(workspace),
                    "--init-workspace",
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("no workspace files changed", second_result.stdout)

    def test_install_rejects_profile_names_that_are_not_safe_slugs(self) -> None:
        script = ROOT / "scripts" / "install_profile.py"
        unsafe_names = [
            "../escape-profile",
            "bad/name",
            'bad"name',
            "",
            "-starts-with-dash",
            "UppercaseName",
            "has.dot",
            "x" * 65,
        ]
        for unsafe_name in unsafe_names:
            with self.subTest(profile_name=unsafe_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    hermes_home = Path(tmpdir) / "hermes-home"
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(script),
                            "--hermes-home",
                            str(hermes_home),
                            "--workspace",
                            str(ROOT / "examples" / "workspace"),
                            f"--profile-name={unsafe_name}",
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                    )

                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("Hermes-compatible profile slug", result.stderr)
                    self.assertFalse((hermes_home / "escape-profile").exists())
                    self.assertFalse((Path(tmpdir) / "escape-profile").exists())

    def test_capture_command_builder_outputs_real_hermes_command(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_agent_capture.py",
                "--input",
                "examples/inputs/001-customer-feedback-thread.md",
                "--workspace",
                "examples/workspace",
                "--dry-run",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("hermes chat", result.stdout)
        self.assertIn("--profile product-teams", result.stdout)
        self.assertIn("product-team-memory", result.stdout)
        self.assertIn("examples/inputs/001-customer-feedback-thread.md", result.stdout)
        self.assertIn("examples/workspace", result.stdout)

    def test_weekly_brief_command_builder_outputs_real_hermes_command(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_weekly_brief.py",
                "--workspace",
                "examples/workspace",
                "--dry-run",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("hermes chat", result.stdout)
        self.assertIn("--profile product-teams", result.stdout)
        self.assertIn("product-team-memory", result.stdout)
        self.assertIn("examples/workspace", result.stdout)
        self.assertIn("weekly-brief.md", result.stdout)

    def test_interview_capture_command_builder_includes_interview_specific_instructions(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_agent_capture.py",
                "--input",
                "examples/inputs/002-user-interview-notes.md",
                "--workspace",
                "examples/workspace",
                "--dry-run",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("User Interview", result.stdout)
        self.assertIn("Interviewee role:", result.stdout)
        self.assertIn("Segment:", result.stdout)
        self.assertIn("Goals:", result.stdout)
        self.assertIn("Assumptions to validate", result.stdout)
        self.assertIn("Follow-up questions", result.stdout)


if __name__ == "__main__":
    unittest.main()
