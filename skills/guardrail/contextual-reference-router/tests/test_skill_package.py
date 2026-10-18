import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
SCRIPT = ROOT / "scripts" / "reference_router.py"


class SkillPackageTests(unittest.TestCase):
    def test_skill_frontmatter_is_minimal_and_body_is_compact(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        keys = [line.split(":", 1)[0].strip() for line in frontmatter.splitlines() if ":" in line]
        self.assertEqual(["name", "description"], keys)
        self.assertLessEqual(len(text.splitlines()), 500)

    def test_all_progressive_disclosure_files_exist_and_are_linked(self):
        skill_text = SKILL.read_text(encoding="utf-8")
        required = {
            "source-registry.md",
            "routing-matrix.md",
            "search-playbook.md",
            "reference-analysis-template.md",
            "quality-checklist.md",
        }
        for name in required:
            with self.subTest(name=name):
                self.assertTrue((ROOT / "references" / name).is_file())
                self.assertIn(f"references/{name}", skill_text)

    def test_source_registry_contains_every_plan_source(self):
        registry = (ROOT / "references" / "source-registry.md").read_text(encoding="utf-8")
        expected = {
            "Deck.gallery", "Behance", "SlideShare", "Pitch", "Dribbble", "Slidesgo",
            "Awwwards", "Mobbin", "Page Flows", "Land-book", "Lapa Ninja", "SiteInspire",
            "Recent.design", "Refero", "OpenAI", "Anthropic", "Cursor Directory",
            "Prompt Engineering Guide", "Fabric", "Cookbook", "ECharts", "From Data to Viz",
            "Observable", "D3 Gallery", "Flourish", "Datawrapper", "Data Viz Project",
            "BioRender", "AWS", "Azure", "Google Cloud", "Excalidraw", "Coolors",
            "Typewolf", "Iconify", "unDraw",
        }
        for name in expected:
            with self.subTest(name=name):
                self.assertIn(name, registry)
        self.assertEqual(6, registry.count("| 来源 | 域名 | 主要用途 | 适用任务 |"))

    def test_routing_matrix_documents_script_extensions(self):
        matrix = (ROOT / "references" / "routing-matrix.md").read_text(encoding="utf-8")
        self.assertIn("报告 / 汇报模板", matrix)
        self.assertIn("图标与插画系统", matrix)
        self.assertIn("Behance + SlideShare + Pitch", matrix)
        self.assertIn("Iconify + unDraw + Behance", matrix)

    def test_package_has_no_placeholders(self):
        excluded = {"__pycache__", "tests"}
        candidates = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and not any(part in excluded for part in path.parts)
            and path.suffix.lower() in {".md", ".py", ".yaml", ".json"}
        ]
        forbidden = ("TODO", "TBD", "PLACEHOLDER", "待补充", "尚未实现")
        for path in candidates:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                with self.subTest(path=str(path), token=token):
                    self.assertNotIn(token, text)

    def test_openai_metadata_invokes_skill_explicitly(self):
        metadata = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name:", metadata)
        self.assertIn("short_description:", metadata)
        self.assertIn("$contextual-reference-router", metadata)

    def test_cli_returns_nonzero_for_invalid_brief(self):
        invalid = {
            "task": {},
            "live_access": True,
            "sources": [],
            "rules": [],
            "applied_to_final": [],
            "limitations": [],
            "fact_observation_inference_separated": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.json"
            output = Path(directory) / "check.json"
            source.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(SCRIPT), "validate-brief", "--input", str(source), "--output", str(output)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(2, result.returncode)
            self.assertEqual("BLOCK", json.loads(output.read_text(encoding="utf-8"))["status"])


if __name__ == "__main__":
    unittest.main()
