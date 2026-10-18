from __future__ import annotations

import json
import hashlib
import base64
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import analyze_project  # noqa: E402
import check_environment as environment_tool  # noqa: E402


class ProjectAnalysisTests(unittest.TestCase):
    def make_mixed_project(self, root: Path) -> None:
        (root / "frontend" / "src").mkdir(parents=True)
        (root / "backend").mkdir()
        (root / "native").mkdir()
        (root / "java" / "src").mkdir(parents=True)
        (root / "go").mkdir()
        (root / "package.json").write_text(
            json.dumps({"dependencies": {"react": "test", "vue": "test"}}),
            encoding="utf-8",
        )
        (root / "requirements.txt").write_text("Flask\nDjango\nfastapi\n", encoding="utf-8")
        (root / "pom.xml").write_text(
            "<artifactId>spring-boot-starter-web</artifactId>", encoding="utf-8"
        )
        (root / "frontend" / "src" / "index.js").write_text("export const value = 1;\n", encoding="utf-8")
        (root / "frontend" / "src" / "main.ts").write_text("const value: number = 1;\n", encoding="utf-8")
        (root / "frontend" / "src" / "Page.vue").write_text("<template><main /></template>\n", encoding="utf-8")
        (root / "frontend" / "src" / "App.tsx").write_text("export const App = () => <main />;\n", encoding="utf-8")
        (root / "backend" / "app.py").write_text(
            "from flask import Flask\nfrom fastapi import FastAPI\napp = FastAPI()\n@app.get('/items')\ndef items(): return []\n",
            encoding="utf-8",
        )
        (root / "backend" / "settings.py").write_text("INSTALLED_APPS = []\n", encoding="utf-8")
        (root / "java" / "src" / "Application.java").write_text(
            "@SpringBootApplication public class Application {}\n", encoding="utf-8"
        )
        (root / "native" / "engine.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
        (root / "native" / "engine.cpp").write_text("int compute() { return 1; }\n", encoding="utf-8")
        (root / "go" / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")

    def test_detects_required_languages_frameworks_and_split_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_mixed_project(root)
            report = analyze_project.analyze_project(root)
            detected = set(report["technology_stack"])
            expected = {
                "Python",
                "JavaScript",
                "TypeScript",
                "Vue",
                "React",
                "Flask",
                "Django",
                "FastAPI",
                "Java",
                "Spring Boot",
                "C/C++",
                "Go",
            }
            self.assertTrue(expected.issubset(detected), expected - detected)
            self.assertEqual(report["project_layout"], "frontend-backend-separated")
            self.assertFalse(report["business_inference_performed"])
            self.assertIn("/items", report["api_endpoints"])

    def test_unknown_stack_degrades_to_generic_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("unknown stack", encoding="utf-8")
            report = analyze_project.analyze_project(root)
            self.assertEqual(report["status"], "CAUTION")
            self.assertEqual(report["detection_mode"], "generic")

    def test_mode_c_readiness_writes_exact_reports_and_blocks_without_runtime_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "analyze_project.py"), str(root), "--readiness"],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 2, completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["readiness"]["status"], "BLOCK")
            report_root = root / "软件著作权申请资料" / "04-校验报告"
            self.assertTrue((report_root / "readiness-report.json").is_file())
            self.assertTrue((report_root / "readiness-report.md").is_file())
            self.assertFalse(payload["readiness"]["formal_generation_authorized"])

    def test_mode_c_readiness_can_reach_ready_only_with_real_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            (root / "test_app.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")
            (root / "README.md").write_text("Run with python app.py", encoding="utf-8")
            (root / "LICENSE").write_text("Synthetic test license", encoding="utf-8")
            evidence_dir = root / "runtime-evidence"
            evidence_dir.mkdir()
            for name in ("startup.log", "flow.log", "tests.log"):
                (evidence_dir / name).write_text("verified synthetic test evidence", encoding="utf-8")
            screenshot_dir = root / "软件著作权申请资料" / "02-截图" / "images"
            screenshot_dir.mkdir(parents=True)
            (screenshot_dir / "screen.png").write_bytes(
                base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
            )
            runtime = {
                "schema_version": 1,
                "software_identity": {
                    "software_name": "示例业务系统",
                    "version": "V1.0",
                    "user_confirmed": True,
                },
                "checks": [
                    {
                        "kind": kind,
                        "command": command,
                        "cwd": ".",
                        "started_at": "2026-07-12T12:00:00Z",
                        "finished_at": "2026-07-12T12:00:01Z",
                        "passed": True,
                        "exit_code": 0,
                        "evidence_paths": [f"runtime-evidence/{name}"],
                        "evidence_sha256": {
                            f"runtime-evidence/{name}": hashlib.sha256((evidence_dir / name).read_bytes()).hexdigest()
                        },
                    }
                    for kind, command, name in (
                        ("startup", "python app.py", "startup.log"),
                        ("core-flow", "verified core flow", "flow.log"),
                        ("test", "python -m unittest", "tests.log"),
                    )
                ],
            }
            runtime_path = root / "runtime-evidence.json"
            runtime_path.write_text(json.dumps(runtime, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "analyze_project.py"),
                    str(root),
                    "--readiness",
                    "--runtime-evidence",
                    str(runtime_path),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["readiness"]["status"], "READY")
            self.assertEqual(payload["readiness"]["summary"]["runtime_checks"], 3)

    def test_soft_copyright_routing_and_structure_gate_contract(self) -> None:
        skills_root = SKILL_ROOT.parents[1]
        routing_texts = [
            (skills_root / "SKILL_ROUTING.zh-CN.md").read_text(encoding="utf-8"),
            (skills_root / "guardrail" / "skill-router-zh" / "SKILL.md").read_text(encoding="utf-8"),
        ]
        expected_route = "→ project-structure-architect\n→ engineering-skill-flow-zh\n→ software-copyright-zh"
        for text in routing_texts:
            self.assertIn(expected_route, text)
            self.assertNotIn("engineering-skill-flow-zh / project-dev-zh", text)
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(skill_text.index("project-structure-architect"), skill_text.index("--initialize"))

    def test_environment_initializes_resumable_output_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            command = [sys.executable, str(SCRIPTS / "check_environment.py"), str(root), "--initialize"]
            completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
            self.assertIn(completed.returncode, (0, 1), completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertIn(payload["status"], ("PASS", "CAUTION"))
            material_root = root / "软件著作权申请资料"
            self.assertTrue((material_root / "workflow-state.json").is_file())
            self.assertTrue((material_root / "00-项目证据" / "environment-check.json").is_file())
            state = json.loads((material_root / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(
                state["stages"]["environment"]["evidence"],
                ["00-项目证据/environment-check.json"],
            )
            for folder in ("00-项目证据", "01-草稿", "02-截图/images", "03-正式资料", "04-校验报告"):
                self.assertTrue((material_root / folder).is_dir(), folder)

    def test_environment_rejects_material_root_outside_project_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            outside = Path(outside_tmp) / "materials"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_environment.py"),
                    str(root),
                    "--initialize",
                    "--material-root",
                    str(outside),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertFalse(outside.exists())

    def test_environment_preserves_corrupt_workflow_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root = root / "软件著作权申请资料"
            material_root.mkdir()
            evidence_dir = material_root / "00-项目证据"
            evidence_dir.mkdir()
            project_analysis = evidence_dir / "project-analysis.json"
            project_analysis.write_text('{"status":"PASS"}', encoding="utf-8")
            report_dir = material_root / "04-校验报告"
            report_dir.mkdir()
            for name in ("render-report.md", "consistency-report.md", "provenance-report.md"):
                (report_dir / name).write_text("status: PASS\n", encoding="utf-8")
            state = material_root / "workflow-state.json"
            original = "{broken-state"
            state.write_text(original, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_environment.py"),
                    str(root),
                    "--initialize",
                    "--mode",
                    "B",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "CAUTION")
            self.assertIn("WORKFLOW_STATE_RECOVERED", {item["rule_id"] for item in payload["findings"]})

            recovered = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(recovered["mode"], "B")
            self.assertEqual(recovered["stages"]["project"]["status"], "caution")
            self.assertEqual(
                recovered["stages"]["project"]["evidence"],
                ["00-项目证据/project-analysis.json"],
            )
            self.assertEqual(recovered["stages"]["render-validation"]["status"], "caution")
            self.assertEqual(
                recovered["stages"]["render-validation"]["evidence"],
                [
                    "04-校验报告/consistency-report.md",
                    "04-校验报告/provenance-report.md",
                    "04-校验报告/render-report.md",
                ],
            )
            self.assertTrue(all(value is False for value in recovered["confirmations"].values()))
            self.assertFalse(recovered["formal_generation_authorized"])

            backups = list((material_root / "04-校验报告").glob("workflow-state.corrupt-*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)
            original_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
            self.assertIn(original_hash, backups[0].name)
            report = json.loads(
                (material_root / "04-校验报告" / "workflow-recovery-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["original_sha256"], original_hash)
            self.assertTrue(report["all_user_confirmations_reset"])
            self.assertFalse(report["formal_generation_authorized"])

    def test_environment_rejects_malformed_nested_workflow_state_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root = root / "软件著作权申请资料"
            material_root.mkdir()
            state = material_root / "workflow-state.json"
            state.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "mode": "A",
                        "stages": {"environment": ["bad-shape"]},
                        "confirmations": {},
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_environment.py"), str(root), "--initialize"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(json.loads(completed.stdout)["status"], "CAUTION")
            recovered = json.loads(state.read_text(encoding="utf-8"))
            self.assertTrue(all(value is False for value in recovered["confirmations"].values()))
            self.assertFalse(recovered["formal_generation_authorized"])
            self.assertNotIn("Traceback", completed.stderr)

    def test_environment_recovers_minimal_well_typed_state_with_missing_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = str(SCRIPTS / "check_environment.py")
            initialized = subprocess.run(
                [sys.executable, script, str(root), "--initialize", "--mode", "A"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout)
            material_root = root / "软件著作权申请资料"
            state_path = material_root / "workflow-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["stages"].pop("environment")
            original = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
            state_path.write_text(original, encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, script, str(root), "--initialize", "--mode", "A"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "CAUTION")
            self.assertIn("WORKFLOW_STATE_RECOVERED", {item["rule_id"] for item in payload["findings"]})
            self.assertNotIn("Traceback", completed.stderr)

            recovered = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(recovered["stages"]), 11)
            self.assertEqual(len(recovered["confirmations"]), 6)
            self.assertEqual(recovered["stages"]["environment"]["status"], "pass")
            backups = list((material_root / "04-校验报告").glob("workflow-state.corrupt-*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), original)

    def test_workflow_state_contract_requires_exact_confirmations_and_top_level_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state = environment_tool.make_workflow_state(Path(tmp), "A")
            self.assertIs(environment_tool.validate_workflow_state(state), state)

            missing_confirmation = json.loads(json.dumps(state))
            missing_confirmation["confirmations"].pop("business")
            with self.assertRaisesRegex(ValueError, "exactly 6 keys"):
                environment_tool.validate_workflow_state(missing_confirmation)

            extra_confirmation = json.loads(json.dumps(state))
            extra_confirmation["confirmations"]["unexpected"] = False
            with self.assertRaisesRegex(ValueError, "exactly 6 keys"):
                environment_tool.validate_workflow_state(extra_confirmation)

            missing_top_level = json.loads(json.dumps(state))
            missing_top_level.pop("updated_at")
            with self.assertRaisesRegex(ValueError, "missing required top-level keys"):
                environment_tool.validate_workflow_state(missing_top_level)

            wrong_type = json.loads(json.dumps(state))
            wrong_type["formal_generation_authorized"] = 0
            with self.assertRaisesRegex(ValueError, "must be a boolean"):
                environment_tool.validate_workflow_state(wrong_type)

    def test_workflow_state_rejects_stage_jumps_and_invalid_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = environment_tool.make_workflow_state(root, "A")
            state["stages"]["business"]["status"] = "pass"
            state["stages"]["business"]["evidence"] = ["01-草稿/业务理解.json"]
            with self.assertRaisesRegex(ValueError, "stage order"):
                environment_tool.validate_workflow_state(state)

            state = environment_tool.make_workflow_state(root, "A")
            state["current_stage"] = "business"
            with self.assertRaisesRegex(ValueError, "first incomplete"):
                environment_tool.validate_workflow_state(state)

            state = environment_tool.make_workflow_state(root, "A")
            state["updated_at"] = "not-a-time"
            with self.assertRaisesRegex(ValueError, "ISO-8601"):
                environment_tool.validate_workflow_state(state)

    def test_stage_transition_cli_advances_in_order_and_invalidates_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = str(SCRIPTS / "check_environment.py")
            initialized = subprocess.run(
                [sys.executable, script, str(root), "--initialize", "--mode", "A"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout)
            material_root = root / "软件著作权申请资料"
            evidence = material_root / "00-项目证据"
            for name in ("project-analysis.json", "source-manifest.json", "source-line-count.json"):
                (evidence / name).write_text('{"status":"PASS"}', encoding="utf-8")
            project_evidence = [
                "00-项目证据/project-analysis.json",
                "00-项目证据/source-manifest.json",
                "00-项目证据/source-line-count.json",
            ]
            advanced = subprocess.run(
                [
                    sys.executable,
                    script,
                    str(root),
                    "--advance-stage",
                    "project",
                    "--confirm",
                    *[part for path in project_evidence for part in ("--evidence", path)],
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(advanced.returncode, 0, advanced.stdout)
            state = json.loads((material_root / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "readiness")
            self.assertTrue(state["confirmations"]["project"])
            jumped = subprocess.run(
                [sys.executable, script, str(root), "--advance-stage", "business", "--confirm"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(jumped.returncode, 3)
            invalidated = subprocess.run(
                [sys.executable, script, str(root), "--invalidate-from", "project"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(invalidated.returncode, 0, invalidated.stdout)
            state = json.loads((material_root / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_stage"], "project")
            self.assertFalse(state["confirmations"]["project"])

    def test_runtime_receipt_requires_test_hash_time_and_bound_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "startup.log"
            log.write_text("ok", encoding="utf-8")
            runtime = {
                "schema_version": 1,
                "checks": [
                    {
                        "kind": "startup",
                        "command": "python app.py",
                        "cwd": ".",
                        "started_at": "2026-07-12T12:00:00Z",
                        "finished_at": "2026-07-12T12:00:01Z",
                        "passed": True,
                        "exit_code": 0,
                        "evidence_paths": ["startup.log"],
                        "evidence_sha256": {"startup.log": "0" * 64},
                    }
                ],
            }
            _, findings = analyze_project.validate_runtime_evidence(root, runtime)
            rules = {item["rule_id"] for item in findings}
            self.assertIn("RUNTIME_EVIDENCE_HASH_MISMATCH", rules)
            self.assertIn("RUNTIME_EVIDENCE_INCOMPLETE", rules)

    def test_analyzer_rejects_malformed_nested_package_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                json.dumps({"dependencies": ["bad-shape"]}), encoding="utf-8"
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "analyze_project.py"), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_environment_fills_empty_mode_but_blocks_mode_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = str(SCRIPTS / "check_environment.py")
            first = subprocess.run(
                [sys.executable, script, str(root), "--initialize"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(first.returncode, 0)
            second = subprocess.run(
                [sys.executable, script, str(root), "--initialize", "--mode", "C"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(second.returncode, 0, second.stdout)
            state_path = root / "软件著作权申请资料" / "workflow-state.json"
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["mode"], "C")
            conflicting = subprocess.run(
                [sys.executable, script, str(root), "--initialize", "--mode", "A"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(conflicting.returncode, 3)
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["mode"], "C")

    def test_small_project_analysis_stage_runs_through_real_clis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_mixed_project(root)
            outputs = root / "software-material-test"
            outputs.mkdir()
            analysis = outputs / "project-analysis.json"
            manifest = outputs / "source-manifest.json"
            selection = outputs / "selection.json"
            selection_md = outputs / "selection.md"
            commands = [
                [sys.executable, str(SCRIPTS / "analyze_project.py"), str(root), "--output", str(analysis)],
                [sys.executable, str(SCRIPTS / "collect_source_manifest.py"), str(root), "--output", str(manifest)],
                [sys.executable, str(SCRIPTS / "count_source_lines.py"), str(root), "--manifest", str(manifest)],
                [
                    sys.executable,
                    str(SCRIPTS / "propose_code_selection.py"),
                    str(root),
                    "--manifest",
                    str(manifest),
                    "--json-output",
                    str(selection),
                    "--markdown-output",
                    str(selection_md),
                ],
            ]
            for command in commands:
                completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
                self.assertIn(completed.returncode, (0, 1), completed.stderr or completed.stdout)
                self.assertIsInstance(json.loads(completed.stdout), dict)
            for path in (analysis, manifest, selection, selection_md):
                self.assertTrue(path.is_file(), path)

    def test_all_public_clis_expose_help(self) -> None:
        names = (
            "check_environment.py",
            "analyze_project.py",
            "collect_source_manifest.py",
            "count_source_lines.py",
            "propose_code_selection.py",
            "validate_application_fields.py",
            "validate_consistency.py",
            "validate_outputs.py",
        )
        forced_legacy_environment = os.environ.copy()
        forced_legacy_environment["PYTHONIOENCODING"] = "cp1252"
        for name in names:
            with self.subTest(name=name):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPTS / name), "--help"],
                    capture_output=True,
                    env=forced_legacy_environment,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                help_text = completed.stdout.decode("utf-8")
                self.assertIn("usage", help_text.lower())
                self.assertNotIn("--analysis", help_text if name == "propose_code_selection.py" else "")

        utf8_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    f"sys.path.insert(0, {str(SCRIPTS)!r}); "
                    "from collect_source_manifest import JsonArgumentParser; "
                    "JsonArgumentParser(description='中文帮助').parse_args(['--help'])"
                ),
            ],
            capture_output=True,
            env=forced_legacy_environment,
        )
        self.assertEqual(utf8_probe.returncode, 0, utf8_probe.stderr)
        self.assertIn("中文帮助", utf8_probe.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
