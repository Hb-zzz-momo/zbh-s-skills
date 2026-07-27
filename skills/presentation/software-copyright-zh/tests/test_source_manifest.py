from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import collect_source_manifest as manifest_tool  # noqa: E402
import propose_code_selection as proposal_tool  # noqa: E402


class SourceManifestTests(unittest.TestCase):
    def test_excludes_dependency_and_build_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            for folder in ("node_modules", ".venv", "dist", "build"):
                (root / folder).mkdir()
                (root / folder / "ignored.py").write_text("print('ignored')\n", encoding="utf-8")
            report = manifest_tool.collect_source_manifest(root)
            paths = {item["path"] for item in report["files"]}
            self.assertEqual(paths, {"src/main.py"})
            for folder in ("node_modules", ".venv", "dist", "build"):
                self.assertIn(folder, report["excluded_directories"])

    def test_counts_lf_crlf_and_cr_without_trailing_phantom_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = {
                "lf.py": b"one\ntwo\n",
                "crlf.py": b"one\r\ntwo\r\n",
                "cr.py": b"one\rtwo\r",
                "no-newline.py": b"one\ntwo",
                "empty.py": b"",
            }
            expected = {"lf.py": 2, "crlf.py": 2, "cr.py": 2, "no-newline.py": 2, "empty.py": 0}
            for name, data in cases.items():
                path = root / name
                path.write_bytes(data)
                self.assertEqual(manifest_tool.count_text_lines(path), expected[name], name)

    def test_recognizes_common_source_extensions(self) -> None:
        expected = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".vue": "Vue",
            ".java": "Java",
            ".c": "C",
            ".cpp": "C++",
            ".go": "Go",
        }
        for suffix, language in expected.items():
            with self.subTest(suffix=suffix):
                self.assertEqual(manifest_tool.language_for_path(Path("file" + suffix)), language)

    def test_calculates_and_verifies_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.py"
            data = b"print('hash')\n"
            path.write_bytes(data)
            expected = hashlib.sha256(data).hexdigest()
            self.assertEqual(manifest_tool.sha256_file(path), expected)
            self.assertTrue(manifest_tool.verify_sha256(path, expected))
            path.write_bytes(data + b"# changed\n")
            self.assertFalse(manifest_tool.verify_sha256(path, expected))

    def test_manifest_json_contains_required_traceability_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "service.py").write_text("def run():\n    return 1\n", encoding="utf-8")
            report = manifest_tool.collect_source_manifest(root)
            item = report["files"][0]
            self.assertTrue(
                {"path", "language", "line_count", "sha256", "category", "is_third_party", "selection_reason"}.issubset(item)
            )
            json.dumps(report, ensure_ascii=False)

    def test_manifest_cli_rejects_output_outside_project_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            outside = Path(outside_tmp) / "manifest.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "collect_source_manifest.py"),
                    str(root),
                    "--output",
                    str(outside),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertFalse(outside.exists())

    def test_count_cli_rejects_malformed_manifest_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"files": ["bad-shape"]}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "count_source_lines.py"),
                    str(root),
                    "--manifest",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_selection_cli_rejects_malformed_manifest_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"files": ["bad-shape"]}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "propose_code_selection.py"),
                    str(root),
                    "--manifest",
                    str(manifest),
                    "--json-output",
                    str(root / "selection.json"),
                    "--markdown-output",
                    str(root / "selection.md"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_selection_cli_rejects_malformed_evidence_map_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            evidence_map = root / "evidence-map.json"
            evidence_map.write_text(json.dumps({"features": ["bad-shape"]}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "propose_code_selection.py"),
                    str(root),
                    "--evidence-map",
                    str(evidence_map),
                    "--json-output",
                    str(root / "selection.json"),
                    "--markdown-output",
                    str(root / "selection.md"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_selection_uses_only_fixed_official_general_line_basis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "propose_code_selection.py"),
                    str(root),
                    "--json-output",
                    str(root / "selection.json"),
                    "--markdown-output",
                    str(root / "selection.md"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 1, completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["lines_per_page_basis"]["value"], 50)
            self.assertNotIn("--lines-per-page", subprocess.run(
                [sys.executable, str(SCRIPTS / "propose_code_selection.py"), "--help"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout)

    def test_selection_excludes_snapshots_generated_build_and_dependency_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = (
                ("tests/__snapshots__/page.snap.js", "component"),
                ("snapshots/saved.ts", "source"),
                ("dist/app.js", "entry"),
                ("node_modules/pkg/index.js", "entry"),
                ("src/client.generated.ts", "service"),
                ("package-lock.json", "source"),
                ("tests/test_service.py", "source"),
                ("src/service.py", "service"),
            )
            manifest = {
                "files": [
                    {
                        "path": path,
                        "language": "Python" if path.endswith(".py") else "JavaScript",
                        "line_count": 10,
                        "sha256": "0" * 64,
                        "category": category,
                        "is_third_party": False,
                    }
                    for path, category in paths
                ]
            }
            candidates = proposal_tool.build_candidates(root, manifest)
            by_path = {item["path"]: item for item in candidates}
            for path in (
                "tests/__snapshots__/page.snap.js",
                "snapshots/saved.ts",
                "dist/app.js",
                "node_modules/pkg/index.js",
                "src/client.generated.ts",
                "package-lock.json",
            ):
                self.assertEqual(by_path[path]["recommendation"], "excluded", path)
            self.assertEqual(by_path["tests/test_service.py"]["recommendation"], "consider")
            self.assertEqual(by_path["src/service.py"]["recommendation"], "recommended")


if __name__ == "__main__":
    unittest.main()
